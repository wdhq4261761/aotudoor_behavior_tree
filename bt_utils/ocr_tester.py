import time
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
from PIL import Image
from bt_utils.ocr_manager import OCRManager
from bt_utils.image_preprocessor import ImagePreprocessor


@dataclass
class TestResult:
    """测试结果数据类"""
    success: bool
    recognized_text: str
    confidence: float
    position: Optional[Tuple[int, int]]
    processing_time: float
    preprocessed_image: Image.Image
    accuracy: Optional[float] = None
    error_message: Optional[str] = None


class OCRTester:
    """OCR测试器
    
    执行OCR识别测试并评估结果。
    """
    
    def __init__(self):
        self.ocr_manager = OCRManager()
        self.preprocessor = ImagePreprocessor()
    
    def test_text_recognition(
        self,
        image: Image.Image,
        keywords: str = None,
        language: str = "eng",
        params: Dict[str, Any] = None
    ) -> TestResult:
        """测试文本识别
        
        Args:
            image: 测试图像
            keywords: 关键词
            language: OCR语言
            params: 预处理参数
            
        Returns:
            测试结果
        """
        try:
            start_time = time.time()
            
            if params:
                processed = self.preprocessor.preprocess_with_params(
                    image, params.get('preprocessing', {}), language
                )
            else:
                processed = image
            
            preprocess_mode = params.get('ocr', {}).get('preprocess_mode', 'normal') if params else 'normal'
            
            ocr_params = params.get('ocr', {}) if params else {}
            psm = ocr_params.get('psm', 7)
            oem = ocr_params.get('oem', 3)
            multi_psm = ocr_params.get('multi_psm', True)
            
            if multi_psm:
                found, position = self.ocr_manager.recognize(
                    processed,
                    keywords=keywords,
                    language=language,
                    preprocess_mode=preprocess_mode
                )
            else:
                found, position = self.ocr_manager.recognize_single_psm(
                    processed,
                    keywords=keywords,
                    language=language,
                    preprocess_mode=preprocess_mode,
                    psm=psm,
                    oem=oem
                )
            
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000
            
            all_text = self.ocr_manager.get_all_text(
                processed,
                language=language,
                preprocess_mode=preprocess_mode,
                psm=psm,
                oem=oem
            )
            
            return TestResult(
                success=found,
                recognized_text=all_text,
                confidence=1.0 if found else 0.0,
                position=position,
                processing_time=processing_time,
                preprocessed_image=processed
            )
            
        except Exception as e:
            return TestResult(
                success=False,
                recognized_text="",
                confidence=0.0,
                position=None,
                processing_time=0.0,
                preprocessed_image=image,
                error_message=str(e)
            )
    
    def test_number_recognition(
        self,
        image: Image.Image,
        language: str = "eng",
        params: Dict[str, Any] = None,
        extract_mode: str = "无规则"
    ) -> TestResult:
        """测试数字识别
        
        Args:
            image: 测试图像
            language: OCR语言
            params: 预处理参数
            extract_mode: 提取模式
            
        Returns:
            测试结果
        """
        try:
            start_time = time.time()
            
            if params:
                processed = self.preprocessor.preprocess_with_params(
                    image, params.get('preprocessing', {}), language
                )
            else:
                processed = image
            
            preprocess_mode = params.get('ocr', {}).get('preprocess_mode', 'normal') if params else 'normal'
            
            found, value = self.ocr_manager.recognize_number(
                processed,
                language=language,
                preprocess_mode=preprocess_mode,
                extract_mode=extract_mode
            )
            
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000
            
            return TestResult(
                success=found,
                recognized_text=str(value) if value else "",
                confidence=1.0 if found else 0.0,
                position=None,
                processing_time=processing_time,
                preprocessed_image=processed
            )
            
        except Exception as e:
            return TestResult(
                success=False,
                recognized_text="",
                confidence=0.0,
                position=None,
                processing_time=0.0,
                preprocessed_image=image,
                error_message=str(e)
            )
    
    def calculate_accuracy(
        self,
        recognized: str,
        expected: str
    ) -> float:
        """计算识别准确率 (Levenshtein相似度)
        
        Args:
            recognized: 识别文本
            expected: 预期文本
            
        Returns:
            相似度 (0.0-1.0)
        """
        if not recognized or not expected:
            return 0.0
        
        recognized = recognized.strip()
        expected = expected.strip()
        
        if recognized == expected:
            return 1.0
        
        def levenshtein_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return levenshtein_distance(s2, s1)
            
            if len(s2) == 0:
                return len(s1)
            
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        distance = levenshtein_distance(recognized, expected)
        max_len = max(len(recognized), len(expected))
        
        return 1.0 - (distance / max_len)
