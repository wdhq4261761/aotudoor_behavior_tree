import os
import sys


def get_app_root() -> str:
    """获取应用根目录
    
    兼容开发环境和打包后的环境
    
    Returns:
        应用根目录路径
    """
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(relative_path: str) -> str:
    """获取资源文件的绝对路径
    
    兼容开发环境和打包后的环境
    
    Args:
        relative_path: 相对于项目根目录的路径
        
    Returns:
        资源文件的绝对路径
    """
    app_root = get_app_root()
    return os.path.join(app_root, relative_path)


class ResourceManager:
    """资源管理器
    
    管理应用程序的资源文件路径，包括音效、图标等。
    兼容开发环境和打包后的环境。
    """
    
    _instance = None
    
    DEFAULT_ALARM_SOUND = "assets/sounds/alarm.mp3"
    DEFAULT_START_SOUND = "assets/sounds/alarm.mp3"
    DEFAULT_STOP_SOUND = "assets/sounds/temp_reversed.mp3"
    DEFAULT_ICON = "assets/icons/autodoor.ico"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._app_root = get_app_root()
    
    @property
    def app_root(self) -> str:
        return self._app_root
    
    def get_alarm_sound_path(self) -> str:
        """获取默认报警音效路径"""
        return get_resource_path(self.DEFAULT_ALARM_SOUND)
    
    def get_start_sound_path(self) -> str:
        """获取开始运行音效路径"""
        return get_resource_path(self.DEFAULT_START_SOUND)
    
    def get_stop_sound_path(self) -> str:
        """获取停止运行音效路径"""
        return get_resource_path(self.DEFAULT_STOP_SOUND)
    
    def get_icon_path(self) -> str:
        """获取应用图标路径"""
        return get_resource_path(self.DEFAULT_ICON)
    
    def resource_exists(self, relative_path: str) -> bool:
        """检查资源文件是否存在
        
        Args:
            relative_path: 相对路径
            
        Returns:
            文件是否存在
        """
        full_path = get_resource_path(relative_path)
        return os.path.exists(full_path)
    
    def alarm_sound_exists(self) -> bool:
        """检查报警音效是否存在"""
        return os.path.exists(self.get_alarm_sound_path())
    
    def icon_exists(self) -> bool:
        """检查图标是否存在"""
        return os.path.exists(self.get_icon_path())
    
    def get_all_resources(self) -> dict:
        """获取所有资源路径
        
        Returns:
            资源路径字典
        """
        return {
            "alarm_sound": self.get_alarm_sound_path(),
            "start_sound": self.get_start_sound_path(),
            "stop_sound": self.get_stop_sound_path(),
            "icon": self.get_icon_path(),
            "alarm_sound_exists": self.alarm_sound_exists(),
            "icon_exists": self.icon_exists(),
        }


def get_resource_manager() -> ResourceManager:
    """获取资源管理器单例"""
    return ResourceManager()
