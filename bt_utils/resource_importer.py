import os
import shutil
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
            'script': 'scripts/script',
            'code': 'scripts/code',
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
        new_filename = filename
        
        while os.path.exists(target_path):
            new_filename = f"{name}_{counter}{ext}"
            target_path = os.path.join(self.project_root, target_dir, new_filename)
            counter += 1
        
        return new_filename
