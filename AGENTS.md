# WindAgent AI 开发指引

## 项目概览

WindAgent 是基于 Python 3.8+ 的 AI 智能体框架，采用 FastAPI、插件系统、多平台适配架构。核心：Agent 核心、插件管理器、平台适配器、Web 管理后台。

## 开发规范

- **工具**：`PluginBase`、`@command`、`@tool`、`@hook`，禁止重复实现
- **路径**：`get_config_manager()`、`config.py`、`LOCALAPPDATA\WindAgent\`
- **配置**：`cloud/config/` 默认配置，`LOCALAPPDATA\WindAgent\` 用户配置

## 文档

- [docs/quick-start.md](docs/quick-start.md) - 快速开始
- [docs/plugin-dev.md](docs/plugin-dev.md) - 插件开发
- [docs/platform.md](docs/platform.md) - 平台接入
- [docs/api.md](docs/api.md) - API 参考
- [docs/faq.md](docs/faq.md) - 常见问题

## 项目结构

```
WindAgent/
├── breeze/          # 核心模块 (配置、日志、环境)
├── cloud/           # 云服务模块 (配置、记忆、帮助)
├── storm/           # 插件系统 (插件管理器、内置插件)
│   └── builtin/     # 内置插件目录
├── horizon/         # Web 界面 (静态资源、模板)
├── wind/            # 主程序 (Agent 核心、API 路由)
├── docs/            # 文档目录
├── main.py          # 程序入口
└── install.bat      # 安装脚本
```

## 核心模块

- **wind/agent.py** - Agent 核心，AI 对话处理
- **wind/routes.py** - API 路由定义
- **storm/plugin.py** - 插件管理器
- **cloud/config.py** - 配置管理
- **cloud/memory/** - 记忆系统
