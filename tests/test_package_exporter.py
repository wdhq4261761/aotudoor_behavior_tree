import os
import zipfile
import pytest
from bt_utils.package_exporter import PackageExporter
from bt_utils.project_manager import ProjectManager

class TestPackageExporter:
    def test_export_to_zip(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        output_path = str(tmp_path / "MyProject.zip")
        
        manager = ProjectManager(project_root)
        manager.create_project("MyProject", "Test project")
        
        exporter = PackageExporter(project_root)
        zip_path = exporter.export_to_zip(output_path)
        
        assert os.path.exists(zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            namelist = zipf.namelist()
            assert any("project.json" in name for name in namelist)
            assert any("tree.json" in name for name in namelist)
    
    def test_exclude_temp_files(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        output_path = str(tmp_path / "MyProject.zip")
        
        manager = ProjectManager(project_root)
        manager.create_project("MyProject", "Test project")
        
        pyc_file = os.path.join(project_root, "test.pyc")
        with open(pyc_file, 'w') as f:
            f.write("test")
        
        exporter = PackageExporter(project_root)
        zip_path = exporter.export_to_zip(output_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            namelist = zipf.namelist()
            assert not any(".pyc" in name for name in namelist)
    
    def test_generate_readme(self, tmp_path):
        project_root = str(tmp_path / "MyProject")
        output_path = str(tmp_path / "MyProject.zip")
        
        manager = ProjectManager(project_root)
        manager.create_project("MyProject", "Test project")
        
        exporter = PackageExporter(project_root)
        zip_path = exporter.export_to_zip(output_path)
        
        readme_path = os.path.splitext(zip_path)[0] + "_使用说明.txt"
        assert os.path.exists(readme_path)
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "MyProject" in content
            assert "使用说明" in content
