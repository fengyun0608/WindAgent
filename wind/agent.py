# -*- coding: utf-8 -*-
"""
WindAgent 核心Agent
"""

import os
import re
import json
import time
import logging
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime

from cloud.config import get_config
from cloud.env import get_environment, get_command_adapter
from storm.plugin import get_plugin_manager
from eye.models import get_db, Message
from eye.memory.short_term import ShortTermMemory
from eye.memory.long_term import LongTermMemory
from wind.token_tracker import get_tracker, count_tokens
from wind.log_manager import get_log_manager


class WindAgent:
    """WindAgent 核心类"""
    
    def __init__(self):
        self.config = get_config()
        self.env = get_environment()
        self.cmd_adapter = get_command_adapter()
        self.plugin_manager = get_plugin_manager()
        self.db = get_db()
        self.token_tracker = get_tracker()
        
        self.short_memory = ShortTermMemory(
            max_items=self.config.memory.short_term_limit
        )
        self.long_memory = LongTermMemory()
        self.current_conversation_id: Optional[int] = None
        self.pending_code: Dict[str, Dict] = {}  # 存储待确认的代码
        
        self.logger = logging.getLogger("windagent")
        self.log_manager = get_log_manager(self.env.data_dir)
        
        self._load_prompts()
        self._init_plugins()
    
    def _load_prompts(self):
        """加载提示词"""
        prompt_dir = os.path.join(os.path.dirname(__file__), "..", "cloud", "prompts")
        
        self.system_prompt = ""
        self.agent_prompt = ""
        self.tools_prompt = ""
        
        system_path = os.path.join(prompt_dir, "system.txt")
        if os.path.exists(system_path):
            with open(system_path, 'r', encoding='utf-8') as f:
                self.system_prompt = f.read()
        
        agent_path = os.path.join(prompt_dir, "agent.txt")
        if os.path.exists(agent_path):
            with open(agent_path, 'r', encoding='utf-8') as f:
                self.agent_prompt = f.read()
        
        tools_path = os.path.join(prompt_dir, "tools.txt")
        if os.path.exists(tools_path):
            with open(tools_path, 'r', encoding='utf-8') as f:
                self.tools_prompt = f.read()
    
    def _init_plugins(self):
        """初始化插件"""
        if self.config.plugin.enabled and self.config.plugin.auto_load:
            self.plugin_manager.load_all()
    
    def start_conversation(self, title: str = "") -> int:
        """开始新对话"""
        conversation = self.db.create_conversation(title=title)
        self.current_conversation_id = conversation.id
        self.short_memory.clear()
        return conversation.id
    
    def get_context(self) -> List[Dict]:
        """获取对话上下文"""
        context = []
        
        if self.system_prompt:
            context.append({
                "role": "system",
                "content": self._build_system_prompt()
            })
        
        context.extend(self.short_memory.get_context())
        
        return context
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        prompt = self.system_prompt
        
        persona = self.config.persona
        
        persona_info = f"""
## 你的身份
- 名字: {persona.name}
- 描述: {persona.description}
- 性格: {persona.personality}
- 说话风格: {persona.speaking_style}
- 擅长领域: {', '.join(persona.expertise)}
"""
        prompt += persona_info
        
        if persona.custom_prompt:
            prompt += f"\n## 自定义提示\n{persona.custom_prompt}\n"
        
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "config.json")
        
        env_info = f"""
## 当前环境
- 设备类型: {self.env.device_type.value}
- 操作系统: {self.env.os_name}
- 是否平板: {'是' if self.env.is_tablet else '否'}
- Shell类型: {self.env.shell_type}
- 工作目录: {base_dir}

## 重要提示
- 修改配置时，请使用正确的工作目录: {base_dir}
- 不要创建新的配置目录，配置文件位于用户数据目录
- 执行命令时使用相对路径或完整路径

## 可用能力
你可以通过调用工具来帮助用户完成任务。

### 当前可用工具列表：
"""
        
        tools = self.plugin_manager.tools
        if tools:
            for tool_name, tool_info in tools.items():
                description = tool_info.get("description", "无描述")
                prompt += f"- {tool_name}: {description}\n"
        else:
            prompt += "- 暂无可用工具\n"
        
        prompt += """
### 工具使用说明：
- set_persona: 修改你的人设配置（名字、性格、说话风格等）
- 当用户要求修改你的名字或人设时，请使用 set_persona 工具
- 当用户请求需要实时信息或网络搜索时，请主动使用 web_search 工具
- 当用户需要执行系统操作时，请使用 execute_command 工具
- 当用户问你有什么工具或能力时，请列出上述工具列表
"""
        prompt += env_info
        
        if self.plugin_manager.commands:
            prompt += "\n## 可用命令\n"
            prompt += self.plugin_manager.get_commands_help()
        
        return prompt
    
    def process_message(self, message: str) -> str:
        """处理消息"""
        if message.startswith("/"):
            return self._handle_command(message)
        
        return self._handle_chat(message)
    
    def _handle_command(self, message: str) -> str:
        """处理命令"""
        parts = message[1:].split(" ", 1)
        cmd_name = parts[0]
        cmd_args = parts[1] if len(parts) > 1 else ""
        
        if cmd_name == "help":
            return self._get_help()
        elif cmd_name == "status":
            return self._get_status()
        elif cmd_name == "usage":
            return self._get_usage()
        elif cmd_name == "clear":
            return self._clear_conversation()
        elif cmd_name == "plugins":
            return self._list_plugins()
        elif cmd_name == "env":
            return self._get_env_info()
        elif cmd_name == "confirm":
            return self._confirm_code(cmd_args.strip())
        elif cmd_name == "cancel":
            return self._cancel_code(cmd_args.strip())
        else:
            return self.plugin_manager.execute_command(cmd_name, cmd_args)
    
    def _handle_chat(self, message: str) -> str:
        """处理聊天"""
        self.short_memory.add("user", message, count_tokens(message))
        self.log_manager.log_chat("user", message, self.current_conversation_id)
        
        self.plugin_manager.trigger_hook("on_message", {"content": message})
        
        if not self.config.ai.api_key:
            response = "请先配置API Key。编辑配置文件或设置环境变量 WINDAGENT_AI_API_KEY"
        else:
            response = self._call_api(message)
        
        response = self._execute_code_blocks(response)
        
        response_tokens = count_tokens(response)
        self.short_memory.add("assistant", response, response_tokens)
        self.log_manager.log_chat("assistant", response, self.current_conversation_id)
        
        if self.current_conversation_id:
            self.db.add_message(
                self.current_conversation_id,
                "user", message, count_tokens(message)
            )
            self.db.add_message(
                self.current_conversation_id,
                "assistant", response, response_tokens
            )
        
        self.token_tracker.record(
            count_tokens(message) + response_tokens,
            self.config.ai.model
        )
        
        self.plugin_manager.trigger_hook("on_response", {"content": response})
        
        return response
    
    def _execute_code_blocks(self, response: str) -> str:
        """执行响应中的代码块"""
        pattern = r'```execute:(\w+)\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        if not matches:
            return response
        
        results = []
        for lang, code in matches:
            result = self._run_code(lang, code.strip())
            results.append(f"\n[执行结果]\n{result}")
        
        return response + "\n" + "\n".join(results)
    
    def _run_code(self, lang: str, code: str) -> str:
        """执行代码"""
        try:
            if lang == "python":
                result = self._run_python(code)
            elif lang == "powershell":
                result = self._run_powershell(code)
            elif lang == "bash":
                result = self._run_bash(code)
            else:
                result = f"不支持的语言: {lang}"
                self.log_manager.log_execute(lang, code, result, success=False)
                return result
            
            self.log_manager.log_execute(lang, code, result, success=True)
            return result
        except Exception as e:
            error_msg = f"执行错误: {str(e)}"
            self.log_manager.log_execute(lang, code, error_msg, success=False)
            return error_msg
    
    def _run_python(self, code: str) -> str:
        """执行Python代码"""
        work_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ['python', temp_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=work_dir
            )
            return result.stdout or result.stderr or "执行完成（无输出）"
        except subprocess.TimeoutExpired:
            return "执行超时（30秒）"
        finally:
            os.unlink(temp_path)
    
    def _run_powershell(self, code: str) -> str:
        """执行PowerShell代码"""
        work_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        try:
            result = subprocess.run(
                ['powershell', '-Command', code],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=work_dir
            )
            return result.stdout or result.stderr or "执行完成（无输出）"
        except subprocess.TimeoutExpired:
            return "执行超时（30秒）"
    
    def _run_bash(self, code: str) -> str:
        """执行Bash代码"""
        work_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        try:
            result = subprocess.run(
                ['bash', '-c', code],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=work_dir
            )
            return result.stdout or result.stderr or "执行完成（无输出）"
        except subprocess.TimeoutExpired:
            return "执行超时（30秒）"
    
    def _get_tools(self):
        """获取可用工具列表"""
        tools = []
        for name, info in self.plugin_manager.tools.items():
            func = info.get("func")
            params = {"type": "object", "properties": {}, "required": []}
            
            if func:
                import inspect
                sig = inspect.signature(func)
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    
                    param_type = "string"
                    if param.annotation != inspect.Parameter.empty:
                        if param.annotation == int:
                            param_type = "integer"
                        elif param.annotation == float:
                            param_type = "number"
                        elif param.annotation == bool:
                            param_type = "boolean"
                    
                    params["properties"][param_name] = {"type": param_type}
                    
                    if param.default == inspect.Parameter.empty:
                        params["required"].append(param_name)
            
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": info.get("description", ""),
                    "parameters": params
                }
            })
        return tools
    
    def _call_api(self, message: str) -> str:
        """调用API"""
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=self.config.ai.api_key,
                base_url=self.config.ai.api_base
            )
            
            tools = self._get_tools()
            
            messages = self.get_context()
            
            max_iterations = 5
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                kwargs = {
                    "model": self.config.ai.model,
                    "messages": messages,
                    "max_tokens": self.config.ai.max_tokens,
                    "temperature": self.config.ai.temperature,
                    "timeout": self.config.ai.timeout
                }
                
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                
                response = client.chat.completions.create(**kwargs)
                
                if response.choices[0].message.tool_calls:
                    tool_call = response.choices[0].message.tool_calls[0]
                    tool_name = tool_call.function.name
                    tool_args = {}
                    
                    import json
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except:
                        pass
                    
                    self.log_manager.log_execute(f"tool:{tool_name}", str(tool_args), "执行中...", success=True)
                    
                    result = self.plugin_manager.execute_tool(tool_name, **tool_args)
                    
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": tool_call.function.arguments
                            }
                        }]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                    
                    continue
                
                return response.choices[0].message.content
            
            return "工具调用次数超过限制，请简化请求"
            
        except ImportError:
            return "请安装 openai 库: pip install openai"
        except Exception as e:
            return f"API调用失败: {str(e)}"
    
    async def stream_chat(self, message: str):
        """流式聊天 - 分段返回"""
        self.short_memory.add("user", message, count_tokens(message))
        
        if not self.config.ai.api_key:
            yield {"type": "text", "content": "请先配置API Key"}
            yield {"type": "done", "full_response": "请先配置API Key"}
            return
        
        full_response = ""
        
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=self.config.ai.api_key,
                base_url=self.config.ai.api_base
            )
            
            stream = client.chat.completions.create(
                model=self.config.ai.model,
                messages=self.get_context(),
                max_tokens=self.config.ai.max_tokens,
                temperature=self.config.ai.temperature,
                timeout=self.config.ai.timeout,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield {"type": "text", "content": content}
            
            yield {"type": "done", "full_response": full_response}
            
            response_tokens = count_tokens(full_response)
            self.short_memory.add("assistant", full_response, response_tokens)
            self.log_manager.log_chat("assistant", full_response, self.current_conversation_id)
            
            if self.current_conversation_id:
                self.db.add_message(
                    self.current_conversation_id,
                    "user", message, count_tokens(message)
                )
                self.db.add_message(
                    self.current_conversation_id,
                    "assistant", full_response, response_tokens
                )
            
            self.token_tracker.record(
                count_tokens(message) + response_tokens,
                self.config.ai.model
            )
            
        except ImportError:
            yield {"type": "error", "content": "请安装 openai 库: pip install openai"}
        except Exception as e:
            yield {"type": "error", "content": f"API调用失败: {str(e)}"}
    
    def _confirm_code(self, code_id: str) -> str:
        """确认执行代码"""
        if code_id not in self.pending_code:
            return f"❌ 未找到待执行的代码: {code_id}"
        
        import time
        pending = self.pending_code[code_id]
        
        if time.time() - pending["created_at"] > 300:
            del self.pending_code[code_id]
            return "❌ 代码已过期（超过5分钟），请重新生成"
        
        results = []
        for lang, code in pending["codes"]:
            result = self._run_code(lang, code)
            results.append(f"**{lang}**:\n```\n{result}\n```")
        
        del self.pending_code[code_id]
        return "✅ 代码执行结果:\n" + "\n\n".join(results)
    
    def _cancel_code(self, code_id: str) -> str:
        """取消执行代码"""
        if code_id not in self.pending_code:
            return f"❌ 未找到待执行的代码: {code_id}"
        
        del self.pending_code[code_id]
        return f"✅ 已取消执行代码: {code_id}"
    
    def _get_help(self) -> str:
        """获取帮助"""
        help_text = """
WindAgent 帮助
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

系统命令:
  /help      - 显示帮助
  /status    - 查看状态
  /usage     - 查看Token使用统计
  /clear     - 清除对话
  /plugins   - 查看已加载插件
  /env       - 查看环境信息

代码执行:
  /confirm <ID> - 确认执行待执行的代码
  /cancel <ID>  - 取消执行待执行的代码

插件命令:
"""
        help_text += self.plugin_manager.get_commands_help()
        return help_text
    
    def _get_status(self) -> str:
        """获取状态"""
        return f"""
WindAgent 状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
版本: {self.config.version}
API已配置: {'是' if self.config.ai.api_key else '否'}
模型: {self.config.ai.model}
已加载插件: {len(self.plugin_manager.plugins)}
当前对话ID: {self.current_conversation_id or '无'}
"""
    
    def _get_usage(self) -> str:
        """获取使用统计"""
        stats = self.token_tracker.get_stats()
        return f"""
Token 使用统计（最近30天）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
总Token数: {stats['total_tokens']:,}
请求数: {stats['request_count']}
平均每次: {stats['avg_per_request']:.1f}

按模型:
{self._format_dict(stats['by_model'])}

按日期:
{self._format_daily(self.token_tracker.get_daily_usage(7))}
"""
    
    def _format_dict(self, d: Dict) -> str:
        """格式化字典"""
        if not d:
            return "  无数据"
        return "\n".join(f"  {k}: {v:,}" for k, v in d.items())
    
    def _format_daily(self, daily: List[Dict]) -> str:
        """格式化每日数据"""
        lines = []
        for d in daily:
            bar = "█" * min(d['tokens'] // 100, 20)
            lines.append(f"  {d['date']}: {bar} {d['tokens']:,}")
        return "\n".join(lines)
    
    def _clear_conversation(self) -> str:
        """清除对话"""
        self.short_memory.clear()
        return "对话已清除"
    
    def _list_plugins(self) -> str:
        """列出插件"""
        plugins = self.plugin_manager.list_plugins()
        if not plugins:
            return "没有已加载的插件"
        
        result = "已加载插件:\n"
        for p in plugins:
            result += f"  - {p['name']} v{p['version']}: {p['description']}\n"
        return result
    
    def _get_env_info(self) -> str:
        """获取环境信息"""
        return f"""
运行环境
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
设备类型: {self.env.device_type.value}
操作系统: {self.env.os_name} {self.env.os_version}
架构: {self.env.arch}
是否平板: {'是' if self.env.is_tablet else '否'}
是否便携: {'是' if self.env.is_portable else '否'}
GPU: {'有' if self.env.has_gpu else '无'}
内存: {self.env.memory_gb} GB
Python: {self.env.python_version}
Shell: {self.env.shell_type}
数据目录: {self.env.data_dir}
"""


_agent: Optional[WindAgent] = None


def get_agent() -> WindAgent:
    """获取Agent实例"""
    global _agent
    if not _agent:
        _agent = WindAgent()
    return _agent
