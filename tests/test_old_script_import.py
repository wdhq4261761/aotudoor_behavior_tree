# -*- coding: utf-8 -*-
"""
测试旧脚本导入功能
"""
import os
import sys
import json
import tempfile
import shutil
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bt_utils.project_manager import ProjectManager
from bt_utils.resource_importer import ResourceImporter


class TestOldScriptImport(unittest.TestCase):
    """测试旧脚本导入功能"""
    
    def setUp(self):
        """创建临时测试目录"""
        self.test_dir = tempfile.mkdtemp()
        
        self.old_script_dir = os.path.join(self.test_dir, "old_project")
        os.makedirs(self.old_script_dir)
        
        self.test_script_content = "@echo off\necho Hello World"
        self.test_script_path = os.path.join(self.old_script_dir, "test_batch.bat")
        with open(self.test_script_path, 'w', encoding='utf-8') as f:
            f.write(self.test_script_content)
        
        self.old_script_data = {
            "version": "2.0",
            "nodes": {
                "node_1": {
                    "id": "node_1",
                    "type": "SequenceNode",
                    "config": {}
                },
                "node_2": {
                    "id": "node_2",
                    "type": "CodeNode",
                    "config": {
                        "code_path": self.test_script_path
                    }
                }
            }
        }
        
        self.old_script_json = os.path.join(self.old_script_dir, "old_tree.json")
        with open(self.old_script_json, 'w', encoding='utf-8') as f:
            json.dump(self.old_script_data, f)
    
    def tearDown(self):
        """清理测试目录"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_migrate_resources_with_dict_nodes(self):
        """测试迁移字典格式的节点资源"""
        from bt_utils.resource_importer import ResourceImporter
        from bt_gui.bt_editor.editor import BehaviorTreeEditor
        
        project_path = os.path.join(self.test_dir, "new_project")
        os.makedirs(project_path)
        
        resource_importer = ResourceImporter(project_path)
        
        def is_resource_path(path):
            if not path:
                return False
            
            resource_extensions = [
                '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff',
                '.wav', '.mp3', '.ogg', '.flac',
                '.py', '.bat', '.cmd', '.sh',
                '.json', '.yaml', '.yml', '.txt', '.csv'
            ]
            
            path_lower = path.lower()
            return any(path_lower.endswith(ext) for ext in resource_extensions)
        
        def resolve_old_path(path, script_dir):
            if os.path.isabs(path):
                return path
            
            if path.startswith('./'):
                relative_path = path[2:]
            else:
                relative_path = path
            
            absolute_path = os.path.join(script_dir, relative_path)
            return os.path.normpath(absolute_path)
        
        def detect_resource_type(key, path):
            path_lower = path.lower()
            
            if any(path_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff']):
                return 'image'
            elif any(path_lower.endswith(ext) for ext in ['.wav', '.mp3', '.ogg', '.flac']):
                return 'audio'
            elif any(path_lower.endswith(ext) for ext in ['.py', '.bat', '.cmd', '.sh', '.ps1']):
                return 'script'
            else:
                if 'image' in key.lower() or 'template' in key.lower() or 'screenshot' in key.lower():
                    return 'image'
                elif 'sound' in key.lower() or 'audio' in key.lower() or 'alarm' in key.lower():
                    return 'audio'
                elif 'script' in key.lower() or 'code' in key.lower():
                    return 'script'
                else:
                    return 'data'
        
        def migrate_resources(data, script_dir, importer):
            if "nodes" in data:
                if isinstance(data["nodes"], dict):
                    for node_id, node in data["nodes"].items():
                        if "config" in node:
                            config = node["config"]
                            
                            for key, value in list(config.items()):
                                if isinstance(value, str) and is_resource_path(value):
                                    absolute_path = resolve_old_path(value, script_dir)
                                    
                                    if absolute_path and os.path.exists(absolute_path):
                                        resource_type = detect_resource_type(key, value)
                                        
                                        try:
                                            new_relative_path = importer.import_resource(absolute_path, resource_type)
                                            config[key] = new_relative_path
                                        except Exception as e:
                                            print(f"导入资源失败 {absolute_path}: {e}")
            return data
        
        updated_data = migrate_resources(
            self.old_script_data.copy(), self.old_script_dir, resource_importer
        )
        
        code_node = updated_data["nodes"]["node_2"]
        new_code_path = code_node["config"]["code_path"]
        
        self.assertTrue(new_code_path.startswith("./scripts/"), f"路径不是相对路径: {new_code_path}")
        
        absolute_path = os.path.join(project_path, new_code_path[2:])
        self.assertTrue(os.path.exists(absolute_path), f"脚本文件未被复制到项目目录: {absolute_path}")
        
        with open(absolute_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, self.test_script_content, "脚本内容不匹配")


if __name__ == '__main__':
    unittest.main()
