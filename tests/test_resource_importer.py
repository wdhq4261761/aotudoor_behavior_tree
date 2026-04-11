import os
import pytest
from bt_utils.resource_importer import ResourceImporter

class TestResourceImporter:
    def test_detect_resource_type_image(self):
        importer = ResourceImporter("/tmp/test")
        
        assert importer._detect_resource_type("test.png") == "image"
        assert importer._detect_resource_type("test.jpg") == "image"
        assert importer._detect_resource_type("test.bmp") == "image"
    
    def test_detect_resource_type_script(self):
        importer = ResourceImporter("/tmp/test")
        
        assert importer._detect_resource_type("test.py") == "script"
        assert importer._detect_resource_type("test.bat") == "script"
    
    def test_detect_resource_type_audio(self):
        importer = ResourceImporter("/tmp/test")
        
        assert importer._detect_resource_type("test.mp3") == "audio"
        assert importer._detect_resource_type("test.wav") == "audio"
    
    def test_import_resource(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        os.makedirs(project_root)
        
        source_file = tmp_path / "source.png"
        source_file.write_text("test image")
        
        importer = ResourceImporter(project_root)
        relative_path = importer.import_resource(str(source_file))
        
        assert relative_path == "./images/templates/source.png"
        
        target_file = os.path.join(project_root, "images", "templates", "source.png")
        assert os.path.exists(target_file)
    
    def test_handle_name_conflict(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        os.makedirs(project_root)
        
        existing_file = os.path.join(project_root, "images", "templates", "test.png")
        os.makedirs(os.path.dirname(existing_file))
        with open(existing_file, 'w') as f:
            f.write("existing")
        
        importer = ResourceImporter(project_root)
        new_filename = importer._handle_name_conflict("images/templates", "test.png")
        
        assert new_filename == "test_2.png"
