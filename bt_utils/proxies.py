from typing import Tuple, Optional, List
from PIL import Image


class OCRProxy:
    """OCR代理类

    封装OCR识别功能，提供统一的OCR接口。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        from bt_utils.ocr_manager import OCRManager
        self._ocr = OCRManager()

    def recognize(self, image: Image.Image, keywords: str = None,
                  language: str = "eng", preprocess_mode: str = "normal"
                  ) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """执行OCR识别

        Args:
            image: PIL.Image 图像
            keywords: 关键词
            language: 语言
            preprocess_mode: 预处理模式

        Returns:
            (是否找到, 位置坐标) 元组
        """
        return self._ocr.recognize(image, keywords, language, preprocess_mode)

    def recognize_number(self, image: Image.Image, language: str = "eng",
                         preprocess_mode: str = "normal", extract_mode: str = "无规则",
                         extract_pattern: str = "", min_confidence: float = 0.5
                         ) -> Tuple[bool, Optional[float]]:
        """识别数字

        Args:
            image: PIL.Image 图像
            language: 语言
            preprocess_mode: 预处理模式
            extract_mode: 提取模式
            extract_pattern: 提取模式
            min_confidence: 最小置信度

        Returns:
            (是否成功, 数字值) 元组
        """
        return self._ocr.recognize_number(
            image, language, preprocess_mode,
            extract_mode, extract_pattern, min_confidence
        )

    def get_all_text(self, image: Image.Image, language: str = "eng",
                     preprocess_mode: str = "normal") -> str:
        """获取所有文本

        Args:
            image: PIL.Image 图像
            language: 语言
            preprocess_mode: 预处理模式

        Returns:
            识别文本
        """
        return self._ocr.get_all_text(image, language, preprocess_mode)

    @classmethod
    def set_tesseract_path(cls, path: str) -> None:
        """设置Tesseract路径

        Args:
            path: Tesseract安装目录
        """
        from bt_utils.ocr_manager import OCRManager
        OCRManager.set_tesseract_path(path)


class ImageDetectionProxy:
    """图像检测代理类

    封装图像检测功能，提供统一的图像识别接口。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        from bt_utils.image_processor import ImageProcessor
        self._processor = ImageProcessor()
        self._template_cache = {}

    def find_template(self, source: Image.Image, template: Image.Image,
                      threshold: float = 0.8, use_cache: bool = True
                      ) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """模板匹配

        Args:
            source: 源图像
            template: 模板图像
            threshold: 匹配阈值
            use_cache: 是否使用缓存

        Returns:
            (是否找到, 位置坐标) 元组
        """
        return self._processor.find_template(source, template, threshold)

    def find_color(self, source: Image.Image, target_color: Tuple[int, int, int],
                   tolerance: int = 10) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """颜色检测

        Args:
            source: 源图像
            target_color: 目标颜色 (R, G, B)
            tolerance: 容差

        Returns:
            (是否找到, 位置坐标) 元组
        """
        return self._processor.find_color(source, target_color, tolerance)

    def compute_hash(self, image: Image.Image, hash_type: str = "phash") -> str:
        """计算图像哈希

        Args:
            image: PIL.Image 图像
            hash_type: 哈希类型 (phash/dhash/ahash)

        Returns:
            哈希字符串
        """
        if hash_type == "phash":
            return self._processor.compute_phash(image)
        elif hash_type == "dhash":
            return self._processor.compute_dhash(image)
        else:
            return self._processor.compute_ahash(image)

    def find_by_hash(self, source: Image.Image, templates: List[Image.Image],
                     threshold: float = 5, hash_type: str = "phash"
                     ) -> Tuple[bool, Optional[Tuple[int, int]], Optional[int]]:
        """基于哈希的图像查找

        Args:
            source: 源图像
            templates: 模板图像列表
            threshold: 最大汉明距离阈值
            hash_type: 哈希类型

        Returns:
            (是否找到, 位置坐标, 最佳匹配索引) 元组
        """
        return self._processor.find_by_hash(source, templates, threshold, hash_type)


class InputProxy:
    """输入代理类

    封装输入控制功能，提供统一的输入接口。
    """

    _instance = None
    _use_dd = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._controller = None

    def _get_controller(self):
        if self._controller is None:
            if self._use_dd:
                try:
                    from bt_utils.dd_input import DDVirtualInput
                    self._controller = DDVirtualInput()
                except Exception:
                    from bt_utils.input_controller import InputController
                    self._controller = InputController()
            else:
                from bt_utils.input_controller import InputController
                self._controller = InputController()
        return self._controller

    @classmethod
    def use_dd_input(cls, use_dd: bool = True) -> None:
        """设置是否使用DD虚拟输入

        Args:
            use_dd: 是否使用DD虚拟输入
        """
        cls._use_dd = use_dd
        if cls._instance:
            cls._instance._controller = None

    def key_press(self, key: str, action: str = "press", duration: int = 0) -> None:
        """按键操作

        Args:
            key: 按键名称
            action: 动作类型 (press/down/up)
            duration: 按住时长（毫秒）
        """
        self._get_controller().key_press(key, action, duration)

    def mouse_click(self, button: str = "left", position: Tuple[int, int] = None,
                   action: str = "press", duration: int = 0) -> None:
        """鼠标点击

        Args:
            button: 鼠标按钮 (left/right/middle)
            position: 点击位置 (x, y)
            action: 动作类型 (press/down/up)
            duration: 按住时长（毫秒）
        """
        self._get_controller().mouse_click(button, position, action, duration)

    def mouse_move(self, position: Tuple[int, int], relative: bool = False,
                   smooth: bool = False, duration: float = 0.3) -> None:
        """移动鼠标

        Args:
            position: 目标位置 (x, y)
            relative: 是否相对移动
            smooth: 是否平滑移动
            duration: 平滑移动时长
        """
        controller = self._get_controller()
        if hasattr(controller, 'mouse_move'):
            controller.mouse_move(position, relative, smooth, duration)
        else:
            controller.mouse_move(position, relative)

    def mouse_scroll(self, amount: int, position: Tuple[int, int] = None) -> None:
        """鼠标滚轮

        Args:
            amount: 滚动量
            position: 滚动位置
        """
        self._get_controller().mouse_scroll(amount, position)


class ScreenshotProxy:
    """截图代理类

    封装截图功能，提供统一的截图接口。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        from bt_utils.screenshot import ScreenshotManager
        self._screenshot = ScreenshotManager()

    def get_full_screenshot(self) -> Image.Image:
        """获取全屏截图

        Returns:
            PIL.Image 图像
        """
        return self._screenshot.get_full_screenshot()

    def get_region_screenshot(self, region: Tuple[int, int, int, int]) -> Image.Image:
        """获取区域截图

        Args:
            region: 区域 (left, top, right, bottom)

        Returns:
            PIL.Image 图像
        """
        return self._screenshot.get_region_screenshot(region)

    def capture_window(self, hwnd) -> Optional[Image.Image]:
        """捕获窗口图像

        Args:
            hwnd: 窗口句柄

        Returns:
            PIL.Image 图像
        """
        try:
            from bt_utils.window_capture import WindowCapture
            return WindowCapture.capture_window(hwnd)
        except Exception:
            return None

    def capture_window_by_title(self, title: str) -> Optional[Image.Image]:
        """根据标题捕获窗口

        Args:
            title: 窗口标题

        Returns:
            PIL.Image 图像
        """
        try:
            from bt_utils.window_capture import WindowCapture
            return WindowCapture.capture_by_title(title)
        except Exception:
            return None


class AlarmProxy:
    """报警代理类

    封装报警功能，提供统一的报警接口。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        from bt_utils.alarm import AlarmPlayer
        self._alarm = AlarmPlayer()

    def play(self, sound_path: str = "", volume: int = 70, wait_complete: bool = True) -> None:
        """播放报警音效

        Args:
            sound_path: 音效文件路径
            volume: 音量 (0-100)
            wait_complete: 是否等待播放完成
        """
        self._alarm.play(sound_path, volume, wait_complete)

    def stop(self) -> None:
        """停止播放"""
        try:
            self._alarm.stop()
        except Exception:
            pass
