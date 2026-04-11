import json
import os
from typing import Dict, Any, Tuple, List
import copy


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
        return copy.deepcopy(self.DEFAULT_PARAMS)
    
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
