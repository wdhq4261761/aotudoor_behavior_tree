from .screenshot import ScreenshotManager
from .input_controller_factory import InputController
from .ocr_manager import OCRManager
from .image_processor import ImageProcessor
from .recorder import ScriptRecorder
from .script_executor import ScriptExecutor
from .alarm import AlarmPlayer
from .consistency_checker import (
    ConsistencyChecker,
    ConsistencyReport,
    ConsistencyIssue,
    run_consistency_check,
    print_consistency_report,
)
from .proxies import (
    OCRProxy,
    ImageDetectionProxy,
    InputProxy,
    ScreenshotProxy,
    AlarmProxy,
)
from .recognizers import (
    BaseRecognizer,
    OCRRecognizer,
    ImageRecognizer,
    ColorRecognizer,
    NumberRecognizer,
    RecognizerFactory,
)
from .coordinate import CoordinateConverter
from .window_capture import WindowCapture
from .base_input import BaseInputController
from .resource_manager import (
    ResourceManager,
    get_resource_manager,
    get_app_root,
    get_resource_path,
)


def __getattr__(name):
    """延迟导入 config 模块以避免循环导入"""
    if name in ("ConfigManager", "SettingsManager"):
        from config.settings_manager import SettingsManager
        return SettingsManager
    elif name == "BlackboardConfig":
        from config.settings_manager import BlackboardConfig
        return BlackboardConfig
    elif name == "SessionConfig":
        from config.settings_manager import SessionConfig
        return SessionConfig
    elif name == "BehaviorTreeConfig":
        from config.settings_manager import SessionConfig
        return SessionConfig
    elif name == "get_default_position_key":
        from config.settings_manager import get_default_position_key
        return get_default_position_key
    elif name == "get_default_value_key":
        from config.settings_manager import get_default_value_key
        return get_default_value_key
    elif name == "get_blackboard_config":
        from config.settings_manager import get_blackboard_config
        return get_blackboard_config
    elif name in ("get_behavior_tree_config", "get_session_config"):
        from config.settings_manager import get_session_config
        return get_session_config
    elif name == "get_settings_manager":
        from config.settings_manager import get_settings_manager
        return get_settings_manager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ScreenshotManager",
    "InputController",
    "OCRManager",
    "ImageProcessor",
    "ScriptRecorder",
    "ScriptExecutor",
    "AlarmPlayer",
    "ConfigManager",
    "BehaviorTreeConfig",
    "BlackboardConfig",
    "SessionConfig",
    "get_default_position_key",
    "get_default_value_key",
    "get_blackboard_config",
    "get_behavior_tree_config",
    "get_session_config",
    "get_settings_manager",
    "ConsistencyChecker",
    "ConsistencyReport",
    "ConsistencyIssue",
    "run_consistency_check",
    "print_consistency_report",
    "OCRProxy",
    "ImageDetectionProxy",
    "InputProxy",
    "ScreenshotProxy",
    "AlarmProxy",
    "BaseRecognizer",
    "OCRRecognizer",
    "ImageRecognizer",
    "ColorRecognizer",
    "NumberRecognizer",
    "RecognizerFactory",
    "CoordinateConverter",
    "WindowCapture",
    "BaseInputController",
    "ResourceManager",
    "get_resource_manager",
    "get_app_root",
    "get_resource_path",
]
