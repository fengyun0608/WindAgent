# -*- coding: utf-8 -*-
"""
WindAgent API 路由
"""

import os
import json
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from cloud.config import get_config, AI_PROVIDERS, PLATFORMS, is_dangerous_command
from wind.agent import get_agent


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    conversation_id: Optional[int] = None


class ConfigRequest(BaseModel):
    """配置请求"""
    section: str
    key: str
    value: Any


class ConnectionManager:
    """WebSocket连接管理器"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


_manager = ConnectionManager()


def broadcast_to_all(message: dict):
    """广播消息到所有连接的客户端"""
    import asyncio
    asyncio.create_task(_manager.broadcast(message))


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    config = get_config()
    
    app = FastAPI(
        title="WindAgent",
        description="轻量级本地AI智能体",
        version=config.version
    )
    
    static_dir = os.path.join(os.path.dirname(__file__), "..", "horizon", "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动时加载平台配置"""
        from breeze.logger import print_log
        from cloud.config import get_config_manager
        from storm.platform import get_platform_manager
        
        manager = get_config_manager()
        platform_manager = get_platform_manager()
        
        discovered = platform_manager.discover_adapters()
        print_log("INFO", f"发现 {len(discovered)} 个平台适配器: {', '.join(discovered)}", "平台管理")
        
        if hasattr(manager.config, 'platform') and manager.config.platform:
            platform_cfg = manager.config.platform
            
            if platform_cfg.feishu_enabled and platform_cfg.feishu_app_id and platform_cfg.feishu_app_secret:
                print_log("INFO", "飞书平台配置已加载", "平台管理")
                
                try:
                    feishu_config = {
                        "app_id": platform_cfg.feishu_app_id,
                        "app_secret": platform_cfg.feishu_app_secret,
                        "encrypt_key": platform_cfg.feishu_encrypt_key or "",
                        "verification_token": platform_cfg.feishu_verification_token or ""
                    }
                    
                    platform_manager.load_adapter("feishu", agent, feishu_config)
                    platform_manager.start_adapter("feishu")
                    
                except Exception as e:
                    print_log("ERROR", f"飞书启动失败: {str(e)}", "飞书")
            else:
                print_log("INFO", "飞书平台未启用", "平台管理")
    
    agent = get_agent()
    
    @app.get("/", response_class=HTMLResponse)
    async def index():
        """首页 - 管理后台"""
        import os
        template_path = os.path.join(
            os.path.dirname(__file__), 
            "..", "horizon", "templates", "index.html"
        )
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @app.get("/api/status")
    async def get_status():
        """获取状态"""
        return {
            "version": config.version,
            "api_configured": bool(config.ai.api_key),
            "model": config.ai.model,
            "plugins_loaded": len(agent.plugin_manager.plugins)
        }
    
    @app.get("/api/env")
    async def get_env():
        """获取环境信息"""
        env = agent.env
        return {
            "device_type": env.device_type.value,
            "os_name": env.os_name,
            "os_version": env.os_version,
            "arch": env.arch,
            "is_tablet": env.is_tablet,
            "is_portable": env.is_portable,
            "has_gpu": env.has_gpu,
            "memory_gb": env.memory_gb,
            "python_version": env.python_version,
            "shell_type": env.shell_type,
            "data_dir": env.data_dir
        }
    
    @app.post("/api/chat")
    async def chat(request: ChatRequest):
        """聊天接口"""
        if request.conversation_id and request.conversation_id != agent.current_conversation_id:
            agent.current_conversation_id = request.conversation_id
            agent.short_memory.clear()
        
        response = agent.process_message(request.message)
        
        await _manager.broadcast({
            "type": "sync_conversations"
        })
        
        return {
            "response": response,
            "conversation_id": agent.current_conversation_id
        }
    
    @app.websocket("/ws/stream")
    async def websocket_stream(websocket: WebSocket):
        """流式聊天WebSocket"""
        await websocket.accept()
        
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    request = json.loads(data)
                    message = request.get("message", "")
                except json.JSONDecodeError:
                    message = data
                
                async for chunk in agent.stream_chat(message):
                    await websocket.send_json(chunk)
                    
                    if chunk.get("type") == "execute_result":
                        await _manager.broadcast({
                            "type": "sync_conversations"
                        })
                        
        except WebSocketDisconnect:
            pass
    
    @app.get("/api/usage")
    async def get_usage():
        """获取使用统计"""
        return agent.token_tracker.get_stats()
    
    @app.get("/api/usage/daily")
    async def get_daily_usage(days: int = 7):
        """获取每日使用量"""
        return agent.token_tracker.get_daily_usage(days)
    
    @app.get("/api/plugins")
    async def list_plugins():
        """列出插件"""
        plugins = agent.plugin_manager.list_plugins()
        for p in plugins:
            plugin = agent.plugin_manager.plugins.get(p["name"])
            if plugin and hasattr(plugin, 'get_config_schema'):
                p["config_schema"] = plugin.get_config_schema()
        return plugins
    
    @app.get("/api/plugins/{plugin_name}/config")
    async def get_plugin_config_schema(plugin_name: str):
        """获取插件配置模式"""
        plugin = agent.plugin_manager.plugins.get(plugin_name)
        if plugin and hasattr(plugin, 'get_config_schema'):
            schema = plugin.get_config_schema()
            schema["values"] = agent.plugin_manager.get_plugin_config(plugin_name)
            return schema
        return {"fields": [], "values": {}}
    
    @app.post("/api/plugins/{plugin_name}/config")
    async def save_plugin_config(plugin_name: str, config: dict):
        """保存插件配置"""
        for key, value in config.items():
            agent.plugin_manager.set_plugin_config(plugin_name, key, value)
        return {"success": True, "message": "配置已保存"}
    
    @app.get("/api/platforms")
    async def list_platforms():
        """列出所有可用平台"""
        from storm.platform import get_platform_manager
        from cloud.config import PLATFORMS
        from dataclasses import asdict
        manager = get_platform_manager()
        
        from storm.plugin import ConfigField
        
        platforms = []
        
        for name, info in PLATFORMS.items():
            adapter = manager.adapters.get(name)
            is_running = adapter.is_running() if adapter else False
            
            fields = [
                asdict(ConfigField(key="app_id", label="App ID", type="text", required=True)),
                asdict(ConfigField(key="app_secret", label="App Secret", type="password", required=True)),
                asdict(ConfigField(key="encrypt_key", label="Encrypt Key", type="password", required=False)),
                asdict(ConfigField(key="verification_token", label="Verification Token", type="text", required=False))
            ]
            
            schema = {
                "name": name,
                "description": info.get("name", name),
                "icon": info.get("icon", "📱"),
                "running": is_running,
                "fields": fields
            }
            platforms.append(schema)
        
        return platforms
    
    @app.get("/api/platforms/{platform_name}/config")
    async def get_platform_config_schema(platform_name: str):
        """获取平台配置模式"""
        from cloud.config import get_config_manager
        manager = get_config_manager()
        
        fields = [
            {"key": "app_id", "label": "App ID", "type": "text", "required": True, "default": "", "placeholder": "cli_xxx"},
            {"key": "app_secret", "label": "App Secret", "type": "password", "required": True, "default": "", "placeholder": "应用密钥"},
            {"key": "verification_token", "label": "Verification Token", "type": "text", "required": False, "default": "", "placeholder": "可选"}
        ]
        
        values = {}
        
        if platform_name == "feishu":
            values = {
                "app_id": manager.config.platform.feishu_app_id or "",
                "app_secret": manager.config.platform.feishu_app_secret or "",
                "verification_token": manager.config.platform.feishu_verification_token or ""
            }
        
        return {"fields": fields, "values": values}
    
    @app.post("/api/platforms/{platform_name}/config")
    async def save_platform_config(platform_name: str, config: dict):
        """保存平台配置"""
        from cloud.config import get_config_manager
        from breeze.logger import print_log
        
        config_manager = get_config_manager()
        
        if platform_name == "feishu":
            config_manager.config.platform.feishu_app_id = config.get("app_id", "")
            config_manager.config.platform.feishu_app_secret = config.get("app_secret", "")
            config_manager.config.platform.feishu_verification_token = config.get("verification_token", "")
            
            if "enabled" in config:
                config_manager.config.platform.feishu_enabled = config["enabled"]
            
            config_manager.save()
            print_log("SUCCESS", "飞书配置已保存，重启后生效", "平台配置")
            return {"success": True, "message": "配置已保存，重启后生效"}
        
        return {"success": False, "message": f"平台 {platform_name} 不支持"}
    
    @app.get("/api/plugins/{plugin_name}/files")
    async def get_plugin_files(plugin_name: str):
        """获取插件文件列表"""
        import os
        from pathlib import Path
        
        base_dir = Path(__file__).parent.parent
        
        possible_paths = [
            base_dir / "plugins" / plugin_name,
            base_dir / "storm" / "plugins" / plugin_name,
            base_dir / "storm" / "builtin" / plugin_name,
        ]
        
        for plugin_dir in possible_paths:
            if plugin_dir.exists() and plugin_dir.is_dir():
                files = []
                for f in plugin_dir.rglob("*"):
                    if f.is_file() and not f.name.endswith(".pyc") and "__pycache__" not in str(f):
                        files.append({
                            "name": f.name,
                            "path": str(f.absolute())
                        })
                return {"files": files, "plugin_dir": str(plugin_dir.absolute())}
        
        single_files = [
            (base_dir / "plugins" / f"{plugin_name}.py", f"{plugin_name}.py"),
            (base_dir / "storm" / "plugins" / f"{plugin_name}.py", f"{plugin_name}.py"),
            (base_dir / "storm" / "builtin" / f"{plugin_name}.py", f"{plugin_name}.py"),
        ]
        
        for single_file, name in single_files:
            if single_file.exists():
                return {"files": [{"name": name, "path": str(single_file.absolute())}]}
        
        return {"files": [], "error": f"插件 {plugin_name} 不存在"}
    
    @app.get("/api/plugins/{plugin_name}/file")
    async def get_plugin_file(plugin_name: str, file_path: str = ""):
        """获取插件文件内容"""
        from pathlib import Path
        
        if file_path:
            file = Path(file_path)
        else:
            file = Path("plugins") / plugin_name / "__init__.py"
            if not file.exists():
                file = Path("storm/plugins") / f"{plugin_name}.py"
        
        if not file.exists():
            return {"error": "文件不存在"}
        
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {"content": content, "path": str(file)}
    
    @app.post("/api/plugins/{plugin_name}/file")
    async def save_plugin_file(plugin_name: str, file_path: str, content: str):
        """保存插件文件"""
        from pathlib import Path
        from breeze.logger import print_log
        
        file = Path(file_path)
        if not file.exists():
            return {"error": "文件不存在"}
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_log("SUCCESS", f"文件已保存: {file.name}", "PluginEditor")
        return {"success": True, "message": "文件已保存"}
    
    @app.post("/api/plugins/{plugin_name}/reload")
    async def reload_plugin(plugin_name: str):
        """热重载插件"""
        try:
            from breeze.logger import print_log
            print_log("HOTRELOAD", f"正在热更新插件: {plugin_name}", "PluginManager")
            agent.plugin_manager.reload_plugin(plugin_name)
            print_log("SUCCESS", f"插件 {plugin_name} 热更新成功", "PluginManager")
            return {"success": True, "message": f"插件 {plugin_name} 已重载"}
        except Exception as e:
            from breeze.logger import print_log
            print_log("ERROR", f"插件 {plugin_name} 热更新失败: {str(e)}", "PluginManager")
            return {"success": False, "error": str(e)}
    
    @app.post("/api/plugins/{plugin_name}/enable")
    async def enable_plugin(plugin_name: str):
        """启用插件"""
        try:
            from breeze.logger import print_log
            from cloud.config import get_config_manager
            
            config_manager = get_config_manager()
            
            if plugin_name in config_manager.config.plugin.disabled_plugins:
                config_manager.config.plugin.disabled_plugins.remove(plugin_name)
                config_manager.save()
            
            if plugin_name not in agent.plugin_manager.plugins:
                agent.plugin_manager.load_plugin(plugin_name)
            
            if plugin_name in agent.plugin_manager.plugins:
                agent.plugin_manager.plugins[plugin_name].enabled = True
            
            print_log("SUCCESS", f"插件 {plugin_name} 已启用", "PluginManager")
            return {"success": True, "message": f"插件 {plugin_name} 已启用"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    @app.post("/api/plugins/{plugin_name}/disable")
    async def disable_plugin(plugin_name: str):
        """禁用插件"""
        try:
            from breeze.logger import print_log
            from cloud.config import get_config_manager
            
            config_manager = get_config_manager()
            
            if plugin_name not in config_manager.config.plugin.disabled_plugins:
                config_manager.config.plugin.disabled_plugins.append(plugin_name)
                config_manager.save()
            
            if plugin_name in agent.plugin_manager.plugins:
                agent.plugin_manager.plugins[plugin_name].enabled = False
            
            print_log("SUCCESS", f"插件 {plugin_name} 已禁用", "PluginManager")
            return {"success": True, "message": f"插件 {plugin_name} 已禁用"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    @app.get("/help/{doc_name}")
    async def get_help_doc(doc_name: str):
        """获取帮助文档"""
        from fastapi.responses import HTMLResponse
        import os
        
        doc_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cloud", "help", f"{doc_name}.md")
        
        if not os.path.exists(doc_path):
            return HTMLResponse(content="<h1>文档未找到</h1>", status_code=404)
        
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>WindAgent 文档</title>
            <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #0f0f1a;
                    color: #f1f5f9;
                    min-height: 100vh;
                    padding: 40px 20px;
                }}
                .container {{
                    max-width: 900px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #333;
                }}
                .header h1 {{
                    font-size: 2em;
                    margin-bottom: 10px;
                    background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                .header a {{
                    color: #6366f1;
                    text-decoration: none;
                }}
                .content {{
                    line-height: 1.8;
                }}
                .content h1 {{ font-size: 1.8em; margin: 40px 0 20px; color: #fff; }}
                .content h2 {{ font-size: 1.5em; margin: 30px 0 15px; color: #e2e8f0; border-bottom: 1px solid #333; padding-bottom: 10px; }}
                .content h3 {{ font-size: 1.2em; margin: 20px 0 10px; color: #cbd5e1; }}
                .content p {{ margin: 15px 0; color: #94a3b8; }}
                .content ul, .content ol {{ margin: 15px 0; padding-left: 30px; }}
                .content li {{ margin: 8px 0; color: #94a3b8; }}
                .content code {{
                    background: #1a1a2e;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-family: 'Consolas', monospace;
                    color: #f472b6;
                }}
                .content pre {{
                    background: #1a1a2e;
                    padding: 20px;
                    border-radius: 12px;
                    overflow-x: auto;
                    margin: 20px 0;
                    border: 1px solid #333;
                }}
                .content pre code {{
                    background: none;
                    padding: 0;
                    color: #e2e8f0;
                }}
                .content a {{
                    color: #6366f1;
                    text-decoration: none;
                }}
                .content a:hover {{
                    text-decoration: underline;
                }}
                .content table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                .content th, .content td {{
                    border: 1px solid #333;
                    padding: 12px;
                    text-align: left;
                }}
                .content th {{
                    background: #1a1a2e;
                }}
                .content blockquote {{
                    border-left: 4px solid #6366f1;
                    padding-left: 20px;
                    margin: 20px 0;
                    color: #94a3b8;
                }}
                .content hr {{
                    border: none;
                    border-top: 1px solid #333;
                    margin: 30px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>WindAgent 文档</h1>
                    <a href="/">← 返回首页</a>
                </div>
                <div class="content" id="content"></div>
            </div>
            <script>
                document.getElementById('content').innerHTML = marked.parse({repr(content)});
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html)
    
    @app.get("/api/conversations")
    async def list_conversations(limit: int = 20, platform: str = None):
        """列出对话"""
        if platform:
            conversations = agent.db.get_conversations_by_platform(platform, limit=limit)
        else:
            conversations = agent.db.get_conversations(limit=limit)
        return [
            {
                "id": c.id,
                "title": c.title,
                "platform": c.platform,
                "created_at": c.created_at,
                "updated_at": c.updated_at
            }
            for c in conversations
        ]
    
    @app.post("/api/conversations/default")
    async def get_or_create_default_conversation():
        """获取或创建默认会话"""
        conv = agent.db.get_or_create_default_conversation(platform="web")
        agent.current_conversation_id = conv.id
        agent.short_memory.clear()
        return {"conversation_id": conv.id, "title": conv.title}
    
    @app.post("/api/conversations")
    async def create_conversation(request: dict):
        """创建对话"""
        title = request.get("title", "新对话")
        platform = request.get("platform", "web")
        conv = agent.db.create_conversation(title=title, platform=platform)
        return {"conversation_id": conv.id, "title": conv.title}
    
    @app.delete("/api/conversations/{conv_id}")
    async def delete_conversation(conv_id: int):
        """删除对话"""
        from breeze.logger import print_log
        
        agent.db.delete_conversation(conv_id)
        
        if agent.current_conversation_id == conv_id:
            agent.current_conversation_id = None
            agent.short_memory.clear()
        
        print_log("INFO", f"会话 {conv_id} 已被删除", "系统")
        
        broadcast_to_all({
            "type": "conversation_deleted",
            "conversation_id": conv_id
        })
        
        return {"success": True}
    
    @app.post("/api/plugins/install")
    async def install_plugin(request: dict):
        """从URL安装插件"""
        url = request.get("url", "")
        if not url:
            return {"success": False, "message": "请提供仓库地址"}
        
        import subprocess
        from pathlib import Path
        from breeze.logger import print_log
        
        plugin_dir = Path("plugins")
        plugin_dir.mkdir(exist_ok=True)
        
        try:
            repo_name = url.split('/')[-1].replace('.git', '')
            plugin_path = plugin_dir / repo_name
            
            result = subprocess.run(
                ["git", "clone", url, str(plugin_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print_log("SUCCESS", f"插件 {repo_name} 安装成功", "PluginManager")
                return {"success": True, "message": f"插件 {repo_name} 安装成功"}
            else:
                return {"success": False, "message": f"克隆失败: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "克隆超时"}
        except FileNotFoundError:
            return {"success": False, "message": "请先安装 git"}
        except Exception as e:
            return {"success": False, "message": f"安装失败: {str(e)}"}
    
    @app.post("/api/plugins/create")
    async def create_plugin(request: dict):
        """创建新插件"""
        from pathlib import Path
        from breeze.logger import print_log
        import os
        
        name = request.get("name", "").strip()
        plugin_type = request.get("type", "single")  # single 或 package
        description = request.get("description", "")
        author = request.get("author", "")
        
        if not name:
            return {"success": False, "message": "请提供插件名称"}
        
        if not name.replace("_", "").replace("-", "").isalnum():
            return {"success": False, "message": "插件名称只能包含字母、数字、下划线和横线"}
        
        plugin_dir = Path("plugins")
        plugin_dir.mkdir(exist_ok=True)
        
        if plugin_type == "package":
            plugin_path = plugin_dir / name
            if plugin_path.exists():
                return {"success": False, "message": "插件已存在"}
            
            plugin_path.mkdir()
            
            init_content = f'''# -*- coding: utf-8 -*-
"""
{name} - {description}
"""

from storm.plugin import Plugin, command


class {name.title().replace("_", "").replace("-", "")}Plugin(Plugin):
    """插件描述"""
    
    name = "{name}"
    description = "{description}"
    version = "1.0.0"
    author = "{author}"
    
    def on_load(self):
        """加载插件"""
        self.log("info", "{name} 插件已加载")
    
    def on_unload(self):
        """卸载插件"""
        self.log("info", "{name} 插件已卸载")
'''
            
            with open(plugin_path / "__init__.py", 'w', encoding='utf-8') as f:
                f.write(init_content)
            
            adapter_content = f'''# -*- coding: utf-8 -*-
"""
{name} 适配器 - 可对接其他框架
"""

class Adapter:
    """消息适配器"""
    
    def __init__(self, plugin):
        self.plugin = plugin
    
    async def on_message(self, message: str, context: dict) -> str:
        """处理消息
        
        Args:
            message: 消息内容
            context: 上下文信息 (平台、用户等)
        
        Returns:
            回复内容
        """
        return None
    
    async def send_message(self, message: str, context: dict):
        """发送消息"""
        pass
'''
            
            with open(plugin_path / "adapter.py", 'w', encoding='utf-8') as f:
                f.write(adapter_content)
            
            print_log("SUCCESS", f"插件包 {name} 创建成功", "PluginManager")
            return {"success": True, "message": f"插件包 {name} 创建成功", "path": str(plugin_path)}
        
        else:
            plugin_file = plugin_dir / f"{name}.py"
            if plugin_file.exists():
                return {"success": False, "message": "插件已存在"}
            
            single_content = f'''# -*- coding: utf-8 -*-
"""
{name} - {description}
"""

from storm.plugin import Plugin, command


class {name.title().replace("_", "").replace("-", "")}Plugin(Plugin):
    """插件描述"""
    
    name = "{name}"
    description = "{description}"
    version = "1.0.0"
    author = "{author}"
    
    def on_load(self):
        """加载插件"""
        self.log("info", "{name} 插件已加载")
    
    @command(
        name="example",
        description="示例命令",
        usage="/example <参数>"
    )
    def example_command(self, args: str = "") -> str:
        """示例命令"""
        return f"你输入了: {{args}}"
'''
            
            with open(plugin_file, 'w', encoding='utf-8') as f:
                f.write(single_content)
            
            print_log("SUCCESS", f"单文件插件 {name} 创建成功", "PluginManager")
            return {"success": True, "message": f"插件 {name} 创建成功", "path": str(plugin_file)}
    
    @app.delete("/api/plugins/{name}")
    async def uninstall_plugin(name: str):
        """卸载插件"""
        success = agent.plugin_manager.unload_plugin(name)
        return {"success": success}
    
    @app.get("/api/plugins/available")
    async def get_available_plugins():
        """获取可安装的插件列表"""
        return agent.plugin_manager.discover_plugins()
    
    @app.get("/api/tools")
    async def get_tools():
        """获取所有可用工具"""
        tools = {}
        for name, info in agent.plugin_manager.tools.items():
            tools[name] = {
                "description": info.get("description", ""),
                "plugin": info.get("plugin", "unknown")
            }
        return {"tools": tools}
    
    @app.get("/api/conversations/{conv_id}/messages")
    async def get_messages(conv_id: int):
        """获取对话消息"""
        messages = agent.db.get_messages(conv_id)
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tokens": m.tokens,
                "created_at": m.created_at
            }
            for m in messages
        ]
    
    @app.delete("/api/conversations/{conv_id}/messages")
    async def clear_messages(conv_id: int):
        """清空对话消息"""
        from breeze.logger import print_log
        
        agent.db.delete_messages(conv_id)
        
        if agent.current_conversation_id == conv_id:
            agent.short_memory.clear()
        
        print_log("INFO", f"会话 {conv_id} 的消息已清空", "系统")
        
        return {"success": True}
    
    @app.post("/api/conversations/{conv_id}/switch")
    async def switch_conversation(conv_id: int):
        """切换会话并加载历史记忆"""
        from breeze.logger import print_log
        
        agent.short_memory.clear()
        agent.current_conversation_id = conv_id
        
        messages = agent.db.get_messages(conv_id, limit=agent.config.memory.short_term_limit)
        
        for msg in messages:
            from wind.token_tracker import count_tokens
            agent.short_memory.add(msg.role, msg.content, msg.tokens or count_tokens(msg.content))
        
        print_log("INFO", f"已切换到会话 {conv_id}，加载了 {len(messages)} 条历史消息", "记忆")
        
        return {"success": True, "loaded_messages": len(messages)}
    
    @app.get("/api/config")
    async def get_config_api():
        """获取配置"""
        from dataclasses import asdict
        return asdict(agent.config)
    
    @app.post("/api/config")
    async def set_config(request: ConfigRequest):
        """设置配置"""
        from cloud.config import get_config_manager
        manager = get_config_manager()
        manager.set(request.section, request.key, request.value)
        manager.save()
        return {"success": True}
    
    @app.post("/api/system/restart")
    async def restart_service():
        """重启服务"""
        import os
        import sys
        import subprocess
        
        def do_restart():
            import time
            time.sleep(1)
            python = sys.executable
            script = os.path.abspath("main.py")
            subprocess.Popen([python, script], cwd=os.path.dirname(script))
            os._exit(0)
        
        import threading
        threading.Thread(target=do_restart, daemon=True).start()
        
        return {"success": True, "message": "服务正在重启..."}
    
    @app.post("/api/system/stop")
    async def stop_service():
        """关闭服务"""
        import os
        
        def do_stop():
            import time
            time.sleep(1)
            os._exit(0)
        
        import threading
        threading.Thread(target=do_stop, daemon=True).start()
        
        return {"success": True, "message": "服务正在关闭..."}
    
    @app.get("/api/ai/providers")
    async def get_ai_providers():
        """获取AI厂商列表"""
        return AI_PROVIDERS
    
    @app.post("/api/platforms/{platform}/test")
    async def test_platform_connection(platform: str, config: dict = {}):
        """测试平台连接"""
        from breeze.logger import print_log
        
        if not config:
            return {"success": False, "message": "请先配置平台信息"}
        
        platform_validators = {
            "telegram": ["telegramToken", "telegramChatId"],
            "feishu": ["feishuAppId", "feishuSecret"],
            "qq": ["qqBotId", "qqToken"],
            "wechat": ["wechatAppId", "wechatSecret"],
            "discord": ["discordToken"],
            "slack": ["slackToken"]
        }
        
        required_fields = platform_validators.get(platform, [])
        missing_fields = [f for f in required_fields if f not in config or not config.get(f)]
        
        if missing_fields:
            return {"success": False, "message": f"缺少必要配置: {', '.join(missing_fields)}"}
        
        if platform == "feishu":
            print_log("INFO", f"正在测试飞书连接...", "飞书")
            try:
                import httpx
                app_id = config.get("feishuAppId")
                app_secret = config.get("feishuSecret")
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                        json={"app_id": app_id, "app_secret": app_secret},
                        timeout=10.0
                    )
                    data = response.json()
                    
                    if data.get("code") == 0:
                        print_log("SUCCESS", "飞书连接成功", "飞书")
                        return {"success": True, "message": "飞书连接成功！API验证通过"}
                    else:
                        error_msg = data.get("msg", "未知错误")
                        print_log("ERROR", f"飞书连接失败: {error_msg}", "飞书")
                        return {"success": False, "message": f"连接失败: {error_msg}"}
            except Exception as e:
                print_log("ERROR", f"飞书连接异常: {str(e)}", "飞书")
                return {"success": False, "message": f"连接异常: {str(e)}"}
        
        return {"success": True, "message": "配置验证通过"}
    
    @app.post("/webhook/feishu")
    async def feishu_webhook(request: dict):
        """飞书事件订阅回调"""
        from breeze.logger import print_log
        
        event_type = request.get("type")
        
        if event_type == "url_verification":
            print_log("SUCCESS", "飞书URL验证成功", "飞书")
            return {"challenge": request.get("challenge")}
        
        if hasattr(app.state, "feishu") and app.state.feishu:
            return await app.state.feishu.handle_webhook_event(request)
        
        return {"success": True}
    
    _guardian = None
    
    @app.get("/api/guardian/status")
    async def get_guardian_status():
        """获取守护模式状态"""
        global _guardian
        if _guardian is None:
            from wind.guardian import GuardianMode
            _guardian = GuardianMode(agent)
        return _guardian.get_status()
    
    @app.post("/api/guardian/start")
    async def start_guardian():
        """启动守护模式"""
        global _guardian
        if _guardian is None:
            from wind.guardian import GuardianMode
            _guardian = GuardianMode(agent)
        return _guardian.start()
    
    @app.post("/api/guardian/stop")
    async def stop_guardian():
        """停止守护模式"""
        global _guardian
        if _guardian:
            return _guardian.stop()
        return {"success": False, "message": "守护模式未初始化"}
    
    @app.post("/api/guardian/learn")
    async def guardian_learn(key: str, value: Any):
        """守护模式学习用户偏好"""
        global _guardian
        if _guardian:
            _guardian.learn_user_preference(key, value)
            return {"success": True, "message": f"已学习: {key}"}
        return {"success": False, "message": "守护模式未初始化"}
    
    @app.post("/api/guardian/ask")
    async def guardian_ask(context: str):
        """向守护AI请求建议"""
        global _guardian
        if _guardian:
            advice = _guardian.ask_ai_for_advice(context)
            return {"success": True, "advice": advice}
        return {"success": False, "message": "守护模式未初始化"}
    
    @app.get("/api/logs/stats")
    async def get_log_stats():
        """获取日志统计"""
        return agent.log_manager.get_log_stats()
    
    @app.get("/api/logs/chat")
    async def get_chat_logs(limit: int = 100):
        """获取聊天日志"""
        return {"logs": agent.log_manager.get_chat_logs(limit)}
    
    @app.get("/api/logs/execute")
    async def get_execute_logs(limit: int = 50):
        """获取执行日志"""
        return {"logs": agent.log_manager.get_execute_logs(limit)}
    
    @app.get("/api/logs/system")
    async def get_system_logs(limit: int = 200):
        """获取系统日志"""
        return {"logs": agent.log_manager.get_system_logs(limit)}
    
    @app.delete("/api/logs")
    async def clear_logs(log_type: str = 'all'):
        """清除日志"""
        agent.log_manager.clear_logs(log_type)
        return {"success": True, "message": f"{log_type} 日志已清除"}
    
    @app.get("/api/logs/export")
    async def export_logs(log_type: str = 'all'):
        """导出日志"""
        import tempfile
        output_path = tempfile.mktemp(suffix='.json')
        agent.log_manager.export_logs(output_path, log_type)
        from fastapi.responses import FileResponse
        return FileResponse(
            output_path,
            filename=f"windagent_logs_{log_type}.json",
            media_type="application/json"
        )
    
    @app.post("/api/security/check")
    async def check_command_security(command: str):
        """检查命令安全性"""
        is_dangerous = is_dangerous_command(command)
        return {
            "safe": not is_dangerous,
            "message": "该命令被安全系统拦截" if is_dangerous else "命令安全"
        }
    
    @app.get("/api/persona")
    async def get_persona():
        """获取人设配置"""
        from dataclasses import asdict
        return asdict(agent.config.persona)
    
    @app.post("/api/persona")
    async def set_persona(name: str = "", description: str = "", personality: str = "", speaking_style: str = "", custom_prompt: str = ""):
        """设置人设"""
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
        if custom_prompt:
            manager.config.persona.custom_prompt = custom_prompt
        manager.save()
        return {"success": True}
    
    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket):
        """WebSocket聊天 - 支持多设备同步"""
        await _manager.connect(websocket)
        
        try:
            while True:
                data = await websocket.receive_text()
                
                try:
                    request = json.loads(data)
                    message = request.get("message", "")
                except json.JSONDecodeError:
                    message = data
                
                response = agent.process_message(message)
                
                result = {
                    "type": "message",
                    "response": response,
                    "conversation_id": agent.current_conversation_id
                }
                
                await _manager.broadcast(result)
                
                await _manager.broadcast({"type": "sync_conversations"})
                
        except WebSocketDisconnect:
            _manager.disconnect(websocket)
    
    @app.websocket("/ws/sync")
    async def websocket_sync(websocket: WebSocket):
        """WebSocket同步 - 用于实时更新对话列表"""
        await _manager.connect(websocket)
        
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            _manager.disconnect(websocket)
    
    return app
