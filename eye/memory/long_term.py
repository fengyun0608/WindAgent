# -*- coding: utf-8 -*-
"""
长期记忆系统
使用向量数据库存储重要记忆
"""

import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime


class LongTermMemory:
    """长期记忆"""
    
    def __init__(self, storage_path: str = None, use_vector: bool = True):
        from cloud.env import get_environment
        env = get_environment()
        
        self.storage_path = storage_path or os.path.join(env.data_dir, "memory")
        os.makedirs(self.storage_path, exist_ok=True)
        
        self.use_vector = use_vector
        self.vector_store = None
        
        if use_vector:
            self._init_vector_store()
        
        self.index_path = os.path.join(self.storage_path, "index.json")
        self.index: Dict[str, Dict] = {}
        self._load_index()
    
    def _init_vector_store(self):
        """初始化向量存储"""
        try:
            import chromadb
            self.vector_store = chromadb.PersistentClient(
                path=os.path.join(self.storage_path, "vectors")
            )
            self.collection = self.vector_store.get_or_create_collection(
                name="memories"
            )
        except ImportError:
            self.use_vector = False
            self.vector_store = None
    
    def _load_index(self):
        """加载索引"""
        if os.path.exists(self.index_path):
            with open(self.index_path, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
    
    def _save_index(self):
        """保存索引"""
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
    
    def save(self, key: str, content: str, metadata: Dict = None):
        """保存记忆"""
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(content) % 10000}"
        
        memory_data = {
            "id": memory_id,
            "key": key,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }
        
        self.index[memory_id] = memory_data
        self._save_index()
        
        if self.use_vector and self.vector_store:
            self._add_to_vector_store(memory_id, content, metadata)
        
        return memory_id
    
    def _add_to_vector_store(self, memory_id: str, content: str, metadata: Dict):
        """添加到向量存储"""
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata or {}],
                ids=[memory_id]
            )
        except Exception:
            pass
    
    def get(self, memory_id: str) -> Optional[Dict]:
        """获取记忆"""
        return self.index.get(memory_id)
    
    def get_by_key(self, key: str) -> List[Dict]:
        """按键获取记忆"""
        return [
            mem for mem in self.index.values()
            if mem.get("key") == key
        ]
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """搜索记忆"""
        if self.use_vector and self.vector_store:
            return self._vector_search(query, limit)
        return self._keyword_search(query, limit)
    
    def _vector_search(self, query: str, limit: int) -> List[Dict]:
        """向量搜索"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            memories = []
            for i, doc_id in enumerate(results['ids'][0]):
                if doc_id in self.index:
                    memory = self.index[doc_id].copy()
                    memory['score'] = 1 - results['distances'][0][i] if results.get('distances') else 1.0
                    memories.append(memory)
            return memories
        except Exception:
            return self._keyword_search(query, limit)
    
    def _keyword_search(self, query: str, limit: int) -> List[Dict]:
        """关键词搜索"""
        query_lower = query.lower()
        results = []
        
        for memory in self.index.values():
            if query_lower in memory.get("content", "").lower():
                results.append(memory)
        
        return results[:limit]
    
    def delete(self, memory_id: str):
        """删除记忆"""
        if memory_id in self.index:
            del self.index[memory_id]
            self._save_index()
            
            if self.use_vector and self.vector_store:
                try:
                    self.collection.delete(ids=[memory_id])
                except Exception:
                    pass
    
    def clear(self):
        """清除所有记忆"""
        self.index = {}
        self._save_index()
        
        if self.use_vector and self.vector_store:
            try:
                self.vector_store.delete_collection("memories")
                self.collection = self.vector_store.get_or_create_collection("memories")
            except Exception:
                pass
    
    def get_all(self) -> List[Dict]:
        """获取所有记忆"""
        return list(self.index.values())
    
    def count(self) -> int:
        """获取记忆数量"""
        return len(self.index)
    
    def __len__(self) -> int:
        return self.count()
    
    def __str__(self) -> str:
        return f"LongTermMemory(items={self.count()}, vector={self.use_vector})"
