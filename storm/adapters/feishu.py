# -*- coding: utf-8 -*-
"""
飞书平台适配器 - 使用官方SDK长连接模式
"""

import asyncio
import json
from typing import Optional, Dict, Any, List

from breeze.logger import print_log
from storm.platform import PlatformAdapter, ConfigField

try:
    import lark_oapi as lark
    from lark_oapi.ws import Client as WSClient
    from lark_oapi import EventDispatcherHandler
    HAS_LARK_SDK = True
except ImportError:
    HAS_LARK_SDK = False


class FeishuAdapter(PlatformAdapter):
    """飞书适配器 - 官方SDK长连接模式"""
    
    name = "feishu"
    description = "飞书机器人接入，支持私聊和群聊"
    icon = "🪽"
    
    config_fields: List[ConfigField] = [
        ConfigField(
            key="app_id",
            label="App ID",
            type="text",
            required=True,
            placeholder="飞书应用的 App ID"
        ),
        ConfigField(
            key="app_secret",
            label="App Secret",
            type="password",
            required=True,
            placeholder="飞书应用的 App Secret"
        ),
        ConfigField(
            key="encrypt_key",
            label="Encrypt Key",
            type="password",
            required=False,
            placeholder="消息加密密钥（可选）"
        ),
        ConfigField(
            key="verification_token",
            label="Verification Token",
            type="password",
            required=False,
            placeholder="验证令牌（可选）"
        )
    ]
    
    _processed_messages = set()
    
    def __init__(self, agent, config: Dict[str, Any] = None):
        super().__init__(agent, config)
        self.client = None
        self.feishu_conversation_id = None
    
    def _on_message_receive(self, event):
        """处理消息事件"""
        try:
            print_log("DEBUG", f"收到事件类型: {type(event)}", "飞书")
            
            if hasattr(event, 'event'):
                event_data = event.event
            else:
                event_data = event
            
            if hasattr(event_data, 'message'):
                message = event_data.message
            else:
                message = event_data.get("message", {}) if isinstance(event_data, dict) else {}
            
            message_id = message.message_id if hasattr(message, 'message_id') else message.get("message_id")
            
            print_log("DEBUG", f"消息ID: {message_id}", "飞书")
            
            if message_id is None:
                print_log("WARNING", "消息ID为空，忽略此消息", "飞书")
                return
            
            create_time_str = message.create_time if hasattr(message, 'create_time') else message.get("create_time", "0")
            print_log("DEBUG", f"消息创建时间: {create_time_str}", "飞书")
            
            try:
                import time
                if create_time_str:
                    create_time = int(create_time_str) / 1000 if len(str(create_time_str)) > 10 else int(create_time_str)
                    current_time = int(time.time())
                    if current_time - create_time > 60:
                        print_log("DEBUG", f"忽略超过1分钟的旧消息: {message_id}", "飞书")
                        return
            except:
                pass
            
            if message_id in FeishuAdapter._processed_messages:
                print_log("DEBUG", f"消息已处理过: {message_id}", "飞书")
                return
            
            FeishuAdapter._processed_messages.add(message_id)
            
            if len(FeishuAdapter._processed_messages) > 1000:
                FeishuAdapter._processed_messages = set(list(FeishuAdapter._processed_messages)[-500:])
            
            chat_id = message.chat_id if hasattr(message, 'chat_id') else message.get("chat_id")
            msg_type = message.message_type if hasattr(message, 'message_type') else message.get("message_type")
            chat_type = message.chat_type if hasattr(message, 'chat_type') else message.get("chat_type", "p2p")
            
            print_log("DEBUG", f"聊天类型: {chat_type}, 消息类型: {msg_type}", "飞书")
            
            if msg_type == "text" and chat_id:
                content = message.content if hasattr(message, 'content') else message.get("content", "{}")
                try:
                    if isinstance(content, str):
                        content_data = json.loads(content)
                    else:
                        content_data = content
                    text = content_data.get("text", "")
                except:
                    text = content if isinstance(content, str) else str(content)
                
                if text:
                    is_group = chat_type in ["group", "topic"]
                    has_mention = "@" in text
                    
                    if is_group and not has_mention:
                        print_log("DEBUG", f"群聊消息未@机器人，忽略: {text[:30]}...", "飞书")
                        return
                    
                    print_log("INFO", f"收到飞书消息: {text[:50]}...", "飞书")
                    
                    if not self.feishu_conversation_id:
                        conv = self.agent.db.get_or_create_default_conversation(platform="feishu")
                        self.feishu_conversation_id = conv.id
                        print_log("INFO", f"飞书会话ID: {conv.id}", "飞书")
                    
                    self.agent.current_conversation_id = self.feishu_conversation_id
                    
                    messages = self.agent.db.get_messages(self.feishu_conversation_id, limit=self.agent.config.memory.short_term_limit)
                    self.agent.short_memory.clear()
                    for msg in messages:
                        from wind.token_tracker import count_tokens
                        self.agent.short_memory.add(msg.role, msg.content, msg.tokens or count_tokens(msg.content))
                    
                    print_log("INFO", f"加载了 {len(messages)} 条历史记忆", "记忆")
                    
                    response_text = self.agent.process_message(text)
                    print_log("INFO", f"AI回复: {response_text[:50]}...", "飞书")
                    
                    from wind.routes import broadcast_to_all
                    broadcast_to_all({
                        "type": "new_message",
                        "conversation_id": self.feishu_conversation_id,
                        "platform": "feishu"
                    })
                    
                    asyncio.create_task(self._send_formatted_message(chat_id, response_text))
        
        except Exception as e:
            import traceback
            print_log("ERROR", f"处理消息异常: {str(e)}", "飞书")
            print_log("ERROR", traceback.format_exc(), "飞书")
    
    async def _send_formatted_message(self, chat_id: str, response: str) -> bool:
        """发送格式化消息，分离代码和执行结果"""
        import re
        
        code_pattern = r'```execute:(\w+)\n([\s\S]*?)```'
        result_pattern = r'```result\n([\s\S]*?)```'
        
        codes = re.findall(code_pattern, response)
        results = re.findall(result_pattern, response)
        
        clean_response = re.sub(code_pattern, '', response)
        clean_response = re.sub(result_pattern, '', clean_response)
        clean_response = clean_response.strip()
        
        if clean_response:
            await self._send_message(chat_id, clean_response)
        
        for i, (lang, code) in enumerate(codes):
            code_msg = f"🔧 执行代码 ({lang}):\n```\n{code.strip()}\n```"
            await self._send_message(chat_id, code_msg)
        
        for i, result in enumerate(results):
            result_msg = f"📋 执行结果:\n```\n{result.strip()}\n```"
            await self._send_message(chat_id, result_msg)
        
        return True
    
    async def _send_message(self, chat_id: str, text: str) -> bool:
        """发送消息"""
        try:
            import httpx
            
            app_id = self.get_config("app_id")
            app_secret = self.get_config("app_secret")
            
            async with httpx.AsyncClient() as client:
                token_res = await client.post(
                    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                    json={"app_id": app_id, "app_secret": app_secret},
                    timeout=10.0
                )
                token_data = token_res.json()
                
                if token_data.get("code") == 0:
                    tenant_token = token_data.get("tenant_access_token")
                    
                    send_res = await client.post(
                        "https://open.feishu.cn/open-apis/im/v1/messages",
                        params={"receive_id_type": "chat_id"},
                        headers={
                            "Authorization": f"Bearer {tenant_token}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "receive_id": chat_id,
                            "msg_type": "text",
                            "content": json.dumps({"text": text})
                        },
                        timeout=10.0
                    )
                    send_data = send_res.json()
                    
                    if send_data.get("code") == 0:
                        print_log("SUCCESS", "消息已发送", "飞书")
                        return True
                    else:
                        print_log("ERROR", f"发送失败: {send_data.get('msg')}", "飞书")
                else:
                    print_log("ERROR", f"获取token失败: {token_data.get('msg')}", "飞书")
                    
        except Exception as e:
            print_log("ERROR", f"发送消息异常: {str(e)}", "飞书")
        
        return False
    
    def start(self):
        """启动长连接"""
        if not HAS_LARK_SDK:
            print_log("ERROR", "请先安装飞书SDK: pip install lark-oapi", "飞书")
            return
        
        app_id = self.get_config("app_id")
        app_secret = self.get_config("app_secret")
        encrypt_key = self.get_config("encrypt_key", "")
        verification_token = self.get_config("verification_token", "")
        
        if not app_id or not app_secret:
            print_log("ERROR", "飞书 App ID 或 App Secret 未配置", "飞书")
            return
        
        try:
            event_handler = EventDispatcherHandler.builder(
                encrypt_key=encrypt_key,
                verification_token=verification_token
            ).register_p2_im_message_receive_v1(self._on_message_receive).build()
            
            self.client = WSClient(
                app_id=app_id,
                app_secret=app_secret,
                event_handler=event_handler,
                log_level=lark.LogLevel.ERROR
            )
            
            import asyncio
            loop = asyncio.get_event_loop()
            
            asyncio.ensure_future(self._run_client(), loop=loop)
            
            self.running = True
            print_log("SUCCESS", "飞书长连接已启动", "飞书")
            print_log("INFO", "无需配置事件订阅地址，直接接收消息", "飞书")
            
        except Exception as e:
            print_log("ERROR", f"启动飞书长连接失败: {str(e)}", "飞书")
    
    async def _run_client(self):
        """运行客户端"""
        try:
            await self.client._connect()
        except Exception as e:
            print_log("ERROR", f"飞书连接异常: {str(e)}", "飞书")
    
    def stop(self):
        """停止"""
        if self.client:
            self.client.stop()
        self.running = False
        print_log("INFO", "飞书长连接已停止", "飞书")
