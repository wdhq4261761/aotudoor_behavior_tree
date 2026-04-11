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
