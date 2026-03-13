# WindAgent - 风云智能体

<div align="center">

![WindAgent Logo](https://img.shields.io/badge/WindAgent-v0.1.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8%2B-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**一个强大的 AI 智能体框架，支持多平台接入和插件扩展**

[快速开始](#快速开始) · [功能特性](#功能特性) · [文档](#文档) · [贡献指南](#贡献指南)

</div>

---

## 简介

WindAgent 是一个开源的 AI 智能体框架，具有以下特点：

- **多厂商支持**：兼容 OpenAI、Claude、通义千问、DeepSeek 等主流 AI 厂商
- **多平台接入**：支持飞书、Telegram、QQ、微信等平台
- **插件系统**：强大的插件机制，轻松扩展 AI 能力
- **Web 管理后台**：现代化的管理界面，可视化配置
- **记忆系统**：支持短期记忆和长期记忆
- **工具调用**：AI 可自主调用工具完成任务

## 功能特性

### 核心功能

| 功能 | 描述 |
|------|------|
| 智能对话 | 多平台 AI 对话，支持上下文记忆 |
| 多厂商配置 | 每个厂商独立配置，一键切换 |
| 插件系统 | 支持单文件和多文件插件包 |
| 平台接入 | 飞书、Telegram、QQ 等平台适配器 |
| 工具调用 | AI 自主调用工具完成任务 |
| 人设配置 | 自定义 AI 的名字、性格、说话风格 |

### 内置工具

- **web_search**: 搜索互联网获取实时信息
- **fetch_url**: 获取网页内容
- **get_weather**: 获取天气信息
- **get_current_time**: 获取当前时间
- **calculate**: 计算数学表达式
- **execute_command**: 执行系统命令
- **set_persona**: 修改 AI 人设配置

## 项目结构

```
WindAgent/
├── breeze/                 # 核心模块
│   ├── config.py          # 配置管理
│   ├── env.py             # 环境检测
│   └── logger.py          # 日志系统
├── cloud/                  # 云服务模块
│   ├── config/            # 配置定义
│   ├── help/              # 帮助文档
│   └── memory/            # 记忆系统
├── storm/                  # 插件系统
│   ├── builtin/           # 内置插件
│   │   ├── official/      # 官方插件包
│   │   ├── example.py     # 示例插件
│   │   └── example_package/ # 示例插件包
│   └── plugin.py          # 插件管理器
├── horizon/                # Web 界面
│   ├── static/            # 静态资源
│   └── templates/         # 页面模板
├── wind/                   # 主程序
│   ├── agent.py           # 智能体核心
│   └── routes.py          # API 路由
├── docs/                   # 文档目录
│   ├── README.md          # 文档首页
│   ├── quick-start.md     # 快速开始
│   ├── plugin-dev.md      # 插件开发
│   ├── platform.md        # 平台接入
│   ├── api.md             # API 参考
│   └── faq.md             # 常见问题
├── main.py                 # 程序入口
├── CHANGELOG.md            # 更新日志
├── LICENSE                 # 开源协议
└── README.md               # 项目说明
```

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/fengyun0608/WindAgent.git
cd WindAgent

# 安装依赖
pip install -r requirements.txt
```

### 启动

```bash
python main.py
```

### 访问

- 本地访问: http://127.0.0.1:8765
- 管理后台: http://127.0.0.1:8765/

详细说明请查看 [快速开始指南](./docs/quick-start.md)

## 文档

| 文档 | 说明 |
|------|------|
| [快速开始](./docs/quick-start.md) | 安装和启动指南 |
| [插件开发](./docs/plugin-dev.md) | 插件开发完整教程 |
| [平台接入](./docs/platform.md) | 飞书等平台接入指南 |
| [API 参考](./docs/api.md) | API 接口文档 |
| [常见问题](./docs/faq.md) | FAQ 解答 |

## 插件开发

### 单文件插件

```python
# storm/builtin/hello.py

from storm.plugin import PluginBase, command, tool

class HelloPlugin(PluginBase):
    name = "hello"
    version = "1.0.0"
    description = "问候插件"
    author = "你的名字"
    
    @command("hello", help="发送问候")
    def hello(self, args: str):
        return f"你好！{args}"
    
    @tool("greet", description="发送问候")
    def greet(self, name: str = "朋友") -> str:
        return f"你好，{name}！"
```

### 多文件插件包

```
storm/builtin/my_plugin/
├── __init__.py      # 主插件类
├── api.py           # API 调用
└── utils.py         # 工具函数
```

详细文档请查看 [插件开发指南](./docs/plugin-dev.md)

## 平台接入

### 飞书

1. 创建飞书应用
2. 配置 App ID 和 App Secret
3. 启用飞书平台
4. 重启服务

详细文档请查看 [平台接入指南](./docs/platform.md)

## 配置

配置文件位于用户数据目录：

- Windows: `%LOCALAPPDATA%\WindAgent\config.json`
- Linux/macOS: `~/.local/share/WindAgent/config.json`

### AI 配置

```json
{
  "ai": {
    "provider": "openai",
    "api_key": "your-api-key",
    "api_base": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo"
  }
}
```

### 人设配置

```json
{
  "persona": {
    "name": "风云",
    "description": "一个友好的 AI 助手",
    "personality": "热情、耐心、专业",
    "speaking_style": "亲切自然"
  }
}
```

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 开源协议

本项目采用 [MIT](./LICENSE) 协议开源。

## 作者

- **风云** - [fengyun0608](https://github.com/fengyun0608)

## 致谢

感谢所有贡献者和开源社区的支持！

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**

</div>
