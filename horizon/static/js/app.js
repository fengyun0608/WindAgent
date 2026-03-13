const API = '';
let currentConversationId = null;
let ws = null;
let reconnectTimer = null;
let currentProvider = 'openai';
let currentPlatform = null;
let providers = {};
let platforms = {};
let guardianMode = false;
let guardianInterval = null;
let isInitialized = false;
let isLoadingConversations = false;

function showToast(message, type = 'success') {
    const iconMap = {
        success: 'OK',
        error: 'X',
        warning: '!',
        info: '*'
    };
    
    document.getElementById('toastIcon').textContent = iconMap[type] || '*';
    document.getElementById('toastMessage').textContent = message;
    document.getElementById('toastModal').classList.add('active');
}

function hideToastModal() {
    document.getElementById('toastModal').classList.remove('active');
}

let confirmCallback = null;

function showConfirm(title, message) {
    return new Promise((resolve) => {
        document.getElementById('confirmTitle').textContent = title;
        document.getElementById('confirmMessage').textContent = message;
        document.getElementById('confirmModal').classList.add('active');
        confirmCallback = resolve;
    });
}

function hideConfirmModal(result) {
    document.getElementById('confirmModal').classList.remove('active');
    if (confirmCallback) {
        confirmCallback(result);
        confirmCallback = null;
    }
}

function connectWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) return;
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/chat`);
    
    ws.onopen = () => document.getElementById('connectionStatus').classList.remove('disconnected');
    ws.onclose = () => {
        document.getElementById('connectionStatus').classList.add('disconnected');
        if (reconnectTimer) clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(connectWebSocket, 5000);
    };
    ws.onerror = () => {};
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'message' && data.response) {
            addMessage('assistant', data.response);
            currentConversationId = data.conversation_id;
        } else if (data.type === 'new_message') {
            loadConversations();
            if (data.conversation_id === currentConversationId) {
                loadConversationMessages(currentConversationId);
            }
        } else if (data.type === 'sync_conversations') {
            loadConversations();
        } else if (data.type === 'conversation_deleted') {
            if (data.conversation_id === currentConversationId) {
                initDefaultConversation();
            }
            loadConversations();
        }
    };
}

function init() {
    if (isInitialized) return;
    isInitialized = true;
    
    connectWebSocket();
    loadStatus();
    loadConversations();
    loadProviders();
    
    const savedPage = localStorage.getItem('currentPage') || 'chat';
    switchPage(savedPage);
    
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => switchPage(item.dataset.page));
    });
}

function switchPage(page) {
    localStorage.setItem('currentPage', page);
    
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    
    document.querySelector(`.nav-item[data-page="${page}"]`).classList.add('active');
    document.getElementById(`page-${page}`).classList.add('active');
    
    const titles = {
        chat: { title: '智能对话', subtitle: '与 AI 智能体进行对话交流' },
        plugins: { title: '插件管理', subtitle: '管理插件，扩展智能体能力' },
        persona: { title: '人设配置', subtitle: '自定义 AI 的性格和说话风格' },
        config: { title: 'AI 配置', subtitle: '配置 AI 厂商和 API' },
        platforms: { title: '平台接入', subtitle: '接入 Telegram、飞书、QQ 等平台' },
        usage: { title: '使用统计', subtitle: '查看 Token 使用情况' },
        env: { title: '环境信息', subtitle: '智能体自动检测运行环境' },
        system: { title: '系统管理', subtitle: '管理系统服务状态' }
    };
    
    document.getElementById('pageTitle').textContent = titles[page]?.title || '';
    document.getElementById('pageSubtitle').textContent = titles[page]?.subtitle || '';
    
    if (page === 'plugins') loadPlugins();
    if (page === 'usage') loadUsage();
    if (page === 'env') loadEnv();
    if (page === 'config') loadConfig();
    if (page === 'persona') loadPersona();
    if (page === 'platforms') loadPlatforms();
    if (page === 'system') loadSystemInfo();
}

async function loadStatus() {
    try {
        const res = await fetch(`${API}/api/status`);
        const data = await res.json();
        
        const dot = document.getElementById('apiStatusDot');
        const text = document.getElementById('apiStatusText');
        
        if (data.api_configured) {
            dot.classList.remove('warning', 'error');
            text.textContent = `API: ${data.model}`;
        } else {
            dot.classList.add('warning');
            text.textContent = 'API: 未配置';
        }
        
        document.getElementById('pluginCount').textContent = data.plugins_loaded || 0;
    } catch (e) {}
}

async function loadProviders() {
    try {
        const res = await fetch(`${API}/api/ai/providers`);
        providers = await res.json();
        renderProviderSelect();
        
        const platformRes = await fetch(`${API}/api/platforms`);
        platforms = await platformRes.json();
        renderPlatformGrid();
    } catch (e) {}
}

function renderProviderSelect() {
    const container = document.getElementById('providerSelect');
    if (!container) return;
    container.innerHTML = Object.entries(providers).map(([key, p]) => `
        <div class="provider-option ${key === currentProvider ? 'active' : ''}" onclick="selectProvider('${key}')">
            <div class="provider-name">${p.name}</div>
        </div>
    `).join('');
}

function selectProvider(key) {
    currentProvider = key;
    renderProviderSelect();
    
    const provider = providers[key];
    document.getElementById('configApiBase').value = provider.api_base;
    
    const modelList = document.getElementById('modelList');
    modelList.innerHTML = provider.models.map(m => `<option value="${m}">`).join('');
    document.getElementById('configModel').value = provider.default_model;
}

function renderPlatformGrid() {
    const container = document.getElementById('platformGrid');
    if (!container) return;
    container.innerHTML = Object.entries(platforms).map(([key, p]) => `
        <div class="platform-card" onclick="selectPlatform('${key}')">
            <div class="platform-icon">${p.icon}</div>
            <div class="platform-name">${p.name}</div>
            <div class="platform-status">${p.description}</div>
        </div>
    `).join('');
}

async function selectPlatform(key) {
    currentPlatform = key;
    document.querySelectorAll('.platform-card').forEach(c => c.classList.remove('active'));
    document.querySelector(`.platform-card:nth-child(${Object.keys(platforms).indexOf(key) + 1})`).classList.add('active');
    
    const card = document.getElementById('platformConfigCard');
    const title = document.getElementById('platformConfigTitle');
    const body = document.getElementById('platformConfigBody');
    
    card.style.display = 'block';
    title.textContent = platforms[key].name + ' 配置';
    
    body.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 20px;">加载中...</p>';
    
    try {
        const res = await fetch(`${API}/api/platforms/${key}/config`);
        const savedConfig = await res.json();
        
        const configs = {
        telegram: `
            <div class="config-section">
                <h4>📱 Telegram Bot 配置</h4>
                <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 0.9em;">
                    1. 在 Telegram 中搜索 @BotFather<br>
                    2. 发送 /newbot 创建机器人<br>
                    3. 获取 Bot Token 并填入下方
                </p>
                <div class="config-item">
                    <label class="config-label">Bot Token</label>
                    <input type="text" class="config-input" id="tgToken" placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz">
                </div>
                <div class="config-item">
                    <label class="config-label">Webhook URL</label>
                    <input type="text" class="config-input" id="tgWebhook" placeholder="https://your-domain.com/webhook/telegram" readonly>
                </div>
                <div style="display: flex; gap: 12px; margin-top: 16px;">
                    <button class="btn btn-primary" onclick="savePlatformConfig('telegram')">💾 保存配置</button>
                    <button class="btn btn-secondary" onclick="testPlatformConnection('telegram')">🔌 测试连接</button>
                </div>
            </div>
        `,
        feishu: `
            <div class="config-section">
                <h4>🪽 飞书机器人配置</h4>
                <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 0.9em;">
                    1. 访问飞书开放平台创建应用<br>
                    2. 获取 App ID 和 App Secret<br>
                    3. 在「事件订阅」中开启「使用长连接接收事件」
                </p>
                <div class="config-item">
                    <label class="config-label">App ID</label>
                    <input type="text" class="config-input" id="feishuAppId" placeholder="cli_xxxxxxxxxxxx">
                </div>
                <div class="config-item">
                    <label class="config-label">App Secret</label>
                    <input type="password" class="config-input" id="feishuSecret" placeholder="xxxxxxxxxxxxxxxx">
                </div>
                <div class="config-item">
                    <label class="config-label">Encrypt Key (加密策略)</label>
                    <input type="text" class="config-input" id="feishuEncryptKey" placeholder="可选">
                </div>
                <div class="config-item">
                    <label class="config-label">Verification Token</label>
                    <input type="text" class="config-input" id="feishuVerifyToken" placeholder="可选">
                </div>
                <div class="config-item" style="background: var(--bg-input); padding: 12px; border-radius: 8px; margin-top: 12px;">
                    <label class="config-label">⚙️ 长连接配置步骤</label>
                    <ol style="color: var(--text-muted); font-size: 0.85em; margin-top: 8px; padding-left: 20px;">
                        <li>飞书开放平台 → 事件订阅</li>
                        <li>开启「使用长连接接收事件」</li>
                        <li>添加事件：im.message.receive_v1</li>
                        <li>保存配置后自动连接</li>
                    </ol>
                    <p style="color: var(--success); font-size: 0.85em; margin-top: 8px;">
                        ✅ 无需公网IP，无需配置事件订阅地址
                    </p>
                </div>
                <div style="display: flex; gap: 12px; margin-top: 16px;">
                    <button class="btn btn-primary" onclick="savePlatformConfig('feishu')">💾 保存配置</button>
                    <button class="btn btn-secondary" onclick="testPlatformConnection('feishu')">🔌 测试连接</button>
                </div>
            </div>
        `,
        qq: `
            <div class="config-section">
                <h4>🐧 QQ 机器人配置</h4>
                <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 0.9em;">
                    1. 使用 NapCat/LLOneBot 等框架<br>
                    2. 获取机器人账号信息<br>
                    3. 配置反向 WebSocket
                </p>
                <div class="config-item">
                    <label class="config-label">Bot ID</label>
                    <input type="text" class="config-input" id="qqBotId" placeholder="机器人QQ号">
                </div>
                <div class="config-item">
                    <label class="config-label">Access Token</label>
                    <input type="text" class="config-input" id="qqToken" placeholder="访问令牌">
                </div>
                <div class="config-item">
                    <label class="config-label">WebSocket 地址</label>
                    <input type="text" class="config-input" id="qqWsUrl" placeholder="ws://127.0.0.1:3001">
                </div>
                <div style="display: flex; gap: 12px; margin-top: 16px;">
                    <button class="btn btn-primary" onclick="savePlatformConfig('qq')">💾 保存配置</button>
                    <button class="btn btn-secondary" onclick="testPlatformConnection('qq')">🔌 测试连接</button>
                </div>
            </div>
        `,
        wechat: `
            <div class="config-section">
                <h4>💬 微信接入配置</h4>
                <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 0.9em;">
                    1. 申请微信公众号或企业微信<br>
                    2. 配置服务器地址<br>
                    3. 设置消息加密
                </p>
                <div class="config-item">
                    <label class="config-label">App ID</label>
                    <input type="text" class="config-input" id="wechatAppId" placeholder="wx1234567890">
                </div>
                <div class="config-item">
                    <label class="config-label">App Secret</label>
                    <input type="password" class="config-input" id="wechatSecret" placeholder="xxxxxxxx">
                </div>
                <div class="config-item">
                    <label class="config-label">Token</label>
                    <input type="text" class="config-input" id="wechatToken" placeholder="自定义Token">
                </div>
                <div class="config-item">
                    <label class="config-label">EncodingAESKey</label>
                    <input type="text" class="config-input" id="wechatAesKey" placeholder="消息加密密钥">
                </div>
                <div style="display: flex; gap: 12px; margin-top: 16px;">
                    <button class="btn btn-primary" onclick="savePlatformConfig('wechat')">💾 保存配置</button>
                    <button class="btn btn-secondary" onclick="testPlatformConnection('wechat')">🔌 测试连接</button>
                </div>
            </div>
        `,
        discord: `
            <div class="config-section">
                <h4>🎮 Discord Bot 配置</h4>
                <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 0.9em;">
                    1. 访问 Discord Developer Portal<br>
                    2. 创建 Bot 获取 Token<br>
                    3. 邀请 Bot 到服务器
                </p>
                <div class="config-item">
                    <label class="config-label">Bot Token</label>
                    <input type="text" class="config-input" id="discordToken" placeholder="OTk5OTk5OTk5OTk5OTk5.Xxxxxx.xxxxxxxxxxxxx">
                </div>
                <div class="config-item">
                    <label class="config-label">Client ID</label>
                    <input type="text" class="config-input" id="discordClientId" placeholder="999999999999999999">
                </div>
                <div style="display: flex; gap: 12px; margin-top: 16px;">
                    <button class="btn btn-primary" onclick="savePlatformConfig('discord')">💾 保存配置</button>
                    <button class="btn btn-secondary" onclick="testPlatformConnection('discord')">🔌 测试连接</button>
                </div>
            </div>
        `,
        slack: `
            <div class="config-section">
                <h4>💼 Slack App 配置</h4>
                <p style="color: var(--text-muted); margin-bottom: 20px; font-size: 0.9em;">
                    1. 创建 Slack App<br>
                    2. 获取 Bot User OAuth Token<br>
                    3. 配置权限和事件
                </p>
                <div class="config-item">
                    <label class="config-label">Bot Token</label>
                    <input type="text" class="config-input" id="slackToken" placeholder="xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx">
                </div>
                <div class="config-item">
                    <label class="config-label">App Token</label>
                    <input type="text" class="config-input" id="slackAppToken" placeholder="xapp-x-x-xxxxxxxxxx-xxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx">
                </div>
                <div style="display: flex; gap: 12px; margin-top: 16px;">
                    <button class="btn btn-primary" onclick="savePlatformConfig('slack')">💾 保存配置</button>
                    <button class="btn btn-secondary" onclick="testPlatformConnection('slack')">🔌 测试连接</button>
                </div>
            </div>
        `
    };
    
        body.innerHTML = configs[key] || '<p style="color: var(--text-muted);">该平台配置即将推出</p>';
        
        if (savedConfig && Object.keys(savedConfig).length > 0) {
            setTimeout(() => {
                Object.keys(savedConfig).forEach(fieldId => {
                    const input = document.getElementById(fieldId);
                    if (input) {
                        input.value = savedConfig[fieldId];
                    }
                });
            }, 100);
        }
    } catch (e) {
        body.innerHTML = configs[key] || '<p style="color: var(--text-muted);">该平台配置即将推出</p>';
    }
}

async function savePlatformConfig(platform) {
    const config = {};
    const inputs = document.querySelectorAll('#platformConfigBody input');
    let hasConfig = false;
    
    inputs.forEach(input => {
        if (input.value && input.value.trim()) {
            config[input.id] = input.value.trim();
            hasConfig = true;
        }
    });
    
    if (!hasConfig) {
        showToast('请先配置平台信息', 'warning');
        return;
    }
    
    try {
        const res = await fetch(`${API}/api/platforms/${platform}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const data = await res.json();
        
        if (data.success) {
            showToast('配置已保存', 'success');
        } else {
            showToast(data.message || '保存失败', 'error');
        }
    } catch (e) {
        showToast('保存失败: ' + e.message, 'error');
    }
}

async function testPlatformConnection(platform) {
    const config = {};
    const inputs = document.querySelectorAll('#platformConfigBody input');
    let hasConfig = false;
    
    inputs.forEach(input => {
        if (input.value && input.value.trim()) {
            config[input.id] = input.value.trim();
            hasConfig = true;
        }
    });
    
    if (!hasConfig) {
        showToast('请先配置平台信息', 'warning');
        return;
    }
    
    showToast('正在测试连接...', 'info');
    
    try {
        const res = await fetch(`${API}/api/platforms/${platform}/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const data = await res.json();
        
        if (data.success) {
            showToast('连接成功！', 'success');
        } else {
            showToast(data.message || '连接失败', 'error');
        }
    } catch (e) {
        showToast('测试失败: ' + e.message, 'error');
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;
    
    addMessage('user', message);
    input.value = '';
    
    const statusEl = document.getElementById('chatStatus');
    let dotCount = 0;
    statusEl.textContent = '思考中';
    
    const thinkingInterval = setInterval(() => {
        dotCount = (dotCount + 1) % 4;
        statusEl.textContent = '思考中' + '.'.repeat(dotCount);
    }, 400);
    
    const assistantBubble = document.createElement('div');
    assistantBubble.className = 'message message-assistant';
    assistantBubble.innerHTML = '<div class="bubble" id="streaming-bubble"></div>';
    document.getElementById('chatMessages').appendChild(assistantBubble);
    
    const bubbleEl = document.getElementById('streaming-bubble');
    let fullText = '';
    let inCode = false;
    let codeContent = '';
    let isThinking = true;
    const startTime = Date.now();
    
    try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const streamWs = new WebSocket(`${protocol}//${window.location.host}/ws/stream`);
        
        streamWs.onopen = () => {
            streamWs.send(JSON.stringify({ message, conversation_id: currentConversationId }));
        };
        
        streamWs.onmessage = (event) => {
            const chunk = JSON.parse(event.data);
            
            if (isThinking && chunk.type === 'text') {
                const elapsed = Date.now() - startTime;
                const minThinkTime = 800;
                
                if (elapsed < minThinkTime) {
                    setTimeout(() => {
                        clearInterval(thinkingInterval);
                        statusEl.textContent = '回复中...';
                        isThinking = false;
                    }, minThinkTime - elapsed);
                } else {
                    clearInterval(thinkingInterval);
                    statusEl.textContent = '回复中...';
                    isThinking = false;
                }
            }
            
            switch (chunk.type) {
                case 'text':
                    fullText += chunk.content;
                    bubbleEl.innerHTML = escapeHtml(fullText).replace(/\n/g, '<br>');
                    break;
                    
                case 'done':
                    clearInterval(thinkingInterval);
                    statusEl.textContent = '等待输入...';
                    bubbleEl.removeAttribute('id');
                    currentConversationId = chunk.conversation_id || currentConversationId;
                    loadConversations();
                    streamWs.close();
                    break;
                    
                case 'error':
                    clearInterval(thinkingInterval);
                    statusEl.textContent = '发生错误';
                    bubbleEl.innerHTML = '<span style="color:#ef4444;">错误: ' + escapeHtml(chunk.content) + '</span>';
                    bubbleEl.removeAttribute('id');
                    streamWs.close();
                    break;
            }
            
            const container = document.getElementById('chatMessages');
            container.scrollTop = container.scrollHeight;
        };
        
        streamWs.onerror = () => {
            clearInterval(thinkingInterval);
            statusEl.textContent = '连接错误';
            bubbleEl.innerHTML = '<span style="color:#ef4444;">WebSocket连接失败</span>';
            bubbleEl.removeAttribute('id');
        };
        
    } catch (e) {
        clearInterval(thinkingInterval);
        statusEl.textContent = '发生错误';
        bubbleEl.innerHTML = '<span style="color:#ef4444;">错误: ' + escapeHtml(e.message) + '</span>';
        bubbleEl.removeAttribute('id');
    }
}

function addMessage(role, content) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `message message-${role}`;
    div.innerHTML = `<div class="bubble">${escapeHtml(content)}</div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function handleKeyPress(e) {
    if (e.key === 'Enter') sendMessage();
}

async function loadConversations() {
    if (isLoadingConversations) return;
    isLoadingConversations = true;
    
    try {
        const res = await fetch(`${API}/api/conversations`);
        let data = await res.json();
        
        console.log('会话数据:', data);
        
        if (!data || data.length === 0) {
            await initDefaultConversation();
            isLoadingConversations = false;
            return;
        }
        
        let webConv = data.find(c => c.platform === 'web');
        
        console.log('网页会话:', webConv);
        
        if (!webConv) {
            await initDefaultConversation();
            isLoadingConversations = false;
            return;
        }
        
        const savedConvId = localStorage.getItem('currentConversationId');
        if (savedConvId && data.find(c => c.id === savedConvId)) {
            currentConversationId = savedConvId;
            await loadConversationMessages(savedConvId);
        } else {
            currentConversationId = webConv.id;
            await loadConversationMessages(webConv.id);
        }
        
        const sessionList = document.getElementById('sessionList');
        if (!sessionList) {
            isLoadingConversations = false;
            return;
        }
        
        const platformIcons = {
            'web': '🌐',
            'feishu': '🪽',
            'telegram': '📱',
            'qq': '🐧',
            'wechat': '💬',
            'discord': '🎮',
            'slack': '💼'
        };
        
        const platformNames = {
            'web': '网页会话',
            'feishu': '飞书会话',
            'telegram': 'Telegram会话',
            'qq': 'QQ会话',
            'wechat': '微信会话',
            'discord': 'Discord会话',
            'slack': 'Slack会话'
        };
        
        let sessionHTML = `
            <div class="session-item ${currentConversationId === webConv.id ? 'active' : ''}" id="webSession" onclick="switchToWebSession()">
                <span class="session-icon">🌐</span>
                <span class="session-name">网页会话</span>
            </div>`;
        
        const platforms = [...new Set(data.map(c => c.platform))].filter(p => p !== 'web');
        
        for (const platform of platforms) {
            const conv = data.find(c => c.platform === platform);
            if (conv) {
                const icon = platformIcons[platform] || '📱';
                const name = platformNames[platform] || `${platform}会话`;
                const isActive = currentConversationId === conv.id;
                sessionHTML += `
            <div class="session-item ${isActive ? 'active' : ''}" id="${platform}Session" onclick="switchToPlatformSession('${platform}')">
                <span class="session-icon">${icon}</span>
                <span class="session-name">${name}</span>
            </div>`;
            }
        }
        
        sessionList.innerHTML = sessionHTML;
        
    } catch (e) {
        console.error('加载会话失败:', e);
    } finally {
        isLoadingConversations = false;
    }
}

async function switchToPlatformSession(platform) {
    const res = await fetch(`${API}/api/conversations`);
    const data = await res.json();
    const conv = data.find(c => c.platform === platform);
    if (conv) {
        await loadConversation(conv.id);
    } else {
        showToast(`暂无${platform}会话，请先在该平台发送消息`, 'info');
    }
}

async function switchToWebSession() {
    const res = await fetch(`${API}/api/conversations`);
    const data = await res.json();
    const webConv = data.find(c => c.platform === 'web' && c.title === '网页会话') || data.find(c => c.platform === 'web');
    if (webConv) {
        await loadConversation(webConv.id);
    }
}

async function switchToFeishuSession() {
    const res = await fetch(`${API}/api/conversations`);
    const data = await res.json();
    const feishuConv = data.find(c => c.platform === 'feishu');
    if (feishuConv) {
        await loadConversation(feishuConv.id);
    } else {
        showToast('暂无飞书会话，请先在飞书发送消息', 'info');
    }
}

async function clearCurrentConversation() {
    if (!currentConversationId) {
        showToast('请先选择一个会话', 'warning');
        return;
    }
    
    const confirmed = await showConfirm('清空对话', '确定要清空当前对话吗？此操作不可恢复。');
    if (!confirmed) return;
    
    try {
        const res = await fetch(`${API}/api/conversations/${currentConversationId}/messages`, {
            method: 'DELETE'
        });
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('chatMessages').innerHTML = '';
            showToast('对话已清空', 'success');
        } else {
            showToast('清空失败: ' + (data.error || '未知错误'), 'error');
        }
    } catch (e) {
        console.error('清空对话失败:', e);
        showToast('清空对话失败: ' + e.message, 'error');
    }
}

async function initDefaultConversation() {
    try {
        const res = await fetch(`${API}/api/conversations/default`, { method: 'POST' });
        const data = await res.json();
        currentConversationId = data.conversation_id;
        document.getElementById('chatMessages').innerHTML = '';
        document.getElementById('chatTitle').textContent = '网页会话';
        
        const webSessionEl = document.getElementById('webSession');
        if (webSessionEl) {
            webSessionEl.classList.add('active');
        }
    } catch (e) {
        console.error('初始化默认会话失败:', e);
    }
}

function toggleSessionList() {
    const header = document.querySelector('.session-header');
    const list = document.getElementById('sessionList');
    header.classList.toggle('expanded');
    list.style.display = list.style.display === 'none' ? 'block' : 'block';
}

async function loadConversationMessages(id) {
    try {
        await fetch(`${API}/api/conversations/${id}/switch`, { method: 'POST' });
        
        const res = await fetch(`${API}/api/conversations/${id}/messages`);
        const messages = await res.json();
        const container = document.getElementById('chatMessages');
        container.innerHTML = '';
        messages.forEach(m => addMessage(m.role, m.content));
        
        const convRes = await fetch(`${API}/api/conversations`);
        const convs = await convRes.json();
        const conv = convs.find(c => c.id === id);
        if (conv) {
            let title = '网页会话';
            if (conv.platform === 'feishu') {
                title = '飞书会话';
            } else if (conv.platform === 'web') {
                title = '网页会话';
            }
            document.getElementById('chatTitle').textContent = title;
        }
    } catch (e) {
        console.error('加载消息失败:', e);
    }
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`;
    return date.toLocaleDateString();
}

async function newConversation() {
    document.getElementById('newConvName').value = '';
    document.getElementById('newConvModal').classList.add('active');
    document.getElementById('newConvName').focus();
}

function hideNewConvModal() {
    document.getElementById('newConvModal').classList.remove('active');
}

async function createNewConversation() {
    const name = document.getElementById('newConvName').value.trim() || '新对话';
    
    try {
        const res = await fetch(`${API}/api/conversations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: name, platform: 'web' })
        });
        const data = await res.json();
        
        hideNewConvModal();
        document.getElementById('chatMessages').innerHTML = '';
        currentConversationId = data.conversation_id;
        document.getElementById('chatTitle').textContent = data.title || name;
        loadConversations();
    } catch (e) {
        console.error('新建会话失败:', e);
    }
}

async function deleteConversation(id) {
    const confirmed = await showConfirm('删除会话', '确定要删除这个会话吗？');
    if (!confirmed) return;
    
    try {
        await fetch(`${API}/api/conversations/${id}`, { method: 'DELETE' });
        if (currentConversationId === id) {
            currentConversationId = null;
            document.getElementById('chatMessages').innerHTML = '';
        }
        loadConversations();
    } catch (e) {
        console.error('删除会话失败:', e);
    }
}

async function loadConversation(id) {
    currentConversationId = id;
    localStorage.setItem('currentConversationId', id);
    document.getElementById('chatMessages').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted)">加载中...</div>';
    
    try {
        await fetch(`${API}/api/conversations/${id}/switch`, { method: 'POST' });
        
        const res = await fetch(`${API}/api/conversations/${id}/messages`);
        const messages = await res.json();
        
        document.getElementById('chatMessages').innerHTML = '';
        messages.forEach(m => addMessage(m.role, m.content));
        
        const convRes = await fetch(`${API}/api/conversations`);
        const convs = await convRes.json();
        const conv = convs.find(c => c.id === id);
        if (conv) {
            let title = '网页会话';
            if (conv.platform === 'feishu') {
                title = '飞书会话';
            } else if (conv.platform === 'web') {
                title = '网页会话';
            }
            document.getElementById('chatTitle').textContent = title;
        }
        
        const webConv = convs.find(c => c.platform === 'web');
        const feishuConv = convs.find(c => c.platform === 'feishu');
        
        const webSessionEl = document.getElementById('webSession');
        const feishuSessionEl = document.getElementById('feishuSession');
        
        if (webSessionEl && webConv) {
            webSessionEl.classList.toggle('active', id === webConv.id);
        }
        
        if (feishuSessionEl && feishuConv) {
            feishuSessionEl.classList.toggle('active', id === feishuConv.id);
        }
        
    } catch (e) {
        console.error('加载会话失败:', e);
        document.getElementById('chatMessages').innerHTML = '<div style="text-align:center;padding:20px;color:#ef4444">加载失败</div>';
    }
}

async function loadPlugins() {
    try {
        console.log('加载插件列表...');
        const res = await fetch(`${API}/api/plugins`);
        const data = await res.json();
        console.log('插件数据:', data);
        const list = document.getElementById('pluginList');
        console.log('插件列表元素:', list);
        
        if (!list) {
            console.error('找不到 pluginList 元素');
            return;
        }
        
        const toolsRes = await fetch(`${API}/api/tools`);
        const toolsData = await toolsRes.json();
        console.log('工具数据:', toolsData);
        
        data.sort((a, b) => {
            const exampleNames = ['example', 'example_package'];
            const aIsExample = exampleNames.includes(a.name);
            const bIsExample = exampleNames.includes(b.name);
            if (aIsExample && !bIsExample) return -1;
            if (!aIsExample && bIsExample) return 1;
            return 0;
        });
        
        list.innerHTML = data.map(p => {
            const pluginTools = Object.entries(toolsData.tools || {}).filter(([name, info]) => {
                return info.plugin === p.name;
            });
            
            let toolsHtml = '';
            if (pluginTools.length > 0) {
                toolsHtml = `
                <div class="plugin-tools">
                    <div class="plugin-tools-title">可用工具:</div>
                    <div class="plugin-tools-list">
                        ${pluginTools.map(([name, info]) => `<span class="tool-tag" title="${info.description || ''}">${name}</span>`).join('')}
                    </div>
                </div>`;
            }
            
            return `
            <div class="plugin-card">
                <div class="plugin-header">
                    <div class="plugin-name">${escapeHtml(p.name)}</div>
                    <div class="plugin-version">v${p.version}</div>
                </div>
                <div class="plugin-desc">${escapeHtml(p.description || '暂无描述')}</div>
                ${toolsHtml}
                <div class="plugin-status">
                    <span class="dot ${p.enabled ? '' : 'disabled'}"></span>
                    <span>${p.enabled ? '已启用' : '已禁用'}</span>
                </div>
                <div class="plugin-actions">
                    <button class="btn ${p.enabled ? 'btn-warning' : 'btn-success'} btn-small" onclick="togglePlugin('${escapeHtml(p.name)}', ${!p.enabled})">${p.enabled ? '停用' : '启用'}</button>
                    <button class="btn btn-secondary btn-small" onclick="openPluginEditor('${escapeHtml(p.name)}')">编辑</button>
                    <button class="btn btn-secondary btn-small" onclick="reloadPlugin('${escapeHtml(p.name)}')">重载</button>
                    <button class="btn btn-danger btn-small" onclick="uninstallPlugin('${escapeHtml(p.name)}')">卸载</button>
                </div>
            </div>`;
        }).join('');
        console.log('插件列表已渲染');
    } catch (e) {
        console.error('加载插件失败:', e);
    }
}

let currentEditingPlugin = null;
let currentEditingFile = null;

async function openPluginEditor(pluginName) {
    currentEditingPlugin = pluginName;
    document.getElementById('editorPluginName').textContent = pluginName;
    document.getElementById('pluginCodeEditor').value = '';
    document.getElementById('pluginFileList').innerHTML = '<span style="color:var(--text-muted)">加载中...</span>';
    document.getElementById('pluginToolsList').innerHTML = '<span style="color:var(--text-muted)">加载中...</span>';
    
    try {
        const [filesRes, toolsRes] = await Promise.all([
            fetch(`${API}/api/plugins/${encodeURIComponent(pluginName)}/files`),
            fetch(`${API}/api/tools`)
        ]);
        
        const filesData = await filesRes.json();
        const toolsData = await toolsRes.json();
        
        const fileList = document.getElementById('pluginFileList');
        if (filesData.files && filesData.files.length > 0) {
            fileList.innerHTML = filesData.files.map(f => {
                const escapedPath = f.path.replace(/\\/g, '\\\\');
                return `<button class="btn btn-secondary btn-small" onclick="loadPluginFile('${pluginName}', '${escapedPath}')">${f.name}</button>`;
            }).join('');
            
            currentEditingFile = filesData.files[0].path;
            await loadPluginFile(pluginName, currentEditingFile);
        } else {
            fileList.innerHTML = '<span style="color:var(--text-muted)">' + (filesData.error || '无文件') + '</span>';
            document.getElementById('pluginCodeEditor').value = '// ' + (filesData.error || '无文件可编辑');
        }
        
        const pluginTools = Object.entries(toolsData.tools || {}).filter(([name, info]) => info.plugin === pluginName);
        const toolsList = document.getElementById('pluginToolsList');
        if (pluginTools.length > 0) {
            toolsList.innerHTML = pluginTools.map(([name, info]) => 
                `<div class="tool-item-editor"><span class="tool-name">${name}</span><span class="tool-desc">${info.description || ''}</span></div>`
            ).join('');
        } else {
            toolsList.innerHTML = '<span style="color:var(--text-muted)">无工具</span>';
        }
    } catch (e) {
        console.error('加载插件文件列表失败:', e);
        showToast('加载插件文件列表失败: ' + e.message, 'error');
    }
    
    document.getElementById('pluginEditorModal').classList.add('active');
}

async function loadPluginFile(pluginName, filePath) {
    currentEditingFile = filePath;
    document.getElementById('pluginCodeEditor').value = '// 加载中...';
    
    try {
        const res = await fetch(`${API}/api/plugins/${encodeURIComponent(pluginName)}/file?file_path=${encodeURIComponent(filePath)}`);
        const data = await res.json();
        
        if (data.content) {
            document.getElementById('pluginCodeEditor').value = data.content;
        } else {
            document.getElementById('pluginCodeEditor').value = '// ' + (data.error || '无法加载文件内容');
        }
    } catch (e) {
        console.error('加载文件失败:', e);
        document.getElementById('pluginCodeEditor').value = '// 加载文件失败: ' + e.message;
    }
}

async function savePluginFile() {
    if (!currentEditingPlugin || !currentEditingFile) return;
    
    const content = document.getElementById('pluginCodeEditor').value;
    
    try {
        const res = await fetch(`${API}/api/plugins/${encodeURIComponent(currentEditingPlugin)}/file?file_path=${encodeURIComponent(currentEditingFile)}&content=${encodeURIComponent(content)}`, {
            method: 'POST'
        });
        const data = await res.json();
        if (data.success) {
            showToast('文件已保存', 'success');
        } else {
            showToast(data.error || '保存失败', 'error');
        }
    } catch (e) {
        showToast('保存失败: ' + e.message, 'error');
    }
}

async function hotReloadPlugin() {
    if (!currentEditingPlugin) return;
    
    try {
        const res = await fetch(`${API}/api/plugins/${encodeURIComponent(currentEditingPlugin)}/reload`, {
            method: 'POST'
        });
        const data = await res.json();
        if (data.success) {
            showToast('插件已热更新', 'success');
        } else {
            showToast(data.error || '热更新失败', 'error');
        }
    } catch (e) {
        showToast('热更新失败: ' + e.message, 'error');
    }
}

function hidePluginEditor() {
    document.getElementById('pluginEditorModal').classList.remove('active');
}

async function togglePlugin(name, enable) {
    try {
        const res = await fetch(`${API}/api/plugins/${encodeURIComponent(name)}/${enable ? 'enable' : 'disable'}`, { method: 'POST' });
        const data = await res.json();
        
        if (data.success) {
            showToast(`插件 ${name} 已${enable ? '启用' : '停用'}`, 'success');
            loadPlugins();
        } else {
            showToast(data.message || '操作失败', 'error');
        }
    } catch (e) {
        showToast('操作失败: ' + e.message, 'error');
    }
}

async function reloadPlugin(name) {
    try {
        await fetch(`${API}/api/plugins/${encodeURIComponent(name)}/reload`, { method: 'POST' });
        loadPlugins();
    } catch (e) {}
}

async function uninstallPlugin(name) {
    const confirmed = await showConfirm('卸载插件', `确定要卸载插件 "${name}" 吗？`);
    if (!confirmed) return;
    
    try {
        await fetch(`${API}/api/plugins/${encodeURIComponent(name)}`, { method: 'DELETE' });
        loadPlugins();
        loadStatus();
        showToast(`插件 ${name} 已卸载`, 'success');
    } catch (e) {
        showToast('卸载失败: ' + e.message, 'error');
    }
}

function showInstallModal() { document.getElementById('installModal').classList.add('active'); }
function hideInstallModal() { document.getElementById('installModal').classList.remove('active'); }

function switchInstallTab(tab) {
    document.querySelectorAll('.install-tab').forEach(t => t.classList.remove('active'));
    document.getElementById(`tab${tab === 'new' ? 'New' : 'Clone'}`).classList.add('active');
    document.getElementById('installNew').style.display = tab === 'new' ? 'block' : 'none';
    document.getElementById('installClone').style.display = tab === 'clone' ? 'block' : 'none';
}

function switchInstallTab(tab) {
    document.querySelectorAll('.install-tab').forEach(t => t.classList.remove('active'));
    document.getElementById(`tab${tab === 'url' ? 'Url' : 'Local'}`).classList.add('active');
    document.getElementById('installUrl').style.display = tab === 'url' ? 'block' : 'none';
    document.getElementById('installLocal').style.display = tab === 'local' ? 'block' : 'none';
    document.getElementById('installProgress').style.display = 'none';
    document.getElementById('installResult').style.display = 'none';
    document.getElementById('installActions').style.display = 'flex';
}

async function installPlugin() {
    const isUrl = document.getElementById('installUrl').style.display !== 'none';
    
    document.getElementById('installActions').style.display = 'none';
    document.getElementById('installProgress').style.display = 'block';
    document.getElementById('installResult').style.display = 'none';
    
    if (isUrl) {
        const url = document.getElementById('installUrlInput').value.trim();
        const platform = document.getElementById('installPlatform').value;
        
        if (!url) {
            showInstallResult(false, '请输入仓库地址');
            return;
        }
        
        document.getElementById('installStatus').textContent = `正在从 ${platform} 克隆仓库...`;
        
        try {
            const res = await fetch(`${API}/api/plugins/install?url=${encodeURIComponent(url)}&platform=${platform}`, { method: 'POST' });
            const data = await res.json();
            
            if (data.success) {
                showInstallResult(true, data.message);
                loadPlugins();
            } else {
                showInstallResult(false, data.message);
            }
        } catch (e) {
            showInstallResult(false, '安装失败: ' + e.message);
        }
    } else {
        const name = document.getElementById('newPluginName').value.trim();
        const desc = document.getElementById('newPluginDesc').value.trim();
        const author = document.getElementById('newPluginAuthor').value.trim();
        const type = document.getElementById('newPluginType').value;
        
        if (!name) {
            showInstallResult(false, '请输入插件名称');
            return;
        }
        
        document.getElementById('installStatus').textContent = '正在创建插件...';
        
        try {
            const res = await fetch(`${API}/api/plugins/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    description: desc,
                    author: author,
                    type: type
                })
            });
            const data = await res.json();
            
            if (data.success) {
                showInstallResult(true, data.message + '\n路径: ' + data.path);
                loadPlugins();
            } else {
                showInstallResult(false, data.message);
            }
        } catch (e) {
            showInstallResult(false, '创建失败: ' + e.message);
        }
    }
}

function showInstallResult(success, message) {
    document.getElementById('installProgress').style.display = 'none';
    document.getElementById('installResult').style.display = 'block';
    document.getElementById('installResultIcon').textContent = success ? '✅' : '❌';
    document.getElementById('installResultIcon').className = success ? 'install-success' : 'install-error';
    document.getElementById('installResultText').textContent = message;
    document.getElementById('installResultText').style.color = success ? 'var(--success)' : 'var(--error)';
    
    setTimeout(() => {
        if (success) {
            hideInstallModal();
        } else {
            document.getElementById('installActions').style.display = 'flex';
        }
    }, success ? 1500 : 3000);
}

async function loadPersona() {
    try {
        const res = await fetch(`${API}/api/persona`);
        const data = await res.json();
        document.getElementById('personaName').value = data.name || '';
        document.getElementById('personaDesc').value = data.description || '';
        document.getElementById('personaPersonality').value = data.personality || '';
        document.getElementById('personaStyle').value = data.speaking_style || '';
        document.getElementById('personaCustom').value = data.custom_prompt || '';
    } catch (e) {}
}

async function savePersona() {
    try {
        const params = new URLSearchParams();
        const name = document.getElementById('personaName').value.trim();
        const desc = document.getElementById('personaDesc').value.trim();
        const personality = document.getElementById('personaPersonality').value.trim();
        const style = document.getElementById('personaStyle').value.trim();
        const custom = document.getElementById('personaCustom').value.trim();
        
        if (name) params.append('name', name);
        if (desc) params.append('description', desc);
        if (personality) params.append('personality', personality);
        if (style) params.append('speaking_style', style);
        if (custom) params.append('custom_prompt', custom);
        
        await fetch(`${API}/api/persona?${params.toString()}`, { method: 'POST' });
        alert('✅ 人设已保存');
    } catch (e) {
        alert('❌ 保存失败');
    }
}

async function loadConfig() {
    try {
        const res = await fetch(`${API}/api/config`);
        const data = await res.json();
        currentProvider = data.ai?.provider || 'openai';
        
        const activeProviderSelect = document.getElementById('activeProvider');
        if (activeProviderSelect) {
            activeProviderSelect.value = currentProvider;
        }
        
        document.getElementById('configTemp').value = data.ai?.temperature ?? 0.7;
        document.getElementById('configMaxTokens').value = data.ai?.max_tokens || 2000;
        
        loadProviderConfig(currentProvider);
    } catch (e) {}
}

function onProviderChange() {
    const provider = document.getElementById('activeProvider').value;
    currentProvider = provider;
    
    const presets = {
        openai: { base: 'https://api.openai.com/v1', model: 'gpt-3.5-turbo' },
        claude: { base: 'https://api.anthropic.com/v1', model: 'claude-3-sonnet-20240229' },
        qwen: { base: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-turbo' },
        deepseek: { base: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
        moonshot: { base: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
        zhipu: { base: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4' },
        custom: { base: '', model: '' }
    };
    
    loadProviderConfig(provider);
}

async function loadProviderConfig(provider) {
    try {
        const res = await fetch(`${API}/api/config`);
        const data = await res.json();
        const ai = data.ai || {};
        
        const apiKeyField = document.getElementById('configApiKey');
        const apiBaseField = document.getElementById('configApiBase');
        const modelField = document.getElementById('configModel');
        
        if (provider === 'openai') {
            apiKeyField.value = ai.openai_api_key || ai.api_key || '';
            apiBaseField.value = ai.openai_api_base || ai.api_base || 'https://api.openai.com/v1';
            modelField.value = ai.openai_model || ai.model || 'gpt-3.5-turbo';
        } else if (provider === 'claude') {
            apiKeyField.value = ai.claude_api_key || '';
            apiBaseField.value = ai.claude_api_base || 'https://api.anthropic.com/v1';
            modelField.value = ai.claude_model || 'claude-3-sonnet-20240229';
        } else if (provider === 'qwen') {
            apiKeyField.value = ai.qwen_api_key || '';
            apiBaseField.value = ai.qwen_api_base || 'https://dashscope.aliyuncs.com/compatible-mode/v1';
            modelField.value = ai.qwen_model || 'qwen-turbo';
        } else if (provider === 'deepseek') {
            apiKeyField.value = ai.deepseek_api_key || '';
            apiBaseField.value = ai.deepseek_api_base || 'https://api.deepseek.com/v1';
            modelField.value = ai.deepseek_model || 'deepseek-chat';
        } else if (provider === 'moonshot') {
            apiKeyField.value = ai.moonshot_api_key || '';
            apiBaseField.value = ai.moonshot_api_base || 'https://api.moonshot.cn/v1';
            modelField.value = ai.moonshot_model || 'moonshot-v1-8k';
        } else if (provider === 'zhipu') {
            apiKeyField.value = ai.zhipu_api_key || '';
            apiBaseField.value = ai.zhipu_api_base || 'https://open.bigmodel.cn/api/paas/v4';
            modelField.value = ai.zhipu_model || 'glm-4';
        } else if (provider === 'custom') {
            apiKeyField.value = ai.custom_api_key || ai.api_key || '';
            apiBaseField.value = ai.custom_api_base || ai.api_base || '';
            modelField.value = ai.custom_model || ai.model || '';
        }
    } catch (e) {
        console.error('加载厂商配置失败:', e);
    }
}

async function restartService() {
    const confirmed = await showConfirm('重启服务', '确定要重启服务吗？所有连接将暂时断开。');
    if (!confirmed) return;
    
    try {
        showToast('正在重启服务...', 'info');
        await fetch(`${API}/api/system/restart`, { method: 'POST' });
        setTimeout(() => {
            showToast('服务已重启，正在重新连接...', 'success');
            setTimeout(() => location.reload(), 2000);
        }, 3000);
    } catch (e) {
        showToast('重启失败: ' + e.message, 'error');
    }
}

async function stopService() {
    const confirmed = await showConfirm('关闭服务', '确定要关闭服务吗？关闭后需要手动启动。');
    if (!confirmed) return;
    
    try {
        showToast('正在关闭服务...', 'info');
        await fetch(`${API}/api/system/stop`, { method: 'POST' });
        showToast('服务已关闭', 'success');
    } catch (e) {
        showToast('关闭失败: ' + e.message, 'error');
    }
}

async function loadSystemInfo() {
    try {
        const res = await fetch(`${API}/api/status`);
        const data = await res.json();
        
        const container = document.getElementById('systemInfo');
        if (!container) return;
        
        container.innerHTML = `
            <div class="env-item"><span class="env-label">版本</span><span class="env-value">${data.version || 'v0.1.0'}</span></div>
            <div class="env-item"><span class="env-label">运行状态</span><span class="env-value" style="color: var(--success);">运行中</span></div>
            <div class="env-item"><span class="env-label">API状态</span><span class="env-value">${data.api_configured ? '已配置' : '未配置'}</span></div>
            <div class="env-item"><span class="env-label">当前模型</span><span class="env-value">${data.model || '-'}</span></div>
            <div class="env-item"><span class="env-label">已加载插件</span><span class="env-value">${data.plugins_loaded || 0} 个</span></div>
        `;
    } catch (e) {
        console.error('加载系统信息失败:', e);
    }
}

async function saveConfig() {
    try {
        const activeProvider = document.getElementById('activeProvider')?.value || currentProvider;
        const apiKey = document.getElementById('configApiKey').value;
        const apiBase = document.getElementById('configApiBase').value;
        const model = document.getElementById('configModel').value;
        const temperature = parseFloat(document.getElementById('configTemp').value) || 0.7;
        const maxTokens = parseInt(document.getElementById('configMaxTokens').value) || 2000;
        
        const configs = [
            { section: 'ai', key: 'provider', value: activeProvider },
            { section: 'ai', key: 'api_key', value: apiKey },
            { section: 'ai', key: 'api_base', value: apiBase },
            { section: 'ai', key: 'model', value: model },
            { section: 'ai', key: 'temperature', value: temperature },
            { section: 'ai', key: 'max_tokens', value: maxTokens },
            { section: 'ai', key: `${activeProvider}_api_key`, value: apiKey },
            { section: 'ai', key: `${activeProvider}_api_base`, value: apiBase },
            { section: 'ai', key: `${activeProvider}_model`, value: model }
        ];
        
        for (const c of configs) {
            await fetch(`${API}/api/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(c)
            });
        }
        
        showToast('配置已保存', 'success');
        loadStatus();
    } catch (e) {
        showToast('保存失败: ' + e.message, 'error');
    }
}

async function loadUsage() {
    try {
        const res = await fetch(`${API}/api/usage`);
        const data = await res.json();
        
        document.getElementById('statsGrid').innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${(data.total_tokens || 0).toLocaleString()}</div>
                <div class="stat-label">📊 总 Token</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.request_count || 0}</div>
                <div class="stat-label">🔄 请求次数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.request_count ? (data.total_tokens / data.request_count).toFixed(1) : 0}</div>
                <div class="stat-label">📈 平均 Token</div>
            </div>
        `;
        
        const dailyRes = await fetch(`${API}/api/usage/daily?days=7`);
        const daily = await dailyRes.json();
        const maxTokens = Math.max(...daily.map(d => d.tokens), 1);
        
        document.getElementById('dailyUsage').innerHTML = daily.map((d, i) => `
            <div class="daily-bar">
                <span class="daily-date">${d.date}</span>
                <div class="daily-progress">
                    <div class="daily-fill" style="width: ${(d.tokens / maxTokens * 100)}%"></div>
                </div>
                <span class="daily-value">${d.tokens.toLocaleString()}</span>
            </div>
        `).join('');
    } catch (e) {}
}

async function loadEnv() {
    try {
        const res = await fetch(`${API}/api/env`);
        const data = await res.json();
        
        const labels = {
            device_type: '📱 设备类型',
            os_name: '💻 操作系统',
            os_version: '🔢 系统版本',
            arch: '🏗️ 架构',
            is_tablet: '📲 平板设备',
            is_portable: '🎒 便携设备',
            has_gpu: '🎮 GPU',
            memory_gb: '💾 内存',
            python_version: '🐍 Python',
            shell_type: '⌨️ Shell',
            data_dir: '📁 数据目录'
        };
        
        const formatValue = (key, value) => {
            if (typeof value === 'boolean') return value ? '✅ 是' : '❌ 否';
            if (key === 'memory_gb') return `${value} GB`;
            return String(value);
        };
        
        document.getElementById('envInfo').innerHTML = Object.entries(data).map(([k, v], i) => `
            <div class="env-item">
                <div class="env-label">${labels[k] || k}</div>
                <div class="env-value ${k === 'device_type' ? 'highlight' : ''}">${formatValue(k, v)}</div>
            </div>
        `).join('');
    } catch (e) {}
}

function toggleGuardian() {
    guardianMode = !guardianMode;
    const toggle = document.getElementById('guardianToggle');
    
    if (guardianMode) {
        toggle.classList.add('active');
        toggle.querySelector('.icon').textContent = '🛡️';
        toggle.querySelector('.text').textContent = '守护中...';
        startGuardian();
    } else {
        toggle.classList.remove('active');
        toggle.querySelector('.icon').textContent = '🛡️';
        toggle.querySelector('.text').textContent = '开启守护';
        stopGuardian();
    }
}

async function startGuardian() {
    try {
        const res = await fetch(`${API}/api/guardian/start`, { method: 'POST' });
        const data = await res.json();
        console.log('守护模式:', data.message);
        
        guardianInterval = setInterval(async () => {
            const statusRes = await fetch(`${API}/api/guardian/status`);
            const status = await statusRes.json();
            updateGuardianUI(status);
        }, 5000);
    } catch (e) {
        console.error('启动守护失败:', e);
    }
}

async function stopGuardian() {
    if (guardianInterval) {
        clearInterval(guardianInterval);
        guardianInterval = null;
    }
    try {
        await fetch(`${API}/api/guardian/stop`, { method: 'POST' });
    } catch (e) {}
}

function updateGuardianUI(status) {
    const toggle = document.getElementById('guardianToggle');
    if (!toggle) return;
    
    const text = toggle.querySelector('.text');
    if (status.system) {
        const cpu = status.system.cpu_percent.toFixed(0);
        const mem = status.system.memory_percent.toFixed(0);
        text.textContent = `守护中 CPU:${cpu}% 内存:${mem}%`;
    }
    
    if (status.recent_alerts && status.recent_alerts.length > 0) {
        const latest = status.recent_alerts[status.recent_alerts.length - 1];
        if (latest.type === 'warning') {
            toggle.style.borderColor = 'rgba(245, 158, 11, 0.5)';
        }
    }
}

async function loadPlatforms() {
    const container = document.getElementById('platformList');
    if (!container) return;
    
    container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);">加载中...</div>';
    
    try {
        const res = await fetch(`${API}/api/platforms`);
        const platforms = await res.json();
        
        if (!platforms || platforms.length === 0) {
            container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);">暂无可用平台</div>';
            return;
        }
        
        const configRes = await fetch(`${API}/api/config`);
        const config = await configRes.json();
        
        container.innerHTML = platforms.map(p => {
            let isEnabled = p.running;
            
            if (p.name === 'feishu' && config.platform) {
                isEnabled = config.platform.feishu_enabled || false;
            }
            
            const hasConfig = p.fields && p.fields.length > 0;
            
            return `
            <div class="platform-item" data-platform="${p.name}">
                <div class="platform-header-row">
                    <div class="platform-info">
                        <span class="platform-icon">${p.icon}</span>
                        <div class="platform-details">
                            <div class="platform-name">${p.description || p.name}</div>
                            <div class="platform-status">${isEnabled ? '已启用' : '未启用'}</div>
                        </div>
                    </div>
                    <div class="platform-actions">
                        <label class="switch">
                            <input type="checkbox" ${isEnabled ? 'checked' : ''} onchange="togglePlatform('${p.name}', this.checked)">
                            <span class="slider"></span>
                        </label>
                        ${hasConfig ? `<button class="btn btn-secondary btn-small" onclick="showPlatformConfig('${p.name}')">配置</button>` : ''}
                    </div>
                </div>
                <div class="platform-config-form" id="platform-config-${p.name}" style="display:none;"></div>
            </div>`;
        }).join('');
    } catch (e) {
        console.error('加载平台列表失败:', e);
        container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);">加载失败</div>';
    }
}

async function togglePlatform(platformName, enabled) {
    try {
        const res = await fetch(`${API}/api/platforms/${platformName}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: enabled })
        });
        const data = await res.json();
        
        if (data.success) {
            showToast(`${platformName} ${enabled ? '已启用' : '已禁用'}，重启后生效`, 'success');
            
            const statusEl = document.querySelector(`[data-platform="${platformName}"] .platform-status`);
            if (statusEl) {
                statusEl.textContent = enabled ? '已启用' : '未启用';
            }
        } else {
            showToast('保存失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (e) {
        showToast('保存失败: ' + e.message, 'error');
    }
}

async function showPlatformConfig(platformName) {
    const form = document.getElementById(`platform-config-${platformName}`);
    if (!form) return;
    
    if (form.style.display !== 'none') {
        form.style.display = 'none';
        return;
    }
    
    form.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);">加载配置...</div>';
    form.style.display = 'block';
    
    try {
        const res = await fetch(`${API}/api/platforms/${platformName}/config`);
        const data = await res.json();
        
        if (!data.fields || data.fields.length === 0) {
            form.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);">无需配置</div>';
            return;
        }
        
        const values = data.values || {};
        
        form.innerHTML = `
            <div class="config-form">
                ${data.fields.map(f => {
                    const value = values[f.key] || f.default || '';
                    if (f.type === 'password') {
                        return `
                        <div class="form-group">
                            <label>${f.label}${f.required ? ' *' : ''}</label>
                            <input type="password" class="form-input" data-key="${f.key}" value="${value}" placeholder="${f.placeholder || ''}">
                        </div>`;
                    } else if (f.type === 'select') {
                        return `
                        <div class="form-group">
                            <label>${f.label}${f.required ? ' *' : ''}</label>
                            <select class="form-input" data-key="${f.key}">
                                ${(f.options || []).map(opt => `<option value="${opt}" ${value === opt ? 'selected' : ''}>${opt}</option>`).join('')}
                            </select>
                        </div>`;
                    } else if (f.type === 'number') {
                        return `
                        <div class="form-group">
                            <label>${f.label}${f.required ? ' *' : ''}</label>
                            <input type="number" class="form-input" data-key="${f.key}" value="${value}" placeholder="${f.placeholder || ''}">
                        </div>`;
                    } else {
                        return `
                        <div class="form-group">
                            <label>${f.label}${f.required ? ' *' : ''}</label>
                            <input type="text" class="form-input" data-key="${f.key}" value="${value}" placeholder="${f.placeholder || ''}">
                        </div>`;
                    }
                }).join('')}
                <div class="form-actions">
                    <button class="btn btn-primary" onclick="savePlatformConfig('${platformName}')">保存配置</button>
                    <button class="btn btn-secondary" onclick="document.getElementById('platform-config-${platformName}').style.display='none'">取消</button>
                </div>
            </div>`;
    } catch (e) {
        console.error('加载平台配置失败:', e);
        form.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);">加载失败</div>';
    }
}

async function savePlatformConfig(platformName) {
    const form = document.getElementById(`platform-config-${platformName}`);
    const inputs = form.querySelectorAll('[data-key]');
    const config = {};
    
    inputs.forEach(input => {
        config[input.dataset.key] = input.value;
    });
    
    try {
        const res = await fetch(`${API}/api/platforms/${platformName}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        const data = await res.json();
        
        if (data.success) {
            showToast('配置已保存，重启后生效', 'success');
            form.style.display = 'none';
        } else {
            showToast('保存失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (e) {
        showToast('保存失败: ' + e.message, 'error');
    }
}

init();
