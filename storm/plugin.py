# -*- coding: utf-8 -*-
"""
WindAgent 插件系统核心
支持动态加载、命令注册、钩子机制
"""

import os
import sys
import json
import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from functools import wraps


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str = ""
    author: str = ""
    main: str = "__init__.py"
    commands: List[str] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    enabled: bool = True
    config_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigField:
    """配置字段"""
    key: str
    label: str
    type: str = "text"
    default: Any = None
    required: bool = False
    placeholder: str = ""
    options: List[str] = field(default_factory=list)


class PluginBase:
    """插件基类"""
    
    name: str = "unknown"
    version: str = "0.0.0"
    description: str = ""
    author: str = ""
    icon: str = "📦"
    
    config_fields: List[ConfigField] = []
    
    def __init__(self, manager: 'PluginManager' = None):
        self.manager = manager
        self.logger = logging.getLogger(f"plugin.{self.name}")
        self._commands: Dict[str, Callable] = {}
        self._tools: Dict[str, Callable] = {}
        self._hooks: Dict[str, Callable] = {}
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "fields": [
                {
                    "key": f.key,
                    "label": f.label,
                    "type": f.type,
                    "default": f.default,
                    "required": f.required,
                    "placeholder": f.placeholder,
                    "options": f.options
                }
                for f in self.config_fields
            ]
        }
    
    def on_load(self):
        """插件加载时调用"""
        pass
    
    def on_unload(self):
        """插件卸载时调用"""
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取插件配置"""
        if self.manager:
            return self.manager.get_plugin_config(self.name, key, default)
        return default
    
    def set_config(self, key: str, value: Any):
        """设置插件配置"""
        if self.manager:
            self.manager.set_plugin_config(self.name, key, value)
    
    def register_command(self, name: str, func: Callable, help_text: str = ""):
        """注册命令"""
        self._commands[name] = {
            "func": func,
            "help": help_text
        }
    
    def register_tool(self, name: str, func: Callable, description: str = "", plugin_name: str = ""):
        """注册工具"""
        self._tools[name] = {
            "func": func,
            "description": description,
            "plugin": plugin_name or self.name
        }
    
    def register_hook(self, event: str, func: Callable):
        """注册钩子"""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(func)


def command(name: str, help: str = "", aliases: List[str] = None):
    """命令装饰器"""
    def decorator(func):
        func._is_command = True
        func._command_name = name
        func._command_help = help
        func._command_aliases = aliases or []
        return func
    return decorator


def tool(name: str, description: str = ""):
    """工具装饰器"""
    def decorator(func):
        func._is_tool = True
        func._tool_name = name
        func._tool_description = description
        return func
    return decorator


def hook(event: str):
    """钩子装饰器"""
    def decorator(func):
        func._is_hook = True
        func._hook_event = event
        return func
    return decorator


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_dir: str = None):
        self.plugin_dir = plugin_dir or os.path.join(os.path.dirname(__file__), "builtin")
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_info: Dict[str, PluginInfo] = {}
        self.commands: Dict[str, Dict] = {}
        self.tools: Dict[str, Dict] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.configs: Dict[str, Dict] = {}
        
        self.logger = logging.getLogger("plugin.manager")
        
        self.config_file = os.path.join(os.path.dirname(__file__), "..", "data", "plugin_configs.json")
        self._load_configs()
    
    def _load_configs(self):
        """从配置文件加载插件配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.configs = json.load(f)
        except Exception as e:
            self.logger.warning(f"加载插件配置失败: {e}")
            self.configs = {}
    
    def _save_configs(self):
        """保存插件配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.configs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存插件配置失败: {e}")
    
    def get_plugin_config(self, plugin_name: str, key: str = None, default: Any = None) -> Any:
        """获取插件配置"""
        plugin_configs = self.configs.get(plugin_name, {})
        if key:
            return plugin_configs.get(key, default)
        return plugin_configs
    
    def set_plugin_config(self, plugin_name: str, key: str, value: Any):
        """设置插件配置"""
        if plugin_name not in self.configs:
            self.configs[plugin_name] = {}
        self.configs[plugin_name][key] = value
        self._save_configs()
    
    def discover_plugins(self) -> List[str]:
        """发现可用插件"""
        discovered = []
        
        plugin_dirs = [
            self.plugin_dir,
            os.path.join(os.path.dirname(self.plugin_dir), "plugins"),
            os.path.join(os.path.dirname(self.plugin_dir), "..", "plugins")
        ]
        
        for plugin_dir in plugin_dirs:
            if os.path.exists(plugin_dir):
                for item in os.listdir(plugin_dir):
                    plugin_path = os.path.join(plugin_dir, item)
                    
                    if os.path.isdir(plugin_path):
                        init_file = os.path.join(plugin_path, "__init__.py")
                        if os.path.exists(init_file):
                            discovered.append(item)
                    
                    elif item.endswith(".py") and item != "__init__.py":
                        discovered.append(item[:-3])
        
        return discovered
    
    def load_plugin(self, name: str) -> bool:
        """加载插件"""
        if name in self.plugins:
            self.logger.warning(f"插件 {name} 已加载")
            return True
        
        plugin_dirs = [
            self.plugin_dir,
            os.path.join(os.path.dirname(self.plugin_dir), "plugins"),
            os.path.join(os.path.dirname(self.plugin_dir), "..", "plugins")
        ]
        
        plugin_path = None
        for pd in plugin_dirs:
            test_path = os.path.join(pd, name)
            if os.path.isdir(test_path) and os.path.exists(os.path.join(test_path, "__init__.py")):
                plugin_path = test_path
                break
            elif os.path.exists(f"{test_path}.py"):
                plugin_path = f"{test_path}.py"
                break
        
        if not plugin_path:
            self.logger.error(f"无法找到插件 {name}")
            return False
        
        try:
            if os.path.isdir(plugin_path):
                spec = importlib.util.spec_from_file_location(
                    name, 
                    os.path.join(plugin_path, "__init__.py")
                )
            else:
                spec = importlib.util.spec_from_file_location(
                    name,
                    plugin_path
                )
            
            if not spec or not spec.loader:
                self.logger.error(f"无法加载插件 {name}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugins.{name}"] = module
            spec.loader.exec_module(module)
            
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if inspect.isclass(attr) and issubclass(attr, PluginBase) and attr != PluginBase:
                    plugin_class = attr
                    break
            
            if not plugin_class:
                if hasattr(module, 'plugin'):
                    plugin_class = module.plugin
                else:
                    self.logger.error(f"插件 {name} 未找到插件类")
                    return False
            
            plugin_instance = plugin_class(self)
            
            self._register_plugin(plugin_instance)
            
            plugin_instance.on_load()
            
            self.plugins[name] = plugin_instance
            self.logger.info(f"插件 {name} 加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"加载插件 {name} 失败: {e}")
            return False
    
    def _register_plugin(self, plugin: PluginBase):
        """注册插件的命令、工具和钩子"""
        for attr_name in dir(plugin):
            attr = getattr(plugin, attr_name)
            
            if hasattr(attr, '_is_command'):
                cmd_name = attr._command_name
                self.commands[cmd_name] = {
                    "func": attr,
                    "plugin": plugin.name,
                    "help": attr._command_help,
                    "aliases": attr._command_aliases
                }
                
                for alias in attr._command_aliases:
                    self.commands[alias] = self.commands[cmd_name]
            
            if hasattr(attr, '_is_tool'):
                tool_name = attr._tool_name
                self.tools[tool_name] = {
                    "func": attr,
                    "plugin": plugin.name,
                    "description": attr._tool_description
                }
            
            if hasattr(attr, '_is_hook'):
                event = attr._hook_event
                if event not in self.hooks:
                    self.hooks[event] = []
                self.hooks[event].append(attr)
    
    def unload_plugin(self, name: str) -> bool:
        """卸载插件"""
        if name not in self.plugins:
            self.logger.warning(f"插件 {name} 未加载")
            return False
        
        try:
            plugin = self.plugins[name]
            plugin.on_unload()
            
            for cmd_name, cmd_info in list(self.commands.items()):
                if cmd_info["plugin"] == name:
                    del self.commands[cmd_name]
            
            for tool_name, tool_info in list(self.tools.items()):
                if tool_info["plugin"] == name:
                    del self.tools[tool_name]
            
            for event, hooks in self.hooks.items():
                self.hooks[event] = [h for h in hooks if h.__self__.name != name]
            
            del self.plugins[name]
            
            if f"plugins.{name}" in sys.modules:
                del sys.modules[f"plugins.{name}"]
            
            self.logger.info(f"插件 {name} 已卸载")
            return True
            
        except Exception as e:
            self.logger.error(f"卸载插件 {name} 失败: {e}")
            return False
    
    def reload_plugin(self, name: str) -> bool:
        """重载插件"""
        if self.unload_plugin(name):
            return self.load_plugin(name)
        return False
    
    def load_all(self):
        """加载所有插件"""
        from cloud.config import get_config_manager
        
        config_manager = get_config_manager()
        disabled_plugins = config_manager.config.plugin.disabled_plugins
        
        discovered = self.discover_plugins()
        for name in discovered:
            if name in disabled_plugins:
                self.logger.info(f"插件 {name} 已禁用，跳过加载")
                continue
            self.load_plugin(name)
    
    def execute_command(self, name: str, args: str = "") -> Any:
        """执行命令"""
        if name not in self.commands:
            return f"未知命令: {name}"
        
        cmd_info = self.commands[name]
        try:
            return cmd_info["func"](args)
        except Exception as e:
            self.logger.error(f"执行命令 {name} 失败: {e}")
            return f"执行命令失败: {e}"
    
    def execute_tool(self, name: str, **kwargs) -> Any:
        """执行工具"""
        if name not in self.tools:
            return f"未知工具: {name}"
        
        tool_info = self.tools[name]
        try:
            return tool_info["func"](**kwargs)
        except Exception as e:
            self.logger.error(f"执行工具 {name} 失败: {e}")
            return f"执行工具失败: {e}"
    
    def trigger_hook(self, event: str, *args, **kwargs) -> List[Any]:
        """触发钩子"""
        results = []
        if event in self.hooks:
            for hook_func in self.hooks[event]:
                try:
                    result = hook_func(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"钩子 {event} 执行失败: {e}")
        return results
    
    def get_plugin_config(self, plugin_name: str, key: str, default: Any = None) -> Any:
        """获取插件配置"""
        if plugin_name not in self.configs:
            self.configs[plugin_name] = {}
        return self.configs[plugin_name].get(key, default)
    
    def set_plugin_config(self, plugin_name: str, key: str, value: Any):
        """设置插件配置"""
        if plugin_name not in self.configs:
            self.configs[plugin_name] = {}
        self.configs[plugin_name][key] = value
    
    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        from cloud.config import get_config_manager
        
        config_manager = get_config_manager()
        disabled_plugins = config_manager.config.plugin.disabled_plugins
        
        result = []
        discovered = self.discover_plugins()
        
        for name in discovered:
            if name in self.plugins:
                plugin = self.plugins[name]
                possible_paths = [
                    os.path.join(self.plugin_dir, name),
                    os.path.join(self.plugin_dir, f"{name}.py"),
                    os.path.join(os.path.dirname(self.plugin_dir), "plugins", name),
                    os.path.join(os.path.dirname(self.plugin_dir), "plugins", f"{name}.py"),
                    os.path.join(os.path.dirname(self.plugin_dir), "..", "plugins", name),
                    os.path.join(os.path.dirname(self.plugin_dir), "..", "plugins", f"{name}.py"),
                ]
                
                path = ""
                for p in possible_paths:
                    if os.path.exists(p):
                        path = p
                        break
                
                result.append({
                    "name": plugin.name,
                    "version": plugin.version,
                    "description": plugin.description,
                    "author": plugin.author,
                    "icon": getattr(plugin, 'icon', '📦'),
                    "enabled": name not in disabled_plugins,
                    "path": path
                })
            else:
                possible_paths = [
                    os.path.join(self.plugin_dir, name),
                    os.path.join(self.plugin_dir, f"{name}.py"),
                    os.path.join(os.path.dirname(self.plugin_dir), "plugins", name),
                    os.path.join(os.path.dirname(self.plugin_dir), "plugins", f"{name}.py"),
                    os.path.join(os.path.dirname(self.plugin_dir), "..", "plugins", name),
                    os.path.join(os.path.dirname(self.plugin_dir), "..", "plugins", f"{name}.py"),
                ]
                
                path = ""
                for p in possible_paths:
                    if os.path.exists(p):
                        path = p
                        break
                
                result.append({
                    "name": name,
                    "version": "unknown",
                    "description": "已禁用的插件",
                    "author": "unknown",
                    "icon": "📦",
                    "enabled": False,
                    "path": path
                })
        
        return result
    
    def get_commands_help(self) -> str:
        """获取命令帮助"""
        help_text = "可用命令:\n"
        for name, info in self.commands.items():
            if name == info.get("_command_name", name):
                help_text += f"  /{name} - {info['help']}\n"
        return help_text


_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取插件管理器"""
    global _plugin_manager
    if not _plugin_manager:
        _plugin_manager = PluginManager()
    return _plugin_manager
