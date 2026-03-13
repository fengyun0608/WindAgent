#!/bin/bash

# WindAgent 一键部署脚本 (Linux/macOS)

# 静默检测代理设置
USE_PROXY=0
PROXY_URL=""

# 检测环境变量代理
if [ -n "$HTTP_PROXY" ]; then
    USE_PROXY=1
    PROXY_URL="$HTTP_PROXY"
fi

if [ -n "$HTTPS_PROXY" ]; then
    USE_PROXY=1
    PROXY_URL="$HTTPS_PROXY"
fi

# 检测系统代理配置
if [ "$USE_PROXY" -eq 0 ]; then
    if [ -f "/etc/environment" ]; then
        PROXY_CHECK=$(grep -i "http_proxy\|https_proxy" /etc/environment 2>/dev/null)
        if [ -n "$PROXY_CHECK" ]; then
            USE_PROXY=1
        fi
    fi
fi

# 设置 pip 代理参数
if [ "$USE_PROXY" -eq 1 ] && [ -n "$PROXY_URL" ]; then
    PIP_PROXY="--proxy $PROXY_URL"
else
    PIP_PROXY=""
fi

echo ""
echo "========================================================"
echo "          WindAgent - 风云智能体 一键部署"
echo "========================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检测操作系统
OS="$(uname -s)"
case "$OS" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN";;
esac

# 检测是否为服务器环境
IS_SERVER=0
if [ "$MACHINE" = "Linux" ]; then
    # 检测是否为服务器（无图形界面）
    if [ -z "$DISPLAY" ] || [ ! -d "/usr/share/xsessions" ]; then
        IS_SERVER=1
    fi
fi

# 服务器环境安装到主目录
if [ "$IS_SERVER" -eq 1 ]; then
    INSTALL_DIR="$HOME/WindAgent"
    if [ "$SCRIPT_DIR" != "$INSTALL_DIR" ]; then
        echo -e "${GREEN}[提示] 检测到服务器环境，将安装到: $INSTALL_DIR${NC}"
        if [ ! -d "$INSTALL_DIR" ]; then
            mkdir -p "$INSTALL_DIR"
        fi
        # 复制文件到安装目录
        if [ "$SCRIPT_DIR" != "$INSTALL_DIR" ]; then
            cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/" 2>/dev/null
        fi
        cd "$INSTALL_DIR"
    fi
else
    INSTALL_DIR="$SCRIPT_DIR"
fi

echo -e "${GREEN}[1/6] 检测系统环境...${NC}"
echo ""
echo "操作系统: $MACHINE"
if [ "$IS_SERVER" -eq 1 ]; then
    echo "环境类型: 服务器"
fi

# 检测 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误] 未检测到 Python3${NC}"
    echo ""
    echo "是否自动安装 Python？(y/n)"
    read -r INSTALL_PYTHON
    if [ "$INSTALL_PYTHON" = "y" ] || [ "$INSTALL_PYTHON" = "Y" ]; then
        echo "正在安装 Python..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update -qq
            sudo apt-get install -y python3 python3-pip python3-venv -qq
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3 python3-pip -q
        elif command -v brew &> /dev/null; then
            brew install python3
        else
            echo -e "${RED}[错误] 无法自动安装，请手动安装 Python 3.8+${NC}"
            exit 1
        fi
        echo -e "${GREEN}[成功] Python 已安装${NC}"
    else
        echo "Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
        echo "CentOS/RHEL: sudo yum install python3 python3-pip"
        echo "macOS: brew install python3"
        exit 1
    fi
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}[成功] Python 版本: $PYTHON_VERSION${NC}"

# 检测 pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}[错误] 未检测到 pip3${NC}"
    exit 1
fi
echo -e "${GREEN}[成功] pip3 已安装${NC}"

echo ""
echo -e "${GREEN}[2/6] 创建虚拟环境...${NC}"
echo ""

# 创建虚拟环境
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}[成功] 虚拟环境已创建${NC}"
else
    echo -e "${GREEN}[成功] 虚拟环境已存在${NC}"
fi

echo ""
echo -e "${GREEN}[3/6] 安装依赖...${NC}"
echo ""

# 激活虚拟环境
source venv/bin/activate

# 升级 pip（使用代理）
if [ "$USE_PROXY" -eq 1 ] && [ -n "$PIP_PROXY" ]; then
    pip install --upgrade pip -q $PIP_PROXY 2>/dev/null
else
    pip install --upgrade pip -q 2>/dev/null
fi

# 安装依赖（使用代理）
if [ -f "requirements.txt" ]; then
    if [ "$USE_PROXY" -eq 1 ] && [ -n "$PIP_PROXY" ]; then
        pip install -r requirements.txt -q $PIP_PROXY 2>/dev/null
    else
        pip install -r requirements.txt -q 2>/dev/null
    fi
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}[警告] 部分依赖可能安装失败，正在重试...${NC}"
        pip install -r requirements.txt -q 2>/dev/null
    fi
    echo -e "${GREEN}[成功] 依赖安装完成${NC}"
else
    echo -e "${RED}[错误] 未找到 requirements.txt${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}[4/6] 检测配置目录...${NC}"
echo ""

# 设置配置目录
CONFIG_DIR="$HOME/.local/share/WindAgent"
if [ ! -d "$CONFIG_DIR" ]; then
    mkdir -p "$CONFIG_DIR"
    echo -e "${GREEN}[成功] 配置目录已创建: $CONFIG_DIR${NC}"
else
    echo -e "${GREEN}[成功] 配置目录已存在: $CONFIG_DIR${NC}"
fi

echo ""
echo -e "${GREEN}[5/6] 创建启动脚本...${NC}"
echo ""

# 创建启动脚本
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 main.py
EOF
chmod +x start.sh
echo -e "${GREEN}[成功] start.sh 已创建${NC}"

# 创建后台启动脚本
cat > start_silent.sh << EOF
#!/bin/bash
cd "$INSTALL_DIR"
source venv/bin/activate
nohup python3 main.py > windagent.log 2>&1 &
echo \$! > windagent.pid
echo "WindAgent 已后台启动，PID: \$(cat windagent.pid)"
EOF
chmod +x start_silent.sh
echo -e "${GREEN}[成功] start_silent.sh 已创建（后台运行）${NC}"

# 创建停止脚本
cat > stop.sh << 'EOF'
#!/bin/bash
if [ -f windagent.pid ]; then
    kill $(cat windagent.pid) 2>/dev/null
    rm windagent.pid
    echo "WindAgent 已停止"
else
    echo "未找到运行中的 WindAgent"
fi
EOF
chmod +x stop.sh
echo -e "${GREEN}[成功] stop.sh 已创建${NC}"

echo ""
echo -e "${GREEN}[6/6] 设置开机自启...${NC}"
echo ""

# 设置 systemd 服务 (Linux 服务器)
if [ "$MACHINE" = "Linux" ] && [ "$IS_SERVER" -eq 1 ]; then
    SERVICE_FILE="/etc/systemd/system/windagent.service"
    
    if [ "$EUID" -eq 0 ]; then
        cat > $SERVICE_FILE << EOF
[Unit]
Description=WindAgent Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        systemctl daemon-reload
        systemctl enable windagent
        echo -e "${GREEN}[成功] systemd 服务已创建并启用${NC}"
    else
        echo -e "${YELLOW}[提示] 需要 root 权限设置 systemd 服务${NC}"
        echo "请运行: sudo $0"
    fi
elif [ "$MACHINE" = "Linux" ] && [ "$IS_SERVER" -eq 0 ]; then
    # Linux 桌面环境
    STARTUP_FILE="$HOME/.config/autostart/windagent.desktop"
    mkdir -p "$(dirname "$STARTUP_FILE")"
    cat > "$STARTUP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=WindAgent
Exec=$INSTALL_DIR/start_silent.sh
Terminal=false
Hidden=false
EOF
    echo -e "${GREEN}[成功] 开机自启已设置${NC}"
elif [ "$MACHINE" = "Mac" ]; then
    # macOS 使用 launchd
    PLIST_FILE="$HOME/Library/LaunchAgents/com.windagent.plist"
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.windagent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/venv/bin/python3</string>
        <string>main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF
    launchctl load "$PLIST_FILE" 2>/dev/null
    echo -e "${GREEN}[成功] launchd 服务已创建并启用${NC}"
fi

echo ""
echo "========================================================"
echo "                    部署完成！"
echo "========================================================"
echo ""
echo "  启动方式："
echo "  1. ./start.sh          - 前台启动（带控制台输出）"
echo "  2. ./start_silent.sh   - 后台启动（无输出）"
echo "  3. ./stop.sh           - 停止后台运行"
echo ""
echo "  访问地址: http://127.0.0.1:8765"
echo ""
echo "  配置文件: $CONFIG_DIR/config.json"
echo ""
echo "  开机自启: 已设置"
echo ""
echo "========================================================"
echo ""

# 询问是否立即启动
read -p "是否立即启动 WindAgent？(y/n): " START_NOW
if [ "$START_NOW" = "y" ] || [ "$START_NOW" = "Y" ]; then
    echo ""
    echo "正在启动 WindAgent..."
    ./start.sh
fi
