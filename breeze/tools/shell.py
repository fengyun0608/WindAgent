# -*- coding: utf-8 -*-
"""
Shell 工具
"""

import os
import subprocess
from typing import Dict, Any, Optional

from cloud.env import get_environment, get_command_adapter, OSType


class ShellTool:
    """Shell工具"""
    
    def __init__(self):
        self.env = get_environment()
        self.adapter = get_command_adapter()
    
    def execute(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """执行命令"""
        try:
            if self.env.os_type == OSType.WINDOWS:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding='utf-8',
                    errors='ignore'
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"命令执行超时（{timeout}秒）"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_env_var(self, name: str) -> str:
        """获取环境变量"""
        return os.environ.get(name, "")
    
    def set_env_var(self, name: str, value: str) -> bool:
        """设置环境变量"""
        try:
            os.environ[name] = value
            return True
        except Exception:
            return False
    
    def list_env_vars(self) -> Dict[str, str]:
        """列出所有环境变量"""
        return dict(os.environ)
    
    def get_current_dir(self) -> str:
        """获取当前目录"""
        return os.getcwd()
    
    def change_dir(self, path: str) -> Dict[str, Any]:
        """切换目录"""
        try:
            os.chdir(path)
            return {
                "success": True,
                "current_dir": os.getcwd()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_adapted_command(self, command_type: str, *args) -> str:
        """获取适配后的命令"""
        if command_type == "list_dir":
            return self.adapter.get_list_dir(*args)
        elif command_type == "copy":
            return self.adapter.get_copy_cmd(*args)
        elif command_type == "move":
            return self.adapter.get_move_cmd(*args)
        elif command_type == "delete":
            return self.adapter.get_delete_cmd(*args)
        elif command_type == "kill":
            return self.adapter.get_kill_cmd(*args)
        else:
            return ""
