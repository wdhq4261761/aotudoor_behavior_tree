import json
import os
from typing import Any, Dict


class SettingsManager:
    """设置管理器

    管理应用程序设置，支持持久化存储和默认值合并。

    Attributes:
        DEFAULT_SETTINGS: 默认设置字典
    """
    DEFAULT_SETTINGS = {
        "tesseract_path": "",
        "alarm_sound_path": "",
        "alarm_volume": 70,
        "shortcuts": {
            "start": "F10",
            "stop": "F12",
            "record": "F11"
        },
        "behavior_tree": {
            "tick_interval": 50,
            "auto_save_interval": 30,
            "default_format": "json"
        },
        "ui": {
            "theme": "dark",
            "language": "zh_CN",
            "font_size": 10
        }
    }

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = self._get_default_config_dir()

        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "settings.json")
        self.settings: Dict[str, Any] = {}

        self._load_settings()

    def _get_default_config_dir(self) -> str:
        """获取默认配置目录

        Returns:
            配置目录路径
        """
        if os.name == 'nt':
            base_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
        else:
            base_dir = os.environ.get('XDG_CONFIG_HOME',
                                       os.path.join(os.path.expanduser('~'), '.config'))

        return os.path.join(base_dir, "behavior_tree_standalone")

    def _load_settings(self) -> None:
        """加载设置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                self._merge_defaults()
            except Exception:
                self.settings = dict(self.DEFAULT_SETTINGS)
        else:
            self.settings = dict(self.DEFAULT_SETTINGS)

    def _merge_defaults(self) -> None:
        """合并默认设置"""
        def merge_dict(base: dict, default: dict) -> dict:
            for key, value in default.items():
                if key not in base:
                    base[key] = value
                elif isinstance(value, dict):
                    merge_dict(base[key], value)
            return base

        merge_dict(self.settings, self.DEFAULT_SETTINGS)

    def save_settings(self) -> None:
        """保存设置到文件"""
        os.makedirs(self.config_dir, exist_ok=True)

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """获取设置值

        Args:
            key: 设置键（支持点号分隔的嵌套键）
            default: 默认值

        Returns:
            设置值
        """
        keys = key.split('.')
        value = self.settings

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """设置值

        Args:
            key: 设置键（支持点号分隔的嵌套键）
            value: 设置值
        """
        keys = key.split('.')
        data = self.settings

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

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
