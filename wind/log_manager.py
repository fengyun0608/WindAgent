# -*- coding: utf-8 -*-
"""
WindAgent 日志管理器
记录AI对话、执行结果、系统事件
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class LogManager:
    """日志管理器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.logs_dir = self.data_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.chat_log_file = self.logs_dir / "chat.log"
        self.execute_log_file = self.logs_dir / "execute.log"
        self.system_log_file = self.logs_dir / "system.log"
        
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        self.logger = logging.getLogger("WindAgent")
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            handler = logging.FileHandler(
                self.system_log_file,
                encoding='utf-8'
            )
            handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            self.logger.addHandler(handler)
    
    def log_chat(self, role: str, content: str, conversation_id: Optional[int] = None):
        """记录聊天日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{role.upper()}] [会话:{conversation_id or '新'}]\n{content}\n{'─' * 60}\n"
        
        with open(self.chat_log_file, 'a', encoding='utf-8-sig') as f:
            f.write(log_entry)
        
        self.logger.info(f"聊天记录: {role} - {len(content)}字符")
    
    def log_execute(self, lang: str, code: str, result: str, success: bool = True):
        """记录执行日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = "✓ 成功" if success else "✗ 失败"
        
        log_entry = f"""[{timestamp}] [{lang.upper()}] {status}
代码:
{code}
结果:
{result}
{'═' * 60}
"""
        
        with open(self.execute_log_file, 'a', encoding='utf-8-sig') as f:
            f.write(log_entry)
        
        self.logger.info(f"代码执行: {lang} - {status}")
    
    def log_system(self, level: str, message: str):
        """记录系统日志"""
        level_map = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR
        }
        self.logger.log(level_map.get(level.lower(), logging.INFO), message)
    
    def get_chat_logs(self, limit: int = 100) -> List[Dict]:
        """获取聊天日志"""
        logs = []
        if not self.chat_log_file.exists():
            return logs
        
        with open(self.chat_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        entries = content.split('─' * 60)
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            
            lines = entry.split('\n')
            if len(lines) >= 2:
                header = lines[0]
                body = '\n'.join(lines[1:])
                
                logs.append({
                    'header': header,
                    'content': body,
                    'raw': entry
                })
        
        return logs[-limit:]
    
    def get_execute_logs(self, limit: int = 50) -> List[Dict]:
        """获取执行日志"""
        logs = []
        if not self.execute_log_file.exists():
            return logs
        
        with open(self.execute_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        entries = content.split('═' * 60)
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            
            logs.append({
                'raw': entry
            })
        
        return logs[-limit:]
    
    def get_system_logs(self, limit: int = 200) -> List[str]:
        """获取系统日志"""
        if not self.system_log_file.exists():
            return []
        
        with open(self.system_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        return [line.strip() for line in lines[-limit:]]
    
    def clear_logs(self, log_type: str = 'all'):
        """清除日志"""
        if log_type in ('all', 'chat') and self.chat_log_file.exists():
            self.chat_log_file.unlink()
        if log_type in ('all', 'execute') and self.execute_log_file.exists():
            self.execute_log_file.unlink()
        if log_type in ('all', 'system') and self.system_log_file.exists():
            self.system_log_file.unlink()
        
        self.logger.info(f"日志已清除: {log_type}")
    
    def get_log_stats(self) -> Dict:
        """获取日志统计"""
        stats = {
            'chat': {'size': 0, 'lines': 0},
            'execute': {'size': 0, 'lines': 0},
            'system': {'size': 0, 'lines': 0}
        }
        
        for name, path in [
            ('chat', self.chat_log_file),
            ('execute', self.execute_log_file),
            ('system', self.system_log_file)
        ]:
            if path.exists():
                stats[name]['size'] = path.stat().st_size
                with open(path, 'r', encoding='utf-8') as f:
                    stats[name]['lines'] = len(f.readlines())
        
        return stats
    
    def export_logs(self, output_path: str, log_type: str = 'all') -> str:
        """导出日志"""
        export_data = {
            'export_time': datetime.now().isoformat(),
            'logs': {}
        }
        
        if log_type in ('all', 'chat'):
            export_data['logs']['chat'] = self.get_chat_logs()
        if log_type in ('all', 'execute'):
            export_data['logs']['execute'] = self.get_execute_logs()
        if log_type in ('all', 'system'):
            export_data['logs']['system'] = self.get_system_logs()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return output_path


_log_manager: Optional[LogManager] = None


def get_log_manager(data_dir: str = None) -> LogManager:
    """获取日志管理器实例"""
    global _log_manager
    
    if _log_manager is None and data_dir:
        _log_manager = LogManager(data_dir)
    
    return _log_manager
