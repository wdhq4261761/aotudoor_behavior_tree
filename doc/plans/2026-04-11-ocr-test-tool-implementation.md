# OCR测试工具实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建独立的OCR参数测试工具，用于微调AutoDoor行为树系统的OCR识别参数，提升中英文和数字的识别准确率。

**Architecture:** 采用三层架构设计 - 表现层(GUI)、业务层(测试逻辑)、基础设施层(截图/参数管理)。使用CustomTkinter构建GUI，复用现有OCRManager保证参数一致性。

**Tech Stack:** Python 3.10+, CustomTkinter, Pillow, Tesseract OCR, pytesseract

---

## Task 1: 创建图像预处理器核心类

**Files:**
- Create: `bt_utils/image_preprocessor.py`
- Test: `tests/test_image_preprocessor.py`

**Step 1: 创建测试文件**

```python
# tests/test_image_preprocessor.py
import pytest
from PIL import Image
from bt_utils.image_preprocessor import ImagePreprocessor


class TestImagePreprocessor:
    def setup_method(self):
        self.preprocessor = ImagePreprocessor()
        
    def test_preprocess_chinese_with_small_image(self):
        """测试小尺寸中文图像预处理"""
        image = Image.new('RGB', (50, 50), color='white')
        result = self.preprocessor.preprocess_chinese(
            image,
            scale_factor=2.5,
            median_filter_size=3,
            contrast_enhance=2.5,
            sharpness_enhance=2.0,
            sharpness_iterations=2,
            binary_threshold=130
        )
        
        assert result.mode == '1'
        assert result.size == (125, 125)
        
    def test_preprocess_chinese_with_large_image(self):
        """测试大尺寸中文图像预处理"""
        image = Image.new('RGB', (200, 200), color='white')
        result = self.preprocessor.preprocess_chinese(
            image,
            scale_factor=2.5,
            contrast_enhance=2.5,
            sharpness_enhance=2.0,
            sharpness_iterations=2,
            binary_threshold=130
        )
        
        assert result.mode == '1'
        assert result.size == (200, 200)
        
    def test_preprocess_standard(self):
        """测试标准预处理"""
        image = Image.new('RGB', (100, 100), color='white')
        result = self.preprocessor.preprocess_standard(
            image,
            contrast_enhance=1.5,
            sharpness_enhance=1.5,
            binary_threshold=128
        )
        
        assert result.mode == '1'
        assert result.size == (100, 100)
        
    def test_preprocess_with_params_chinese(self):
        """测试使用参数字典进行中文预处理"""
        image = Image.new('RGB', (50, 50), color='white')
        params = {
            'scale_factor': 3.0,
            'median_filter_size': 3,
            'contrast_enhance': 2.0,
            'sharpness_enhance': 1.5,
            'sharpness_iterations': 2,
            'binary_threshold': 120
        }
        
        result = self.preprocessor.preprocess_with_params(
            image, params, language='chi_sim'
        )
        
        assert result.mode == '1'
        assert result.size == (150, 150)
        
    def test_preprocess_with_params_english(self):
        """测试使用参数字典进行英文预处理"""
        image = Image.new('RGB', (100, 100), color='white')
        params = {
            'contrast_enhance': 2.0,
            'sharpness_enhance': 1.5,
            'binary_threshold': 130
        }
        
        result = self.preprocessor.preprocess_with_params(
            image, params, language='eng'
        )
        
        assert result.mode == '1'
        assert result.size == (100, 100)
```

**Step 2: 运行测试验证失败**

Run: `pytest tests/test_image_preprocessor.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'bt_utils.image_preprocessor'"

**Step 3: 创建图像预处理器实现**

```python
# bt_utils/image_preprocessor.py
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, Any


class ImagePreprocessor:
    """图像预处理器
    
    提供可配置参数的图像预处理功能，用于OCR识别前的图像处理。
    """
    
    CHINESE_LANGS = {"chi_sim", "chi_tra"}
    
    def preprocess_chinese(
        self,
        image: Image.Image,
        scale_factor: float = 2.5,
        median_filter_size: int = 3,
        contrast_enhance: float = 2.5,
        sharpness_enhance: float = 2.0,
        sharpness_iterations: int = 2,
        binary_threshold: int = 130
    ) -> Image.Image:
        """中文图像预处理
        
        流程：放大→中值滤波→灰度→对比度增强→锐化→二值化
        
        Args:
            image: 原始图像
            scale_factor: 放大倍数
            median_filter_size: 中值滤波大小
            contrast_enhance: 对比度增强倍数
            sharpness_enhance: 锐化强度
            sharpness_iterations: 锐化次数
            binary_threshold: 二值化阈值
            
        Returns:
            预处理后的图像
        """
        width, height = image.size
        min_dimension = min(width, height)
        
        if min_dimension < 100:
            new_size = (int(width * scale_factor), int(height * scale_factor))
            image = image.resize(new_size, Image.LANCZOS)
        
        image = image.filter(ImageFilter.MedianFilter(size=median_filter_size))
        
        if image.mode != 'L':
            image = image.convert('L')
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast_enhance)
        
        enhancer = ImageEnhance.Sharpness(image)
        for _ in range(sharpness_iterations):
            image = enhancer.enhance(sharpness_enhance)
        
        image = image.point(lambda x: 255 if x > binary_threshold else 0, '1')
        
        return image
    
    def preprocess_standard(
        self,
        image: Image.Image,
        contrast_enhance: float = 1.5,
        sharpness_enhance: float = 1.5,
        binary_threshold: int = 128
    ) -> Image.Image:
        """标准图像预处理
        
        流程：灰度→对比度增强→锐化→二值化
        
        Args:
            image: 原始图像
            contrast_enhance: 对比度增强倍数
            sharpness_enhance: 锐化强度
            binary_threshold: 二值化阈值
            
        Returns:
            预处理后的图像
        """
        if image.mode != 'L':
            image = image.convert('L')
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast_enhance)
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(sharpness_enhance)
        
        image = image.point(lambda x: 255 if x > binary_threshold else 0, '1')
        
        return image
    
    def preprocess_with_params(
        self,
        image: Image.Image,
        params: Dict[str, Any],
        language: str = "eng"
    ) -> Image.Image:
        """使用参数字典进行预处理
        
        Args:
            image: 原始图像
            params: 参数字典
            language: OCR语言
            
        Returns:
            预处理后的图像
        """
        if language in self.CHINESE_LANGS:
            return self.preprocess_chinese(
                image,
                scale_factor=params.get('scale_factor', 2.5),
                median_filter_size=params.get('median_filter_size', 3),
                contrast_enhance=params.get('contrast_enhance', 2.5),
                sharpness_enhance=params.get('sharpness_enhance', 2.0),
                sharpness_iterations=params.get('sharpness_iterations', 2),
                binary_threshold=params.get('binary_threshold', 130)
            )
        else:
            return self.preprocess_standard(
                image,
                contrast_enhance=params.get('contrast_enhance', 1.5),
                sharpness_enhance=params.get('sharpness_enhance', 1.5),
                binary_threshold=params.get('binary_threshold', 128)
            )
```

**Step 4: 运行测试验证通过**

Run: `pytest tests/test_image_preprocessor.py -v`

Expected: PASS (5 tests)

**Step 5: 提交代码**

```bash
git add bt_utils/image_preprocessor.py tests/test_image_preprocessor.py
git commit -m "feat: add image preprocessor with configurable parameters"
```

---

## Task 2: 创建参数管理器

**Files:**
- Create: `bt_utils/parameter_manager.py`
- Test: `tests/test_parameter_manager.py`

**Step 1: 创建测试文件**

```python
# tests/test_parameter_manager.py
import pytest
import json
import tempfile
import os
from bt_utils.parameter_manager import ParameterManager


class TestParameterManager:
    def setup_method(self):
        self.manager = ParameterManager()
        
    def test_get_default_params(self):
        """测试获取默认参数"""
        params = self.manager.get_default_params()
        
        assert 'preprocessing' in params
        assert 'ocr' in params
        assert 'test' in params
        
        assert params['preprocessing']['scale_factor'] == 2.5
        assert params['ocr']['language'] == 'chi_sim'
        
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        params = self.manager.get_default_params()
        params['preprocessing']['scale_factor'] = 3.0
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            self.manager.save_config(params, temp_path)
            
            loaded_params = self.manager.load_config(temp_path)
            
            assert loaded_params['preprocessing']['scale_factor'] == 3.0
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    def test_validate_params_valid(self):
        """测试参数验证 - 有效参数"""
        params = self.manager.get_default_params()
        
        is_valid, errors = self.manager.validate_params(params)
        
        assert is_valid is True
        assert len(errors) == 0
        
    def test_validate_params_invalid(self):
        """测试参数验证 - 无效参数"""
        params = {
            'preprocessing': {
                'scale_factor': -1.0
            }
        }
        
        is_valid, errors = self.manager.validate_params(params)
        
        assert is_valid is False
        assert len(errors) > 0
        
    def test_compare_params(self):
        """测试参数对比"""
        params1 = self.manager.get_default_params()
        params2 = self.manager.get_default_params()
        params2['preprocessing']['scale_factor'] = 3.0
        
        report = self.manager.compare_params(params1, params2)
        
        assert report['has_differences'] is True
        assert len(report['differences']) > 0
```

**Step 2: 运行测试验证失败**

Run: `pytest tests/test_parameter_manager.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'bt_utils.parameter_manager'"

**Step 3: 创建参数管理器实现**

```python
# bt_utils/parameter_manager.py
import json
import os
from typing import Dict, Any, Tuple, List


class ParameterManager:
    """参数管理器
    
    管理OCR测试参数的保存、加载和对比。
    """
    
    DEFAULT_PARAMS = {
        "version": "1.0",
        "preprocessing": {
            "scale_factor": 2.5,
            "median_filter_size": 3,
            "contrast_enhance": 2.5,
            "sharpness_enhance": 2.0,
            "sharpness_iterations": 2,
            "binary_threshold": 130
        },
        "ocr": {
            "language": "chi_sim",
            "psm_modes": [7, 6, 11],
            "preprocess_mode": "artistic",
            "char_whitelist": "0123456789.-/:*"
        },
        "test": {
            "keywords": "",
            "expected_text": "",
            "expected_number": None,
            "test_iterations": 10
        }
    }
    
    def get_default_params(self) -> Dict[str, Any]:
        """获取默认参数
        
        Returns:
            默认参数字典
        """
        return self.DEFAULT_PARAMS.copy()
    
    def save_config(
        self,
        params: Dict[str, Any],
        filepath: str = None
    ) -> None:
        """保存参数配置
        
        Args:
            params: 参数字典
            filepath: 保存路径，None则使用默认路径
        """
        if filepath is None:
            filepath = self._get_default_config_path()
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(params, f, indent=2, ensure_ascii=False)
    
    def load_config(
        self,
        filepath: str = None
    ) -> Dict[str, Any]:
        """加载参数配置
        
        Args:
            filepath: 配置文件路径，None则使用默认路径
            
        Returns:
            参数字典
        """
        if filepath is None:
            filepath = self._get_default_config_path()
        
        if not os.path.exists(filepath):
            return self.get_default_params()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def validate_params(
        self,
        params: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """验证参数有效性
        
        Args:
            params: 参数字典
            
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        if 'preprocessing' in params:
            prep = params['preprocessing']
            
            if 'scale_factor' in prep:
                if not (0.5 <= prep['scale_factor'] <= 5.0):
                    errors.append("scale_factor must be between 0.5 and 5.0")
            
            if 'median_filter_size' in prep:
                if prep['median_filter_size'] % 2 == 0:
                    errors.append("median_filter_size must be odd")
            
            if 'binary_threshold' in prep:
                if not (0 <= prep['binary_threshold'] <= 255):
                    errors.append("binary_threshold must be between 0 and 255")
        
        if 'ocr' in params:
            ocr = params['ocr']
            
            if 'language' in ocr:
                valid_langs = ['eng', 'chi_sim', 'chi_tra']
                if ocr['language'] not in valid_langs:
                    errors.append(f"language must be one of {valid_langs}")
        
        return len(errors) == 0, errors
    
    def compare_params(
        self,
        params1: Dict[str, Any],
        params2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """对比两组参数
        
        Args:
            params1: 参数字典1
            params2: 参数字典2
            
        Returns:
            对比报告
        """
        differences = []
        
        def compare_dicts(d1, d2, path=""):
            for key in set(list(d1.keys()) + list(d2.keys())):
                current_path = f"{path}.{key}" if path else key
                
                if key not in d1:
                    differences.append({
                        'path': current_path,
                        'type': 'added',
                        'value': d2[key]
                    })
                elif key not in d2:
                    differences.append({
                        'path': current_path,
                        'type': 'removed',
                        'value': d1[key]
                    })
                elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
                    compare_dicts(d1[key], d2[key], current_path)
                elif d1[key] != d2[key]:
                    differences.append({
                        'path': current_path,
                        'type': 'changed',
                        'old_value': d1[key],
                        'new_value': d2[key]
                    })
        
        compare_dicts(params1, params2)
        
        return {
            'has_differences': len(differences) > 0,
            'differences': differences
        }
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        return os.path.join('config', 'ocr_test_params.json')
```

**Step 4: 运行测试验证通过**

Run: `pytest tests/test_parameter_manager.py -v`

Expected: PASS (5 tests)

**Step 5: 提交代码**

```bash
git add bt_utils/parameter_manager.py tests/test_parameter_manager.py
git commit -m "feat: add parameter manager for OCR test configuration"
```

---

## Task 3: 创建OCR测试器核心类

**Files:**
- Create: `bt_utils/ocr_tester.py`
- Test: `tests/test_ocr_tester.py`

**Step 1: 创建测试文件**

```python
# tests/test_ocr_tester.py
import pytest
from PIL import Image
from unittest.mock import Mock, patch
from bt_utils.ocr_tester import OCRTester, TestResult


class TestOCRTester:
    def setup_method(self):
        self.tester = OCRTester()
        
    def test_test_result_dataclass(self):
        """测试TestResult数据类"""
        result = TestResult(
            success=True,
            recognized_text="测试文本",
            confidence=0.95,
            position=(100, 200),
            processing_time=150.5,
            preprocessed_image=Image.new('RGB', (100, 100))
        )
        
        assert result.success is True
        assert result.recognized_text == "测试文本"
        assert result.confidence == 0.95
        assert result.position == (100, 200)
        assert result.processing_time == 150.5
        
    @patch('bt_utils.ocr_tester.OCRManager')
    def test_test_text_recognition_success(self, mock_ocr_manager):
        """测试文本识别成功"""
        mock_ocr_instance = Mock()
        mock_ocr_instance.recognize.return_value = (True, (100, 200))
        mock_ocr_manager.return_value = mock_ocr_instance
        
        image = Image.new('RGB', (100, 100), color='white')
        result = self.tester.test_text_recognition(
            image,
            keywords="测试",
            language="chi_sim"
        )
        
        assert result.success is True
        assert result.position == (100, 200)
        
    @patch('bt_utils.ocr_tester.OCRManager')
    def test_test_text_recognition_failure(self, mock_ocr_manager):
        """测试文本识别失败"""
        mock_ocr_instance = Mock()
        mock_ocr_instance.recognize.return_value = (False, None)
        mock_ocr_manager.return_value = mock_ocr_instance
        
        image = Image.new('RGB', (100, 100), color='white')
        result = self.tester.test_text_recognition(
            image,
            keywords="测试",
            language="chi_sim"
        )
        
        assert result.success is False
        
    def test_calculate_accuracy_identical(self):
        """测试准确率计算 - 完全相同"""
        accuracy = self.tester.calculate_accuracy("测试文本", "测试文本")
        
        assert accuracy == 1.0
        
    def test_calculate_accuracy_different(self):
        """测试准确率计算 - 完全不同"""
        accuracy = self.tester.calculate_accuracy("测试文本", "其他内容")
        
        assert 0.0 <= accuracy < 1.0
        
    def test_calculate_accuracy_empty(self):
        """测试准确率计算 - 空字符串"""
        accuracy = self.tester.calculate_accuracy("", "测试")
        
        assert accuracy == 0.0
```

**Step 2: 运行测试验证失败**

Run: `pytest tests/test_ocr_tester.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'bt_utils.ocr_tester'"

**Step 3: 创建OCR测试器实现**

```python
# bt_utils/ocr_tester.py
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
            
            found, position = self.ocr_manager.recognize(
                processed,
                keywords=keywords,
                language=language,
                preprocess_mode=preprocess_mode
            )
            
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000
            
            all_text = self.ocr_manager.get_all_text(
                processed,
                language=language,
                preprocess_mode=preprocess_mode
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
```

**Step 4: 运行测试验证通过**

Run: `pytest tests/test_ocr_tester.py -v`

Expected: PASS (6 tests)

**Step 5: 提交代码**

```bash
git add bt_utils/ocr_tester.py tests/test_ocr_tester.py
git commit -m "feat: add OCR tester with accuracy calculation"
```

---

## Task 4: 创建测试执行器

**Files:**
- Create: `bt_gui/ocr_test_tool/test_runner.py`
- Test: `tests/test_test_runner.py`

**Step 1: 创建测试文件**

```python
# tests/test_test_runner.py
import pytest
from PIL import Image
from unittest.mock import Mock
from bt_gui.ocr_test_tool.test_runner import TestRunner, StatisticsReport


class TestTestRunner:
    def setup_method(self):
        self.runner = TestRunner()
        
    def test_run_single_test(self):
        """测试单次测试执行"""
        image = Image.new('RGB', (100, 100), color='white')
        params = {
            'preprocessing': {'scale_factor': 2.5},
            'ocr': {'language': 'chi_sim'}
        }
        
        result = self.runner.run_single_test(image, params)
        
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'processing_time')
        
    def test_get_statistics_empty(self):
        """测试空结果统计"""
        stats = self.runner.get_statistics([])
        
        assert stats.total_tests == 0
        assert stats.success_rate == 0.0
        
    def test_get_statistics_with_results(self):
        """测试有结果的统计"""
        from bt_utils.ocr_tester import TestResult
        
        results = [
            TestResult(
                success=True,
                recognized_text="测试1",
                confidence=0.9,
                position=(100, 200),
                processing_time=100.0,
                preprocessed_image=Image.new('RGB', (100, 100))
            ),
            TestResult(
                success=False,
                recognized_text="",
                confidence=0.0,
                position=None,
                processing_time=150.0,
                preprocessed_image=Image.new('RGB', (100, 100))
            )
        ]
        
        stats = self.runner.get_statistics(results)
        
        assert stats.total_tests == 2
        assert stats.success_count == 1
        assert stats.success_rate == 0.5
        assert stats.avg_time == 125.0
```

**Step 2: 运行测试验证失败**

Run: `pytest tests/test_test_runner.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'bt_gui.ocr_test_tool.test_runner'"

**Step 3: 创建测试执行器实现**

```python
# bt_gui/ocr_test_tool/test_runner.py
from dataclasses import dataclass
from typing import List, Dict, Any
from PIL import Image
from bt_utils.ocr_tester import OCRTester, TestResult


@dataclass
class StatisticsReport:
    """统计报告数据类"""
    total_tests: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_time: float
    min_time: float
    max_time: float
    avg_accuracy: float = 0.0


class TestRunner:
    """测试执行器
    
    协调测试流程，管理测试状态。
    """
    
    def __init__(self):
        self.tester = OCRTester()
    
    def run_single_test(
        self,
        image: Image.Image,
        params: Dict[str, Any]
    ) -> TestResult:
        """执行单次测试
        
        Args:
            image: 测试图像
            params: 测试参数
            
        Returns:
            测试结果
        """
        test_params = params.get('test', {})
        keywords = test_params.get('keywords', '')
        language = params.get('ocr', {}).get('language', 'eng')
        
        if keywords:
            return self.tester.test_text_recognition(
                image,
                keywords=keywords,
                language=language,
                params=params
            )
        else:
            return self.tester.test_text_recognition(
                image,
                keywords=None,
                language=language,
                params=params
            )
    
    def run_batch_tests(
        self,
        images: List[Image.Image],
        params: Dict[str, Any]
    ) -> List[TestResult]:
        """执行批量测试
        
        Args:
            images: 测试图像列表
            params: 测试参数
            
        Returns:
            测试结果列表
        """
        results = []
        for image in images:
            result = self.run_single_test(image, params)
            results.append(result)
        return results
    
    def get_statistics(
        self,
        results: List[TestResult]
    ) -> StatisticsReport:
        """生成统计报告
        
        Args:
            results: 测试结果列表
            
        Returns:
            统计报告
        """
        if not results:
            return StatisticsReport(
                total_tests=0,
                success_count=0,
                failure_count=0,
                success_rate=0.0,
                avg_time=0.0,
                min_time=0.0,
                max_time=0.0
            )
        
        total_tests = len(results)
        success_count = sum(1 for r in results if r.success)
        failure_count = total_tests - success_count
        success_rate = success_count / total_tests if total_tests > 0 else 0.0
        
        times = [r.processing_time for r in results]
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        accuracies = [r.accuracy for r in results if r.accuracy is not None]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
        
        return StatisticsReport(
            total_tests=total_tests,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_rate,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            avg_accuracy=avg_accuracy
        )
```

**Step 4: 创建包初始化文件**

```python
# bt_gui/ocr_test_tool/__init__.py
"""OCR测试工具模块"""

from .test_runner import TestRunner, StatisticsReport

__all__ = ['TestRunner', 'StatisticsReport']
```

**Step 5: 运行测试验证通过**

Run: `pytest tests/test_test_runner.py -v`

Expected: PASS (3 tests)

**Step 6: 提交代码**

```bash
git add bt_gui/ocr_test_tool/ tests/test_test_runner.py
git commit -m "feat: add test runner for coordinating OCR tests"
```

---

## Task 5: 创建GUI主窗口框架

**Files:**
- Create: `bt_gui/ocr_test_tool/main_window.py`
- Create: `ocr_test_tool.py` (启动脚本)

**Step 1: 创建主窗口实现**

```python
# bt_gui/ocr_test_tool/main_window.py
import customtkinter as ctk
from typing import Optional
from PIL import Image as PILImage
from bt_gui.ocr_test_tool.test_runner import TestRunner
from bt_utils.parameter_manager import ParameterManager


class OCRTestMainWindow(ctk.CTk):
    """OCR测试工具主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.title("OCR参数测试工具")
        self.geometry("1400x800")
        
        self.test_runner = TestRunner()
        self.param_manager = ParameterManager()
        
        self.current_image: Optional[PILImage.Image] = None
        self.test_history = []
        
        self._create_ui()
        self._setup_layout()
        
    def _create_ui(self):
        """创建UI组件"""
        self._create_toolbar()
        self._create_main_panels()
        self._create_status_bar()
        
    def _create_toolbar(self):
        """创建工具栏"""
        self.toolbar = ctk.CTkFrame(self, height=50)
        self.toolbar.pack(fill="x", padx=10, pady=5)
        
        self.btn_screenshot = ctk.CTkButton(
            self.toolbar,
            text="全屏截图",
            command=self._on_screenshot_full
        )
        self.btn_screenshot.pack(side="left", padx=5)
        
        self.btn_region_screenshot = ctk.CTkButton(
            self.toolbar,
            text="区域截图",
            command=self._on_screenshot_region
        )
        self.btn_region_screenshot.pack(side="left", padx=5)
        
        self.btn_load_image = ctk.CTkButton(
            self.toolbar,
            text="加载图片",
            command=self._on_load_image
        )
        self.btn_load_image.pack(side="left", padx=5)
        
        self.btn_save_config = ctk.CTkButton(
            self.toolbar,
            text="保存配置",
            command=self._on_save_config
        )
        self.btn_save_config.pack(side="left", padx=5)
        
        self.btn_load_config = ctk.CTkButton(
            self.toolbar,
            text="加载配置",
            command=self._on_load_config
        )
        self.btn_load_config.pack(side="left", padx=5)
        
    def _create_main_panels(self):
        """创建主面板"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.main_frame.grid_columnconfigure(0, weight=4)
        self.main_frame.grid_columnconfigure(1, weight=3)
        self.main_frame.grid_columnconfigure(2, weight=3)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        self.screenshot_panel = ctk.CTkFrame(self.main_frame)
        self.screenshot_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.param_panel = ctk.CTkFrame(self.main_frame)
        self.param_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.result_panel = ctk.CTkFrame(self.main_frame)
        self.result_panel.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        
        self._setup_screenshot_panel()
        self._setup_param_panel()
        self._setup_result_panel()
        
    def _setup_screenshot_panel(self):
        """设置截图面板"""
        label = ctk.CTkLabel(
            self.screenshot_panel,
            text="图像预览区",
            font=("Arial", 16, "bold")
        )
        label.pack(pady=10)
        
        self.original_image_label = ctk.CTkLabel(
            self.screenshot_panel,
            text="原始图像",
            font=("Arial", 12)
        )
        self.original_image_label.pack(pady=5)
        
        self.original_image_frame = ctk.CTkFrame(
            self.screenshot_panel,
            width=400,
            height=250
        )
        self.original_image_frame.pack(pady=5, padx=10, fill="x")
        self.original_image_frame.pack_propagate(False)
        
        self.preprocessed_image_label = ctk.CTkLabel(
            self.screenshot_panel,
            text="预处理图像",
            font=("Arial", 12)
        )
        self.preprocessed_image_label.pack(pady=5)
        
        self.preprocessed_image_frame = ctk.CTkFrame(
            self.screenshot_panel,
            width=400,
            height=250
        )
        self.preprocessed_image_frame.pack(pady=5, padx=10, fill="x")
        self.preprocessed_image_frame.pack_propagate(False)
        
        self.btn_start_test = ctk.CTkButton(
            self.screenshot_panel,
            text="开始测试",
            command=self._on_start_test,
            height=40,
            font=("Arial", 14, "bold")
        )
        self.btn_start_test.pack(pady=20)
        
    def _setup_param_panel(self):
        """设置参数面板"""
        label = ctk.CTkLabel(
            self.param_panel,
            text="参数调节区",
            font=("Arial", 16, "bold")
        )
        label.pack(pady=10)
        
        prep_label = ctk.CTkLabel(
            self.param_panel,
            text="预处理参数",
            font=("Arial", 12, "bold")
        )
        prep_label.pack(pady=5)
        
        self.scale_slider = self._create_slider(
            self.param_panel, "放大倍数", 1.0, 5.0, 2.5
        )
        self.contrast_slider = self._create_slider(
            self.param_panel, "对比度增强", 0.5, 5.0, 2.5
        )
        self.sharpness_slider = self._create_slider(
            self.param_panel, "锐化强度", 0.5, 5.0, 2.0
        )
        self.threshold_slider = self._create_slider(
            self.param_panel, "二值化阈值", 50, 200, 130
        )
        
        ocr_label = ctk.CTkLabel(
            self.param_panel,
            text="OCR参数",
            font=("Arial", 12, "bold")
        )
        ocr_label.pack(pady=10)
        
        self.language_var = ctk.StringVar(value="chi_sim")
        language_menu = ctk.CTkOptionMenu(
            self.param_panel,
            variable=self.language_var,
            values=["eng", "chi_sim", "chi_tra"],
            width=200
        )
        language_menu.pack(pady=5)
        
        test_label = ctk.CTkLabel(
            self.param_panel,
            text="测试参数",
            font=("Arial", 12, "bold")
        )
        test_label.pack(pady=10)
        
        self.keywords_entry = ctk.CTkEntry(
            self.param_panel,
            placeholder_text="关键词(逗号分隔)",
            width=200
        )
        self.keywords_entry.pack(pady=5)
        
        self.expected_entry = ctk.CTkEntry(
            self.param_panel,
            placeholder_text="预期结果",
            width=200
        )
        self.expected_entry.pack(pady=5)
        
    def _setup_result_panel(self):
        """设置结果面板"""
        label = ctk.CTkLabel(
            self.result_panel,
            text="结果展示区",
            font=("Arial", 16, "bold")
        )
        label.pack(pady=10)
        
        result_label = ctk.CTkLabel(
            self.result_panel,
            text="识别结果",
            font=("Arial", 12, "bold")
        )
        result_label.pack(pady=5)
        
        self.result_textbox = ctk.CTkTextbox(
            self.result_panel,
            width=300,
            height=150
        )
        self.result_textbox.pack(pady=5, padx=10, fill="x")
        
        stats_label = ctk.CTkLabel(
            self.result_panel,
            text="性能统计",
            font=("Arial", 12, "bold")
        )
        stats_label.pack(pady=10)
        
        self.stats_textbox = ctk.CTkTextbox(
            self.result_panel,
            width=300,
            height=150
        )
        self.stats_textbox.pack(pady=5, padx=10, fill="x")
        
    def _create_slider(self, parent, label: str, min_val: float, max_val: float, default: float):
        """创建滑块控件"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=2)
        
        label_widget = ctk.CTkLabel(frame, text=label, width=100)
        label_widget.pack(side="left")
        
        slider = ctk.CTkSlider(
            frame,
            from_=min_val,
            to=max_val,
            number_of_steps=100
        )
        slider.set(default)
        slider.pack(side="left", fill="x", expand=True, padx=5)
        
        value_label = ctk.CTkLabel(frame, text=f"{default:.1f}", width=50)
        value_label.pack(side="left")
        
        def update_label(value):
            value_label.configure(text=f"{value:.1f}")
        
        slider.configure(command=update_label)
        
        return slider
        
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ctk.CTkFrame(self, height=30)
        self.status_bar.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="就绪",
            font=("Arial", 10)
        )
        self.status_label.pack(side="left", padx=10)
        
    def _setup_layout(self):
        """设置布局"""
        pass
        
    def _on_screenshot_full(self):
        """全屏截图"""
        self.status_label.configure(text="正在截图...")
        self.update()
        
        from PIL import ImageGrab
        self.current_image = ImageGrab.grab()
        
        self.status_label.configure(text="截图完成")
        self._update_image_display()
        
    def _on_screenshot_region(self):
        """区域截图"""
        self.status_label.configure(text="请选择截图区域...")
        
    def _on_load_image(self):
        """加载图片"""
        from tkinter import filedialog
        
        filepath = filedialog.askopenfilename(
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp"),
                ("所有文件", "*.*")
            ]
        )
        
        if filepath:
            self.current_image = PILImage.open(filepath)
            self.status_label.configure(text=f"已加载: {filepath}")
            self._update_image_display()
        
    def _on_save_config(self):
        """保存配置"""
        from tkinter import filedialog
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")]
        )
        
        if filepath:
            params = self._get_current_params()
            self.param_manager.save_config(params, filepath)
            self.status_label.configure(text=f"配置已保存: {filepath}")
        
    def _on_load_config(self):
        """加载配置"""
        from tkinter import filedialog
        
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON文件", "*.json")]
        )
        
        if filepath:
            params = self.param_manager.load_config(filepath)
            self._set_current_params(params)
            self.status_label.configure(text=f"配置已加载: {filepath}")
        
    def _on_start_test(self):
        """开始测试"""
        if not self.current_image:
            self.status_label.configure(text="请先截图或加载图片")
            return
        
        self.status_label.configure(text="正在测试...")
        self.update()
        
        params = self._get_current_params()
        result = self.test_runner.run_single_test(self.current_image, params)
        
        self.test_history.append(result)
        self._display_result(result)
        
        self.status_label.configure(text="测试完成")
        
    def _get_current_params(self) -> dict:
        """获取当前参数"""
        return {
            "preprocessing": {
                "scale_factor": self.scale_slider.get(),
                "contrast_enhance": self.contrast_slider.get(),
                "sharpness_enhance": self.sharpness_slider.get(),
                "binary_threshold": int(self.threshold_slider.get())
            },
            "ocr": {
                "language": self.language_var.get()
            },
            "test": {
                "keywords": self.keywords_entry.get(),
                "expected_text": self.expected_entry.get()
            }
        }
        
    def _set_current_params(self, params: dict):
        """设置当前参数"""
        prep = params.get('preprocessing', {})
        self.scale_slider.set(prep.get('scale_factor', 2.5))
        self.contrast_slider.set(prep.get('contrast_enhance', 2.5))
        self.sharpness_slider.set(prep.get('sharpness_enhance', 2.0))
        self.threshold_slider.set(prep.get('binary_threshold', 130))
        
        ocr = params.get('ocr', {})
        self.language_var.set(ocr.get('language', 'chi_sim'))
        
        test = params.get('test', {})
        self.keywords_entry.delete(0, 'end')
        self.keywords_entry.insert(0, test.get('keywords', ''))
        self.expected_entry.delete(0, 'end')
        self.expected_entry.insert(0, test.get('expected_text', ''))
        
    def _update_image_display(self):
        """更新图像显示"""
        pass
        
    def _display_result(self, result):
        """显示测试结果"""
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", f"识别结果:\n{result.recognized_text}\n\n")
        self.result_textbox.insert("end", f"成功: {'是' if result.success else '否'}\n")
        self.result_textbox.insert("end", f"置信度: {result.confidence:.2f}\n")
        
        if result.position:
            self.result_textbox.insert("end", f"位置: {result.position}\n")
        
        self.stats_textbox.delete("1.0", "end")
        self.stats_textbox.insert("1.0", f"处理时间: {result.processing_time:.2f} ms\n")
        
        if self.test_history:
            stats = self.test_runner.get_statistics(self.test_history)
            self.stats_textbox.insert("end", f"\n统计信息:\n")
            self.stats_textbox.insert("end", f"总测试次数: {stats.total_tests}\n")
            self.stats_textbox.insert("end", f"成功次数: {stats.success_count}\n")
            self.stats_textbox.insert("end", f"成功率: {stats.success_rate:.2%}\n")
            self.stats_textbox.insert("end", f"平均耗时: {stats.avg_time:.2f} ms\n")


def main():
    """主函数"""
    app = OCRTestMainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
```

**Step 2: 创建启动脚本**

```python
# ocr_test_tool.py
"""OCR测试工具启动脚本"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bt_gui.ocr_test_tool.main_window import main

if __name__ == "__main__":
    main()
```

**Step 3: 测试启动**

Run: `python ocr_test_tool.py`

Expected: GUI窗口成功启动

**Step 4: 提交代码**

```bash
git add bt_gui/ocr_test_tool/main_window.py ocr_test_tool.py
git commit -m "feat: add OCR test tool GUI main window"
```

---

## Task 6: 创建默认配置文件

**Files:**
- Create: `config/ocr_test_params.json`

**Step 1: 创建配置文件**

```json
{
  "version": "1.0",
  "preprocessing": {
    "scale_factor": 2.5,
    "median_filter_size": 3,
    "contrast_enhance": 2.5,
    "sharpness_enhance": 2.0,
    "sharpness_iterations": 2,
    "binary_threshold": 130
  },
  "ocr": {
    "language": "chi_sim",
    "psm_modes": [7, 6, 11],
    "preprocess_mode": "artistic",
    "char_whitelist": "0123456789.-/:*"
  },
  "test": {
    "keywords": "",
    "expected_text": "",
    "expected_number": null,
    "test_iterations": 10
  }
}
```

**Step 2: 提交配置文件**

```bash
git add config/ocr_test_params.json
git commit -m "feat: add default OCR test parameters configuration"
```

---

## Task 7: 创建使用文档

**Files:**
- Create: `doc/OCR测试工具使用指南.md`

**Step 1: 创建使用文档**

```markdown
# OCR测试工具使用指南

## 1 工具简介

OCR测试工具是一个独立的参数测试工具，用于微调AutoDoor行为树系统的OCR识别参数，提升中英文和数字的识别准确率。

## 2 启动方式

### 2.1 独立启动

```bash
python ocr_test_tool.py
```

### 2.2 从主应用启动

```python
from bt_gui.ocr_test_tool.main_window import OCRTestMainWindow

app = OCRTestMainWindow()
app.mainloop()
```

## 3 功能说明

### 3.1 截图功能

- **全屏截图**: 点击"全屏截图"按钮，自动截取整个屏幕
- **区域截图**: 点击"区域截图"按钮，选择屏幕区域进行截图
- **加载图片**: 点击"加载图片"按钮，从文件加载测试图片

### 3.2 参数调节

#### 预处理参数

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| 放大倍数 | 1.0-5.0 | 2.5 | 图像放大倍数 |
| 对比度增强 | 0.5-5.0 | 2.5 | 对比度增强倍数 |
| 锐化强度 | 0.5-5.0 | 2.0 | 图像锐化强度 |
| 二值化阈值 | 50-200 | 130 | 二值化阈值 |

#### OCR参数

| 参数 | 选项 | 默认值 | 说明 |
|------|------|--------|------|
| 语言 | eng/chi_sim/chi_tra | chi_sim | OCR识别语言 |

#### 测试参数

| 参数 | 说明 |
|------|------|
| 关键词 | 要检测的关键词(逗号分隔) |
| 预期结果 | 预期的识别结果(用于准确率计算) |

### 3.3 测试执行

1. 截图或加载图片
2. 调节参数
3. 输入关键词和预期结果(可选)
4. 点击"开始测试"按钮
5. 查看识别结果和性能统计

### 3.4 配置管理

- **保存配置**: 将当前参数保存到JSON文件
- **加载配置**: 从JSON文件加载参数配置

## 4 使用示例

### 4.1 中文识别测试

1. 截图包含中文文字的区域
2. 设置语言为"chi_sim"
3. 调节放大倍数为3.0
4. 调节对比度为2.0
5. 输入预期结果
6. 点击"开始测试"
7. 查看准确率和耗时

### 4.2 英文识别测试

1. 截图包含英文文字的区域
2. 设置语言为"eng"
3. 调节对比度为1.5
4. 调节锐化为1.5
5. 点击"开始测试"
6. 查看识别结果

### 4.3 数字识别测试

1. 截图包含数字的区域
2. 设置语言为"eng"
3. 输入关键词(可选)
4. 输入预期数字
5. 点击"开始测试"
6. 查看识别结果和准确率

## 5 参数优化建议

### 5.1 中文识别优化

- 增加放大倍数 (2.5-3.5倍)
- 增强对比度 (2.0-3.0倍)
- 多次锐化 (2-3次)
- 调整二值化阈值 (120-140)

### 5.2 英文识别优化

- 适度放大 (1.5-2.0倍)
- 中等对比度 (1.5-2.0倍)
- 单次锐化 (1.0-1.5倍)
- 标准二值化 (120-140)

### 5.3 数字识别优化

- 使用数字白名单
- 提高对比度
- 降低二值化阈值

## 6 注意事项

1. 确保Tesseract OCR已正确安装
2. 确保所需语言包已下载
3. 测试时保持图像清晰
4. 多次测试取平均值
5. 保存最优参数配置

## 7 故障排除

### 7.1 无法启动

- 检查Python版本 (需要3.10+)
- 检查依赖包是否安装
- 检查Tesseract路径

### 7.2 识别失败

- 检查语言包是否安装
- 调整预处理参数
- 尝试不同的PSM模式

### 7.3 准确率低

- 增加放大倍数
- 调整对比度和锐化
- 尝试不同的二值化阈值
```

**Step 2: 提交文档**

```bash
git add doc/OCR测试工具使用指南.md
git commit -m "docs: add OCR test tool user guide"
```

---

## Task 8: 最终测试和验证

**Step 1: 运行所有单元测试**

Run: `pytest tests/ -v`

Expected: 所有测试通过

**Step 2: 启动GUI测试**

Run: `python ocr_test_tool.py`

Expected: GUI窗口成功启动，界面正常显示

**Step 3: 功能测试**

测试以下功能:
- [ ] 全屏截图
- [ ] 加载图片
- [ ] 参数调节
- [ ] 开始测试
- [ ] 结果显示
- [ ] 保存配置
- [ ] 加载配置

**Step 4: 提交最终版本**

```bash
git add .
git commit -m "feat: complete OCR test tool implementation"
```

---

## 执行选项

计划已完成并保存到 `doc/plans/2026-04-11-ocr-test-tool-implementation.md`。

**两种执行方式:**

**1. Subagent-Driven (当前会话)** - 我在当前会话中逐任务派发子代理执行，任务间进行代码审查，快速迭代

**2. Parallel Session (独立会话)** - 打开新会话使用 executing-plans skill，批量执行并设置检查点

**您选择哪种方式?**
