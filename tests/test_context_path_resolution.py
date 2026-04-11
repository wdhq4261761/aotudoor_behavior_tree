import os
import pytest
from bt_core.context import ExecutionContext

class TestContextPathResolution:
    def test_resolve_relative_path(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        os.makedirs(project_root)
        
        context = ExecutionContext(project_root=project_root)
        
        relative_path = "./images/test.png"
        absolute_path = context.resolve_path(relative_path)
        
        expected = os.path.join(project_root, "images", "test.png")
        assert os.path.normpath(absolute_path) == os.path.normpath(expected)
    
    def test_resolve_absolute_path(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        os.makedirs(project_root)
        
        context = ExecutionContext(project_root=project_root)
        
        absolute_path = "C:/some/absolute/path.png"
        result = context.resolve_path(absolute_path)
        
        assert result == absolute_path
    
    def test_default_project_root(self):
        context = ExecutionContext()
        
        assert context.project_root == os.getcwd()
