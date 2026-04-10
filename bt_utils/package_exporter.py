import os
import zipfile
from datetime import datetime
from typing import List, Optional

class PackageExporter:
    """项目打包导出器"""
    
    EXCLUDE_DIRS = ['.metadata', '__pycache__', '.git', 'node_modules']
    EXCLUDE_EXTENSIONS = ['.pyc', '.pyo', '.tmp', '.bak', '.log']
    
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
                dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
                
                for file in files:
                    if self._should_exclude_file(file):
                        continue
                    
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(self.project_root))
                    zipf.write(file_path, arcname)
        
        self._generate_readme(output_path)
        
        return output_path
    
    def _should_exclude_file(self, filename: str) -> bool:
        """检查文件是否应被排除"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.EXCLUDE_EXTENSIONS
    
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

## 技术支持
如有问题,请联系项目创建者。

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        readme_path = os.path.splitext(zip_path)[0] + "_使用说明.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
