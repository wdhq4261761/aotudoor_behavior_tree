from rapidocr import RapidOCR
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Optional, List
import numpy as np
import re


class OCRManager:
    """OCR管理器

    封装RapidOCR功能，提供文字识别和数字识别。
    支持图像预处理和多语言识别。
    使用单例模式。
    """
    _instance = None
    _initialized: bool = False
    _engine: Optional[RapidOCR] = None
    _available: bool = True
    _unavailable_reason: str = ""

    CHINESE_LANGS = {"chi_sim", "chi_tra"}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        if not self._available:
            print(f"[OCR] OCR功能不可用: {self._unavailable_reason}")
            return
        
        print(f"[OCR] 开始初始化 OCRManager...")
        
        try:
            print(f"[OCR] 尝试创建 RapidOCR 引擎...")
            self._engine = RapidOCR()
            print(f"[OCR] RapidOCR 引擎创建成功: {self._engine}")
            
            if self._engine is None:
                raise RuntimeError("RapidOCR 引擎创建失败，返回 None")
            
            self._initialized = True
            print(f"[OCR] OCRManager 初始化完成")
            
        except Exception as e:
            print(f"[OCR] RapidOCR 初始化失败: {e}")
            import traceback
            traceback.print_exc()
            self._engine = None
            self._initialized = False
            OCRManager._available = False
            OCRManager._unavailable_reason = str(e)

    @classmethod
    def initialize(cls):
        """初始化OCR引擎（在应用启动时调用）"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_unavailable(cls, reason: str):
        """设置OCR不可用
        
        Args:
            reason: 不可用原因
        """
        cls._available = False
        cls._unavailable_reason = reason
        print(f"[OCR] OCR功能已标记为不可用: {reason}")

    @classmethod
    def is_available(cls) -> bool:
        """检查OCR是否可用
        
        Returns:
            是否可用
        """
        return cls._available

    @classmethod
    def get_unavailable_reason(cls) -> str:
        """获取OCR不可用原因
        
        Returns:
            不可用原因
        """
        return cls._unavailable_reason

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
        image = image.point(lambda x: 255 if x > threshold else 0, 'L')
        
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
        image = image.point(lambda x: 255 if x > threshold else 0, 'L')
        
        return image

    def _preprocess_image(self, image: Image.Image, language: str = "eng",
                          preprocess_mode: str = "normal") -> Image.Image:
        """图像预处理

        Args:
            image: 原始图像
            language: OCR语言
            preprocess_mode: 预处理模式

        Returns:
            预处理后的图像
        """
        if preprocess_mode == "artistic":
            return self._preprocess_chinese(image)
        
        if language in self.CHINESE_LANGS:
            return self._preprocess_chinese(image)
        else:
            return self._preprocess_standard(image)

    def recognize(self, image: Image.Image, keywords: str = None,
                  language: str = "eng",
                  preprocess_mode: str = "normal",
                  region: Tuple[int, int, int, int] = None) -> Tuple[bool, Optional[Tuple[int, int]], str]:
        """执行OCR识别

        Args:
            image: PIL.Image 图像
            keywords: 关键词（逗号分隔）
            language: OCR语言
            preprocess_mode: 预处理模式
            region: 截图区域 (left, top, right, bottom)，用于坐标转换

        Returns:
            (是否找到, 位置坐标, 所有识别文本) 元组
        """
        try:
            if not self._available:
                print(f"[OCR] OCR功能不可用: {self._unavailable_reason}")
                return False, None, ""
            
            if self._engine is None:
                print(f"[OCR] 错误: RapidOCR 引擎未初始化！")
                return False, None, ""
            
            print(f"[OCR] 开始识别 - 语言: {language}, 关键词: {keywords}")
            print(f"[OCR] 图像尺寸: {image.size}, 模式: {image.mode}")
            if region:
                print(f"[OCR] 截图区域: {region}")
            
            processed = self._preprocess_image(image, language, preprocess_mode)
            print(f"[OCR] 预处理后图像尺寸: {processed.size}, 模式: {processed.mode}")
            
            img_array = np.array(processed)
            print(f"[OCR] 转换为数组，形状: {img_array.shape}, 数据类型: {img_array.dtype}")
            
            print(f"[OCR] 调用 RapidOCR 引擎...")
            result = self._engine(img_array)
            
            if result is None:
                print(f"[OCR] RapidOCR返回None")
                return False, None, ""
            
            if result.boxes is None or len(result.boxes) == 0:
                print(f"[OCR] 未检测到文本框")
                return False, None, ""
            
            print(f"[OCR] 检测到 {len(result.boxes)} 个文本框")
            
            all_text = " ".join(result.txts) if result.txts else ""
            print(f"[OCR] 识别文本: {all_text}")
            
            for i, (text, score) in enumerate(zip(result.txts, result.scores)):
                print(f"[OCR] 文本{i+1}: '{text}' (置信度: {score:.2f})")
            
            if keywords:
                keyword_list = [k.strip().lower() for k in keywords.split(",")]
                print(f"[OCR] 搜索关键词列表: {keyword_list}")
                
                for i, text in enumerate(result.txts):
                    if not text:
                        continue
                    
                    text_lower = text.lower()
                    for keyword in keyword_list:
                        keyword_idx = text_lower.find(keyword)
                        
                        if keyword_idx != -1:
                            box = result.boxes[i]
                            
                            keyword_len = len(keyword)
                            text_len = len(text)
                            
                            start_ratio = keyword_idx / text_len
                            end_ratio = (keyword_idx + keyword_len) / text_len
                            center_ratio = (start_ratio + end_ratio) / 2
                            
                            box_left = box[0][0]
                            box_right = box[2][0]
                            box_top = box[0][1]
                            box_bottom = box[2][1]
                            box_width = box_right - box_left
                            box_height = box_bottom - box_top
                            
                            x = int(box_left + box_width * center_ratio)
                            y = int(box_top + box_height / 2)
                            
                            if image.size != processed.size:
                                scale_x = image.size[0] / processed.size[0]
                                scale_y = image.size[1] / processed.size[1]
                                x = int(x * scale_x)
                                y = int(y * scale_y)
                            
                            if region:
                                x += region[0]
                                y += region[1]
                                print(f"[OCR] 转换为绝对坐标: ({x}, {y})")
                            
                            print(f"[OCR] 找到关键词 '{keyword}' 在文本 '{text}' 中")
                            print(f"  关键词位置: 文本框左={box_left}, 右={box_right}, 上={box_top}, 下={box_bottom}")
                            print(f"  关键词相对位置: {start_ratio:.2%} - {end_ratio:.2%}, 中心: {center_ratio:.2%}")
                            print(f"  计算位置: ({x}, {y})")
                            
                            return True, (x, y), all_text
                
                print(f"[OCR] 未找到任何关键词")
                return False, None, all_text
            
            print(f"[OCR] 无关键词搜索，返回成功")
            return True, None, all_text
        
        except Exception as e:
            print(f"[OCR] 识别错误: {e}")
            import traceback
            traceback.print_exc()
            return False, None, ""

    def recognize_single_psm(self, image: Image.Image, keywords: str = None,
                             language: str = "eng",
                             preprocess_mode: str = "normal",
                             psm: int = 7, oem: int = 3,
                             region: Tuple[int, int, int, int] = None) -> Tuple[bool, Optional[Tuple[int, int]], str]:
        """执行OCR识别（兼容接口，PSM/OEM参数已废弃）

        Args:
            image: PIL.Image 图像
            keywords: 关键词（逗号分隔）
            language: OCR语言
            preprocess_mode: 预处理模式
            psm: PSM模式 (已废弃，RapidOCR自动处理)
            oem: OEM模式 (已废弃，RapidOCR使用ONNX)
            region: 截图区域

        Returns:
            (是否找到, 位置坐标, 所有识别文本) 元组
        """
        return self.recognize(image, keywords, language, preprocess_mode, region)

    def recognize_number(self, image: Image.Image, language: str = "eng",
                         preprocess_mode: str = "normal",
                         extract_mode: str = "无规则",
                         extract_pattern: str = "",
                         min_confidence: float = 0.5) -> Tuple[bool, Optional[float], str]:
        """识别数字

        Args:
            image: PIL.Image 图像
            language: OCR语言
            preprocess_mode: 预处理模式
            extract_mode: 提取模式 (无规则/x/y/自定义)
            extract_pattern: 自定义提取模式（使用*作为通配符）
            min_confidence: 最小置信度 (RapidOCR自动过滤低置信度结果)

        Returns:
            (是否识别成功, 数字值, 所有识别文本) 元组
        """
        try:
            if not self._available:
                print(f"[OCR] OCR功能不可用: {self._unavailable_reason}")
                return False, None, ""
            
            if self._engine is None:
                print(f"[OCR] 错误: RapidOCR 引擎未初始化！")
                return False, None, ""
            
            print(f"[OCR] 开始数字识别 - 语言: {language}, 提取模式: {extract_mode}")
            print(f"[OCR] 图像尺寸: {image.size}, 模式: {image.mode}")
            
            processed = self._preprocess_image(image, language, preprocess_mode)
            print(f"[OCR] 预处理后图像尺寸: {processed.size}, 模式: {processed.mode}")
            
            img_array = np.array(processed)
            print(f"[OCR] 转换为数组，形状: {img_array.shape}")
            
            result = self._engine(img_array)
            
            if result is None or result.txts is None or len(result.txts) == 0:
                print(f"[OCR] 未检测到文本")
                return False, None, ""
            
            all_text = " ".join(result.txts)
            print(f"[OCR] 识别文本: {all_text}")
            
            for i, (text, score) in enumerate(zip(result.txts, result.scores)):
                print(f"[OCR] 文本{i+1}: '{text}' (置信度: {score:.2f})")
            
            extracted = self._extract_number(all_text, extract_mode, extract_pattern)
            print(f"[OCR] 提取数字结果: {extracted}")
            
            if extracted is not None:
                print(f"[OCR] 成功提取数字: {extracted}")
                return True, extracted, all_text
            
            print(f"[OCR] 未能提取数字")
            return False, None, all_text
        
        except Exception as e:
            print(f"[OCR] 数字识别错误: {e}")
            import traceback
            traceback.print_exc()
            return False, None, ""

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
            psm: PSM模式 (已废弃，RapidOCR自动处理)
            oem: OEM模式 (已废弃，RapidOCR使用ONNX)
            
        Returns:
            识别文本
        """
        try:
            if not self._available:
                print(f"[OCR] OCR功能不可用: {self._unavailable_reason}")
                return ""
            
            if self._engine is None:
                print(f"[OCR] 错误: RapidOCR 引擎未初始化！")
                return ""
            
            processed = self._preprocess_image(image, language, preprocess_mode)
            
            img_array = np.array(processed)
            
            result = self._engine(img_array)
            
            if result is None or result.txts is None or len(result.txts) == 0:
                return ""
            
            return "\n".join(result.txts)
        
        except Exception as e:
            print(f"[WARN] OCR文本识别错误: {e}")
            return ""
