# -*- coding: utf-8 -*-
"""
短期记忆系统
存储最近对话上下文
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryItem:
    """记忆项"""
    role: str
    content: str
    timestamp: str
    tokens: int = 0


class ShortTermMemory:
    """短期记忆"""
    
    def __init__(self, max_items: int = 10):
        self.max_items = max_items
        self.items: List[MemoryItem] = []
    
    def add(self, role: str, content: str, tokens: int = 0):
        """添加记忆"""
        item = MemoryItem(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            tokens=tokens
        )
        self.items.append(item)
        
        while len(self.items) > self.max_items:
            self.items.pop(0)
    
    def get_context(self, max_tokens: int = None) -> List[Dict]:
        """获取上下文"""
        context = []
        total_tokens = 0
        
        for item in reversed(self.items):
            if max_tokens and total_tokens + item.tokens > max_tokens:
                break
            context.insert(0, {
                "role": item.role,
                "content": item.content
            })
            total_tokens += item.tokens
        
        return context
    
    def clear(self):
        """清除记忆"""
        self.items = []
    
    def get_last(self, n: int = 1) -> List[MemoryItem]:
        """获取最近n条记忆"""
        return self.items[-n:]
    
    def search(self, keyword: str) -> List[MemoryItem]:
        """搜索记忆"""
        return [item for item in self.items if keyword.lower() in item.content.lower()]
    
    def to_dict(self) -> List[Dict]:
        """转换为字典"""
        return [
            {
                "role": item.role,
                "content": item.content,
                "timestamp": item.timestamp,
                "tokens": item.tokens
            }
            for item in self.items
        ]
    
    def from_dict(self, data: List[Dict]):
        """从字典加载"""
        self.items = [
            MemoryItem(
                role=item["role"],
                content=item["content"],
                timestamp=item["timestamp"],
                tokens=item.get("tokens", 0)
            )
            for item in data
        ]
    
    def __len__(self) -> int:
        return len(self.items)
    
    def __str__(self) -> str:
        return f"ShortTermMemory(items={len(self.items)}, max={self.max_items})"
