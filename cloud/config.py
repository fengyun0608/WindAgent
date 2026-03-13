# -*- coding: utf-8 -*-
"""
WindAgent 配置管理
完全开源免费 - 用户自行对接API
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

from cloud.env import get_environment, DeviceType, OSType


AI_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default_model": "gpt-3.5-turbo"
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "api_base": "https://api.anthropic.com",
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "default_model": "claude-3-sonnet"
    },
    "google": {
        "name": "Google Gemini",
        "api_base": "https://generativelanguage.googleapis.com/v1",
        "models": ["gemini-pro", "gemini-pro-vision"],
        "default_model": "gemini-pro"
    },
    "deepseek": {
        "name": "DeepSeek 深度求索",
        "api_base": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-coder"],
        "default_model": "deepseek-chat"
    },
    "moonshot": {
        "name": "Moonshot Kimi",
        "api_base": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "default_model": "moonshot-v1-8k"
    },
    "zhipu": {
        "name": "智谱 GLM",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4", "glm-3-turbo"],
        "default_model": "glm-3-turbo"
    },
    "qwen": {
        "name": "阿里通义千问",
        "api_base": "https://dashscope.aliyuncs.com/api/v1",
        "models": ["qwen-turbo", "qwen-plus", "qwen-max"],
        "default_model": "qwen-turbo"
    },
    "baidu": {
        "name": "百度文心一言",
        "api_base": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1",
        "models": ["ernie-4.0", "ernie-3.5-turbo"],
        "default_model": "ernie-3.5-turbo"
    },
    "custom": {
        "name": "自定义",
        "api_base": "",
        "models": [],
        "default_model": ""
    }
}

PLATFORMS = {
    "feishu": {
        "name": "飞书",
        "icon": "🪽",
        "description": "飞书机器人接入",
        "adapter": "storm.adapters.feishu.FeishuAdapter"
    }
}

DANGEROUS_COMMANDS = [
    "rm -rf",
    "del /f /s /q",
    "format",
    "fdisk",
    "mkfs",
    "dd if=",
    "> /dev/sd",
    "shutdown",
    "reboot",
    "init 0",
    "init 6",
    "systemctl stop",
    "net stop",
    "taskkill /f /im",
    "reg delete",
    "bcdedit /delete",
    "bootcfg /delete",
    "attrib -r -s -h",
    "icacls /reset",
    "takeown /f",
    "cipher /w",
    "sdelete",
    "wipefs",
    "shred",
]


@dataclass
class PersonaConfig:
    """人设配置"""
    name: str = "纳西妲"
    description: str = "一个友好、专业的AI助手"
    personality: str = "温和、耐心、乐于助人"
    speaking_style: str = "简洁明了，直接回答问题"
    expertise: List[str] = field(default_factory=lambda: ["编程", "写作", "问答"])
    custom_prompt: str = ""


@dataclass
class SecurityConfig:
    """安全配置"""
    enabled: bool = True
    block_dangerous_commands: bool = True
    max_file_size_mb: int = 100
    allowed_file_types: List[str] = field(default_factory=lambda: [
        ".txt", ".md", ".py", ".js", ".json", ".yaml", ".yml",
        ".html", ".css", ".xml", ".csv", ".log"
    ])
    sandbox_mode: bool = False


@dataclass
class AIConfig:
    """AI配置 - 用户自行配置API"""
    provider: str = "openai"
    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 60
    active: bool = True
    
    openai_api_key: str = ""
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"
    
    claude_api_key: str = ""
    claude_api_base: str = "https://api.anthropic.com/v1"
    claude_model: str = "claude-3-sonnet-20240229"
    
    qwen_api_key: str = ""
    qwen_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-turbo"
    
    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    
    moonshot_api_key: str = ""
    moonshot_api_base: str = "https://api.moonshot.cn/v1"
    moonshot_model: str = "moonshot-v1-8k"
    
    zhipu_api_key: str = ""
    zhipu_api_base: str = "https://open.bigmodel.cn/api/paas/v4"
    zhipu_model: str = "glm-4"
    
    custom_api_key: str = ""
    custom_api_base: str = ""
    custom_model: str = ""


@dataclass
class TokenConfig:
    """Token统计配置 - 仅本地统计，不涉及付费"""
    enabled: bool = True
    show_usage: bool = True
    warn_threshold: int = 100000
    history_days: int = 30


@dataclass
class MemoryConfig:
    """记忆配置"""
    enabled: bool = True
    short_term_limit: int = 10
    long_term_enabled: bool = True
    vector_db: str = "chroma"


@dataclass
class PluginConfig:
    """插件配置"""
    enabled: bool = True
    auto_load: bool = True
    builtin_plugins: List[str] = field(default_factory=lambda: [
        "weather", "search", "calculator"
    ])
    external_plugins_dir: str = ""
    disabled_plugins: List[str] = field(default_factory=list)


@dataclass
class ServerConfig:
    """服务器配置"""
    host: str = "127.0.0.1"
    port: int = 8765
    debug: bool = False
    cors_origins: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class PlatformConfig:
    """平台配置"""
    telegram_token: str = ""
    telegram_enabled: bool = False
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_encrypt_key: str = ""
    feishu_verification_token: str = ""
    feishu_enabled: bool = False
    qq_bot_id: str = ""
    qq_bot_token: str = ""
    qq_enabled: bool = False
    wechat_token: str = ""
    wechat_enabled: bool = False
    discord_token: str = ""
    discord_enabled: bool = False
    slack_token: str = ""
    slack_enabled: bool = False


@dataclass
class UIConfig:
    """界面配置"""
    language: str = "zh-CN"
    theme: str = "auto"
    show_token_count: bool = True
    show_env_info: bool = True


@dataclass
class WindAgentConfig:
    """WindAgent 主配置"""
    name: str = "WindAgent"
    version: str = "0.1.0"
    author: str = "风云"
    license: str = "MIT"
    
    persona: PersonaConfig = field(default_factory=PersonaConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    token: TokenConfig = field(default_factory=TokenConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    plugin: PluginConfig = field(default_factory=PluginConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    platform: PlatformConfig = field(default_factory=PlatformConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    
    data_dir: str = ""
    log_level: str = "INFO"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.env = get_environment()
        self.config_path = config_path or self._get_default_config_path()
        self.config: WindAgentConfig = WindAgentConfig()
        self._load_config()
        self._apply_env_overrides()
        self._adjust_for_device()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        return os.path.join(self.env.data_dir, "config.json")
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._apply_dict(data)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
    
    def _apply_dict(self, data: Dict[str, Any]):
        """应用字典配置"""
        for key, value in data.items():
            if hasattr(self.config, key):
                attr = getattr(self.config, key)
                if hasattr(attr, '__dataclass_fields__'):
                    for sub_key, sub_value in value.items():
                        if hasattr(attr, sub_key):
                            setattr(attr, sub_key, sub_value)
                else:
                    setattr(self.config, key, value)
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        env_mappings = {
            "WINDAGENT_AI_API_KEY": ("ai", "api_key"),
            "WINDAGENT_AI_API_BASE": ("ai", "api_base"),
            "WINDAGENT_AI_MODEL": ("ai", "model"),
            "WINDAGENT_SERVER_HOST": ("server", "host"),
            "WINDAGENT_SERVER_PORT": ("server", "port"),
            "WINDAGENT_LOG_LEVEL": (None, "log_level"),
            "WINDAGENT_DATA_DIR": (None, "data_dir"),
        }
        
        for env_key, (section, attr) in env_mappings.items():
            value = os.environ.get(env_key)
            if value:
                if section:
                    section_obj = getattr(self.config, section)
                    setattr(section_obj, attr, value)
                else:
                    setattr(self.config, attr, value)
    
    def _adjust_for_device(self):
        """根据设备类型调整配置"""
        if not self.config.data_dir:
            self.config.data_dir = self.env.data_dir
        
        if self.env.is_tablet:
            self.config.memory.short_term_limit = 5
            self.config.ai.max_tokens = min(self.config.ai.max_tokens, 1000)
        
        if self.env.is_portable:
            self.config.ai.timeout = 30
    
    def save(self):
        """保存配置"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        data = asdict(self.config)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get(self, section: str, key: str = None) -> Any:
        """获取配置项"""
        section_obj = getattr(self.config, section)
        if key:
            return getattr(section_obj, key)
        return section_obj
    
    def set(self, section: str, key: str, value: Any):
        """设置配置项"""
        section_obj = getattr(self.config, section)
        setattr(section_obj, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self.config)


_config_manager: Optional[ConfigManager] = None


def get_config() -> WindAgentConfig:
    """获取配置"""
    global _config_manager
    if not _config_manager:
        _config_manager = ConfigManager()
    return _config_manager.config


def get_config_manager() -> ConfigManager:
    """获取配置管理器"""
    global _config_manager
    if not _config_manager:
        _config_manager = ConfigManager()
    return _config_manager


def is_dangerous_command(command: str) -> bool:
    """检查是否为危险命令"""
    command_lower = command.lower()
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous.lower() in command_lower:
            return True
    return False


def get_ai_providers() -> Dict:
    """获取AI厂商列表"""
    return AI_PROVIDERS


def get_platforms() -> Dict:
    """获取平台列表"""
    return PLATFORMS
