import os
import json
import pytest
from bt_utils.project_manager import ProjectManager

class TestProjectManager:
    def test_create_project(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        
        manager = ProjectManager(project_root)
        manager.create_project("MyProject", "Test project")
        
        assert os.path.exists(project_root)
        assert os.path.exists(os.path.join(project_root, "project.json"))
        assert os.path.exists(os.path.join(project_root, "tree.json"))
        
        with open(os.path.join(project_root, "project.json"), 'r') as f:
            config = json.load(f)
            assert config["project_info"]["name"] == "MyProject"
    
    def test_load_project(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        
        manager = ProjectManager(project_root)
        manager.create_project("MyProject", "Test project")
        
        config = manager.load_project()
        
        assert config["project_info"]["name"] == "MyProject"
    
    def test_save_project(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        
        manager = ProjectManager(project_root)
        manager.create_project("MyProject", "Test project")
        
        tree_data = {"nodes": {}, "connections": []}
        manager.save_project(tree_data)
        
        with open(os.path.join(project_root, "tree.json"), 'r') as f:
            saved_data = json.load(f)
            assert "nodes" in saved_data
    
    def test_validate_project(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        
        manager = ProjectManager(project_root)
        manager.create_project("MyProject", "Test project")
        
        is_valid = manager.validate_project()
        assert is_valid == True
        
        os.remove(os.path.join(project_root, "project.json"))
        is_valid = manager.validate_project()
        assert is_valid == False
