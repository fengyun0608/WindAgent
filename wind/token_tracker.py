# -*- coding: utf-8 -*-
"""
WindAgent Token 统计系统
仅用于本地统计，不涉及付费
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class TokenRecord:
    """Token记录"""
    timestamp: str
    tokens: int
    model: str
    action: str = "chat"


class TokenTracker:
    """Token追踪器"""
    
    def __init__(self, storage_path: str = None):
        from cloud.env import get_environment
        env = get_environment()
        
        self.storage_path = storage_path or os.path.join(env.data_dir, "token_usage.json")
        self.records: List[TokenRecord] = []
        self._load()
    
    def _load(self):
        """加载记录"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [TokenRecord(**r) for r in data.get("records", [])]
            except Exception:
                self.records = []
    
    def _save(self):
        """保存记录"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump({
                "records": [asdict(r) for r in self.records]
            }, f, ensure_ascii=False, indent=2)
    
    def record(self, tokens: int, model: str = "", action: str = "chat"):
        """记录Token使用"""
        record = TokenRecord(
            timestamp=datetime.now().isoformat(),
            tokens=tokens,
            model=model,
            action=action
        )
        self.records.append(record)
        self._save()
    
    def get_total(self, days: int = None) -> int:
        """获取总Token数"""
        if days is None:
            return sum(r.tokens for r in self.records)
        
        cutoff = datetime.now() - timedelta(days=days)
        return sum(
            r.tokens for r in self.records 
            if datetime.fromisoformat(r.timestamp) >= cutoff
        )
    
    def get_stats(self, days: int = 30) -> Dict:
        """获取统计信息"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_records = [
            r for r in self.records 
            if datetime.fromisoformat(r.timestamp) >= cutoff
        ]
        
        total_tokens = sum(r.tokens for r in recent_records)
        
        by_model: Dict[str, int] = {}
        by_action: Dict[str, int] = {}
        by_date: Dict[str, int] = {}
        
        for r in recent_records:
            by_model[r.model] = by_model.get(r.model, 0) + r.tokens
            by_action[r.action] = by_action.get(r.action, 0) + r.tokens
            
            date = r.timestamp[:10]
            by_date[date] = by_date.get(date, 0) + r.tokens
        
        return {
            "total_tokens": total_tokens,
            "request_count": len(recent_records),
            "by_model": by_model,
            "by_action": by_action,
            "by_date": by_date,
            "avg_per_request": total_tokens / len(recent_records) if recent_records else 0
        }
    
    def get_daily_usage(self, days: int = 7) -> List[Dict]:
        """获取每日使用量"""
        result = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_tokens = sum(
                r.tokens for r in self.records 
                if r.timestamp.startswith(date)
            )
            result.append({
                "date": date,
                "tokens": day_tokens
            })
        return result[::-1]
    
    def clear_old(self, days: int = 90):
        """清除旧记录"""
        cutoff = datetime.now() - timedelta(days=days)
        self.records = [
            r for r in self.records 
            if datetime.fromisoformat(r.timestamp) >= cutoff
        ]
        self._save()
    
    def estimate_cost(self, price_per_1k: float = 0.002) -> float:
        """估算费用（仅供参考）"""
        return self.get_total() / 1000 * price_per_1k


_tracker: Optional[TokenTracker] = None


def get_tracker() -> TokenTracker:
    """获取Token追踪器"""
    global _tracker
    if not _tracker:
        _tracker = TokenTracker()
    return _tracker


def count_tokens(text: str) -> int:
    """估算Token数量"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return chinese_chars + other_chars // 4
