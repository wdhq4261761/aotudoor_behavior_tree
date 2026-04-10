from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json
import os


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
    recent_files: list = field(default_factory=list)
    window_geometry: str = "1200x800"
    
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
            window_geometry=data.get("window_geometry", "1200x800"),
        )


@dataclass
class BehaviorTreeConfig:
    blackboard: BlackboardConfig = field(default_factory=BlackboardConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    default_check_interval_ms: int = 300
    default_timeout_ms: int = 0
    default_retry_count: int = 0
    default_repeat_count: int = 0
    default_child_interval: int = 0
    auto_save_interval_sec: int = 60
    max_undo_history: int = 50
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "blackboard": self.blackboard.to_dict(),
            "session": self.session.to_dict(),
            "default_check_interval_ms": self.default_check_interval_ms,
            "default_timeout_ms": self.default_timeout_ms,
            "default_retry_count": self.default_retry_count,
            "default_repeat_count": self.default_repeat_count,
            "default_child_interval": self.default_child_interval,
            "auto_save_interval_sec": self.auto_save_interval_sec,
            "max_undo_history": self.max_undo_history,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BehaviorTreeConfig":
        blackboard_data = data.get("blackboard", {})
        session_data = data.get("session", {})
        return cls(
            blackboard=BlackboardConfig.from_dict(blackboard_data),
            session=SessionConfig.from_dict(session_data),
            default_check_interval_ms=data.get("default_check_interval_ms", 300),
            default_timeout_ms=data.get("default_timeout_ms", 0),
            default_retry_count=data.get("default_retry_count", 0),
            default_repeat_count=data.get("default_repeat_count", 0),
            default_child_interval=data.get("default_child_interval", 0),
            auto_save_interval_sec=data.get("auto_save_interval_sec", 60),
            max_undo_history=data.get("max_undo_history", 50),
        )


class ConfigManager:
    _instance: Optional["ConfigManager"] = None
    _config: BehaviorTreeConfig = field(default_factory=BehaviorTreeConfig)
    _config_path: str = ""
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = BehaviorTreeConfig()
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_config(cls) -> BehaviorTreeConfig:
        return cls.get_instance()._config
    
    @classmethod
    def get_blackboard_config(cls) -> BlackboardConfig:
        return cls.get_config().blackboard
    
    @classmethod
    def get_session_config(cls) -> SessionConfig:
        return cls.get_config().session
    
    @classmethod
    def get_last_file_path(cls) -> str:
        return cls.get_session_config().last_file_path
    
    @classmethod
    def set_last_file_path(cls, file_path: str):
        config = cls.get_instance()._config
        config.session.last_file_path = file_path
        if file_path:
            cls._add_recent_file(file_path)
    
    @classmethod
    def get_recent_files(cls) -> list:
        return cls.get_session_config().recent_files
    
    @classmethod
    def _add_recent_file(cls, file_path: str):
        config = cls.get_instance()._config
        recent = config.session.recent_files
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        config.session.recent_files = recent[:10]
    
    @classmethod
    def clear_recent_files(cls):
        cls.get_instance()._config.session.recent_files = []
    
    @classmethod
    def get_default_position_key(cls) -> str:
        return cls.get_blackboard_config().default_position_key
    
    @classmethod
    def get_default_value_key(cls) -> str:
        return cls.get_blackboard_config().default_value_key
    
    @classmethod
    def set_config(cls, config: BehaviorTreeConfig):
        cls.get_instance()._config = config
    
    @classmethod
    def load_from_file(cls, file_path: str) -> bool:
        try:
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cls.get_instance()._config = BehaviorTreeConfig.from_dict(data)
            cls.get_instance()._config_path = file_path
            return True
        except Exception as e:
            print(f"[WARN] 加载配置文件失败: {e}")
            return False
    
    @classmethod
    def save_to_file(cls, file_path: str = None) -> bool:
        try:
            path = file_path or cls.get_instance()._config_path
            if not path:
                return False
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(cls.get_config().to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[WARN] 保存配置文件失败: {e}")
            return False
    
    @classmethod
    def reset_to_defaults(cls):
        cls.get_instance()._config = BehaviorTreeConfig()


def get_default_position_key() -> str:
    return ConfigManager.get_default_position_key()


def get_default_value_key() -> str:
    return ConfigManager.get_default_value_key()


def get_blackboard_config() -> BlackboardConfig:
    return ConfigManager.get_blackboard_config()


def get_behavior_tree_config() -> BehaviorTreeConfig:
    return ConfigManager.get_config()
