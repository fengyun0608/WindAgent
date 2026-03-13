# 平台接入指南

本文档介绍如何将 WindAgent 接入各大平台。

## 支持的平台

| 平台 | 状态 | 说明 |
|------|------|------|
| 飞书 | ✅ 已支持 | 长连接模式，无需公网服务器 |
| Telegram | 🚧 开发中 | 即将支持 |
| QQ | 🚧 开发中 | 即将支持 |
| 微信 | 🚧 开发中 | 即将支持 |
| Discord | 📅 计划中 | 计划支持 |
| Slack | 📅 计划中 | 计划支持 |

---

## 飞书接入

### 1. 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 App ID 和 App Secret

### 2. 配置权限

在飞书应用管理后台，添加以下权限：

- `im:message` - 获取与发送消息
- `im:message:send_as_bot` - 以应用身份发消息
- `im:chat` - 获取群组信息

### 3. 配置 WindAgent

#### 通过 Web 界面

1. 进入「平台接入」页面
2. 找到飞书平台，点击「配置」
3. 填写 App ID 和 App Secret
4. 启用飞书平台
5. 重启服务

#### 手动配置

编辑配置文件：

```json
{
  "platform": {
    "feishu_app_id": "cli_xxx",
    "feishu_app_secret": "xxx",
    "feishu_enabled": true
  }
}
```

### 4. 事件订阅

飞书平台使用长连接模式，无需配置公网服务器地址。

### 5. 测试

1. 在飞书中找到你的应用
2. 发送消息测试

---

## Telegram 接入（开发中）

### 1. 创建机器人

1. 在 Telegram 中找到 @BotFather
2. 发送 `/newbot` 创建机器人
3. 获取 Bot Token

### 2. 配置 WindAgent

```json
{
  "platform": {
    "telegram_token": "xxx",
    "telegram_enabled": true
  }
}
```

---

## QQ 接入（开发中）

支持多种 QQ 协议：

- go-cqhttp
- OneBot
- Mirai

---

## 微信接入（开发中）

支持：

- 企业微信
- 微信公众号

---

## 自定义平台

你可以通过开发插件来支持更多平台。

### 平台适配器接口

```python
from storm.platform import PlatformAdapter

class MyPlatform(PlatformAdapter):
    name = "my_platform"
    
    async def start(self):
        """启动平台"""
        pass
    
    async def stop(self):
        """停止平台"""
        pass
    
    async def send_message(self, user_id: str, message: str):
        """发送消息"""
        pass
    
    async def on_message(self, message: dict):
        """收到消息"""
        # 调用 AI 处理
        reply = await self.agent.process_message(message["content"])
        await self.send_message(message["user_id"], reply)
```

---

## 常见问题

### Q: 飞书消息收不到？

A: 检查：
1. App ID 和 App Secret 是否正确
2. 权限是否配置
3. 服务是否启动

### Q: 如何支持多平台同时运行？

A: 在配置中启用多个平台即可，WindAgent 会同时运行所有启用的平台。

---

## 下一步

- [API 参考](./api.md) - 了解 API 接口
- [插件开发](./plugin-dev.md) - 开发自定义插件
