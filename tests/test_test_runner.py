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
