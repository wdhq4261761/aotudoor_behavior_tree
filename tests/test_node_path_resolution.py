# -*- coding: utf-8 -*-
"""
测试节点路径解析功能
"""
import os
import sys
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bt_core.context import ExecutionContext
from bt_nodes.actions.code import CodeNode
from bt_nodes.conditions.image import ImageConditionNode
from bt_nodes.actions.script import ScriptNode
from bt_core.config import NodeConfig


class TestNodePathResolution(unittest.TestCase):
    """测试节点路径解析功能"""
    
    def setUp(self):
        """创建临时测试目录"""
        self.test_dir = tempfile.mkdtemp()
        
        self.project_dir = os.path.join(self.test_dir, "test_project")
        os.makedirs(self.project_dir)
        
        self.script_dir = os.path.join(self.project_dir, "scripts")
        os.makedirs(self.script_dir)
        
        self.test_script = os.path.join(self.script_dir, "test.bat")
        with open(self.test_script, 'w') as f:
            f.write("@echo off\necho Test Script")
        
        self.image_dir = os.path.join(self.project_dir, "images")
        os.makedirs(self.image_dir)
        
        self.test_image = os.path.join(self.image_dir, "test.png")
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.test_image)
    
    def tearDown(self):
        """清理测试目录"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_code_node_relative_path(self):
        """测试代码节点相对路径解析"""
        context = ExecutionContext(project_root=self.project_dir)
        
        config = NodeConfig()
        config.set("code_path", "./scripts/test.bat")
        
        code_node = CodeNode("test_code", config)
        
        result = code_node._execute_action(context)
        
        self.assertEqual(result.name, "SUCCESS")
    
    def test_code_node_absolute_path(self):
        """测试代码节点绝对路径"""
        context = ExecutionContext()
        
        config = NodeConfig()
        config.set("code_path", self.test_script)
        
        code_node = CodeNode("test_code", config)
        
        result = code_node._execute_action(context)
        
        self.assertEqual(result.name, "SUCCESS")
    
    def test_image_node_relative_path(self):
        """测试图像节点相对路径解析"""
        context = ExecutionContext(project_root=self.project_dir)
        
        config = NodeConfig()
        config.set("template_path", "./images/test.png")
        
        image_node = ImageConditionNode("test_image", config)
        
        result = image_node._check_condition(context)
        
        self.assertTrue(result)
    
    def test_script_node_relative_path(self):
        """测试脚本节点相对路径解析"""
        context = ExecutionContext(project_root=self.project_dir)
        
        config = NodeConfig()
        config.set("script_path", "./scripts/test.bat")
        
        script_node = ScriptNode("test_script", config)
        
        result = script_node._execute_action(context)
        
        self.assertEqual(result.name, "SUCCESS")


if __name__ == '__main__':
    unittest.main()
