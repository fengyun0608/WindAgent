# -*- coding: utf-8 -*-
"""
WindAgent 入口文件
"""

import os
import sys
import argparse
import logging
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cloud.config import get_config, get_config_manager
from cloud.env import get_environment
from breeze.logger import setup_beautiful_logging, print_startup_sequence, print_log, print_status_box
from wind.routes import create_app


class ChineseLogFormatter(logging.Formatter):
    """中文日志格式化器"""
    
    LEVEL_MAP = {
        'INFO': '信息',
        'WARNING': '警告',
        'ERROR': '错误',
        'DEBUG': '调试',
        'CRITICAL': '严重'
    }
    
    def format(self, record):
        from datetime import datetime
        ts = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        level = self.LEVEL_MAP.get(record.levelname, record.levelname)
        
        msg = record.getMessage()
        
        if 'WebSocket' in msg:
            msg = msg.replace('WebSocket', 'WebSocket连接')
        if 'connection open' in msg:
            msg = '连接已建立'
        if 'connection closed' in msg:
            msg = '连接已关闭'
        if 'Started server process' in msg:
            msg = f'服务器进程已启动 [PID: {msg.split()[-1]}]'
        if 'Waiting for application startup' in msg:
            msg = '等待应用启动...'
        if 'Application startup complete' in msg:
            msg = '应用启动完成'
        if 'Uvicorn running on' in msg:
            msg = msg.replace('Uvicorn running on', '服务运行于')
        if 'Shutting down' in msg:
            msg = '正在关闭...'
        if '"GET' in msg or '"POST' in msg or '"DELETE' in msg or '"PUT' in msg:
            pass
        
        return f"\033[90m{ts}\033[0m \033[94m●\033[0m \033[1m[{level}]\033[0m {msg}"


def setup_chinese_logging():
    """设置中文日志"""
    logging.getLogger('uvicorn').handlers = []
    logging.getLogger('uvicorn.access').handlers = []
    logging.getLogger('uvicorn.error').handlers = []
    
    handler = logging.StreamHandler()
    handler.setFormatter(ChineseLogFormatter())
    
    for name in ['uvicorn', 'uvicorn.access', 'uvicorn.error']:
        logger = logging.getLogger(name)
        logger.handlers = [handler]
        logger.propagate = False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="WindAgent - 轻量级本地AI智能体")
    parser.add_argument("--host", type=str, help="服务器地址")
    parser.add_argument("--port", type=int, help="服务器端口")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--env", action="store_true", help="显示环境信息")
    parser.add_argument("--config", type=str, help="配置文件路径")
    
    args = parser.parse_args()
    
    if args.config:
        config_manager = get_config_manager(args.config)
    else:
        config_manager = get_config_manager()
    
    config = config_manager.config
    
    if args.env:
        env = get_environment()
        print_status_box([
            ("设备类型", str(env.device_type.value), "info"),
            ("操作系统", env.os_name, "info"),
            ("系统版本", env.os_version[:30], "info"),
            ("架构", env.arch, "info"),
            ("Python", env.python_version, "info"),
            ("内存", f"{env.memory_gb} GB", "info"),
            ("GPU", "是" if env.has_gpu else "否", "success" if env.has_gpu else "warning"),
        ], "🖥️ 环境信息")
        return
    
    log_level = "DEBUG" if args.debug else config.log_level
    setup_beautiful_logging(log_level)
    setup_chinese_logging()
    
    host = args.host or config.server.host
    port = args.port or config.server.port
    debug = args.debug or config.server.debug
    
    print_startup_sequence(config)
    
    if not config.ai.api_key:
        print_log("WARNING", "API Key 未配置，请在管理后台设置", "config")
    
    os.makedirs(config.data_dir, exist_ok=True)
    
    app = create_app()
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level.lower(),
        access_log=debug
    )


if __name__ == "__main__":
    main()
