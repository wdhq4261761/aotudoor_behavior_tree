# -*- coding: utf-8 -*-
"""
测试中文路径和中文文件名支持
"""
import os
import sys
import json
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bt_utils.project_manager import ProjectManager
from bt_utils.path_resolver import PathResolver
from bt_utils.resource_importer import ResourceImporter
from bt_utils.package_exporter import PackageExporter
from bt_core.serializer import Serializer


class TestChinesePathSupport(unittest.TestCase):
    """测试中文路径和文件名支持"""
    
    def setUp(self):
        """创建临时测试目录"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """清理测试目录"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_chinese_project_name(self):
        """测试中文项目名称"""
        project_name = "测试项目_中文"
        project_path = os.path.join(self.test_dir, project_name)
        
        manager = ProjectManager(project_path)
        manager.create_project(project_name, "这是一个中文描述")
        
        self.assertTrue(os.path.exists(project_path))
        self.assertTrue(os.path.exists(os.path.join(project_path, "project.json")))
        
        config = manager.load_project()
        self.assertEqual(config["project_info"]["name"], project_name)
        self.assertEqual(config["project_info"]["description"], "这是一个中文描述")
    
    def test_chinese_file_name(self):
        """测试中文文件名"""
        project_name = "TestProject"
        project_path = os.path.join(self.test_dir, project_name)
        
        manager = ProjectManager(project_path)
        manager.create_project(project_name)
        
        chinese_file_name = "测试图片_中文.png"
        test_file = os.path.join(self.test_dir, chinese_file_name)
        
        with open(test_file, 'wb') as f:
            f.write(b'fake image data')
        
        importer = ResourceImporter(project_path)
        relative_path = importer.import_resource(test_file, "image")
        
        self.assertTrue(relative_path.startswith("./images/"))
        
        resolver = PathResolver(project_path)
        absolute_path = resolver.to_absolute(relative_path)
        self.assertTrue(os.path.exists(absolute_path))
        self.assertIn("测试图片_中文", absolute_path)
    
    def test_chinese_path_serialization(self):
        """测试中文路径序列化"""
        from bt_nodes.actions.alarm import AlarmNode
        from bt_core.config import NodeConfig
        
        project_name = "测试项目"
        project_path = os.path.join(self.test_dir, project_name)
        os.makedirs(project_path)
        
        test_node = AlarmNode("test_node", NodeConfig())
        test_node.config.set("chinese_path", "./images/测试图片.png")
        test_node.config.set("chinese_name", "测试节点")
        
        tree_data = Serializer.serialize(test_node)
        
        tree_file = os.path.join(project_path, "tree.json")
        Serializer.save_to_file(test_node, tree_file, format="json")
        
        loaded_node, _, _ = Serializer.load_from_file(tree_file)
        
        self.assertEqual(loaded_node.config.get("chinese_path"), "./images/测试图片.png")
        self.assertEqual(loaded_node.config.get("chinese_name"), "测试节点")
    
    def test_chinese_project_export(self):
        """测试中文项目导出"""
        project_name = "导出测试项目"
        project_path = os.path.join(self.test_dir, project_name)
        
        manager = ProjectManager(project_path)
        manager.create_project(project_name, "测试导出功能")
        
        chinese_file_name = "中文文件.txt"
        test_file = os.path.join(self.test_dir, chinese_file_name)
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("测试内容")
        
        importer = ResourceImporter(project_path)
        importer.import_resource(test_file, "data")
        
        tree_data = {
            "name": "测试行为树",
            "nodes": [],
            "connections": []
        }
        manager.save_project(tree_data)
        
        zip_path = os.path.join(self.test_dir, "测试导出.zip")
        exporter = PackageExporter(project_path)
        result_path = exporter.export_to_zip(zip_path)
        
        self.assertTrue(os.path.exists(result_path))
        
        import zipfile
        with zipfile.ZipFile(result_path, 'r') as zipf:
            namelist = zipf.namelist()
            self.assertTrue(any("中文文件" in name for name in namelist))
    
    def test_chinese_json_content(self):
        """测试JSON文件中文内容"""
        project_name = "JSON测试"
        project_path = os.path.join(self.test_dir, project_name)
        
        manager = ProjectManager(project_path)
        manager.create_project(project_name, "测试JSON中文支持")
        
        project_file = os.path.join(project_path, "project.json")
        with open(project_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data["project_info"]["name"], project_name)
        self.assertEqual(data["project_info"]["description"], "测试JSON中文支持")
        
        data["project_info"]["extra_field"] = "额外的中文字段"
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(project_file, 'r', encoding='utf-8') as f:
            reloaded = json.load(f)
        
        self.assertEqual(reloaded["project_info"]["extra_field"], "额外的中文字段")


if __name__ == '__main__':
    unittest.main()
