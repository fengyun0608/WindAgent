# 快速开始

本指南将帮助你快速安装和启动 WindAgent。

## 系统要求

- Python 3.8 或更高版本
- 支持 Windows / Linux / macOS

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/fengyun0608/WindAgent.git
cd WindAgent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python main.py
```

### 4. 访问界面

启动成功后，打开浏览器访问：

- 本地访问: http://127.0.0.1:8765
- 网络访问: http://你的IP:8765

## 配置 AI

### 方法1：通过 Web 界面配置

1. 访问管理后台 http://127.0.0.1:8765/
2. 进入「AI 配置」页面
3. 选择 AI 厂商
4. 填写 API Key 和其他配置
5. 点击「保存配置」

### 方法2：手动编辑配置文件

配置文件位置：

- Windows: `%LOCALAPPDATA%\WindAgent\config.json`
- Linux/macOS: `~/.local/share/WindAgent/config.json`

编辑配置文件：

```json
{
  "ai": {
    "provider": "openai",
    "api_key": "your-api-key",
    "api_base": "https://api.openai.com/v1",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

## 支持的 AI 厂商

| 厂商 | API 地址 | 默认模型 |
|------|----------|----------|
| OpenAI | https://api.openai.com/v1 | gpt-3.5-turbo |
| Claude | https://api.anthropic.com/v1 | claude-3-sonnet-20240229 |
| 通义千问 | https://dashscope.aliyuncs.com/compatible-mode/v1 | qwen-turbo |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| Moonshot | https://api.moonshot.cn/v1 | moonshot-v1-8k |
| 智谱AI | https://open.bigmodel.cn/api/paas/v4 | glm-4 |
| 自定义 | 自定义 | 自定义 |

## 配置人设

### 通过 Web 界面

1. 进入「人设配置」页面
2. 修改 AI 的名字、描述、性格、说话风格
3. 点击「保存配置」

### 配置项说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| 名字 | AI 的名字 | 风云 |
| 描述 | AI 的简介 | 一个友好的 AI 助手 |
| 性格 | AI 的性格特点 | 热情、耐心、专业 |
| 说话风格 | AI 的说话方式 | 亲切自然 |

## 开始对话

### 网页端

1. 访问 http://127.0.0.1:8765
2. 在输入框输入消息
3. 点击发送或按回车

### 使用命令

```
/help          # 查看帮助
/weather 北京   # 查询天气
/calc 1+1      # 计算
```

### 使用工具

直接在对话中描述你的需求，AI 会自动调用工具：

```
帮我搜索一下今天的新闻
北京今天天气怎么样？
现在几点了？
```

## 下一步

- [插件开发指南](./plugin-dev.md) - 开发自定义插件
- [平台接入指南](./platform.md) - 接入飞书等平台
- [API 参考](./api.md) - 了解 API 接口

## 常见问题

### Q: 启动失败怎么办？

A: 检查 Python 版本是否 >= 3.8，依赖是否安装完整。

### Q: API Key 无效？

A: 确认 API Key 是否正确，是否已激活。

### Q: 如何修改端口？

A: 编辑 `cloud/config.py` 中的 `WEB_PORT` 配置。
