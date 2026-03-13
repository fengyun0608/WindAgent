# -*- coding: utf-8 -*-
"""
官方插件包 - WindAgent内置插件集合
包含计算器、搜索、天气等常用功能
"""

from storm.plugin import PluginBase, command, tool, ConfigField
from typing import List
import math


class OfficialPlugin(PluginBase):
    """官方插件集合"""
    
    name = "official"
    description = "官方插件包 - 计算器、搜索、天气"
    version = "1.0.0"
    author = "风云"
    icon = "🔧"
    
    config_fields: List[ConfigField] = [
        ConfigField(
            key="search_engine",
            label="搜索引擎",
            type="select",
            default="duckduckgo",
            options=["duckduckgo", "google", "bing"]
        )
    ]
    
    def on_load(self):
        """插件加载"""
        self.logger.info("官方插件包已加载")
        
        self._safe_dict = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow, "sqrt": math.sqrt,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "log": math.log, "log10": math.log10, "exp": math.exp,
            "pi": math.pi, "e": math.e
        }
    
    @command("calc", help="计算: /calc <表达式>")
    def calculate(self, args: str):
        """计算表达式"""
        if not args:
            return "请输入计算表达式，例如: /calc 1+2*3"
        try:
            result = eval(args, {"__builtins__": {}}, self._safe_dict)
            return f"计算结果: {args} = {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    @tool("calculate", description="计算数学表达式，如加减乘除、三角函数等")
    def calculate_tool(self, expression: str) -> str:
        """计算数学表达式
        
        Args:
            expression: 数学表达式，如 "1+2*3", "sqrt(16)", "sin(pi/2)"
        
        Returns:
            计算结果
        """
        try:
            result = eval(expression, {"__builtins__": {}}, self._safe_dict)
            return f"计算结果: {expression} = {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    @command("search", help="搜索: /search <关键词>")
    def search(self, args: str):
        """搜索功能"""
        if not args:
            return "请输入搜索关键词，例如: /search Python教程"
        return self._do_search(args)
    
    @tool("web_search", description="搜索互联网获取实时信息，如新闻、教程、技术文档等")
    def search_tool(self, query: str) -> str:
        """搜索互联网信息
        
        Args:
            query: 搜索关键词或问题
        
        Returns:
            搜索结果摘要
        """
        return self._do_search(query)
    
    def _do_search(self, query: str) -> str:
        """执行网络搜索"""
        try:
            import urllib.parse
            import urllib.request
            import json
            
            encoded_query = urllib.parse.quote(query)
            
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            results = []
            
            if data.get('AbstractText'):
                results.append(f"摘要: {data['AbstractText']}")
            
            if data.get('Answer'):
                results.append(f"答案: {data['Answer']}")
            
            related_topics = data.get('RelatedTopics', [])[:5]
            for topic in related_topics:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append(f"- {topic['Text'][:200]}")
            
            if results:
                return f"搜索 '{query}' 的结果:\n\n" + "\n".join(results)
            else:
                return f"未找到关于 '{query}' 的相关信息，请尝试其他关键词"
                
        except Exception as e:
            return f"搜索失败: {str(e)}\n请检查网络连接"
    
    @tool("fetch_url", description="获取网页内容，用于读取特定网页的信息")
    def fetch_url(self, url: str) -> str:
        """获取网页内容
        
        Args:
            url: 网页URL
        
        Returns:
            网页内容摘要
        """
        try:
            import urllib.request
            import re
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
            
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            if len(text) > 2000:
                text = text[:2000] + "..."
            
            return f"网页内容:\n{text}"
            
        except Exception as e:
            return f"获取网页失败: {str(e)}"
    
    @command("weather", help="天气: /weather <城市>")
    def weather(self, args: str):
        """天气查询"""
        if not args:
            return "请输入城市名称，例如: /weather 北京"
        return self._get_weather(args)
    
    @tool("get_weather", description="获取指定城市的实时天气信息")
    def weather_tool(self, city: str) -> str:
        """获取天气信息
        
        Args:
            city: 城市名称
        
        Returns:
            天气信息
        """
        return self._get_weather(city)
    
    def _get_weather(self, city: str) -> str:
        """获取天气"""
        try:
            import urllib.request
            import json
            
            url = f"https://wttr.in/{city}?format=j1"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'curl/7.68.0'
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            current = data.get('current_condition', [{}])[0]
            temp = current.get('temp_C', 'N/A')
            desc = current.get('weatherDesc', [{}])[0].get('value', 'N/A')
            humidity = current.get('humidity', 'N/A')
            wind = current.get('windspeedKmph', 'N/A')
            
            return f"城市: {city}\n温度: {temp}°C\n天气: {desc}\n湿度: {humidity}%\n风速: {wind} km/h"
            
        except Exception as e:
            return f"获取天气失败: {str(e)}"
    
    @command("time", help="获取当前时间")
    def get_time(self, args: str):
        """获取当前时间"""
        from datetime import datetime
        now = datetime.now()
        return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @tool("get_current_time", description="获取当前日期和时间")
    def time_tool(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        now = datetime.now()
        return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @command("roll", help="掷骰子: /roll [最大值]")
    def roll(self, args: str):
        """掷骰子"""
        import random
        try:
            max_val = int(args) if args else 100
        except:
            max_val = 100
        result = random.randint(1, max_val)
        return f"掷骰子结果: {result} (1-{max_val})"
    
    @tool("random_number", description="生成指定范围内的随机数")
    def random_tool(self, min_val: int = 1, max_val: int = 100) -> str:
        """生成随机数
        
        Args:
            min_val: 最小值，默认1
            max_val: 最大值，默认100
        
        Returns:
            随机数结果
        """
        import random
        result = random.randint(min_val, max_val)
        return f"随机数: {result} (范围: {min_val}-{max_val})"
    
    @command("ping", help="测试机器人是否在线")
    def ping(self, args: str):
        """测试机器人"""
        return "Pong! 机器人在线中~"
    
    @tool("set_persona", description="修改AI的人设配置，包括名字、性格、说话风格等")
    def set_persona_tool(self, name: str = None, description: str = None, personality: str = None, speaking_style: str = None) -> str:
        """修改AI人设配置
        
        Args:
            name: AI的名字
            description: AI的描述
            personality: AI的性格
            speaking_style: AI的说话风格
        
        Returns:
            修改结果
        """
        try:
            from cloud.config import get_config_manager
            
            manager = get_config_manager()
            
            if name:
                manager.config.persona.name = name
            if description:
                manager.config.persona.description = description
            if personality:
                manager.config.persona.personality = personality
            if speaking_style:
                manager.config.persona.speaking_style = speaking_style
            
            manager.save()
            
            result_parts = ["人设配置已更新："]
            if name:
                result_parts.append(f"名字: {name}")
            if description:
                result_parts.append(f"描述: {description}")
            if personality:
                result_parts.append(f"性格: {personality}")
            if speaking_style:
                result_parts.append(f"说话风格: {speaking_style}")
            result_parts.append("\n注意：重启服务后生效")
            
            return "\n".join(result_parts)
            
        except Exception as e:
            return f"修改人设失败: {str(e)}"
    
    @tool("execute_command", description="执行系统命令，用于完成用户指定的操作任务")
    def execute_command_tool(self, command: str, shell: str = "powershell") -> str:
        """执行系统命令
        
        Args:
            command: 要执行的命令
            shell: shell类型，可选 powershell, bash, python
        
        Returns:
            命令执行结果
        """
        import subprocess
        
        try:
            if shell == "powershell":
                result = subprocess.run(
                    ['powershell', '-Command', command],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            elif shell == "bash":
                result = subprocess.run(
                    ['bash', '-c', command],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            elif shell == "python":
                result = subprocess.run(
                    ['python', '-c', command],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                return f"不支持的shell类型: {shell}"
            
            output = result.stdout or result.stderr or "执行完成（无输出）"
            return f"命令: {command}\n结果:\n{output}"
            
        except subprocess.TimeoutExpired:
            return "命令执行超时（30秒）"
        except Exception as e:
            return f"执行失败: {str(e)}"
