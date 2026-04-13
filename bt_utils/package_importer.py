import os
import zipfile
import shutil
from typing import Optional, Tuple
from datetime import datetime


class PackageImporter:
    """项目导入器"""
    
    REQUIRED_FILES = ["project.json", "tree.json"]
    
    def __init__(self):
        pass
    
    def validate_package(self, zip_path: str) -> Tuple[bool, str]:
        """验证 ZIP 文件是否为有效的项目压缩包
        
        Args:
            zip_path: ZIP 文件路径
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        if not os.path.exists(zip_path):
            return False, "文件不存在"
        
        if not zipfile.is_zipfile(zip_path):
            return False, "不是有效的 ZIP 文件"
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                namelist = zipf.namelist()
                
                if not namelist:
                    return False, "ZIP 文件为空"
                
                found_project_json = False
                found_tree_json = False
                
                for name in namelist:
                    basename = os.path.basename(name)
                    if basename == "project.json":
                        found_project_json = True
                    elif basename == "tree.json":
                        found_tree_json = True
                
                if not found_project_json:
                    return False, "缺少 project.json 文件"
                
                if not found_tree_json:
                    return False, "缺少 tree.json 文件"
                
                return True, ""
                
        except zipfile.BadZipFile:
            return False, "ZIP 文件已损坏"
        except Exception as e:
            return False, f"读取 ZIP 文件失败: {str(e)}"
    
    def get_project_name(self, zip_path: str) -> Optional[str]:
        """从 ZIP 文件中获取项目名称
        
        Args:
            zip_path: ZIP 文件路径
            
        Returns:
            项目名称，如果无法获取则返回 None
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                namelist = zipf.namelist()
                
                if not namelist:
                    return None
                
                first_entry = namelist[0]
                if '/' in first_entry:
                    project_folder = first_entry.split('/')[0]
                    return project_folder
                
                for name in namelist:
                    basename = os.path.basename(name)
                    if basename == "project.json":
                        import json
                        with zipf.open(name) as f:
                            project_config = json.load(f)
                            project_info = project_config.get("project_info", {})
                            return project_info.get("name", None)
                
                return None
                
        except Exception:
            return None
    
    def get_project_root_in_zip(self, zip_path: str) -> Optional[str]:
        """获取 ZIP 内项目的根目录路径
        
        Args:
            zip_path: ZIP 文件路径
            
        Returns:
            ZIP 内项目根目录的路径前缀
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                namelist = zipf.namelist()
                
                if not namelist:
                    return None
                
                for name in namelist:
                    if name.endswith("project.json"):
                        parts = name.rsplit("/", 1)
                        if len(parts) > 1:
                            return parts[0]
                        return ""
                
                return None
                
        except Exception:
            return None
    
    def import_from_zip(
        self, 
        zip_path: str, 
        target_dir: str,
        overwrite: bool = False,
        new_name: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """从 ZIP 文件导入项目
        
        Args:
            zip_path: ZIP 文件路径
            target_dir: 目标目录
            overwrite: 是否覆盖已存在的项目
            new_name: 新项目名称（用于重命名）
            
        Returns:
            Tuple[bool, str, Optional[str]]: (是否成功, 错误信息, 导入后的项目路径)
        """
        is_valid, error_msg = self.validate_package(zip_path)
        if not is_valid:
            return False, error_msg, None
        
        project_name = new_name or self.get_project_name(zip_path)
        if not project_name:
            project_name = os.path.splitext(os.path.basename(zip_path))[0]
        
        project_root = os.path.join(target_dir, project_name)
        
        if os.path.exists(project_root) and not overwrite:
            return False, "PROJECT_EXISTS", project_root
        
        try:
            os.makedirs(target_dir, exist_ok=True)
            
            if os.path.exists(project_root):
                shutil.rmtree(project_root)
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zip_root = self.get_project_root_in_zip(zip_path)
                
                for member in zipf.namelist():
                    if zip_root:
                        if not member.startswith(zip_root + "/") and member != zip_root + "/":
                            continue
                        relative_path = member[len(zip_root) + 1:]
                    else:
                        relative_path = member
                    
                    if not relative_path or relative_path.endswith("/"):
                        continue
                    
                    target_path = os.path.join(project_root, relative_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    with zipf.open(member) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
            
            return True, "", project_root
            
        except Exception as e:
            return False, f"解压失败: {str(e)}", None
    
    def generate_new_name(self, base_name: str, target_dir: str) -> str:
        """生成不冲突的新项目名称
        
        Args:
            base_name: 基础名称
            target_dir: 目标目录
            
        Returns:
            新的项目名称
        """
        if not os.path.exists(os.path.join(target_dir, base_name)):
            return base_name
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}"
            if not os.path.exists(os.path.join(target_dir, new_name)):
                return new_name
            counter += 1
            
            if counter > 1000:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"{base_name}_{timestamp}"
