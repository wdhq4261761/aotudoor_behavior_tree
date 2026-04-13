import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional, List


class ImageProcessor:
    """图像处理器

    提供模板匹配、颜色检测和图像哈希识别功能。
    """

    @staticmethod
    def find_template(source: Image.Image, template: Image.Image,
                      threshold: float = 0.8) -> Tuple[bool, Optional[Tuple[int, int]], float]:
        """模板匹配

        Args:
            source: 源图像
            template: 模板图像
            threshold: 匹配阈值

        Returns:
            (是否找到, 中心位置, 最高置信度) 元组
        """
        source_array = np.array(source)
        template_array = np.array(template)

        if source_array.shape[2] == 4:
            source_array = cv2.cvtColor(source_array, cv2.COLOR_RGBA2RGB)
        if template_array.shape[2] == 4:
            template_array = cv2.cvtColor(template_array, cv2.COLOR_RGBA2RGB)

        source_gray = cv2.cvtColor(source_array, cv2.COLOR_RGB2GRAY)
        template_gray = cv2.cvtColor(template_array, cv2.COLOR_RGB2GRAY)

        result = cv2.matchTemplate(source_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template_gray.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return True, (center_x, center_y), max_val

        return False, None, max_val

    @staticmethod
    def find_color(source: Image.Image, target_color: Tuple[int, int, int],
                   tolerance: int = 10) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """颜色检测

        Args:
            source: 源图像
            target_color: 目标颜色 (R, G, B)
            tolerance: 容差

        Returns:
            (是否找到, 中心位置) 元组
        """
        source_array = np.array(source)

        lower = np.array([max(0, c - tolerance) for c in target_color])
        upper = np.array([min(255, c + tolerance) for c in target_color])

        mask = cv2.inRange(source_array[:, :, :3], lower, upper)

        positions = np.where(mask > 0)

        if len(positions[0]) > 0:
            center_x = int(np.mean(positions[1]))
            center_y = int(np.mean(positions[0]))
            return True, (center_x, center_y)

        return False, None

    @staticmethod
    def find_color_with_count(source: Image.Image, target_color: Tuple[int, int, int],
                              tolerance: int = 10) -> Tuple[bool, Optional[Tuple[int, int]], int]:
        """颜色检测（返回匹配像素数）

        Args:
            source: 源图像
            target_color: 目标颜色 (R, G, B)
            tolerance: 容差

        Returns:
            (是否找到, 中心位置, 匹配像素数) 元组
        """
        source_array = np.array(source)

        lower = np.array([max(0, c - tolerance) for c in target_color])
        upper = np.array([min(255, c + tolerance) for c in target_color])

        mask = cv2.inRange(source_array[:, :, :3], lower, upper)

        positions = np.where(mask > 0)
        match_count = len(positions[0])

        if match_count > 0:
            center_x = int(np.mean(positions[1]))
            center_y = int(np.mean(positions[0]))
            return True, (center_x, center_y), match_count

        return False, None, 0

    @staticmethod
    def compute_phash(image: Image.Image, hash_size: int = 8) -> str:
        """计算感知哈希

        Args:
            image: PIL.Image 图像
            hash_size: 哈希大小

        Returns:
            哈希字符串
        """
        img_array = np.array(image.convert('L').resize((hash_size + 1, hash_size)))
        
        diff = img_array[:, 1:] > img_array[:, :-1]
        
        return ''.join(['1' if b else '0' for b in diff.flatten()])

    @staticmethod
    def compute_dhash(image: Image.Image, hash_size: int = 8) -> str:
        """计算差异哈希

        Args:
            image: PIL.Image 图像
            hash_size: 哈希大小

        Returns:
            哈希字符串
        """
        img_array = np.array(image.convert('L').resize((hash_size + 1, hash_size)))
        
        diff = img_array[:, 1:] > img_array[:, :-1]
        
        return ''.join(['1' if b else '0' for b in diff.flatten()])

    @staticmethod
    def compute_ahash(image: Image.Image, hash_size: int = 8) -> str:
        """计算平均哈希

        Args:
            image: PIL.Image 图像
            hash_size: 哈希大小

        Returns:
            哈希字符串
        """
        img_array = np.array(image.convert('L').resize((hash_size, hash_size)))
        
        avg = img_array.mean()
        
        diff = img_array > avg
        
        return ''.join(['1' if b else '0' for b in diff.flatten()])

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """计算汉明距离

        Args:
            hash1: 哈希字符串1
            hash2: 哈希字符串2

        Returns:
            汉明距离
        """
        if len(hash1) != len(hash2):
            return -1
        
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    @staticmethod
    def find_by_hash(source: Image.Image, templates: List[Image.Image],
                    threshold: float = 5, hash_type: str = "phash") -> Tuple[bool, Optional[Tuple[int, int]], Optional[int]]:
        """基于哈希的图像查找

        Args:
            source: 源图像
            templates: 模板图像列表
            threshold: 最大汉明距离阈值
            hash_type: 哈希类型 (phash/dhash/ahash)

        Returns:
            (是否找到, 中心位置, 最佳匹配索引) 元组
        """
        if hash_type == "phash":
            hash_func = ImageProcessor.compute_phash
        elif hash_type == "dhash":
            hash_func = ImageProcessor.compute_dhash
        else:
            hash_func = ImageProcessor.compute_ahash

        source_array = np.array(source)
        h, w = source_array.shape[:2]
        
        best_match = None
        best_distance = threshold + 1
        best_index = None

        for idx, template in enumerate(templates):
            template_hash = hash_func(template)
            
            template_array = np.array(template)
            th, tw = template_array.shape[:2]
            
            for y in range(0, h - th + 1, max(1, (h - th) // 10)):
                for x in range(0, w - tw + 1, max(1, (w - tw) // 10)):
                    region = source.crop((x, y, x + tw, y + th))
                    source_hash = hash_func(region)
                    
                    distance = ImageProcessor.hamming_distance(source_hash, template_hash)
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_match = (x + tw // 2, y + th // 2)
                        best_index = idx
                        
                        if distance == 0:
                            return True, best_match, best_index

        if best_match:
            return True, best_match, best_index

        return False, None, None
