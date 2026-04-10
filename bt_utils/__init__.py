from .screenshot import ScreenshotManager
from .input_controller import InputController
from .ocr_manager import OCRManager
from .image_processor import ImageProcessor
from .recorder import ScriptRecorder
from .script_executor import ScriptExecutor
from .alarm import AlarmPlayer
from config.settings_manager import (
    SettingsManager as ConfigManager,
    BlackboardConfig,
    SessionConfig,
    get_default_position_key,
    get_default_value_key,
    get_blackboard_config,
    get_settings_manager,
    get_session_config,
)
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

BehaviorTreeConfig = SessionConfig
get_behavior_tree_config = get_session_config

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
