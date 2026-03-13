# API 参考

本文档介绍 WindAgent 的 API 接口。

## 基础信息

- 基础 URL: `http://127.0.0.1:8765`
- 数据格式: JSON
- 编码: UTF-8

---

## 对话接口

### 发送消息

```http
POST /api/chat
```

**请求体：**
```json
{
  "message": "你好",
  "conversation_id": 1
}
```

**响应：**
```json
{
  "reply": "你好！有什么可以帮助你的吗？",
  "conversation_id": 1
}
```

### 获取对话历史

```http
GET /api/conversations/{id}/messages
```

**响应：**
```json
[
  {
    "id": 1,
    "role": "user",
    "content": "你好",
    "created_at": "2026-03-13T09:00:00"
  },
  {
    "id": 2,
    "role": "assistant",
    "content": "你好！有什么可以帮助你的吗？",
    "created_at": "2026-03-13T09:00:01"
  }
]
```

---

## 会话管理

### 获取会话列表

```http
GET /api/conversations
```

**参数：**
- `limit`: 返回数量（默认 20）
- `platform`: 平台过滤

**响应：**
```json
[
  {
    "id": 1,
    "title": "新对话",
    "platform": "web",
    "created_at": "2026-03-13T09:00:00"
  }
]
```

### 创建会话

```http
POST /api/conversations
```

**请求体：**
```json
{
  "title": "新对话"
}
```

### 删除会话

```http
DELETE /api/conversations/{id}
```

---

## 配置接口

### 获取配置

```http
GET /api/config
```

**响应：**
```json
{
  "ai": {
    "provider": "openai",
    "api_key": "xxx",
    "model": "gpt-3.5-turbo"
  },
  "persona": {
    "name": "风云",
    "description": "一个友好的 AI 助手"
  }
}
```

### 设置配置

```http
POST /api/config
```

**请求体：**
```json
{
  "section": "ai",
  "key": "api_key",
  "value": "new-api-key"
}
```

---

## 插件接口

### 获取插件列表

```http
GET /api/plugins
```

**响应：**
```json
[
  {
    "name": "official",
    "version": "1.0.0",
    "description": "官方插件包",
    "enabled": true
  }
]
```

### 启用插件

```http
POST /api/plugins/{name}/enable
```

### 禁用插件

```http
POST /api/plugins/{name}/disable
```

### 重载插件

```http
POST /api/plugins/{name}/reload
```

### 获取插件文件

```http
GET /api/plugins/{name}/files
```

### 保存插件文件

```http
POST /api/plugins/{name}/files
```

**请求体：**
```json
{
  "path": "storm/builtin/official/__init__.py",
  "content": "# code..."
}
```

---

## 工具接口

### 获取工具列表

```http
GET /api/tools
```

**响应：**
```json
{
  "tools": {
    "web_search": {
      "description": "搜索互联网获取实时信息",
      "plugin": "official"
    },
    "get_weather": {
      "description": "获取天气信息",
      "plugin": "official"
    }
  }
}
```

---

## 平台接口

### 获取平台列表

```http
GET /api/platforms
```

**响应：**
```json
[
  {
    "name": "feishu",
    "description": "飞书",
    "icon": "📱",
    "running": false
  }
]
```

### 获取平台配置

```http
GET /api/platforms/{name}/config
```

### 保存平台配置

```http
POST /api/platforms/{name}/config
```

**请求体：**
```json
{
  "app_id": "cli_xxx",
  "app_secret": "xxx"
}
```

---

## 系统接口

### 获取状态

```http
GET /api/status
```

**响应：**
```json
{
  "version": "0.1.0",
  "api_configured": true,
  "model": "gpt-3.5-turbo",
  "plugins_loaded": 3
}
```

### 重启服务

```http
POST /api/system/restart
```

### 停止服务

```http
POST /api/system/stop
```

---

## WebSocket 接口

### 连接

```
ws://127.0.0.1:8765/ws
```

### 发送消息

```json
{
  "type": "chat",
  "message": "你好"
}
```

### 接收消息

```json
{
  "type": "reply",
  "content": "你好！有什么可以帮助你的吗？"
}
```

### 流式响应

```json
{
  "type": "stream",
  "content": "你",
  "done": false
}
```

```json
{
  "type": "stream",
  "content": "好",
  "done": false
}
```

```json
{
  "type": "stream",
  "content": "！",
  "done": true
}
```

---

## 错误响应

所有错误响应格式：

```json
{
  "error": "错误信息",
  "detail": "详细说明"
}
```

---

## 速率限制

- 默认限制：100 请求/分钟
- WebSocket 连接：无限制

---

## 下一步

- [快速开始](./quick-start.md) - 开始使用
- [插件开发](./plugin-dev.md) - 开发插件
- [平台接入](./platform.md) - 接入平台
