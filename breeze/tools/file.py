# -*- coding: utf-8 -*-
"""
文件工具
"""

import os
import shutil
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class FileTool:
    """文件工具"""
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.getcwd()
    
    def _resolve_path(self, path: str) -> str:
        """解析路径"""
        if os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(self.base_path, path))
    
    def read(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """读取文件"""
        try:
            full_path = self._resolve_path(path)
            
            if not os.path.exists(full_path):
                return {"success": False, "error": "文件不存在"}
            
            with open(full_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "path": full_path,
                "size": len(content)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def write(self, path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """写入文件"""
        try:
            full_path = self._resolve_path(path)
            
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return {
                "success": True,
                "path": full_path,
                "size": len(content)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def append(self, path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """追加内容"""
        try:
            full_path = self._resolve_path(path)
            
            with open(full_path, 'a', encoding=encoding) as f:
                f.write(content)
            
            return {"success": True, "path": full_path}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete(self, path: str) -> Dict[str, Any]:
        """删除文件或目录"""
        try:
            full_path = self._resolve_path(path)
            
            if not os.path.exists(full_path):
                return {"success": False, "error": "路径不存在"}
            
            if os.path.isfile(full_path):
                os.remove(full_path)
            else:
                shutil.rmtree(full_path)
            
            return {"success": True, "path": full_path}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_dir(self, path: str = ".") -> Dict[str, Any]:
        """列出目录内容"""
        try:
            full_path = self._resolve_path(path)
            
            if not os.path.exists(full_path):
                return {"success": False, "error": "目录不存在"}
            
            if not os.path.isdir(full_path):
                return {"success": False, "error": "不是目录"}
            
            items = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                stat = os.stat(item_path)
                
                items.append({
                    "name": item,
                    "path": item_path,
                    "is_dir": os.path.isdir(item_path),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            return {
                "success": True,
                "path": full_path,
                "items": items
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def copy(self, src: str, dst: str) -> Dict[str, Any]:
        """复制文件或目录"""
        try:
            src_path = self._resolve_path(src)
            dst_path = self._resolve_path(dst)
            
            if not os.path.exists(src_path):
                return {"success": False, "error": "源路径不存在"}
            
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
            else:
                shutil.copytree(src_path, dst_path)
            
            return {
                "success": True,
                "src": src_path,
                "dst": dst_path
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def move(self, src: str, dst: str) -> Dict[str, Any]:
        """移动文件或目录"""
        try:
            src_path = self._resolve_path(src)
            dst_path = self._resolve_path(dst)
            
            if not os.path.exists(src_path):
                return {"success": False, "error": "源路径不存在"}
            
            shutil.move(src_path, dst_path)
            
            return {
                "success": True,
                "src": src_path,
                "dst": dst_path
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def exists(self, path: str) -> Dict[str, Any]:
        """检查路径是否存在"""
        full_path = self._resolve_path(path)
        
        return {
            "exists": os.path.exists(full_path),
            "is_file": os.path.isfile(full_path),
            "is_dir": os.path.isdir(full_path),
            "path": full_path
        }
    
    def mkdir(self, path: str) -> Dict[str, Any]:
        """创建目录"""
        try:
            full_path = self._resolve_path(path)
            os.makedirs(full_path, exist_ok=True)
            
            return {"success": True, "path": full_path}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_info(self, path: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            full_path = self._resolve_path(path)
            
            if not os.path.exists(full_path):
                return {"success": False, "error": "路径不存在"}
            
            stat = os.stat(full_path)
            
            return {
                "success": True,
                "path": full_path,
                "name": os.path.basename(full_path),
                "is_file": os.path.isfile(full_path),
                "is_dir": os.path.isdir(full_path),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat()
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_json(self, path: str) -> Dict[str, Any]:
        """读取JSON文件"""
        result = self.read(path)
        if not result["success"]:
            return result
        
        try:
            return {
                "success": True,
                "data": json.loads(result["content"]),
                "path": result["path"]
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON解析错误: {e}"}
    
    def write_json(self, path: str, data: Any, indent: int = 2) -> Dict[str, Any]:
        """写入JSON文件"""
        return self.write(path, json.dumps(data, ensure_ascii=False, indent=indent))
