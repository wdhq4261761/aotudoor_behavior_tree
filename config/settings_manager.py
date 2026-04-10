import json
import os
import datetime
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field


VERSION = "1.0.0"


@dataclass
class BlackboardConfig:
    default_position_key: str = "last_detection_position"
    default_value_key: str = "last_number_value"
    default_ocr_text_key: str = "last_ocr_text"
    default_color_key: str = "last_color_value"
    default_image_match_key: str = "last_image_match"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "default_position_key": self.default_position_key,
            "default_value_key": self.default_value_key,
            "default_ocr_text_key": self.default_ocr_text_key,
            "default_color_key": self.default_color_key,
            "default_image_match_key": self.default_image_match_key,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BlackboardConfig":
        return cls(
            default_position_key=data.get("default_position_key", "last_detection_position"),
            default_value_key=data.get("default_value_key", "last_number_value"),
            default_ocr_text_key=data.get("default_ocr_text_key", "last_ocr_text"),
            default_color_key=data.get("default_color_key", "last_color_value"),
            default_image_match_key=data.get("default_image_match_key", "last_image_match"),
        )


@dataclass
class SessionConfig:
    last_file_path: str = ""
    recent_files: List[str] = field(default_factory=list)
    window_geometry: str = "1280x800"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "last_file_path": self.last_file_path,
            "recent_files": self.recent_files[:10],
            "window_geometry": self.window_geometry,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionConfig":
        return cls(
            last_file_path=data.get("last_file_path", ""),
            recent_files=data.get("recent_files", [])[:10],
            window_geometry=data.get("window_geometry", "1280x800"),
        )


class SettingsManager:
    """统一配置管理器
    
    管理应用程序所有设置，支持：
    - 持久化存储到系统目录
    - 版本管理和配置迁移
    - 延迟保存机制
    - 配置变更监听
    """
    
    _instance: Optional["SettingsManager"] = None
    
    VERSION = "1.0.0"
    CONFIG_FILE_NAME = "config.json"
    
    DEFAULT_SETTINGS = {
        "version": VERSION,
        "tesseract_path": "",
        "alarm_sound_path": "",
        "alarm_volume": 70,
        "default_project_path": "",
        "shortcuts": {
            "start": "F10",
            "stop": "F12",
            "record": "F11"
        },
        "behavior_tree": {
            "tick_interval": 50,
            "auto_save_interval": 30,
            "default_format": "json",
            "default_check_interval_ms": 300,
            "default_timeout_ms": 0,
            "default_retry_count": 0,
            "default_repeat_count": 0,
            "default_child_interval": 0,
            "max_undo_history": 50
        },
        "ui": {
            "theme": "dark",
            "language": "zh_CN",
            "font_size": 10
        },
        "session": {
            "last_file_path": "",
            "recent_files": [],
            "window_geometry": "1280x800"
        },
        "blackboard": {
            "default_position_key": "last_detection_position",
            "default_value_key": "last_number_value",
            "default_ocr_text_key": "last_ocr_text",
            "default_color_key": "last_color_value",
            "default_image_match_key": "last_image_match"
        }
    }
    
    def __new__(cls, config_dir: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_dir: str = None):
        if self._initialized:
            return
        
        self._initialized = True
        
        if config_dir is None:
            config_dir = self._get_default_config_dir()
        
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, self.CONFIG_FILE_NAME)
        self.settings: Dict[str, Any] = {}
        
        self._save_timer = None
        self._save_callback = None
        self._listeners: Dict[str, List[Callable]] = {}
        
        self._load_settings()
    
    @classmethod
    def get_instance(cls) -> "SettingsManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        cls._instance = None
    
    def _get_default_config_dir(self) -> str:
        """获取默认配置目录
        
        Windows: %APPDATA%/autodoor_behavior_tree
        Linux/Mac: ~/.config/autodoor_behavior_tree
        """
        if os.name == 'nt':
            base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        else:
            base_dir = os.environ.get('XDG_CONFIG_HOME',
                                       os.path.join(os.path.expanduser('~'), '.config'))
        
        return os.path.join(base_dir, "autodoor_behavior_tree")
    
    @staticmethod
    def get_default_workspace_path() -> str:
        """获取默认workspace路径
        
        默认保存在系统持久化目录下，确保更换客户端不会丢失数据。
        Windows: %APPDATA%/autodoor_behavior_tree/workspace
        Linux/Mac: ~/.config/autodoor_behavior_tree/workspace
        """
        if os.name == 'nt':
            base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        else:
            base_dir = os.environ.get('XDG_CONFIG_HOME',
                                       os.path.join(os.path.expanduser('~'), '.config'))
        
        return os.path.join(base_dir, "autodoor_behavior_tree", "workspace")
    
    def _load_settings(self) -> None:
        """加载设置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                self._merge_defaults()
                self._migrate_config()
            except Exception as e:
                print(f"[WARN] 加载配置文件失败: {e}")
                self.settings = dict(self.DEFAULT_SETTINGS)
        else:
            self.settings = dict(self.DEFAULT_SETTINGS)
    
    def _merge_defaults(self) -> None:
        """合并默认设置"""
        def merge_dict(base: dict, default: dict) -> dict:
            for key, value in default.items():
                if key not in base:
                    base[key] = value
                elif isinstance(value, dict) and isinstance(base.get(key), dict):
                    merge_dict(base[key], value)
            return base
        
        merge_dict(self.settings, self.DEFAULT_SETTINGS)
    
    def _migrate_config(self) -> None:
        """配置迁移处理"""
        config_version = self.settings.get("version", "0.0.0")
        
        if config_version != self.VERSION:
            print(f"[INFO] 配置版本迁移: {config_version} -> {self.VERSION}")
            self.settings["version"] = self.VERSION
            self.settings["last_save_time"] = datetime.datetime.now().isoformat()
            self.save_settings()
    
    def save_settings(self) -> bool:
        """保存设置到文件"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            
            self.settings["last_save_time"] = datetime.datetime.now().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[WARN] 保存配置文件失败: {e}")
            return False
    
    def defer_save(self, delay_ms: int = 1000) -> None:
        """延迟保存配置，避免频繁保存"""
        if self._save_timer is not None:
            try:
                self._save_timer.cancel()
            except Exception:
                pass
        
        import threading
        self._save_timer = threading.Timer(delay_ms / 1000, self._do_deferred_save)
        self._save_timer.daemon = True
        self._save_timer.start()
    
    def _do_deferred_save(self) -> None:
        """执行延迟保存"""
        self.save_settings()
        self._save_timer = None
    
    def set_save_callback(self, callback: Callable) -> None:
        """设置保存回调函数"""
        self._save_callback = callback
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取设置值
        
        Args:
            key: 设置键（支持点号分隔的嵌套键）
            default: 默认值
        """
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        """设置值
        
        Args:
            key: 设置键（支持点号分隔的嵌套键）
            value: 设置值
            auto_save: 是否自动触发延迟保存
        """
        keys = key.split('.')
        data = self.settings
        
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        data[keys[-1]] = value
        
        self._notify_listeners(key, value)
        
        if auto_save:
            self.defer_save()
    
    def add_listener(self, key: str, callback: Callable) -> None:
        """添加配置变更监听器
        
        Args:
            key: 监听的配置键
            callback: 回调函数
        """
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)
    
    def remove_listener(self, key: str, callback: Callable) -> None:
        """移除配置变更监听器"""
        if key in self._listeners:
            try:
                self._listeners[key].remove(callback)
            except ValueError:
                pass
    
    def _notify_listeners(self, key: str, value: Any) -> None:
        """通知监听器"""
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(key, value)
                except Exception as e:
                    print(f"[WARN] 配置监听器回调失败: {e}")
    
    def reset(self, key: str = None) -> None:
        """重置设置
        
        Args:
            key: 设置键，为None时重置所有设置
        """
        if key is None:
            self.settings = dict(self.DEFAULT_SETTINGS)
        else:
            keys = key.split('.')
            default_value = self.DEFAULT_SETTINGS
            
            for k in keys:
                if isinstance(default_value, dict) and k in default_value:
                    default_value = default_value[k]
                else:
                    return
            
            self.set(key, default_value)
        
        self.save_settings()
    
    def get_blackboard_config(self) -> BlackboardConfig:
        """获取黑板配置"""
        data = self.get("blackboard", {})
        return BlackboardConfig.from_dict(data)
    
    def set_blackboard_config(self, config: BlackboardConfig) -> None:
        """设置黑板配置"""
        self.set("blackboard", config.to_dict())
    
    def get_session_config(self) -> SessionConfig:
        """获取会话配置"""
        data = self.get("session", {})
        return SessionConfig.from_dict(data)
    
    def set_session_config(self, config: SessionConfig) -> None:
        """设置会话配置"""
        self.set("session", config.to_dict())
    
    def get_last_file_path(self) -> str:
        """获取上次打开的文件路径"""
        return self.get("session.last_file_path", "")
    
    def set_last_file_path(self, file_path: str) -> None:
        """设置上次打开的文件路径"""
        self.set("session.last_file_path", file_path)
        if file_path:
            self._add_recent_file(file_path)
    
    def get_recent_files(self) -> List[str]:
        """获取最近文件列表"""
        return self.get("session.recent_files", [])
    
    def _add_recent_file(self, file_path: str) -> None:
        """添加到最近文件列表"""
        recent = self.get("session.recent_files", [])
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        self.set("session.recent_files", recent[:10])
    
    def clear_recent_files(self) -> None:
        """清空最近文件列表"""
        self.set("session.recent_files", [])
    
    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置"""
        return dict(self.settings)
    
    def load_all_settings(self, settings: Dict[str, Any]) -> None:
        """加载所有设置"""
        self.settings = settings
        self._merge_defaults()
        self.save_settings()


def get_settings_manager() -> SettingsManager:
    """获取设置管理器单例"""
    return SettingsManager.get_instance()


def get_default_position_key() -> str:
    return get_settings_manager().get("blackboard.default_position_key", "last_detection_position")


def get_default_value_key() -> str:
    return get_settings_manager().get("blackboard.default_value_key", "last_number_value")


def get_blackboard_config() -> BlackboardConfig:
    return get_settings_manager().get_blackboard_config()


def get_session_config() -> SessionConfig:
    return get_settings_manager().get_session_config()
