# 常见问题 (FAQ)

## 安装问题

### Q: Python 版本要求？

A: WindAgent 需要 Python 3.8 或更高版本。

### Q: 依赖安装失败？

A: 尝试以下方法：
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Q: Windows 上启动失败？

A: 确保已安装 Visual C++ Redistributable。

---

## 配置问题

### Q: API Key 在哪里配置？

A: 有两种方式：
1. Web 界面：进入「AI 配置」页面
2. 配置文件：编辑 `%LOCALAPPDATA%\WindAgent\config.json`

### Q: 支持哪些 AI 厂商？

A: 支持以下厂商：
- OpenAI (GPT)
- Claude
- 通义千问
- DeepSeek
- Moonshot
- 智谱AI
- 自定义厂商

### Q: 如何修改 AI 的名字？

A: 进入「人设配置」页面，修改名字后保存。

### Q: 配置文件在哪里？

A: 
- Windows: `%LOCALAPPDATA%\WindAgent\config.json`
- Linux/macOS: `~/.local/share/WindAgent/config.json`

---

## 使用问题

### Q: 如何开始对话？

A: 启动服务后访问 http://127.0.0.1:8765，在输入框输入消息即可。

### Q: 如何使用命令？

A: 在对话中输入 `/命令名 参数`，例如：
- `/help` - 查看帮助
- `/weather 北京` - 查询天气

### Q: AI 有哪些工具？

A: 直接问 AI "你有什么工具？"，它会列出所有可用工具。

### Q: 如何让 AI 执行任务？

A: 直接描述你的需求，AI 会自动判断是否需要调用工具。

---

## 插件问题

### Q: 如何安装插件？

A: 将插件文件放入 `storm/builtin/` 目录，然后重启服务。

### Q: 插件不加载？

A: 检查：
1. 插件类是否继承 `PluginBase`
2. 是否定义了必要属性（name, version, description, author）
3. 文件名或目录名是否正确

### Q: 如何开发插件？

A: 查看 [插件开发指南](./plugin-dev.md)

### Q: 插件热更新不生效？

A: 检查插件代码是否有语法错误，查看控制台日志。

---

## 平台接入问题

### Q: 飞书消息收不到？

A: 检查：
1. App ID 和 App Secret 是否正确
2. 权限是否配置（im:message）
3. 服务是否启动
4. 飞书平台是否启用

### Q: 支持哪些平台？

A: 目前支持：
- ✅ 飞书
- 🚧 Telegram（开发中）
- 🚧 QQ（开发中）
- 🚧 微信（开发中）

### Q: 如何接入其他平台？

A: 可以通过开发插件来支持更多平台，参考 [平台接入指南](./platform.md)

---

## 性能问题

### Q: 响应速度慢？

A: 可能原因：
1. AI 模型响应慢 - 尝试更换模型
2. 网络延迟 - 检查网络连接
3. 上下文过长 - 清空对话历史

### Q: 内存占用高？

A: 尝试：
1. 减少对话历史长度
2. 禁用不必要的插件
3. 重启服务

---

## 其他问题

### Q: 如何备份数据？

A: 备份以下目录：
- `%LOCALAPPDATA%\WindAgent\` (Windows)
- `~/.local/share/WindAgent/` (Linux/macOS)

### Q: 如何更新版本？

A: 
```bash
git pull
pip install -r requirements.txt
```

### Q: 如何贡献代码？

A: 
1. Fork 项目
2. 创建特性分支
3. 提交 Pull Request

### Q: 遇到问题怎么办？

A: 
1. 查看 [文档](./README.md)
2. 搜索 [Issues](https://github.com/fengyun0608/WindAgent/issues)
3. 提交新 Issue

---

## 联系方式

- GitHub: [fengyun0608/WindAgent](https://github.com/fengyun0608/WindAgent)
- Issues: [提交问题](https://github.com/fengyun0608/WindAgent/issues)
