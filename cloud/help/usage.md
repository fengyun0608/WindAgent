# WindAgent 使用指南

## 项目说明

WindAgent 是一个**完全开源免费**的AI智能体框架。
- 用户自行配置API Key
- 本地运行，数据隐私
- Token统计仅用于本地记录，不涉及任何付费

## 快速开始

### 1. 配置API
首次使用需要配置你的API：

**方式一：配置文件**
编辑配置文件（首次运行自动生成）：
- Windows: `%LOCALAPPDATA%\WindAgent\config.json`
- macOS: `~/Library/Application Support/WindAgent/config.json`
- Linux: `~/.windagent/config.json`

修改以下字段：
```json
{
  "ai": {
    "provider": "openai",
    "api_key": "你的API Key",
    "api_base": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo"
  }
}
```

**方式二：环境变量**
```bash
# Windows
set WINDAGENT_AI_API_KEY=你的API Key

# Linux/macOS
export WINDAGENT_AI_API_KEY=你的API Key
```

### 2. 启动服务
```bash
python main.py
```

### 3. 访问界面
打开浏览器访问: http://127.0.0.1:8765

## 支持的API提供商

| 提供商 | api_base |
|--------|----------|
| OpenAI | https://api.openai.com/v1 |
| Azure OpenAI | https://your-resource.openai.azure.com |
| Claude | https://api.anthropic.com |
| 本地模型 | http://localhost:8000 |
| 其他兼容API | 根据服务商文档配置 |

## Token 统计

Token统计仅用于本地记录，帮助你了解使用情况：
- 显示每次对话消耗的Token数
- 统计历史使用量
- 不涉及任何付费功能

## 插件系统

### 查看已安装插件
```
/plugins
```

### 安装插件
```
/plugin install <插件名>
```

### 卸载插件
```
/plugin uninstall <插件名>
```

## 环境感知

WindAgent 会自动检测你的运行环境：
- Windows 桌面
- Windows 平板
- MacBook
- iPad
- Linux 桌面/平板

根据不同环境，会自动适配：
- 命令格式
- 资源使用
- 界面显示

## 常用命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/status` | 查看状态 |
| `/usage` | 查看Token使用统计 |
| `/clear` | 清除对话 |
| `/export` | 导出对话 |
| `/config` | 配置设置 |

## 常见问题

### Q: 如何更换AI模型？
编辑配置文件中的 `ai.model` 字段。

### Q: 如何使用本地模型？
配置 `ai.api_base` 指向本地模型服务地址。

### Q: 数据存储在哪里？
所有数据存储在本地 `data_dir` 目录中。

### Q: Token统计会同步到服务器吗？
不会。所有统计数据仅存储在本地。

## 隐私说明

WindAgent 采用本地优先策略：
- 对话记录存储在本地
- 不会上传任何用户数据
- API调用直接从你的设备发起
- 可以完全离线配置

## 开源协议

MIT License - 完全开源免费
