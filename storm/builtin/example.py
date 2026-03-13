# -*- coding: utf-8 -*-
"""
示例插件 - 展示插件开发方法

这是一个完整的插件示例，展示了如何创建带有配置字段的插件
"""

from storm.plugin import PluginBase, command, ConfigField
from typing import List


class ExamplePlugin(PluginBase):
    """示例插件 - 展示插件开发方法"""
    
    name = "example"
    description = "示例插件 - 展示插件开发方法"
    version = "1.0.0"
    author = "风云"
    icon = "📦"
    
    config_fields: List[ConfigField] = [
        ConfigField(
            key="greeting",
            label="问候语",
            type="text",
            default="你好",
            required=False,
            placeholder="输入默认问候语"
        ),
        ConfigField(
            key="max_count",
            label="最大计数",
            type="number",
            default=100,
            required=False,
            placeholder="最大计数范围"
        ),
        ConfigField(
            key="enabled_features",
            label="启用功能",
            type="select",
            default="all",
            required=False,
            options=["all", "hello", "roll", "time"]
        )
    ]
    
    def on_load(self):
        """插件加载时调用"""
        self.logger.info("示例插件已加载")
        self.counter = 0
    
    def on_unload(self):
        """插件卸载时调用"""
        self.logger.info("示例插件已卸载")
    
    @command(
        name="hello",
        help="打招呼",
        aliases=["hi", "你好"]
    )
    def hello_command(self, args: str = "") -> str:
        """打招呼命令"""
        greeting = self.get_config("greeting", "你好")
        name = args.strip() or "朋友"
        self.counter += 1
        return f"{greeting}，{name}！这是第 {self.counter} 次打招呼 👋"
    
    @command(
        name="roll",
        help="掷骰子"
    )
    def roll_command(self, args: str = "") -> str:
        """掷骰子命令"""
        import random
        max_val = self.get_config("max_count", 100)
        try:
            max_val = int(args.strip()) if args.strip() else max_val
        except:
            pass
        result = random.randint(1, max_val)
        return f"🎲 掷骰子结果: {result} (1-{max_val})"
    
    @command(
        name="time",
        help="获取当前时间"
    )
    def time_command(self, args: str = "") -> str:
        """获取当前时间"""
        from datetime import datetime
        now = datetime.now()
        return f"⏰ 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @command(
        name="echo",
        help="重复你说的话"
    )
    def echo_command(self, args: str = "") -> str:
        """重复命令"""
        if not args.strip():
            return "请输入要重复的内容，例如: /echo 你好"
        return f"📢 {args}"
