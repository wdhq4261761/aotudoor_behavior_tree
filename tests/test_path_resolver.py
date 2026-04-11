import os
import pytest
from bt_utils.path_resolver import PathResolver

class TestPathResolver:
    def test_to_relative_path(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        os.makedirs(project_root)
        
        resolver = PathResolver(project_root)
        
        absolute_path = os.path.join(project_root, "images", "test.png")
        relative_path = resolver.to_relative(absolute_path)
        
        assert relative_path == "./images/test.png"
    
    def test_to_absolute_path(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        os.makedirs(project_root)
        
        resolver = PathResolver(project_root)
        
        relative_path = "./images/test.png"
        absolute_path = resolver.to_absolute(relative_path)
        
        expected = os.path.join(project_root, "images", "test.png")
        assert os.path.normpath(absolute_path) == os.path.normpath(expected)
    
    def test_is_valid_relative_path(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        os.makedirs(project_root)
        
        test_file = os.path.join(project_root, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        resolver = PathResolver(project_root)
        
        assert resolver.is_valid_relative_path("./test.txt") == True
        assert resolver.is_valid_relative_path("./nonexistent.txt") == False
        assert resolver.is_valid_relative_path("test.txt") == False
