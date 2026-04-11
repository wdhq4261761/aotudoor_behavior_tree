import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Optional, List
import os
import re
import sys


def get_tesseract_paths(app_root: str) -> List[str]:
    """获取Tesseract可执行文件的可能路径
    
    Args:
        app_root: 应用根目录
        
    Returns:
        可能的路径列表
    """
    return [
        os.path.join(app_root, "tesseract", "tesseract.exe"),
        os.path.join(app_root, "tesseract.exe"),
    ]


def find_tesseract() -> Optional[str]:
    """自动查找Tesseract路径
    
    Returns:
        Tesseract可执行文件路径，未找到返回None
    """
    if hasattr(sys, '_MEIPASS'):
        app_root = sys._MEIPASS
    else:
        app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    possible_paths = get_tesseract_paths(app_root)
    
    for path in possible_paths:
        if os.path.exists(path):
            tessdata_dir = os.path.join(os.path.dirname(path), "tessdata")
            if os.path.exists(tessdata_dir):
                os.environ["TESSDATA_PREFIX"] = tessdata_dir
            return path
    
    return None


class OCRManager:
    """OCR管理器

    封装Tesseract OCR功能，提供文字识别和数字识别。
    支持图像预处理和多PSM模式识别。
    使用单例模式。
    """
    _instance = None
    _tesseract_path: Optional[str] = None
    _initialized: bool = False

    CHINESE_LANGS = {"chi_sim", "chi_tra"}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._auto_configure_tesseract()

    @classmethod
    def _auto_configure_tesseract(cls):
        """自动配置Tesseract路径"""
        tesseract_path = find_tesseract()
        if tesseract_path:
            cls._tesseract_path = tesseract_path
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    @classmethod
    def set_tesseract_path(cls, path: str) -> None:
        """设置Tesseract OCR路径

        Args:
            path: Tesseract安装目录或可执行文件路径
        """
        cls._tesseract_path = path
        if path and os.path.exists(path):
            if os.path.isdir(path):
                tesseract_exe = os.path.join(path, "tesseract.exe")
            else:
                tesseract_exe = path
            
            if os.path.exists(tesseract_exe):
                pytesseract.pytesseract.tesseract_cmd = tesseract_exe
                
                tessdata_dir = os.path.join(os.path.dirname(tesseract_exe), "tessdata")
                if os.path.exists(tessdata_dir):
                    os.environ["TESSDATA_PREFIX"] = tessdata_dir

    def _preprocess_chinese(self, image: Image.Image) -> Image.Image:
        """中文图像预处理

        流程：放大→中值滤波→灰度→对比度增强→锐化→二值化

        Args:
            image: 原始图像

        Returns:
            预处理后的图像
        """
        width, height = image.size
        min_dimension = min(width, height)
        
        if min_dimension < 100:
            scale_factor = 2.5
            new_size = (int(width * scale_factor), int(height * scale_factor))
            image = image.resize(new_size, Image.LANCZOS)
        
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        if image.mode != 'L':
            image = image.convert('L')
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        image = enhancer.enhance(2.0)
        
        threshold = 130
        image = image.point(lambda x: 255 if x > threshold else 0, '1')
        
        return image

    def _preprocess_standard(self, image: Image.Image) -> Image.Image:
        """标准图像预处理

        流程：灰度→对比度增强→锐化→二值化

        Args:
            image: 原始图像

        Returns:
            预处理后的图像
        """
        if image.mode != 'L':
            image = image.convert('L')
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)
        
        threshold = 128
        image = image.point(lambda x: 255 if x > threshold else 0, '1')
        
        return image

    def _preprocess_image(self, image: Image.Image, language: str = "eng",
                          preprocess_mode: str = "normal") -> Image.Image:
        """图像预处理

        Args:
            image: 原始图像
            language: OCR语言
            preprocess_mode: 预处理模式 (normal/artistic)

        Returns:
            预处理后的图像
        """
        if preprocess_mode == "artistic":
            return self._preprocess_chinese(image)
        
        if language in self.CHINESE_LANGS:
            return self._preprocess_chinese(image)
        else:
            return self._preprocess_standard(image)

    def _try_multi_psm(self, image: Image.Image, language: str,
                       config_extra: str = "") -> Tuple[bool, str]:
        """多PSM模式尝试识别

        PSM顺序：7(单行)→6(文本块)→11(稀疏文本)
        OEM模式：3 (LSTM引擎，最佳识别质量)

        Args:
            image: 图像
            language: 语言
            config_extra: 额外配置

        Returns:
            (是否成功, 识别文本)
        """
        psm_modes = [7, 6, 11]
        
        for psm in psm_modes:
            try:
                config = f"--psm {psm} --oem 3 {config_extra}".strip()
                text = pytesseract.image_to_string(image, lang=language, config=config)
                text = text.strip()
                
                if text:
                    return True, text
            except Exception:
                continue
        
        return False, ""

    def recognize(self, image: Image.Image, keywords: str = None,
                  language: str = "eng",
                  preprocess_mode: str = "normal") -> Tuple[bool, Optional[Tuple[int, int]]]:
        """执行OCR识别

        Args:
            image: PIL.Image 图像
            keywords: 关键词（逗号分隔）
            language: OCR语言
            preprocess_mode: 预处理模式 (normal/artistic)

        Returns:
            (是否找到, 位置坐标) 元组
        """
        try:
            processed = self._preprocess_image(image, language, preprocess_mode)
            
            config = "--oem 3"
            
            data = pytesseract.image_to_data(
                processed, lang=language, config=config,
                output_type=pytesseract.Output.DICT
            )

            if keywords:
                keyword_list = [k.strip().lower() for k in keywords.split(",")]

                for i, text in enumerate(data["text"]):
                    if not text:
                        continue

                    text_lower = text.lower()
                    for keyword in keyword_list:
                        if keyword in text_lower:
                            x = data["left"][i] + data["width"][i] // 2
                            y = data["top"][i] + data["height"][i] // 2
                            
                            if image.size != processed.size:
                                scale_x = image.size[0] / processed.size[0]
                                scale_y = image.size[1] / processed.size[1]
                                x = int(x * scale_x)
                                y = int(y * scale_y)
                            
                            return True, (x, y)

                return False, None

            return True, None

        except Exception as e:
            print(f"[WARN] OCR识别错误: {e}")
            return False, None
    
    def recognize_single_psm(self, image: Image.Image, keywords: str = None,
                             language: str = "eng",
                             preprocess_mode: str = "normal",
                             psm: int = 7, oem: int = 3) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """执行OCR识别（单PSM模式）

        Args:
            image: PIL.Image 图像
            keywords: 关键词（逗号分隔）
            language: OCR语言
            preprocess_mode: 预处理模式 (normal/artistic)
            psm: PSM模式
            oem: OEM模式

        Returns:
            (是否找到, 位置坐标) 元组
        """
        try:
            processed = self._preprocess_image(image, language, preprocess_mode)
            
            config = f"--psm {psm} --oem {oem}"
            
            data = pytesseract.image_to_data(
                processed, lang=language, config=config,
                output_type=pytesseract.Output.DICT
            )

            if keywords:
                keyword_list = [k.strip().lower() for k in keywords.split(",")]

                for i, text in enumerate(data["text"]):
                    if not text:
                        continue

                    text_lower = text.lower()
                    for keyword in keyword_list:
                        if keyword in text_lower:
                            x = data["left"][i] + data["width"][i] // 2
                            y = data["top"][i] + data["height"][i] // 2
                            
                            if image.size != processed.size:
                                scale_x = image.size[0] / processed.size[0]
                                scale_y = image.size[1] / processed.size[1]
                                x = int(x * scale_x)
                                y = int(y * scale_y)
                            
                            return True, (x, y)

                return False, None

            return True, None

        except Exception as e:
            print(f"[WARN] OCR识别错误: {e}")
            return False, None

    def recognize_number(self, image: Image.Image, language: str = "eng",
                         preprocess_mode: str = "normal",
                         extract_mode: str = "无规则",
                         extract_pattern: str = "",
                         min_confidence: float = 0.5) -> Tuple[bool, Optional[float]]:
        """识别数字

        Args:
            image: PIL.Image 图像
            language: OCR语言
            preprocess_mode: 预处理模式 (normal/artistic)
            extract_mode: 提取模式 (无规则/x/y/自定义)
            extract_pattern: 自定义提取模式（使用*作为通配符）
            min_confidence: 最小置信度

        Returns:
            (是否识别成功, 数字值) 元组
        """
        try:
            processed = self._preprocess_image(image, language, preprocess_mode)
            
            success, text = self._try_multi_psm(
                processed, language,
                "-c tessedit_char_whitelist=0123456789.-/:*"
            )
            
            if not success or not text:
                return False, None

            extracted = self._extract_number(text, extract_mode, extract_pattern)
            
            if extracted is not None:
                return True, extracted

            return False, None

        except Exception as e:
            print(f"[WARN] OCR数字识别错误: {e}")
            return False, None

    def _extract_number(self, text: str, extract_mode: str,
                        extract_pattern: str) -> Optional[float]:
        """从文本中提取数字

        Args:
            text: 识别文本
            extract_mode: 提取模式
            extract_pattern: 自定义模式

        Returns:
            提取的数字，失败返回None
        """
        text = text.strip()
        
        if extract_mode == "无规则":
            numbers = re.findall(r'-?\d+\.?\d*', text)
            if numbers:
                try:
                    return float(numbers[0])
                except ValueError:
                    return None
        
        elif extract_mode == "x/y":
            match = re.search(r'(\d+\.?\d*)\s*/\s*\d+\.?\d*', text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return None
        
        elif extract_mode == "自定义" and extract_pattern:
            pattern_parts = extract_pattern.split('*')
            if len(pattern_parts) == 2:
                prefix, suffix = pattern_parts
                prefix_idx = text.find(prefix)
                if prefix_idx != -1:
                    remaining = text[prefix_idx + len(prefix):]
                    suffix_idx = remaining.find(suffix) if suffix else len(remaining)
                    if suffix_idx != -1 or not suffix:
                        number_text = remaining[:suffix_idx] if suffix else remaining
                        numbers = re.findall(r'-?\d+\.?\d*', number_text)
                        if numbers:
                            try:
                                return float(numbers[0])
                            except ValueError:
                                return None
        
        return None

    def get_all_text(self, image: Image.Image, language: str = "eng",
                     preprocess_mode: str = "normal",
                     psm: int = None, oem: int = None) -> str:
        """获取所有识别文本
        
        Args:
            image: PIL.Image 图像
            language: OCR语言
            preprocess_mode: 预处理模式
            psm: PSM模式 (可选)
            oem: OEM模式 (可选)
            
        Returns:
            识别文本
        """
        try:
            processed = self._preprocess_image(image, language, preprocess_mode)
            
            if psm is not None and oem is not None:
                config = f"--psm {psm} --oem {oem}"
            else:
                config = "--oem 3"
            
            return pytesseract.image_to_string(processed, lang=language, config=config)
        except Exception as e:
            print(f"[WARN] OCR文本识别错误: {e}")
            return ""
