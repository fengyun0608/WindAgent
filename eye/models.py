# -*- coding: utf-8 -*-
"""
WindAgent 数据库模型
SQLite 本地存储
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class User:
    """用户模型"""
    id: int = 0
    name: str = "default"
    created_at: str = ""
    settings: Dict = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Conversation:
    """对话模型"""
    id: int = 0
    user_id: int = 1
    title: str = ""
    platform: str = "web"
    platform_user_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class Message:
    """消息模型"""
    id: int = 0
    conversation_id: int = 0
    role: str = "user"
    content: str = ""
    tokens: int = 0
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class TokenUsage:
    """Token使用记录"""
    id: int = 0
    user_id: int = 1
    tokens: int = 0
    model: str = ""
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Memory:
    """记忆模型"""
    id: int = 0
    user_id: int = 1
    key: str = ""
    value: str = ""
    memory_type: str = "short"
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class Database:
    """数据库管理"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            from cloud.env import get_environment
            env = get_environment()
            db_path = os.path.join(env.data_dir, "windagent.db")
        
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TEXT,
                    settings TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    platform TEXT DEFAULT 'web',
                    platform_user_id TEXT DEFAULT '',
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            try:
                cursor.execute("ALTER TABLE conversations ADD COLUMN platform TEXT DEFAULT 'web'")
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE conversations ADD COLUMN platform_user_id TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    role TEXT,
                    content TEXT,
                    tokens INTEGER DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    tokens INTEGER,
                    model TEXT,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    key TEXT,
                    value TEXT,
                    memory_type TEXT DEFAULT 'short',
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("SELECT * FROM users WHERE name = 'default'")
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (name, created_at, settings) VALUES (?, ?, ?)",
                    ("default", datetime.now().isoformat(), "{}")
                )
    
    def create_user(self, name: str, settings: Dict = None) -> User:
        """创建用户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, created_at, settings) VALUES (?, ?, ?)",
                (name, datetime.now().isoformat(), json.dumps(settings or {}))
            )
            return User(id=cursor.lastrowid, name=name, settings=settings)
    
    def get_user(self, user_id: int = 1) -> Optional[User]:
        """获取用户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return User(
                    id=row['id'],
                    name=row['name'],
                    created_at=row['created_at'],
                    settings=json.loads(row['settings'] or '{}')
                )
        return None
    
    def create_conversation(self, user_id: int = 1, title: str = "", platform: str = "web", platform_user_id: str = "") -> Conversation:
        """创建对话"""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (user_id, title, platform, platform_user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, title, platform, platform_user_id, now, now)
            )
            return Conversation(id=cursor.lastrowid, user_id=user_id, title=title, platform=platform, platform_user_id=platform_user_id)
    
    def get_or_create_default_conversation(self, platform: str = "web") -> Conversation:
        """获取或创建默认会话"""
        default_title = "网页会话" if platform == "web" else f"{platform}会话"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM conversations WHERE platform = ? AND title = ?",
                (platform, default_title)
            )
            row = cursor.fetchone()
            if row:
                return Conversation(
                    id=row['id'],
                    user_id=row['user_id'],
                    title=row['title'],
                    platform=row['platform'],
                    platform_user_id=row['platform_user_id'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO conversations (user_id, title, platform, platform_user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (1, default_title, platform, "", now, now)
            )
            return Conversation(id=cursor.lastrowid, user_id=1, title=default_title, platform=platform, platform_user_id="")
    
    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """获取对话"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
            row = cursor.fetchone()
            if row:
                return Conversation(
                    id=row['id'],
                    user_id=row['user_id'],
                    title=row['title'],
                    platform=row['platform'],
                    platform_user_id=row['platform_user_id'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
        return None
    
    def get_conversations(self, user_id: int = 1, platform: str = None, limit: int = 20) -> List[Conversation]:
        """获取用户的对话列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if platform:
                cursor.execute(
                    "SELECT * FROM conversations WHERE user_id = ? AND platform = ? ORDER BY updated_at DESC LIMIT ?",
                    (user_id, platform, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
                    (user_id, limit)
                )
            return [Conversation(
                id=row['id'],
                user_id=row['user_id'],
                title=row['title'],
                platform=row['platform'],
                platform_user_id=row['platform_user_id'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ) for row in cursor.fetchall()]
    
    def get_conversations_by_platform(self, platform: str, limit: int = 50) -> List[Conversation]:
        """获取特定平台的对话列表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM conversations WHERE platform = ? ORDER BY updated_at DESC LIMIT ?",
                (platform, limit)
            )
            return [Conversation(
                id=row['id'],
                user_id=row['user_id'],
                title=row['title'],
                platform=row['platform'],
                platform_user_id=row['platform_user_id'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ) for row in cursor.fetchall()]
    
    def add_message(self, conversation_id: int, role: str, content: str, tokens: int = 0) -> Message:
        """添加消息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO messages (conversation_id, role, content, tokens, created_at) VALUES (?, ?, ?, ?, ?)",
                (conversation_id, role, content, tokens, now)
            )
            cursor.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id)
            )
            return Message(
                id=cursor.lastrowid,
                conversation_id=conversation_id,
                role=role,
                content=content,
                tokens=tokens
            )
    
    def get_messages(self, conversation_id: int, limit: int = 50) -> List[Message]:
        """获取对话消息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
                (conversation_id, limit)
            )
            return [Message(
                id=row['id'],
                conversation_id=row['conversation_id'],
                role=row['role'],
                content=row['content'],
                tokens=row['tokens'],
                created_at=row['created_at']
            ) for row in cursor.fetchall()]
    
    def record_token_usage(self, user_id: int, tokens: int, model: str = ""):
        """记录Token使用"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO token_usage (user_id, tokens, model, created_at) VALUES (?, ?, ?, ?)",
                (user_id, tokens, model, datetime.now().isoformat())
            )
    
    def get_token_usage(self, user_id: int = 1, days: int = 30) -> Dict:
        """获取Token使用统计"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    SUM(tokens) as total,
                    COUNT(*) as count
                FROM token_usage 
                WHERE user_id = ? AND created_at >= date('now', ?)
            """, (user_id, f'-{days} days'))
            row = cursor.fetchone()
            return {
                "total_tokens": row['total'] or 0,
                "request_count": row['count'] or 0
            }
    
    def save_memory(self, user_id: int, key: str, value: str, memory_type: str = "short"):
        """保存记忆"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO memories (user_id, key, value, memory_type, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, key, value, memory_type, datetime.now().isoformat())
            )
    
    def get_memory(self, user_id: int, key: str) -> Optional[str]:
        """获取记忆"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM memories WHERE user_id = ? AND key = ?",
                (user_id, key)
            )
            row = cursor.fetchone()
            return row['value'] if row else None
    
    def get_all_memories(self, user_id: int, memory_type: str = None) -> Dict[str, str]:
        """获取所有记忆"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if memory_type:
                cursor.execute(
                    "SELECT key, value FROM memories WHERE user_id = ? AND memory_type = ?",
                    (user_id, memory_type)
                )
            else:
                cursor.execute(
                    "SELECT key, value FROM memories WHERE user_id = ?",
                    (user_id,)
                )
            return {row['key']: row['value'] for row in cursor.fetchall()}
    
    def delete_conversation(self, conversation_id: int):
        """删除对话及其消息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    
    def delete_messages(self, conversation_id: int):
        """清空对话消息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))


_db: Optional[Database] = None


def get_db() -> Database:
    """获取数据库实例"""
    global _db
    if not _db:
        _db = Database()
    return _db
