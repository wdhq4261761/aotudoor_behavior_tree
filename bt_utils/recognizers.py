from abc import ABC, abstractmethod
from typing import Tuple, Optional, Any
from PIL import Image


class BaseRecognizer(ABC):
    """识别器基类

    所有识别器的抽象基类，定义统一的识别接口。
    """

    @abstractmethod
    def recognize(self, image: Image.Image, **kwargs) -> Tuple[bool, Any]:
        """执行识别

        Args:
            image: PIL.Image 图像
            **kwargs: 额外参数

        Returns:
            (是否成功, 识别结果) 元组
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """获取识别器名称

        Returns:
            识别器名称
        """
        pass


class OCRRecognizer(BaseRecognizer):
    """OCR识别器

    封装OCR识别功能。
    """

    def __init__(self):
        from bt_utils.ocr_manager import OCRManager
        self._ocr = OCRManager()

    def recognize(self, image: Image.Image, keywords: str = None,
                  language: str = "eng", preprocess_mode: str = "normal",
                  **kwargs) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """执行OCR识别

        Args:
            image: PIL.Image 图像
            keywords: 关键词
            language: 语言
            preprocess_mode: 预处理模式

        Returns:
            (是否找到, 位置坐标) 元组
        """
        return self._ocr.recognize(
            image, keywords, language, preprocess_mode
        )

    def get_name(self) -> str:
        return "OCR"


class ImageRecognizer(BaseRecognizer):
    """图像识别器

    封装模板匹配功能。
    """

    def __init__(self):
        from bt_utils.image_processor import ImageProcessor
        self._processor = ImageProcessor()

    def recognize(self, image: Image.Image, template: Image.Image = None,
                  threshold: float = 0.8, **kwargs) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """执行模板匹配

        Args:
            image: PIL.Image 源图像
            template: PIL.Image 模板图像
            threshold: 匹配阈值

        Returns:
            (是否找到, 位置坐标) 元组
        """
        if template is None:
            return False, None

        return self._processor.find_template(image, template, threshold)

    def get_name(self) -> str:
        return "Image"


class ColorRecognizer(BaseRecognizer):
    """颜色识别器

    封装颜色检测功能。
    """

    def __init__(self):
        from bt_utils.image_processor import ImageProcessor
        self._processor = ImageProcessor()

    def recognize(self, image: Image.Image, target_color: Tuple[int, int, int] = None,
                  tolerance: int = 10, **kwargs) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """执行颜色检测

        Args:
            image: PIL.Image 图像
            target_color: 目标颜色 (R, G, B)
            tolerance: 容差

        Returns:
            (是否找到, 位置坐标) 元组
        """
        if target_color is None:
            return False, None

        return self._processor.find_color(image, target_color, tolerance)

    def get_name(self) -> str:
        return "Color"


class NumberRecognizer(BaseRecognizer):
    """数字识别器

    封装数字识别功能。
    """

    def __init__(self):
        from bt_utils.ocr_manager import OCRManager
        self._ocr = OCRManager()

    def recognize(self, image: Image.Image, language: str = "eng",
                  preprocess_mode: str = "normal", extract_mode: str = "无规则",
                  extract_pattern: str = "", min_confidence: float = 0.5,
                  **kwargs) -> Tuple[bool, Optional[float]]:
        """执行数字识别

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

    def get_name(self) -> str:
        return "Number"


class RecognizerFactory:
    """识别器工厂

    创建和管理识别器实例。
    """

    _recognizers = {
        "ocr": OCRRecognizer,
        "image": ImageRecognizer,
        "color": ColorRecognizer,
        "number": NumberRecognizer,
    }

    _instances = {}

    @classmethod
    def get_recognizer(cls, recognizer_type: str) -> Optional[BaseRecognizer]:
        """获取识别器实例

        Args:
            recognizer_type: 识别器类型

        Returns:
            识别器实例
        """
        if recognizer_type not in cls._recognizers:
            return None

        if recognizer_type not in cls._instances:
            cls._instances[recognizer_type] = cls._recognizers[recognizer_type]()

        return cls._instances[recognizer_type]

    @classmethod
    def register_recognizer(cls, name: str, recognizer_class: type) -> None:
        """注册识别器

        Args:
            name: 识别器名称
            recognizer_class: 识别器类
        """
        cls._recognizers[name] = recognizer_class

    @classmethod
    def list_recognizers(cls) -> list:
        """列出所有识别器

        Returns:
            识别器名称列表
        """
        return list(cls._recognizers.keys())
