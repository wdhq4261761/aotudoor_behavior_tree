from typing import Callable, Optional, Tuple
import os
import time

from .blackboard import Blackboard


class ExecutionContext:
    """执行上下文

    封装行为树执行过程中的运行时依赖，包括黑板系统、
    截图管理器、输入控制器和OCR管理器等。

    Attributes:
        blackboard: 黑板系统实例
        elapsed_time: 已执行时间（秒）
        tick_count: tick执行次数
        project_root: 项目根目录
    """

    def __init__(self, project_root: str = None):
        self.blackboard = Blackboard()
        self.elapsed_time: float = 0.0
        self.tick_count: int = 0
        self.project_root = project_root or os.getcwd()
        self._is_running = True
        self._is_paused = False
        self._on_node_status: Optional[Callable] = None
        self._screenshot_manager = None
        self._input_controller = None
        self._ocr_manager = None
        self._alarm_player = None
        self._path_resolver = None
    
    def check_running(self) -> bool:
        if self._is_paused:
            self._wait_if_paused()
        return self._is_running
    
    def _wait_if_paused(self, check_interval: float = 0.1) -> None:
        while self._is_paused and self._is_running:
            time.sleep(check_interval)

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running

    @property
    def is_paused(self) -> bool:
        """是否暂停"""
        return self._is_paused

    def notify_node_status(self, node_id: str, status: str) -> None:
        """通知节点状态变化

        Args:
            node_id: 节点ID
            status: 状态字符串
        """
        if self._on_node_status:
            try:
                from bt_utils.ui_dispatcher import UIUpdateDispatcher
                dispatcher = UIUpdateDispatcher.get_instance()
                dispatcher.dispatch_node_status(node_id, status, self._on_node_status)
            except ImportError:
                self._on_node_status(node_id, status)

    def get_screenshot(self, region: tuple = None):
        """获取屏幕截图

        Args:
            region: 截图区域 (left, top, right, bottom)

        Returns:
            PIL.Image 截图对象
        """
        if self._screenshot_manager is None:
            from bt_utils.screenshot import ScreenshotManager
            self._screenshot_manager = ScreenshotManager()

        if region:
            return self._screenshot_manager.get_region_screenshot(region)
        return self._screenshot_manager.get_full_screenshot()

    def execute_key_press(self, key: str, action: str = "press", duration: int = 0) -> None:
        """执行按键操作

        Args:
            key: 按键名称
            action: 动作类型 (press/down/up)
            duration: 按住时长（毫秒）
        """
        if self._input_controller is None:
            from bt_utils.input_controller import InputController
            self._input_controller = InputController()

        self._input_controller.key_press(key, action, duration)

    def execute_mouse_click(self, button: str = "left", position: tuple = None,
                           action: str = "press", duration: int = 0) -> None:
        """执行鼠标点击

        Args:
            button: 鼠标按钮 (left/right/middle)
            position: 点击位置 (x, y)
            action: 动作类型 (press/down/up)
            duration: 按住时长（毫秒）
        """
        if self._input_controller is None:
            from bt_utils.input_controller import InputController
            self._input_controller = InputController()

        self._input_controller.mouse_click(button, position, action, duration)

    def execute_mouse_move(self, position: tuple, relative: bool = False, smooth: bool = False) -> None:
        """执行鼠标移动

        Args:
            position: 目标位置 (x, y)
            relative: 是否相对移动
            smooth: 是否平滑移动
        """
        if self._input_controller is None:
            from bt_utils.input_controller import InputController
            self._input_controller = InputController()

        self._input_controller.mouse_move(position, relative, smooth=smooth)

    def get_mouse_position(self) -> Optional[Tuple[int, int]]:
        """获取当前鼠标位置

        Returns:
            当前鼠标位置 (x, y)，如果无法获取则返回 None
        """
        if self._input_controller is None:
            from bt_utils.input_controller import InputController
            self._input_controller = InputController()

        return self._input_controller.get_position()

    def execute_mouse_scroll(self, amount: int, position: tuple = None) -> None:
        """执行鼠标滚轮滚动

        Args:
            amount: 滚动量（正数向上，负数向下）
            position: 滚动位置 (x, y)
        """
        if self._input_controller is None:
            from bt_utils.input_controller import InputController
            self._input_controller = InputController()

        self._input_controller.mouse_scroll(amount, position)

    def perform_ocr(self, image, keywords: str, language: str = "eng", 
                    region: Tuple[int, int, int, int] = None) -> tuple:
        """执行OCR识别

        Args:
            image: PIL.Image 图像
            keywords: 关键词（逗号分隔）
            language: OCR语言
            region: 截图区域 (left, top, right, bottom)，用于坐标转换

        Returns:
            (是否找到, 位置, 所有识别文本) 元组
        """
        if self._ocr_manager is None:
            from bt_utils.ocr_manager import OCRManager
            self._ocr_manager = OCRManager()

        return self._ocr_manager.recognize(image, keywords, language, region=region)
    
    def resolve_path(self, relative_path: str) -> str:
        """解析相对路径为绝对路径
        
        Args:
            relative_path: 相对路径（以 ./ 开头）
        
        Returns:
            绝对路径
        """
        if self._path_resolver is None:
            from bt_utils.path_resolver import PathResolver
            self._path_resolver = PathResolver(self.project_root)
        
        if relative_path.startswith("./"):
            return self._path_resolver.to_absolute(relative_path)
        return relative_path
