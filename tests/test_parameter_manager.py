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
