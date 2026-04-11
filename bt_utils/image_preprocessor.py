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
