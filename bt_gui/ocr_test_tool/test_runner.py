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
