# 插件开发指南

本文档介绍如何为 WindAgent 开发自定义插件。

## 目录

1. [插件结构](#插件结构)
2. [单文件插件](#单文件插件)
3. [多文件插件包](#多文件插件包)
4. [插件基类](#插件基类)
5. [装饰器](#装饰器)
6. [示例插件](#示例插件)
7. [最佳实践](#最佳实践)

---

## 插件结构

WindAgent 支持两种插件形式：

### 1. 单文件插件
```
storm/builtin/
├── my_plugin.py          # 单文件插件
```

### 2. 多文件插件包
```
storm/builtin/
├── my_plugin/            # 插件目录
│   ├── __init__.py       # 必须包含插件类
│   ├── utils.py          # 辅助模块
│   └── config.json       # 配置文件（可选）
```

---

## 单文件插件

创建一个简单的单文件插件：

```python
# storm/builtin/hello.py

from storm.plugin import PluginBase, command, tool

class HelloPlugin(PluginBase):
    """简单的问候插件"""
    
    name = "hello"
    version = "1.0.0"
    description = "一个简单的问候插件"
    author = "你的名字"
    
    @command("hello", help="发送问候")
    def hello(self, args: str):
        """发送问候消息"""
        return f"你好！{args}"
    
    @tool("greet", description="向用户发送问候")
    def greet(self, name: str = "朋友") -> str:
        """发送问候
        
        Args:
            name: 用户名
        
        Returns:
            问候消息
        """
        return f"你好，{name}！很高兴见到你。"
```

---

## 多文件插件包

创建一个多文件插件包：

### 目录结构
```
storm/builtin/weather_plus/
├── __init__.py           # 主插件类
├── api.py                # API 调用
├── utils.py              # 工具函数
└── config.json           # 配置文件
```

### __init__.py
```python
from storm.plugin import PluginBase, command, tool
from .api import WeatherAPI
from .utils import format_weather

class WeatherPlusPlugin(PluginBase):
    """增强版天气插件"""
    
    name = "weather_plus"
    version = "1.0.0"
    description = "增强版天气查询插件"
    author = "你的名字"
    
    def __init__(self, manager):
        super().__init__(manager)
        self.api = WeatherAPI()
    
    @command("天气", aliases=["weather"], help="查询天气")
    def weather(self, args: str):
        """查询天气"""
        if not args:
            return "请输入城市名称，例如：/天气 北京"
        
        data = self.api.get_weather(args)
        return format_weather(data)
    
    @tool("get_weather_detail", description="获取详细天气信息")
    def get_weather_detail(self, city: str) -> str:
        """获取详细天气信息
        
        Args:
            city: 城市名称
        
        Returns:
            详细天气信息
        """
        data = self.api.get_weather(city)
        return format_weather(data, detailed=True)
```

### api.py
```python
import requests

class WeatherAPI:
    """天气 API 封装"""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://api.weatherapi.com/v1"
    
    def get_weather(self, city: str) -> dict:
        """获取天气数据"""
        # API 调用逻辑
        pass
```

### utils.py
```python
def format_weather(data: dict, detailed: bool = False) -> str:
    """格式化天气信息"""
    if detailed:
        return f"""
城市：{data['city']}
温度：{data['temp']}°C
湿度：{data['humidity']}%
风速：{data['wind']}km/h
天气：{data['condition']}
        """.strip()
    else:
        return f"{data['city']}：{data['temp']}°C，{data['condition']}"
```

---

## 插件基类

所有插件必须继承 `PluginBase` 类：

```python
from storm.plugin import PluginBase

class MyPlugin(PluginBase):
    # 必须定义的属性
    name = "my_plugin"           # 插件名称（唯一标识）
    version = "1.0.0"            # 版本号
    description = "插件描述"      # 描述
    author = "作者"               # 作者
    
    # 可选属性
    icon = "📦"                  # 图标
    
    # 生命周期方法
    def on_load(self):
        """插件加载时调用"""
        pass
    
    def on_unload(self):
        """插件卸载时调用"""
        pass
```

---

## 装饰器

### @command - 注册命令

命令是用户可以直接调用的功能，通过 `/命令名` 触发。

```python
from storm.plugin import command

@command(name, aliases=[], help="")
def my_command(self, args: str):
    """命令处理函数
    
    Args:
        args: 用户输入的参数（命令后的所有内容）
    
    Returns:
        命令执行结果（字符串）
    """
    pass
```

**示例：**
```python
@command("计算", aliases=["calc", "calculator"], help="计算数学表达式")
def calculate(self, args: str):
    """计算数学表达式"""
    try:
        result = eval(args)
        return f"计算结果：{result}"
    except:
        return "计算失败，请检查表达式"
```

### @tool - 注册工具

工具是 AI 可以自主调用的功能，用于完成任务。

```python
from storm.plugin import tool

@tool(name, description="")
def my_tool(self, param1: str, param2: int = 0) -> str:
    """工具函数
    
    Args:
        param1: 参数说明
        param2: 可选参数
    
    Returns:
        工具执行结果
    """
    pass
```

**重要提示：**
- 工具函数必须有详细的文档字符串，AI 会根据文档调用
- 参数必须有类型注解
- 返回值必须是字符串
- description 参数描述工具的用途

**示例：**
```python
@tool("search_web", description="搜索互联网获取实时信息")
def search_web(self, query: str, max_results: int = 5) -> str:
    """搜索互联网
    
    Args:
        query: 搜索关键词
        max_results: 最大结果数量
    
    Returns:
        搜索结果摘要
    """
    # 搜索逻辑
    return "搜索结果..."
```

### @hook - 注册钩子

钩子是在特定事件发生时自动执行的函数。

```python
from storm.plugin import hook

@hook(event)
def my_hook(self, *args, **kwargs):
    """钩子函数"""
    pass
```

**可用事件：**
- `on_message`: 收到消息时
- `on_reply`: 发送回复前
- `on_tool_call`: 工具调用时

**示例：**
```python
@hook("on_message")
def log_message(self, message: str):
    """记录消息"""
    print(f"收到消息：{message}")
    return message  # 返回处理后的消息

@hook("on_reply")
def add_signature(self, reply: str):
    """添加签名"""
    return reply + "\n\n——来自 WindAgent"
```

---

## 示例插件

### 完整示例：待办事项插件

```python
# storm/builtin/todo.py

from storm.plugin import PluginBase, command, tool
from typing import List
import json

class TodoPlugin(PluginBase):
    """待办事项管理插件"""
    
    name = "todo"
    version = "1.0.0"
    description = "管理待办事项"
    author = "WindAgent"
    
    def __init__(self, manager):
        super().__init__(manager)
        self.todos = self._load_todos()
    
    def _load_todos(self) -> List[dict]:
        """加载待办事项"""
        config = self.get_plugin_config("todo", "items", [])
        return config
    
    def _save_todos(self):
        """保存待办事项"""
        self.set_plugin_config("todo", "items", self.todos)
    
    @command("todo", aliases=["待办"], help="管理待办事项")
    def todo_command(self, args: str):
        """待办事项命令
        
        用法：
        /todo add 任务内容 - 添加任务
        /todo list - 列出所有任务
        /todo done 编号 - 标记完成
        /todo clear - 清空所有任务
        """
        if not args:
            return "用法：/todo add|list|done|clear [参数]"
        
        parts = args.split(maxsplit=1)
        action = parts[0]
        
        if action == "add":
            if len(parts) < 2:
                return "请输入任务内容"
            task = parts[1]
            self.todos.append({"task": task, "done": False})
            self._save_todos()
            return f"已添加任务：{task}"
        
        elif action == "list":
            if not self.todos:
                return "暂无待办事项"
            result = "待办事项：\n"
            for i, todo in enumerate(self.todos, 1):
                status = "✅" if todo["done"] else "⬜"
                result += f"{i}. {status} {todo['task']}\n"
            return result
        
        elif action == "done":
            if len(parts) < 2:
                return "请输入任务编号"
            try:
                idx = int(parts[1]) - 1
                if 0 <= idx < len(self.todos):
                    self.todos[idx]["done"] = True
                    self._save_todos()
                    return f"已完成：{self.todos[idx]['task']}"
                return "任务编号无效"
            except ValueError:
                return "请输入有效的数字"
        
        elif action == "clear":
            self.todos = []
            self._save_todos()
            return "已清空所有待办事项"
        
        return "未知操作"
    
    @tool("add_todo", description="添加待办事项")
    def add_todo(self, task: str) -> str:
        """添加待办事项
        
        Args:
            task: 任务内容
        
        Returns:
            添加结果
        """
        self.todos.append({"task": task, "done": False})
        self._save_todos()
        return f"已添加待办事项：{task}"
    
    @tool("list_todos", description="列出待办事项")
    def list_todos(self) -> str:
        """列出所有待办事项
        
        Returns:
            待办事项列表
        """
        if not self.todos:
            return "暂无待办事项"
        result = "待办事项：\n"
        for i, todo in enumerate(self.todos, 1):
            status = "✅" if todo["done"] else "⬜"
            result += f"{i}. {status} {todo['task']}\n"
        return result
    
    @tool("complete_todo", description="标记待办事项为完成")
    def complete_todo(self, index: int) -> str:
        """标记待办事项为完成
        
        Args:
            index: 任务编号（从1开始）
        
        Returns:
            操作结果
        """
        idx = index - 1
        if 0 <= idx < len(self.todos):
            self.todos[idx]["done"] = True
            self._save_todos()
            return f"已完成：{self.todos[idx]['task']}"
        return "任务编号无效"
```

---

## 最佳实践

### 1. 命名规范
- 插件名使用小写字母和下划线：`my_plugin`
- 命令名使用中文或英文：`/天气` 或 `/weather`
- 工具名使用英文和下划线：`get_weather`

### 2. 错误处理
```python
@tool("my_tool", description="工具描述")
def my_tool(self, param: str) -> str:
    try:
        # 工具逻辑
        return "成功"
    except Exception as e:
        return f"操作失败：{str(e)}"
```

### 3. 配置管理
```python
# 获取配置
api_key = self.get_plugin_config("my_plugin", "api_key", "")

# 设置配置
self.set_plugin_config("my_plugin", "api_key", "your_key")
```

### 4. 日志记录
```python
from breeze.logger import print_log

@tool("my_tool", description="工具描述")
def my_tool(self, param: str) -> str:
    print_log("INFO", f"执行工具：{param}", "MyPlugin")
    return "结果"
```

### 5. 文档字符串
```python
@tool("my_tool", description="工具描述")
def my_tool(self, param: str) -> str:
    """工具的详细描述
    
    Args:
        param: 参数说明
    
    Returns:
        返回值说明
    
    Example:
        my_tool("示例") -> "结果"
    """
    pass
```

---

## 调试技巧

### 1. 热重载
在插件管理页面点击「热更新」按钮，无需重启服务。

### 2. 查看日志
控制台会显示插件的加载和执行日志。

### 3. 测试命令
```
/命令名 参数
```

### 4. 测试工具
在对话中让 AI 调用工具：
```
请帮我查询天气
```

---

## 发布插件

1. 将插件文件放入 `storm/builtin/` 目录
2. 重启服务或使用热更新
3. 在插件管理页面查看和配置

---

## 常见问题

### Q: 插件不加载？
A: 检查插件类是否继承 `PluginBase`，是否定义了必要属性。

### Q: 工具不显示？
A: 检查 `@tool` 装饰器是否正确，函数是否有类型注解。

### Q: 命令无响应？
A: 检查命令名是否正确，是否有参数要求。

### Q: 如何调试？
A: 使用 `print_log` 输出日志，或使用 Python 调试器。

---

## 更多资源

- [API 参考](./api.md)
- [示例插件](../storm/builtin/)
- [问题反馈](https://github.com/fengyun0608/WindAgent/issues)
