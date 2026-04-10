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
