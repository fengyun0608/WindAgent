# -*- coding: utf-8 -*-
"""
平台管理器 - 动态加载平台适配器
"""

import os
import sys
import importlib
import logging
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass, field


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


class PlatformAdapter:
    """平台适配器基类"""
    
    name: str = "unknown"
    description: str = ""
    icon: str = "📱"
    
    config_fields: List[ConfigField] = []
    
    def __init__(self, agent, config: Dict[str, Any] = None):
        self.agent = agent
        self.config = config or {}
        self.running = False
        self.logger = logging.getLogger(f"platform.{self.name}")
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
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
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def start(self):
        """启动适配器"""
        raise NotImplementedError
    
    def stop(self):
        """停止适配器"""
        raise NotImplementedError
    
    def is_running(self) -> bool:
        """检查是否运行中"""
        return self.running


class PlatformManager:
    """平台管理器"""
    
    def __init__(self):
        self.adapters: Dict[str, PlatformAdapter] = {}
        self.adapter_classes: Dict[str, Type[PlatformAdapter]] = {}
        self.logger = logging.getLogger("platform.manager")
    
    def discover_adapters(self) -> List[str]:
        """发现可用适配器"""
        discovered = []
        
        adapter_dirs = [
            os.path.join(os.path.dirname(__file__), "adapters"),
        ]
        
        for adapter_dir in adapter_dirs:
            if os.path.exists(adapter_dir):
                for item in os.listdir(adapter_dir):
                    if item.endswith(".py") and item != "__init__.py":
                        discovered.append(item[:-3])
                    elif os.path.isdir(os.path.join(adapter_dir, item)):
                        init_file = os.path.join(adapter_dir, item, "__init__.py")
                        if os.path.exists(init_file):
                            discovered.append(item)
        
        return discovered
    
    def load_adapter(self, name: str, agent, config: Dict = None) -> bool:
        """加载平台适配器"""
        if name in self.adapters:
            self.logger.warning(f"适配器 {name} 已加载")
            return True
        
        try:
            module_path = f"storm.adapters.{name}"
            module = importlib.import_module(module_path)
            
            adapter_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, PlatformAdapter) and attr != PlatformAdapter:
                    adapter_class = attr
                    break
            
            if not adapter_class:
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if attr_name.endswith("Adapter") and isinstance(attr, type):
                        adapter_class = attr
                        break
            
            if not adapter_class:
                self.logger.error(f"适配器 {name} 未找到适配器类")
                return False
            
            adapter_instance = adapter_class(agent, config)
            self.adapters[name] = adapter_instance
            self.adapter_classes[name] = adapter_class
            
            self.logger.info(f"适配器 {name} 加载成功")
            return True
            
        except Exception as e:
            self.logger.error(f"加载适配器 {name} 失败: {e}")
            return False
    
    def start_adapter(self, name: str) -> bool:
        """启动适配器"""
        if name not in self.adapters:
            self.logger.error(f"适配器 {name} 未加载")
            return False
        
        try:
            self.adapters[name].start()
            self.logger.info(f"适配器 {name} 已启动")
            return True
        except Exception as e:
            self.logger.error(f"启动适配器 {name} 失败: {e}")
            return False
    
    def stop_adapter(self, name: str) -> bool:
        """停止适配器"""
        if name not in self.adapters:
            return False
        
        try:
            self.adapters[name].stop()
            self.logger.info(f"适配器 {name} 已停止")
            return True
        except Exception as e:
            self.logger.error(f"停止适配器 {name} 失败: {e}")
            return False
    
    def start_all(self):
        """启动所有适配器"""
        for name in self.adapters:
            self.start_adapter(name)
    
    def stop_all(self):
        """停止所有适配器"""
        for name in self.adapters:
            self.stop_adapter(name)
    
    def list_adapters(self) -> List[Dict]:
        """列出所有适配器"""
        return [
            {
                "name": adapter.name,
                "description": adapter.description,
                "icon": adapter.icon,
                "running": adapter.is_running(),
                "config_schema": adapter.get_config_schema()
            }
            for adapter in self.adapters.values()
        ]


_manager: Optional[PlatformManager] = None


def get_platform_manager() -> PlatformManager:
    """获取平台管理器单例"""
    global _manager
    if _manager is None:
        _manager = PlatformManager()
    return _manager
