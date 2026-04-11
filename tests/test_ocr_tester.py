import pytest
from PIL import Image
from unittest.mock import Mock, patch, MagicMock
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
    @patch('bt_utils.ocr_tester.ImagePreprocessor')
    def test_test_text_recognition_success(self, mock_preprocessor_class, mock_ocr_manager_class):
        """测试文本识别成功"""
        mock_preprocessor = Mock()
        mock_preprocessor.preprocess_with_params.return_value = Image.new('RGB', (100, 100))
        mock_preprocessor_class.return_value = mock_preprocessor
        
        mock_ocr_manager = Mock()
        mock_ocr_manager.recognize.return_value = (True, (100, 200))
        mock_ocr_manager.get_all_text.return_value = "测试文本"
        mock_ocr_manager_class.return_value = mock_ocr_manager
        
        tester = OCRTester()
        image = Image.new('RGB', (100, 100), color='white')
        result = tester.test_text_recognition(
            image,
            keywords="测试",
            language="chi_sim"
        )
        
        assert result.success is True
        assert result.position == (100, 200)
        
    @patch('bt_utils.ocr_tester.OCRManager')
    @patch('bt_utils.ocr_tester.ImagePreprocessor')
    def test_test_text_recognition_failure(self, mock_preprocessor_class, mock_ocr_manager_class):
        """测试文本识别失败"""
        mock_preprocessor = Mock()
        mock_preprocessor.preprocess_with_params.return_value = Image.new('RGB', (100, 100))
        mock_preprocessor_class.return_value = mock_preprocessor
        
        mock_ocr_manager = Mock()
        mock_ocr_manager.recognize.return_value = (False, None)
        mock_ocr_manager.get_all_text.return_value = ""
        mock_ocr_manager_class.return_value = mock_ocr_manager
        
        tester = OCRTester()
        image = Image.new('RGB', (100, 100), color='white')
        result = tester.test_text_recognition(
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
        
    def test_calculate_accuracy_partial_match(self):
        """测试准确率计算 - 部分匹配"""
        accuracy = self.tester.calculate_accuracy("测试文本", "测试")
        
        assert 0.0 < accuracy < 1.0
