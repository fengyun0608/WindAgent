# -*- coding: utf-8 -*-
"""
WindAgent 自主学习守护模式
特色功能：AI自主学习、系统保护、知识积累
"""

import os
import psutil
import time
import json
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class SystemStatus:
    """系统状态"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    running_processes: int = 0
    network_connections: int = 0
    timestamp: str = ""


@dataclass
class LearningRecord:
    """学习记录"""
    event_type: str
    content: str
    timestamp: str
    importance: int = 1


class GuardianMode:
    """自主学习守护模式"""
    
    def __init__(self, agent):
        self.agent = agent
        self.enabled = False
        self.thread: Optional[threading.Thread] = None
        self.interval = 60
        self.learning_records: List[LearningRecord] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.user_habits: Dict[str, Any] = {}
        self.alerts: List[Dict] = []
        self.stats = {
            "checks_performed": 0,
            "issues_found": 0,
            "auto_fixed": 0,
            "knowledge_learned": 0
        }
        
        self._load_knowledge()
    
    def _load_knowledge(self):
        """加载知识库"""
        try:
            kb_path = os.path.join(self.agent.env.data_dir, "guardian_knowledge.json")
            if os.path.exists(kb_path):
                with open(kb_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.knowledge_base = data.get("knowledge", {})
                    self.user_habits = data.get("habits", {})
        except Exception:
            pass
    
    def _save_knowledge(self):
        """保存知识库"""
        try:
            kb_path = os.path.join(self.agent.env.data_dir, "guardian_knowledge.json")
            with open(kb_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "knowledge": self.knowledge_base,
                    "habits": self.user_habits
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def start(self):
        """启动守护模式"""
        if self.enabled:
            return {"success": False, "message": "守护模式已在运行"}
        
        self.enabled = True
        self.thread = threading.Thread(target=self._guardian_loop, daemon=True)
        self.thread.start()
        
        return {"success": True, "message": "守护模式已启动"}
    
    def stop(self):
        """停止守护模式"""
        self.enabled = False
        self._save_knowledge()
        return {"success": True, "message": "守护模式已停止"}
    
    def _guardian_loop(self):
        """守护循环"""
        while self.enabled:
            try:
                self._perform_check()
                self._learn_from_patterns()
            except Exception as e:
                self._add_alert("error", f"守护检查出错: {str(e)}")
            
            time.sleep(self.interval)
    
    def _perform_check(self):
        """执行系统检查"""
        self.stats["checks_performed"] += 1
        
        status = self.get_system_status()
        
        if status.cpu_percent > 80:
            self._add_alert("warning", f"CPU使用率过高: {status.cpu_percent:.1f}%")
            self.stats["issues_found"] += 1
            self._check_high_cpu_processes()
        
        if status.memory_percent > 85:
            self._add_alert("warning", f"内存使用率过高: {status.memory_percent:.1f}%")
            self.stats["issues_found"] += 1
        
        if status.disk_percent > 90:
            self._add_alert("warning", f"磁盘空间不足: {status.disk_percent:.1f}%")
            self.stats["issues_found"] += 1
    
    def _check_high_cpu_processes(self):
        """检查高CPU进程"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                if proc.info['cpu_percent'] and proc.info['cpu_percent'] > 50:
                    self._learn("high_cpu_process", f"{proc.info['name']}: {proc.info['cpu_percent']:.1f}%")
        except Exception:
            pass
    
    def _learn_from_patterns(self):
        """从模式中学习"""
        current_hour = datetime.now().hour
        
        if 9 <= current_hour <= 18:
            self.user_habits["work_hours"] = True
        
        if current_hour >= 22 or current_hour <= 6:
            self.user_habits["night_user"] = True
    
    def _learn(self, event_type: str, content: str, importance: int = 1):
        """学习记录"""
        record = LearningRecord(
            event_type=event_type,
            content=content,
            timestamp=datetime.now().isoformat(),
            importance=importance
        )
        self.learning_records.append(record)
        self.stats["knowledge_learned"] += 1
        
        if len(self.learning_records) > 1000:
            self.learning_records = self.learning_records[-500:]
    
    def _add_alert(self, alert_type: str, message: str):
        """添加警报"""
        self.alerts.append({
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-50:]
    
    def get_system_status(self) -> SystemStatus:
        """获取系统状态"""
        return SystemStatus(
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=psutil.virtual_memory().percent,
            disk_percent=psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent,
            running_processes=len(psutil.pids()),
            network_connections=len(psutil.net_connections()),
            timestamp=datetime.now().isoformat()
        )
    
    def get_status(self) -> Dict:
        """获取守护状态"""
        return {
            "enabled": self.enabled,
            "interval": self.interval,
            "stats": self.stats,
            "recent_alerts": self.alerts[-10:],
            "knowledge_count": len(self.knowledge_base),
            "habits": self.user_habits,
            "system": asdict(self.get_system_status())
        }
    
    def ask_ai_for_advice(self, context: str) -> str:
        """向AI请求建议（节省Token，只在必要时调用）"""
        if not self.enabled:
            return "守护模式未启用"
        
        prompt = f"""作为系统守护者，请分析以下情况并给出建议：

{context}

已知用户习惯：{json.dumps(self.user_habits, ensure_ascii=False)}
知识库摘要：{list(self.knowledge_base.keys())[:10]}

请简洁地给出：
1. 问题分析
2. 建议操作
3. 是否需要用户确认"""
        
        try:
            return self.agent.process_message(prompt)
        except Exception as e:
            return f"AI建议获取失败: {str(e)}"
    
    def learn_user_preference(self, key: str, value: Any):
        """学习用户偏好"""
        self.knowledge_base[key] = {
            "value": value,
            "learned_at": datetime.now().isoformat(),
            "times_used": self.knowledge_base.get(key, {}).get("times_used", 0) + 1
        }
        self._save_knowledge()
        self.stats["knowledge_learned"] += 1
