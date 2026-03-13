# -*- coding: utf-8 -*-
"""
WindAgent 环境感知模块
自动检测运行环境，适配不同平台的指令和配置
"""

import platform
import os
import sys
import shutil
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class DeviceType(Enum):
    """设备类型枚举"""
    WINDOWS_DESKTOP = "windows_desktop"
    WINDOWS_TABLET = "windows_tablet"
    MACBOOK = "macbook"
    MAC_TABLET = "mac_tablet"
    LINUX_DESKTOP = "linux_desktop"
    LINUX_TABLET = "linux_tablet"
    ANDROID_TABLET = "android_tablet"
    IPAD = "ipad"
    UNKNOWN = "unknown"


class OSType(Enum):
    """操作系统类型"""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    ANDROID = "android"
    IOS = "ios"
    UNKNOWN = "unknown"


@dataclass
class Environment:
    """环境信息"""
    device_type: DeviceType
    os_type: OSType
    os_name: str
    os_version: str
    arch: str
    is_tablet: bool
    is_portable: bool
    has_gpu: bool
    memory_gb: float
    python_version: str
    shell_type: str
    path_separator: str
    home_dir: str
    data_dir: str


class EnvironmentDetector:
    """环境检测器"""
    
    def __init__(self):
        self._env: Optional[Environment] = None
    
    def detect(self) -> Environment:
        """检测当前环境"""
        if self._env:
            return self._env
        
        os_type = self._detect_os()
        device_type = self._detect_device(os_type)
        
        self._env = Environment(
            device_type=device_type,
            os_type=os_type,
            os_name=self._safe_str(platform.system()),
            os_version=self._safe_str(platform.version()),
            arch=self._safe_str(platform.machine()),
            is_tablet=self._is_tablet(device_type),
            is_portable=self._is_portable(device_type),
            has_gpu=self._check_gpu(),
            memory_gb=self._get_memory(),
            python_version=self._safe_str(platform.python_version()),
            shell_type=self._safe_str(self._detect_shell(os_type)),
            path_separator=os.sep,
            home_dir=self._safe_str(os.path.expanduser("~")),
            data_dir=self._safe_str(self._get_data_dir())
        )
        
        return self._env
    
    def _safe_str(self, value: str) -> str:
        """安全字符串转换，避免编码错误"""
        if value is None:
            return "未知"
        try:
            return str(value).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        except:
            return "未知"
    
    def _detect_os(self) -> OSType:
        """检测操作系统"""
        system = platform.system().lower()
        
        if system == "windows":
            return OSType.WINDOWS
        elif system == "darwin":
            return OSType.MACOS
        elif system == "linux":
            if "android" in platform.platform().lower():
                return OSType.ANDROID
            return OSType.LINUX
        else:
            return OSType.UNKNOWN
    
    def _detect_device(self, os_type: OSType) -> DeviceType:
        """检测设备类型"""
        # 检测是否为平板
        is_tablet = self._check_tablet_hardware()
        
        if os_type == OSType.WINDOWS:
            if is_tablet:
                return DeviceType.WINDOWS_TABLET
            return DeviceType.WINDOWS_DESKTOP
        
        elif os_type == OSType.MACOS:
            # 检测是否为 iPad (运行 macOS 的 iPad)
            if "ipad" in platform.platform().lower():
                return DeviceType.IPAD
            # 检测是否为 MacBook
            if self._is_macbook():
                return DeviceType.MACBOOK
            if is_tablet:
                return DeviceType.MAC_TABLET
            return DeviceType.MACBOOK
        
        elif os_type == OSType.LINUX:
            if is_tablet:
                return DeviceType.LINUX_TABLET
            return DeviceType.LINUX_DESKTOP
        
        elif os_type == OSType.ANDROID:
            return DeviceType.ANDROID_TABLET
        
        elif os_type == OSType.IOS:
            return DeviceType.IPAD
        
        return DeviceType.UNKNOWN
    
    def _check_tablet_hardware(self) -> bool:
        """检测是否为平板硬件"""
        # 检测触摸屏
        try:
            if platform.system() == "Windows":
                import ctypes
                # 检测是否有触摸屏
                SM_MAXIMUMTOUCHES = 95
                max_touches = ctypes.windll.user32.GetSystemMetrics(SM_MAXIMUMTOUCHES)
                if max_touches > 0:
                    # 有触摸能力，可能是平板
                    # 进一步检测屏幕尺寸
                    SM_CXSCREEN = 0
                    SM_CYSCREEN = 1
                    width = ctypes.windll.user32.GetSystemMetrics(SM_CXSCREEN)
                    height = ctypes.windll.user32.GetSystemMetrics(SM_CYSCREEN)
                    # 平板通常屏幕较小（小于15寸对角线）
                    if width < 2000 and height < 1500:
                        return True
        except:
            pass
        
        # 检测电池（平板通常有电池）
        if platform.system() == "Linux":
            if os.path.exists("/sys/class/power_supply"):
                batteries = [d for d in os.listdir("/sys/class/power_supply") 
                           if d.startswith("BAT")]
                if batteries:
                    # 有电池，可能是便携设备
                    return True
        
        return False
    
    def _is_macbook(self) -> bool:
        """检测是否为 MacBook"""
        try:
            if platform.system() == "Darwin":
                import subprocess
                result = subprocess.run(
                    ["sysctl", "-n", "hw.model"],
                    capture_output=True, text=True
                )
                model = result.stdout.strip().lower()
                if "macbook" in model:
                    return True
        except:
            pass
        return False
    
    def _is_tablet(self, device_type: DeviceType) -> bool:
        """判断是否为平板"""
        tablet_types = {
            DeviceType.WINDOWS_TABLET,
            DeviceType.MAC_TABLET,
            DeviceType.LINUX_TABLET,
            DeviceType.ANDROID_TABLET,
            DeviceType.IPAD
        }
        return device_type in tablet_types
    
    def _is_portable(self, device_type: DeviceType) -> bool:
        """判断是否为便携设备"""
        portable_types = {
            DeviceType.WINDOWS_TABLET,
            DeviceType.MAC_TABLET,
            DeviceType.LINUX_TABLET,
            DeviceType.ANDROID_TABLET,
            DeviceType.IPAD,
            DeviceType.MACBOOK
        }
        return device_type in portable_types
    
    def _check_gpu(self) -> bool:
        """检测是否有GPU"""
        try:
            import subprocess
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "name"],
                    capture_output=True, text=True
                )
                gpu_info = result.stdout.lower()
                if "nvidia" in gpu_info or "amd" in gpu_info or "intel" in gpu_info:
                    return True
            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True, text=True
                )
                if "chipset" in result.stdout.lower():
                    return True
        except:
            pass
        return False
    
    def _get_memory(self) -> float:
        """获取内存大小（GB）"""
        try:
            import psutil
            return round(psutil.virtual_memory().total / (1024**3), 1)
        except:
            return 0.0
    
    def _detect_shell(self, os_type: OSType) -> str:
        """检测Shell类型"""
        if os_type == OSType.WINDOWS:
            if os.environ.get("PSModulePath"):
                return "powershell"
            return "cmd"
        elif os_type == OSType.MACOS:
            return "zsh" if os.environ.get("ZSH_VERSION") else "bash"
        elif os_type == OSType.LINUX:
            return os.environ.get("SHELL", "bash").split("/")[-1]
        return "unknown"
    
    def _get_data_dir(self) -> str:
        """获取数据存储目录"""
        home = os.path.expanduser("~")
        
        if platform.system() == "Windows":
            return os.path.join(home, "AppData", "Local", "WindAgent")
        elif platform.system() == "Darwin":
            return os.path.join(home, "Library", "Application Support", "WindAgent")
        else:
            return os.path.join(home, ".windagent")


class CommandAdapter:
    """命令适配器 - 根据环境适配命令"""
    
    def __init__(self, env: Environment):
        self.env = env
    
    def get_file_manager(self) -> str:
        """获取文件管理器命令"""
        if self.env.os_type == OSType.WINDOWS:
            return "explorer"
        elif self.env.os_type == OSType.MACOS:
            return "open"
        else:
            return "xdg-open"
    
    def get_terminal(self) -> str:
        """获取终端命令"""
        if self.env.os_type == OSType.WINDOWS:
            return "cmd" if self.env.shell_type == "cmd" else "powershell"
        elif self.env.os_type == OSType.MACOS:
            return "open -a Terminal"
        else:
            return "gnome-terminal"
    
    def get_python_cmd(self) -> str:
        """获取Python命令"""
        if self.env.os_type == OSType.WINDOWS:
            return "python"
        return "python3"
    
    def get_pip_cmd(self) -> str:
        """获取pip命令"""
        if self.env.os_type == OSType.WINDOWS:
            return "pip"
        return "pip3"
    
    def get_kill_cmd(self, pid: int) -> str:
        """获取终止进程命令"""
        if self.env.os_type == OSType.WINDOWS:
            return f"taskkill /PID {pid} /F"
        return f"kill -9 {pid}"
    
    def get_list_dir(self, path: str = ".") -> str:
        """获取列出目录命令"""
        if self.env.shell_type in ["powershell", "cmd"]:
            return f"dir {path}"
        return f"ls -la {path}"
    
    def get_copy_cmd(self, src: str, dst: str) -> str:
        """获取复制命令"""
        if self.env.os_type == OSType.WINDOWS:
            return f'copy "{src}" "{dst}"'
        return f'cp -r "{src}" "{dst}"'
    
    def get_move_cmd(self, src: str, dst: str) -> str:
        """获取移动命令"""
        if self.env.os_type == OSType.WINDOWS:
            return f'move "{src}" "{dst}"'
        return f'mv "{src}" "{dst}"'
    
    def get_delete_cmd(self, path: str) -> str:
        """获取删除命令"""
        if self.env.os_type == OSType.WINDOWS:
            return f'del /f /q "{path}"' if os.path.isfile(path) else f'rmdir /s /q "{path}"'
        return f'rm -rf "{path}"'
    
    def get_env_var(self, name: str) -> str:
        """获取环境变量命令"""
        if self.env.shell_type == "powershell":
            return f"$env:{name}"
        elif self.env.shell_type == "cmd":
            return f"%{name}%"
        return f"${name}"
    
    def get_run_background(self, cmd: str) -> str:
        """获取后台运行命令"""
        if self.env.os_type == OSType.WINDOWS:
            return f"start /B {cmd}"
        return f"nohup {cmd} &"


# 全局环境检测器
_detector = EnvironmentDetector()


def get_environment() -> Environment:
    """获取当前环境"""
    return _detector.detect()


def get_command_adapter() -> CommandAdapter:
    """获取命令适配器"""
    return CommandAdapter(get_environment())


def print_env_info():
    """打印环境信息"""
    env = get_environment()
    print("=" * 50)
    print("WindAgent 环境信息")
    print("=" * 50)
    print(f"设备类型: {env.device_type.value}")
    print(f"操作系统: {env.os_name} {env.os_version}")
    print(f"架构: {env.arch}")
    print(f"是否平板: {'是' if env.is_tablet else '否'}")
    print(f"是否便携: {'是' if env.is_portable else '否'}")
    print(f"GPU: {'有' if env.has_gpu else '无'}")
    print(f"内存: {env.memory_gb} GB")
    print(f"Python: {env.python_version}")
    print(f"Shell: {env.shell_type}")
    print(f"数据目录: {env.data_dir}")
    print("=" * 50)


if __name__ == "__main__":
    print_env_info()
