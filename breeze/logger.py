# -*- coding: utf-8 -*-
"""
WindAgent 美化日志系统
"""

import os
import sys
import time
import logging
import re
from datetime import datetime
from typing import List, Tuple


class C:
    """ANSI 颜色代码"""
    R = "\033[0m"
    B = "\033[1m"
    D = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAG = "\033[35m"
    CYN = "\033[36m"
    WHI = "\033[37m"
    BR = "\033[91m"
    BG = "\033[92m"
    BY = "\033[93m"
    BB = "\033[94m"
    BM = "\033[95m"
    BC = "\033[96m"
    BW = "\033[97m"
    BGR = "\033[41m"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """打印启动 Banner - ASCII艺术版"""
    print()
    print(f"{C.BC}╔══════════════════════════════════════════════════════════════════╗{C.R}")
    print(f"{C.BC}║{C.R}                                                                  {C.BC}║{C.R}")
    print(f"{C.BC}║{C.R}      {C.BM}██╗    ██╗██╗██████╗ ███████╗ ██████╗ ██████╗{C.R}               {C.BC}║{C.R}")
    print(f"{C.BC}║{C.R}      {C.BM}██║    ██║██║██╔══██╗██╔════╝██╔════╝██╔═══██╗{C.R}              {C.BC}║{C.R}")
    print(f"{C.BC}║{C.R}      {C.BM}██║ █╗ ██║██║██║  ██║█████╗  ██║     ██║   ██║{C.R}              {C.BC}║{C.R}")
    print(f"{C.BC}║{C.R}      {C.BM}██║███╗██║██║██║  ██║██╔══╝  ██║     ██║   ██║{C.R}              {C.BC}║{C.R}")
    print(f"{C.BC}║{C.R}      {C.BM}╚███╔███╔╝██║██████╔╝███████╗╚██████╗╚██████╔╝{C.R}              {C.BC}║{C.R}")
    print(f"{C.BC}║{C.R}       {C.BM}╚══╝╚══╝ ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝{C.R}               {C.BC}║{C.R}")
    print(f"{C.BC}║{C.R}                                                                  {C.BC}║{C.R}")
    print(f"{C.BC}╠══════════════════════════════════════════════════════════════════╣{C.R}")
    print(f"{C.BC}║{C.R}     WindAgent - 风云智能体                                       {C.BC}║{C.R}")
    print(f"{C.BC}║{C.R}     开源免费 | MIT License | 作者: 风云                          {C.BC}║{C.R}")
    print(f"{C.BC}╚══════════════════════════════════════════════════════════════════╝{C.R}")
    print()


def print_loading(text: str, duration: float = 0.3):
    frames = ["|", "/", "-", "\\", "|", "/", "-", "\\", "|", "/"]
    colors = [C.BC, C.BB, C.BM, C.BG]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        print(f"\r{colors[i % 4]}{frames[i % 10]}{C.R} {text}{'.' * (i % 4)}{' ' * 3}", end='', flush=True)
        time.sleep(0.08)
        i += 1
    print(f"\r{C.BG}OK{C.R} {text}    ")


def get_width(text: str) -> int:
    """计算显示宽度（中文=2，emoji=2）"""
    text = re.sub(r'\033\[[0-9;]*m', '', text)
    w = 0
    for c in text:
        if '\u4e00' <= c <= '\u9fff':
            w += 2
        elif ord(c) > 0xFFFF:
            w += 2
        else:
            w += 1
    return w


def print_status_box(items: List[Tuple[str, str, str]], title: str = "状态"):
    """打印状态框"""
    W = 52
    
    tw = get_width(title)
    lp = (W - tw) // 2
    rp = W - tw - lp
    
    print(f"\n{C.BC}╭{'─' * W}╮{C.R}")
    print(f"{C.BC}│{' ' * lp}{C.BW}{C.B}{title}{C.R}{' ' * rp}{C.BC}│{C.R}")
    print(f"{C.BC}├{'─' * W}┤{C.R}")
    
    for label, value, status in items:
        cfg = {"success": (C.BG, "OK"), "warning": (C.BY, "!"), "error": (C.BR, "X"), "info": (C.BB, "*")}
        color, icon = cfg.get(status, (C.WHI, "•"))
        
        content = f"  {color}{icon}{C.R} {label}: {C.BW}{value}{C.R}"
        cw = get_width(f"  {icon} {label}: {value}")
        pad = W - cw
        
        print(f"{C.BC}│{content}{' ' * max(0, pad)}{C.BC}│{C.R}")
    
    print(f"{C.BC}╰{'─' * W}╯{C.R}")


def print_log(level: str, message: str, source: str = ""):
    ts = datetime.now().strftime("%H:%M:%S")
    cfg = {"DEBUG": (C.D, "o"), "INFO": (C.BB, "*"), "SUCCESS": (C.BG, "OK"),
           "WARNING": (C.BY, "!"), "ERROR": (C.BR, "X"), "CRITICAL": (C.BGR + C.BW, "#"),
           "HOTRELOAD": (C.BM, "R")}
    color, icon = cfg.get(level, (C.WHI, "*"))
    src = f"{C.BM}[{source}]{C.R} " if source else ""
    print(f"{C.D}{ts}{C.R} {color}{icon} {level:10}{C.R} {src}{message}")


def print_divider():
    try:
        w = os.get_terminal_size().columns
    except:
        w = 60
    print(f"{C.BM}{'─' * w}{C.R}")


class BeautifulFormatter(logging.Formatter):
    LEVEL_COLORS = {logging.DEBUG: C.D, logging.INFO: C.BB, logging.WARNING: C.BY,
                    logging.ERROR: C.BR, logging.CRITICAL: C.BGR + C.BW}
    LEVEL_ICONS = {logging.DEBUG: "o", logging.INFO: "*", logging.WARNING: "!",
                   logging.ERROR: "X", logging.CRITICAL: "#"}
    
    def format(self, record):
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        color = self.LEVEL_COLORS.get(record.levelno, C.WHI)
        icon = self.LEVEL_ICONS.get(record.levelno, "•")
        src = record.name.split('.')[-1] if record.name else ""
        return f"{C.D}{ts}{C.R} {color}{icon} {record.levelname:8}{C.R} {C.BM}[{src}]{C.R} {record.getMessage()}"


class BeautifulHandler(logging.Handler):
    def emit(self, record):
        try:
            print(self.format(record))
        except:
            self.handleError(record)


def setup_beautiful_logging(log_level: str = "INFO"):
    h = BeautifulHandler()
    h.setFormatter(BeautifulFormatter())
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(h)
    root.setLevel(getattr(logging, log_level.upper()))


def print_startup_sequence(config):
    clear_screen()
    print_banner()
    print_loading("初始化配置", 0.3)
    print_loading("加载插件系统", 0.3)
    print_loading("准备数据库", 0.2)
    print_loading("启动 Web 服务", 0.3)
    print()
    
    data_dir = config.data_dir
    if len(data_dir) > 35:
        data_dir = data_dir[:35] + "..."
    
    print_status_box([
        ("版本", f"v{config.version}", "success"),
        ("作者", config.author, "info"),
        ("协议", config.license, "info"),
        ("数据目录", data_dir, "info"),
        ("API Key", "已配置" if config.ai.api_key else "未配置", "success" if config.ai.api_key else "warning"),
        ("模型", config.ai.model or "未设置", "info"),
    ], ">> 启动状态")
    
    print()
    print_divider()
    
    h, p = config.server.host, config.server.port
    print(f"""
{C.BG}  > 本地访问:{C.R}  http://{h}:{p}
{C.BC}  > 网络访问:{C.R}  http://0.0.0.0:{p}
{C.BY}  > 管理后台:{C.R}  http://{h}:{p}/
""")
    print_divider()
    print(f"\n{C.D}  按 Ctrl+C 停止服务{C.R}\n")
    print(f"{C.BM}{'─' * 60}{C.R}\n")
