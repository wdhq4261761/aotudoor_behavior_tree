import os
import json
import shutil
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
