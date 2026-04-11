import os
import tempfile
import shutil
from bt_utils.project_manager import ProjectManager
from bt_utils.resource_importer import ResourceImporter
from bt_utils.package_exporter import PackageExporter
from bt_core.context import ExecutionContext

def test_complete_project_workflow():
    """测试完整的项目工作流程"""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_name = "TestProject"
        project_root = os.path.join(tmp_dir, project_name)
        
        print(f"1. 创建项目: {project_root}")
        manager = ProjectManager(project_root)
        manager.create_project(project_name, "测试项目")
        
        assert os.path.exists(project_root)
        assert os.path.exists(os.path.join(project_root, "project.json"))
        assert os.path.exists(os.path.join(project_root, "tree.json"))
        print("[OK] 项目创建成功")
        
        print("2. 导入资源文件")
        test_image = os.path.join(tmp_dir, "test_image.png")
        with open(test_image, 'w') as f:
            f.write("fake image content")
        
        importer = ResourceImporter(project_root)
        relative_path = importer.import_resource(test_image)
        
        assert relative_path == "./images/templates/test_image.png"
        assert os.path.exists(os.path.join(project_root, "images", "templates", "test_image.png"))
        print(f"[OK] 资源导入成功: {relative_path}")
        
        print("3. 保存项目")
        tree_data = {
            "version": "2.0",
            "format_type": "behavior_tree_editor",
            "root_node": None,
            "nodes": {},
            "connections": []
        }
        manager.save_project(tree_data)
        
        assert os.path.exists(os.path.join(project_root, "tree.json"))
        print("[OK] 项目保存成功")
        
        print("4. 加载项目")
        config = manager.load_project()
        assert config["project_info"]["name"] == project_name
        print(f"[OK] 项目加载成功: {config['project_info']['name']}")
        
        print("5. 导出项目为 ZIP")
        exporter = PackageExporter(project_root)
        zip_path = os.path.join(tmp_dir, f"{project_name}.zip")
        result_path = exporter.export_to_zip(zip_path)
        
        assert os.path.exists(result_path)
        assert os.path.exists(os.path.splitext(result_path)[0] + "_使用说明.txt")
        print(f"[OK] 项目导出成功: {result_path}")
        
        print("6. 测试路径解析")
        context = ExecutionContext(project_root=project_root)
        abs_path = context.resolve_path(relative_path)
        
        expected = os.path.join(project_root, "images", "templates", "test_image.png")
        assert os.path.normpath(abs_path) == os.path.normpath(expected)
        print(f"[OK] 路径解析成功: {relative_path} -> {abs_path}")
        
        print("\n所有测试通过! [OK]")

if __name__ == "__main__":
    test_complete_project_workflow()
