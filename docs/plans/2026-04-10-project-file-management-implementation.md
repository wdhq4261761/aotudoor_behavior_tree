# 项目工程文件管理系统实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 AutoDoor 行为树系统实现完整的项目工程文件管理功能,包括项目文件夹管理、资源引用、打包导出等核心功能。

**Architecture:** 采用分层架构,在现有 bt_core、bt_utils、bt_gui 模块基础上新增项目管理模块。核心组件包括 PathResolver(路径解析)、ResourceImporter(资源导入)、PackageExporter(打包导出)、ProjectManager(项目管理)。

**Tech Stack:** Python 3.10+, os, shutil, zipfile, json, CustomTkinter

---

## 实施阶段概览

**第一阶段(核心功能)**: 项目文件夹创建和管理、资源导入和相对路径引用、项目保存和加载
**第二阶段(增强功能)**: 项目打包导出、自动备份机制、资源管理面板
**第三阶段(优化功能)**: 最近打开列表、项目完整性验证、用户界面优化

---

## 第一阶段:核心功能

### Task 1: 实现 PathResolver 核心类

**Files:**
- Create: `bt_utils/path_resolver.py`
- Test: `tests/test_path_resolver.py`

**Step 1: 创建测试文件并编写测试用例**

```python
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
```

**Step 2: 运行测试验证失败**

Run: `pytest tests/test_path_resolver.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'bt_utils.path_resolver'"

**Step 3: 实现 PathResolver 类**

```python
import os

class PathResolver:
    """资源路径解析器"""
    
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
    
    def to_relative(self, absolute_path: str) -> str:
        """
        将绝对路径转换为相对路径
        
        Args:
            absolute_path: 资源的绝对路径
        
        Returns:
            相对于项目根目录的相对路径
        """
        abs_path = os.path.abspath(absolute_path)
        rel_path = os.path.relpath(abs_path, self.project_root)
        return f"./{rel_path.replace(os.sep, '/')}"
    
    def to_absolute(self, relative_path: str) -> str:
        """
        将相对路径转换为绝对路径
        
        Args:
            relative_path: 相对于项目根目录的相对路径
        
        Returns:
            资源的绝对路径
        """
        if relative_path.startswith("./"):
            relative_path = relative_path[2:]
        
        abs_path = os.path.join(self.project_root, relative_path)
        return os.path.normpath(abs_path)
    
    def is_valid_relative_path(self, path: str) -> bool:
        """
        检查相对路径是否有效
        
        Args:
            path: 待检查的路径
        
        Returns:
            是否为有效的相对路径
        """
        if not path.startswith("./"):
            return False
        
        abs_path = self.to_absolute(path)
        
        if not os.path.exists(abs_path):
            return False
        
        real_abs_path = os.path.realpath(abs_path)
        real_project_root = os.path.realpath(self.project_root)
        
        return real_abs_path.startswith(real_project_root)
```

**Step 4: 运行测试验证通过**

Run: `pytest tests/test_path_resolver.py -v`
Expected: PASS

**Step 5: 提交代码**

```bash
git add tests/test_path_resolver.py bt_utils/path_resolver.py
git commit -m "feat: add PathResolver for relative/absolute path conversion"
```

---

### Task 2: 实现 ResourceImporter 资源导入类

**Files:**
- Create: `bt_utils/resource_importer.py`
- Test: `tests/test_resource_importer.py`

**Step 1: 创建测试文件并编写测试用例**

```python
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
```

**Step 2: 运行测试验证失败**

Run: `pytest tests/test_resource_importer.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'bt_utils.resource_importer'"

**Step 3: 实现 ResourceImporter 类**

```python
import os
import shutil
from typing import Optional
from bt_utils.path_resolver import PathResolver

class ResourceImporter:
    """资源导入管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.resolver = PathResolver(project_root)
    
    def import_resource(self, source_path: str, resource_type: str = None) -> str:
        """
        导入资源文件到项目目录
        
        Args:
            source_path: 源文件路径
            resource_type: 资源类型
        
        Returns:
            相对路径引用
        """
        if resource_type is None:
            resource_type = self._detect_resource_type(source_path)
        
        target_dir = self._get_target_directory(resource_type)
        filename = os.path.basename(source_path)
        filename = self._handle_name_conflict(target_dir, filename)
        
        target_path = os.path.join(self.project_root, target_dir, filename)
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(source_path, target_path)
        
        return self.resolver.to_relative(target_path)
    
    def _detect_resource_type(self, path: str) -> str:
        """检测资源类型"""
        ext = os.path.splitext(path)[1].lower()
        
        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            return 'image'
        elif ext in ['.py', '.bat', '.sh', '.ps1']:
            return 'script'
        elif ext in ['.mp3', '.wav', '.ogg', '.flac']:
            return 'audio'
        elif ext in ['.json', '.yaml', '.xml', '.txt']:
            return 'data'
        else:
            return 'other'
    
    def _get_target_directory(self, resource_type: str) -> str:
        """获取目标存储目录"""
        type_dir_map = {
            'image': 'images/templates',
            'script': 'scripts/python',
            'audio': 'audio/alarms',
            'data': 'data/config',
            'other': 'data/other'
        }
        return type_dir_map.get(resource_type, 'data/other')
    
    def _handle_name_conflict(self, target_dir: str, filename: str) -> str:
        """处理文件名冲突"""
        target_path = os.path.join(self.project_root, target_dir, filename)
        
        if not os.path.exists(target_path):
            return filename
        
        name, ext = os.path.splitext(filename)
        counter = 2
        
        while os.path.exists(target_path):
            new_filename = f"{name}_{counter}{ext}"
            target_path = os.path.join(self.project_root, target_dir, new_filename)
            counter += 1
        
        return new_filename
```

**Step 4: 运行测试验证通过**

Run: `pytest tests/test_resource_importer.py -v`
Expected: PASS

**Step 5: 提交代码**

```bash
git add tests/test_resource_importer.py bt_utils/resource_importer.py
git commit -m "feat: add ResourceImporter for automatic resource file management"
```

---

### Task 3: 实现 ProjectManager 项目管理类

**Files:**
- Create: `bt_utils/project_manager.py`
- Test: `tests/test_project_manager.py`

**Step 1: 创建测试文件并编写测试用例**

```python
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
```

**Step 2: 运行测试验证失败**

Run: `pytest tests/test_project_manager.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'bt_utils.project_manager'"

**Step 3: 实现 ProjectManager 类**

```python
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from bt_utils.path_resolver import PathResolver
from bt_utils.resource_importer import ResourceImporter

class ProjectManager:
    """项目管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.path_resolver = PathResolver(project_root)
        self.resource_importer = ResourceImporter(project_root)
    
    def create_project(self, name: str, description: str = "") -> None:
        """
        创建新项目
        
        Args:
            name: 项目名称
            description: 项目描述
        """
        os.makedirs(self.project_root, exist_ok=True)
        
        dirs = [
            "images/templates",
            "images/screenshots",
            "scripts/python",
            "scripts/batch",
            "audio/alarms",
            "data/config",
            "docs"
        ]
        
        for dir_path in dirs:
            os.makedirs(os.path.join(self.project_root, dir_path), exist_ok=True)
        
        project_config = {
            "version": "1.0",
            "format_type": "behavior_tree_project",
            "project_info": {
                "name": name,
                "description": description,
                "author": "",
                "created_at": datetime.now().isoformat(),
                "modified_at": datetime.now().isoformat(),
                "app_version": "1.0.0"
            },
            "main_tree": "tree.json",
            "resources": {
                "images": [],
                "scripts": [],
                "audio": []
            }
        }
        
        with open(os.path.join(self.project_root, "project.json"), 'w', encoding='utf-8') as f:
            json.dump(project_config, f, indent=2, ensure_ascii=False)
        
        tree_data = {
            "version": "2.0",
            "format_type": "behavior_tree_editor",
            "root_node": None,
            "nodes": {},
            "connections": []
        }
        
        with open(os.path.join(self.project_root, "tree.json"), 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, indent=2, ensure_ascii=False)
    
    def load_project(self) -> Dict[str, Any]:
        """
        加载项目配置
        
        Returns:
            项目配置字典
        """
        project_file = os.path.join(self.project_root, "project.json")
        
        if not os.path.exists(project_file):
            raise FileNotFoundError(f"项目配置文件不存在: {project_file}")
        
        with open(project_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_project(self, tree_data: Dict[str, Any]) -> None:
        """
        保存项目
        
        Args:
            tree_data: 行为树数据
        """
        tree_file = os.path.join(self.project_root, "tree.json")
        
        self._create_backup()
        
        with open(tree_file, 'w', encoding='utf-8') as f:
            json.dump(tree_data, f, indent=2, ensure_ascii=False)
        
        project_config = self.load_project()
        project_config["project_info"]["modified_at"] = datetime.now().isoformat()
        
        with open(os.path.join(self.project_root, "project.json"), 'w', encoding='utf-8') as f:
            json.dump(project_config, f, indent=2, ensure_ascii=False)
    
    def validate_project(self) -> bool:
        """
        验证项目完整性
        
        Returns:
            项目是否有效
        """
        required_files = ["project.json", "tree.json"]
        
        for filename in required_files:
            if not os.path.exists(os.path.join(self.project_root, filename)):
                return False
        
        return True
    
    def _create_backup(self) -> None:
        """创建备份文件"""
        tree_file = os.path.join(self.project_root, "tree.json")
        
        if not os.path.exists(tree_file):
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(
            self.project_root,
            f"tree_backup_{timestamp}.json"
        )
        
        import shutil
        shutil.copy2(tree_file, backup_file)
        
        self._clean_old_backups()
    
    def _clean_old_backups(self, keep_count: int = 5) -> None:
        """清理旧备份文件"""
        backup_files = []
        
        for filename in os.listdir(self.project_root):
            if filename.startswith("tree_backup_") and filename.endswith(".json"):
                backup_files.append(os.path.join(self.project_root, filename))
        
        backup_files.sort(key=os.path.getmtime, reverse=True)
        
        for old_backup in backup_files[keep_count:]:
            os.remove(old_backup)
```

**Step 4: 运行测试验证通过**

Run: `pytest tests/test_project_manager.py -v`
Expected: PASS

**Step 5: 提交代码**

```bash
git add tests/test_project_manager.py bt_utils/project_manager.py
git commit -m "feat: add ProjectManager for project lifecycle management"
```

---

### Task 4: 扩展 ExecutionContext 支持路径解析

**Files:**
- Modify: `bt_core/context.py:1-50`
- Test: `tests/test_context_path_resolution.py`

**Step 1: 创建测试文件**

```python
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
        
        absolute_path = "/some/absolute/path.png"
        result = context.resolve_path(absolute_path)
        
        assert result == absolute_path
```

**Step 2: 运行测试验证失败**

Run: `pytest tests/test_context_path_resolution.py -v`
Expected: FAIL with "AttributeError: 'ExecutionContext' object has no attribute 'resolve_path'"

**Step 3: 修改 ExecutionContext 类**

在 `bt_core/context.py` 中添加:

```python
from bt_utils.path_resolver import PathResolver

class ExecutionContext:
    def __init__(self, project_root: str = None):
        self.blackboard = Blackboard()
        self.elapsed_time = 0.0
        self.tick_count = 0
        self.project_root = project_root or os.getcwd()
        self.path_resolver = PathResolver(self.project_root)
        
        # ... 其他初始化代码
    
    def resolve_path(self, relative_path: str) -> str:
        """
        解析相对路径为绝对路径
        
        Args:
            relative_path: 相对路径
        
        Returns:
            绝对路径
        """
        if relative_path.startswith("./"):
            return self.path_resolver.to_absolute(relative_path)
        return relative_path
```

**Step 4: 运行测试验证通过**

Run: `pytest tests/test_context_path_resolution.py -v`
Expected: PASS

**Step 5: 提交代码**

```bash
git add tests/test_context_path_resolution.py bt_core/context.py
git commit -m "feat: extend ExecutionContext with path resolution support"
```

---

## 第二阶段:增强功能

### Task 5: 实现 PackageExporter 打包导出类

**Files:**
- Create: `bt_utils/package_exporter.py`
- Test: `tests/test_package_exporter.py`

**Step 1: 创建测试文件**

```python
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
```

**Step 2: 运行测试验证失败**

Run: `pytest tests/test_package_exporter.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'bt_utils.package_exporter'"

**Step 3: 实现 PackageExporter 类**

```python
import os
import zipfile
from datetime import datetime

class PackageExporter:
    """项目打包导出器"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
    
    def export_to_zip(self, output_path: str = None) -> str:
        """
        导出项目为 ZIP 文件
        
        Args:
            output_path: 输出路径(可选)
        
        Returns:
            ZIP 文件路径
        """
        if output_path is None:
            project_name = os.path.basename(self.project_root)
            output_path = f"{project_name}.zip"
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.project_root):
                # 排除临时文件夹
                dirs[:] = [d for d in dirs if d not in ['.metadata', '__pycache__']]
                
                for file in files:
                    # 排除临时文件
                    if file.endswith(('.pyc', '.pyo', '.tmp')):
                        continue
                    
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(self.project_root))
                    zipf.write(file_path, arcname)
        
        # 生成使用说明
        self._generate_readme(output_path)
        
        return output_path
    
    def _generate_readme(self, zip_path: str):
        """生成使用说明"""
        project_name = os.path.basename(self.project_root)
        readme_content = f"""# {project_name} 使用说明

## 如何使用
1. 解压 ZIP 文件到任意目录
2. 打开 AutoDoor 行为树编辑器
3. 选择"文件" -> "打开项目"
4. 选择解压后的文件夹
5. 点击"开始运行"按钮

## 文件说明
- project.json: 项目配置
- tree.json: 行为树定义
- images/: 图像资源
- scripts/: 脚本文件
- audio/: 音频文件

## 注意事项
- 解压后请保持文件夹结构完整
- 不要单独移动或删除资源文件
"""
        readme_path = os.path.splitext(zip_path)[0] + "_使用说明.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
```

**Step 4: 运行测试验证通过**

Run: `pytest tests/test_package_exporter.py -v`
Expected: PASS

**Step 5: 提交代码**

```bash
git add tests/test_package_exporter.py bt_utils/package_exporter.py
git commit -m "feat: add PackageExporter for project ZIP export"
```

---

## 第三阶段:用户界面集成

### Task 6: 在编辑器中集成项目管理功能

**Files:**
- Modify: `bt_gui/bt_editor/editor.py`
- Modify: `bt_gui/app.py`

**Step 1: 在 editor.py 中添加项目管理方法**

在 `BehaviorTreeEditor` 类中添加:

```python
from bt_utils.project_manager import ProjectManager

class BehaviorTreeEditor(CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.project_manager = None
        self.project_root = None
        # ... 其他初始化代码
    
    def new_project(self, name: str, location: str, description: str = ""):
        """创建新项目"""
        self.project_root = os.path.join(location, name)
        self.project_manager = ProjectManager(self.project_root)
        self.project_manager.create_project(name, description)
        
        # 清空画布
        self.canvas.clear_canvas()
        
        # 更新标题
        self._update_title(name)
    
    def open_project(self, project_root: str):
        """打开项目"""
        self.project_root = project_root
        self.project_manager = ProjectManager(project_root)
        
        if not self.project_manager.validate_project():
            raise ValueError("项目文件不完整或损坏")
        
        # 加载项目配置
        config = self.project_manager.load_project()
        
        # 加载行为树
        tree_file = os.path.join(project_root, "tree.json")
        self.load_tree(tree_file)
        
        # 更新标题
        self._update_title(config["project_info"]["name"])
    
    def save_project(self):
        """保存项目"""
        if not self.project_manager:
            raise RuntimeError("未打开项目")
        
        tree_data = self.canvas.get_tree_data()
        self.project_manager.save_project(tree_data)
    
    def export_project(self, output_path: str = None):
        """导出项目"""
        if not self.project_manager:
            raise RuntimeError("未打开项目")
        
        from bt_utils.package_exporter import PackageExporter
        exporter = PackageExporter(self.project_root)
        return exporter.export_to_zip(output_path)
    
    def _update_title(self, project_name: str):
        """更新窗口标题"""
        self.winfo_toplevel().title(f"AutoDoor 行为树编辑器 - {project_name}")
```

**Step 2: 在 app.py 中添加菜单项**

在 `BehaviorTreeApp` 类中添加:

```python
def _create_menu(self):
    """创建菜单"""
    menubar = Menu(self)
    
    file_menu = Menu(menubar, tearoff=0)
    file_menu.add_command(label="新建项目", command=self._new_project, accelerator="Ctrl+N")
    file_menu.add_command(label="打开项目", command=self._open_project, accelerator="Ctrl+O")
    file_menu.add_separator()
    file_menu.add_command(label="保存", command=self._save, accelerator="Ctrl+S")
    file_menu.add_command(label="另存为", command=self._save_as, accelerator="Ctrl+Shift+S")
    file_menu.add_separator()
    file_menu.add_command(label="导出项目", command=self._export_project, accelerator="Ctrl+E")
    file_menu.add_separator()
    file_menu.add_command(label="退出", command=self.quit)
    
    menubar.add_cascade(label="文件", menu=file_menu)
    
    self.config(menu=menubar)

def _new_project(self):
    """新建项目"""
    from bt_gui.dialogs.new_project_dialog import NewProjectDialog
    
    dialog = NewProjectDialog(self)
    self.wait_window(dialog)
    
    if dialog.result:
        self.behavior_tree.new_project(
            name=dialog.result["name"],
            location=dialog.result["location"],
            description=dialog.result.get("description", "")
        )

def _open_project(self):
    """打开项目"""
    from tkinter import filedialog
    
    project_root = filedialog.askdirectory(title="选择项目文件夹")
    if project_root:
        try:
            self.behavior_tree.open_project(project_root)
        except Exception as e:
            messagebox.showerror("错误", f"打开项目失败: {str(e)}")

def _export_project(self):
    """导出项目"""
    from tkinter import filedialog
    
    output_path = filedialog.asksaveasfilename(
        title="导出项目",
        defaultextension=".zip",
        filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
    )
    
    if output_path:
        try:
            zip_path = self.behavior_tree.export_project(output_path)
            messagebox.showinfo("成功", f"项目已导出到:\n{zip_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
```

**Step 3: 测试集成功能**

手动测试:
1. 启动应用
2. 点击"文件" -> "新建项目"
3. 输入项目名称和位置
4. 验证项目文件夹创建成功
5. 添加节点和资源
6. 保存项目
7. 导出项目为 ZIP

**Step 4: 提交代码**

```bash
git add bt_gui/bt_editor/editor.py bt_gui/app.py
git commit -m "feat: integrate project management into editor UI"
```

---

## 完成检查清单

- [ ] PathResolver 实现并通过测试
- [ ] ResourceImporter 实现并通过测试
- [ ] ProjectManager 实现并通过测试
- [ ] ExecutionContext 扩展路径解析功能
- [ ] PackageExporter 实现并通过测试
- [ ] 编辑器集成项目管理功能
- [ ] 用户界面添加项目菜单
- [ ] 手动测试完整流程

---

**计划完成!**
