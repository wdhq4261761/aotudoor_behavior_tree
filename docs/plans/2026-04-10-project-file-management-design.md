# AutoDoor 行为树系统 - 项目工程文件管理方案设计文档

**文档版本**: 1.0  
**创建日期**: 2026-04-10  
**作者**: AI Assistant  
**状态**: 已完成

---

## 1. 概述

### 1.1 设计目标

本方案旨在为 AutoDoor 行为树系统设计一套完整的项目工程文件管理方案,实现以下目标:

1. **系统化管理**: 系统化管理行为树生成的所有文件,包括脚本、图片及其他资源
2. **独立存储**: 建立合理的文件夹组织结构,确保每个行为树脚本及其关联资源能被独立存储为一个完整文件夹
3. **可移植性**: 实现文件夹级别的可移植性,使用户通过分享单个文件夹即可正确运行完整的行为树功能
4. **易用性**: 优化用户使用流程,提供简单直观的操作界面

### 1.2 设计原则

1. **简洁实用**: 避免过度设计,保持方案简单实用
2. **用户友好**: 保持用户导入文件的原始名称,减少用户认知负担
3. **相对路径**: 所有资源使用相对路径引用,确保可移植性
4. **自动化**: 自动化处理文件导入、备份和打包等操作

### 1.3 适用场景

- **产品化分发**: 用户创建的行为树脚本主要用于打包成独立产品分发给最终用户
- **资源类型**: 支持模板图片、外部脚本、音频文件、其他资源文件
- **打包方式**: ZIP 压缩包,保留文件夹结构

---

## 2. 项目文件夹结构设计

### 2.1 标准项目文件夹结构

```
MyBehaviorTree/                    # 项目根文件夹(用户自定义名称)
├── project.json                   # 项目配置文件(元数据)
├── tree.json                      # 行为树定义文件(主文件)
├── tree.yaml                      # 行为树定义文件(YAML格式,可选)
├── tree.txt                       # 行为树文本描述(只读导出)
│
├── images/                        # 图像资源文件夹
│   ├── templates/                 # 模板图片(用于图像匹配节点)
│   │   ├── button_ok.png          # 用户导入(保持原名)
│   │   ├── icon_target.png        # 用户导入(保持原名)
│   │   └── ...
│   ├── screenshots/               # 截图文件(用于OCR检测等)
│   │   ├── screenshot_20260410_143025.png  # 系统生成
│   │   └── ...
│   └── thumbnails/                # 缩略图(编辑器预览)
│       └── ...
│
├── scripts/                       # 脚本资源文件夹
│   ├── python/                    # Python 脚本
│   │   ├── my_helper.py           # 用户导入(保持原名)
│   │   └── ...
│   ├── batch/                     # 批处理脚本
│   │   └── ...
│   └── shell/                     # Shell 脚本(跨平台支持)
│       └── ...
│
├── audio/                         # 音频资源文件夹
│   ├── alarms/                    # 报警音效
│   │   ├── custom_alarm.mp3       # 用户导入(保持原名)
│   │   └── ...
│   ├── notifications/             # 通知音效
│   │   └── ...
│   └── voice/                     # 语音提示
│       └── ...
│
├── data/                          # 数据资源文件夹
│   ├── config/                    # 配置文件
│   │   └── ...
│   ├── templates/                 # 数据模板
│   │   └── ...
│   └── cache/                     # 运行时缓存(不打包)
│       └── ...
│
├── docs/                          # 文档文件夹(可选)
│   ├── README.md                  # 项目说明文档
│   └── user_guide.md              # 用户指南
│
└── .metadata/                     # 元数据文件夹(隐藏)
    ├── version.json               # 版本信息
    └── logs/                      # 运行日志(不打包)
        └── ...
```

### 2.2 项目配置文件 (project.json)

```json
{
  "version": "1.0",
  "format_type": "behavior_tree_project",
  "project_info": {
    "name": "MyBehaviorTree",
    "description": "自动化任务行为树",
    "author": "用户名",
    "created_at": "2026-04-10T12:00:00",
    "modified_at": "2026-04-10T14:30:00",
    "app_version": "1.0.0"
  },
  "main_tree": "tree.json",
  "resources": {
    "images": ["images/templates/button_ok.png", ...],
    "scripts": ["scripts/python/my_helper.py", ...],
    "audio": ["audio/alarms/custom_alarm.mp3", ...]
  },
  "dependencies": {
    "tesseract_languages": ["eng", "chi_sim"],
    "python_packages": ["opencv-python", "Pillow"],
    "external_tools": []
  }
}
```

### 2.3 设计要点

1. **文件夹分类清晰**: 按资源类型分类存储,便于管理和查找
2. **相对路径引用**: 所有资源使用相对于项目根目录的路径
3. **元数据分离**: `.metadata/` 文件夹存储系统元数据,不干扰用户文件
4. **可扩展性**: 文件夹结构支持扩展新的资源类型
5. **文档支持**: 内置 `docs/` 文件夹支持项目文档管理

---

## 3. 文件命名规范

### 3.1 简化命名原则

1. **保持原名**: 用户导入的文件保持原始名称,不做修改
2. **项目文件夹**: 直接使用行为树脚本名称作为文件夹名
3. **自动命名**: 仅对系统自动生成的文件使用规范命名
4. **避免冲突**: 文件名冲突时自动添加序号或时间戳

### 3.2 项目文件夹命名

**规则**: 直接使用行为树脚本文件名(不含扩展名)

**示例**:
```
用户保存文件为: "我的自动化任务.json"
→ 项目文件夹: "我的自动化任务/"

用户保存文件为: "GameHelper_v1.0.json"
→ 项目文件夹: "GameHelper_v1.0/"
```

### 3.3 用户导入文件命名

**规则**: 保持用户导入时的原始文件名

**示例**:
```
用户导入图像: "C:/Downloads/ok_button.png"
→ 项目中保存: "images/templates/ok_button.png"

用户导入脚本: "D:/Scripts/my_helper.py"
→ 项目中保存: "scripts/python/my_helper.py"
```

### 3.4 系统自动生成文件命名

仅对系统自动生成的文件使用规范命名:

#### 3.4.1 截图文件
**格式**: `screenshot_{时间戳}.png`
```
images/screenshots/
├── screenshot_20260410_143025.png
└── screenshot_20260410_143156.png
```

#### 3.4.2 备份文件
**格式**: `tree_backup_{时间戳}.json`
```
MyBehaviorTree/
├── tree.json
├── tree_backup_20260410_143000.json
└── tree_backup_20260410_150000.json
```

### 3.5 文件名冲突处理

当导入文件与现有文件重名时:

**策略1: 自动添加序号**
```
已存在: ok_button.png
新导入: ok_button.png → ok_button_2.png
```

**策略2: 用户选择**
- 保留原文件(跳过导入)
- 替换原文件
- 重命名新文件(自动添加序号)

### 3.6 特殊字符处理

**允许的字符**:
- 中文字符
- 英文字母 (a-z, A-Z)
- 数字 (0-9)
- 下划线 (_)
- 连字符 (-)
- 空格 (转换为下划线)

**禁止的字符**: `\ / : * ? " < > |`

---

## 4. 资源引用机制

### 4.1 相对路径存储策略

**核心原则**: 所有资源路径在行为树文件中存储为相对于项目根目录的相对路径

**路径格式**: `./{资源类型}/{子目录}/{文件名}`

**示例**:
```json
{
  "nodes": {
    "node_1": {
      "type": "ImageConditionNode",
      "config": {
        "template_path": "./images/templates/ok_button.png",
        "threshold": 0.8
      }
    },
    "node_2": {
      "type": "ScriptNode",
      "config": {
        "script_path": "./scripts/python/my_helper.py"
      }
    }
  }
}
```

### 4.2 PathResolver 类设计

```python
class PathResolver:
    """资源路径解析器"""
    
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
    
    def to_relative(self, absolute_path: str) -> str:
        """将绝对路径转换为相对路径"""
        abs_path = os.path.abspath(absolute_path)
        rel_path = os.path.relpath(abs_path, self.project_root)
        return f"./{rel_path.replace(os.sep, '/')}"
    
    def to_absolute(self, relative_path: str) -> str:
        """将相对路径转换为绝对路径"""
        if relative_path.startswith("./"):
            relative_path = relative_path[2:]
        abs_path = os.path.join(self.project_root, relative_path)
        return os.path.normpath(abs_path)
    
    def is_valid_relative_path(self, path: str) -> bool:
        """检查相对路径是否有效"""
        if not path.startswith("./"):
            return False
        abs_path = self.to_absolute(path)
        if not os.path.exists(abs_path):
            return False
        real_abs_path = os.path.realpath(abs_path)
        real_project_root = os.path.realpath(self.project_root)
        return real_abs_path.startswith(real_project_root)
```

### 4.3 资源导入流程

```
用户选择文件
    │
    │ 1. 获取文件绝对路径
    ▼
file_dialog.get_open_filename()
    │
    │ 2. 确定目标存储位置
    ▼
resource_type = detect_type(source)
target_dir = get_target_dir(type)
    │
    │ 3. 复制文件到项目目录
    ▼
target_path = copy_to_project(source_path, target_dir)
    │
    │ 4. 生成相对路径引用
    ▼
relative_path = resolver.to_relative(target_path)
    │
    │ 5. 存储到节点配置
    ▼
node.config["template_path"] = relative_path
```

### 4.4 ResourceImporter 类设计

```python
class ResourceImporter:
    """资源导入管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.resolver = PathResolver(project_root)
    
    def import_resource(self, source_path: str, resource_type: str = None) -> str:
        """导入资源文件到项目目录"""
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
```

### 4.5 运行时路径解析

```python
class ExecutionContext:
    """执行上下文(扩展)"""
    
    def __init__(self, project_root: str = None):
        self.blackboard = Blackboard()
        self.elapsed_time = 0.0
        self.tick_count = 0
        self.project_root = project_root or os.getcwd()
        self.path_resolver = PathResolver(self.project_root)
    
    def resolve_path(self, relative_path: str) -> str:
        """解析相对路径为绝对路径"""
        if relative_path.startswith("./"):
            return self.path_resolver.to_absolute(relative_path)
        return relative_path
```

### 4.6 跨平台兼容性

```python
def normalize_path(path: str) -> str:
    """规范化路径分隔符"""
    return path.replace('\\', '/')

def denormalize_path(path: str) -> str:
    """转换为本地路径分隔符"""
    return path.replace('/', os.sep)
```

---

## 5. 打包与导出流程

### 5.1 打包流程

```
用户触发打包操作
    │
    │ 1. 验证项目完整性
    ▼
ProjectValidator.validate_project()
    │
    │ 2. 收集打包文件列表
    ▼
collect_files_to_package()
    │
    │ 3. 创建 ZIP 文件
    ▼
create_zip_archive()
    │
    │ 4. 生成使用说明
    ▼
generate_readme()
    │
    ▼
打包完成
```

### 5.2 PackageExporter 类设计

```python
class PackageExporter:
    """项目打包导出器"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
    
    def export_to_zip(self, output_path: str = None) -> str:
        """导出项目为 ZIP 文件"""
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

### 5.3 文件过滤规则

**默认排除**:
- `*.pyc`, `*.pyo` - Python 编译文件
- `__pycache__/` - Python 缓存目录
- `.metadata/` - 元数据目录
- `*.tmp`, `*.temp` - 临时文件
- `.DS_Store`, `Thumbs.db` - 系统文件

### 5.4 ZIP 文件内部结构

```
MyBehaviorTree.zip
└── MyBehaviorTree/                # 项目根文件夹
    ├── project.json               # 项目配置
    ├── tree.json                  # 行为树定义
    ├── images/                    # 图像资源
    │   └── templates/
    │       ├── ok_button.png
    │       └── target_icon.png
    ├── scripts/                   # 脚本资源
    │   └── python/
    │       └── my_helper.py
    └── audio/                     # 音频资源
        └── alarms/
            └── custom_alarm.mp3
```

---

## 6. 版本控制建议

### 6.1 简化版本管理

#### 6.1.1 基本版本信息

仅在 `project.json` 中记录基本版本信息:

```json
{
  "version": "1.0",
  "project_info": {
    "name": "MyBehaviorTree",
    "created_at": "2026-04-10T12:00:00",
    "modified_at": "2026-04-10T14:30:00"
  }
}
```

#### 6.1.2 版本号规则

- 使用简单的递增版本号: `1.0`, `1.1`, `1.2`, ...
- 用户手动更新版本号
- 无需自动版本管理

### 6.2 简单备份机制

```python
def create_backup_before_save(project_root: str):
    """保存前自动创建备份"""
    tree_file = os.path.join(project_root, "tree.json")
    if os.path.exists(tree_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(
            project_root,
            f"tree_backup_{timestamp}.json"
        )
        shutil.copy2(tree_file, backup_file)
        
        # 清理旧备份,只保留最近 5 个
        clean_old_backups(project_root, keep_count=5)

def clean_old_backups(project_root: str, keep_count: int = 5):
    """清理旧备份文件"""
    backup_files = []
    for filename in os.listdir(project_root):
        if filename.startswith("tree_backup_") and filename.endswith(".json"):
            backup_files.append(os.path.join(project_root, filename))
    
    backup_files.sort(key=os.path.getmtime, reverse=True)
    
    for old_backup in backup_files[keep_count:]:
        os.remove(old_backup)
```

---

## 7. 用户使用流程优化

### 7.1 创建新项目流程

```
用户点击"新建项目"
    │
    │ 1. 弹出项目配置对话框
    ▼
┌──────────────────────────────────────┐
│  项目名称: [未命名项目]              │
│  保存位置: [浏览...]                │
│  项目描述: [可选]                   │
│                                      │
│  [确定]  [取消]                      │
└──────────────────────────────────────┘
    │
    │ 2. 创建项目文件夹结构
    ▼
创建文件夹: {项目名称}/
├─ images/templates/
├─ scripts/python/
├─ audio/alarms/
└─ data/
    │
    │ 3. 生成项目配置文件
    ▼
生成 project.json
生成 tree.json (空树)
    │
    │ 4. 打开编辑器
    ▼
用户开始编辑行为树
```

### 7.2 打开已有项目流程

```
用户点击"打开项目"
    │
    │ 1. 弹出文件夹选择对话框
    ▼
选择项目文件夹
最近打开列表
    │
    │ 2. 验证项目完整性
    ▼
检查 project.json 是否存在
检查 tree.json 是否存在
检查资源文件是否完整
    │
    │ 3. 加载项目
    ▼
加载 project.json
加载 tree.json
初始化 PathResolver
    │
    │ 4. 显示编辑器
    ▼
用户继续编辑行为树
```

### 7.3 资源导入流程

```
用户在节点属性面板点击"选择资源"
    │
    │ 1. 弹出文件选择对话框
    ▼
选择文件,显示预览
    │
    │ 2. 自动导入到项目
    ▼
复制文件到对应目录(保持原名)
    │
    │ 3. 生成相对路径引用
    ▼
节点配置: "./images/templates/ok_button.png"
    │
    │ 4. 更新界面
    ▼
属性面板显示相对路径
```

### 7.4 保存项目流程

```
用户点击"保存"或按 Ctrl+S
    │
    │ 1. 创建备份
    ▼
备份当前 tree.json
→ tree_backup_20260410_143000.json
    │
    │ 2. 保存项目文件
    ▼
保存 tree.json
更新 project.json 的修改时间
    │
    │ 3. 清理旧备份
    ▼
只保留最近 5 个备份文件
    │
    ▼
保存完成
```

### 7.5 打包分享流程

```
用户点击"导出项目"
    │
    │ 1. 弹出导出对话框
    ▼
选择输出位置
选择包含内容
    │
    │ 2. 验证项目完整性
    ▼
检查所有资源文件是否存在
    │
    │ 3. 创建 ZIP 文件
    ▼
压缩项目文件夹
保持目录结构
    │
    │ 4. 生成使用说明
    ▼
创建 README.txt
    │
    ▼
导出完成
```

### 7.6 界面优化建议

#### 7.6.1 项目管理界面

```
┌──────────────────────────────────────────────────┐
│  文件  编辑  视图  帮助                           │
│  ├─ 新建项目 (Ctrl+N)                            │
│  ├─ 打开项目 (Ctrl+O)                            │
│  ├─ 最近打开 ▶                                   │
│  │  ├─ MyBehaviorTree (D:/Projects/)            │
│  │  └─ GameHelper (D:/Projects/)                │
│  ├─ 保存 (Ctrl+S)                                │
│  ├─ 另存为 (Ctrl+Shift+S)                        │
│  ├─ 导出项目                                     │
│  └─ 退出                                         │
└──────────────────────────────────────────────────┘
```

#### 7.6.2 状态栏显示

```
┌──────────────────────────────────────────────────┐
│  项目: MyBehaviorTree | 已保存 | v1.0 | 3个资源  │
└──────────────────────────────────────────────────┘
```

#### 7.6.3 资源管理面板

```
┌──────────────────────────────────────┐
│  项目资源                            │
├──────────────────────────────────────┤
│  📁 images (5)                       │
│    ├─ 📁 templates (3)               │
│    │   ├─ ok_button.png              │
│    │   └─ target_icon.png            │
│    └─ 📁 screenshots (2)             │
│  📁 scripts (2)                      │
│    └─ 📁 python (2)                  │
│        ├─ my_helper.py               │
│        └─ data_processor.py          │
│  📁 audio (1)                        │
│    └─ 📁 alarms (1)                  │
│        └─ custom_alarm.mp3           │
│                                      │
│  [+ 导入资源]  [刷新]                │
└──────────────────────────────────────┘
```

### 7.7 快捷键优化

| 操作 | 快捷键 | 说明 |
|------|--------|------|
| 新建项目 | Ctrl+N | 创建新项目 |
| 打开项目 | Ctrl+O | 打开已有项目 |
| 保存 | Ctrl+S | 保存当前项目 |
| 另存为 | Ctrl+Shift+S | 另存为新项目 |
| 导出 | Ctrl+E | 导出为 ZIP |
| 导入资源 | Ctrl+I | 导入资源文件 |
| 项目属性 | Ctrl+P | 查看项目属性 |

---

## 8. 实施建议

### 8.1 开发优先级

**第一阶段(核心功能)**:
1. 实现项目文件夹创建和管理
2. 实现资源导入和相对路径引用
3. 实现项目保存和加载

**第二阶段(增强功能)**:
1. 实现项目打包导出
2. 实现自动备份机制
3. 实现资源管理面板

**第三阶段(优化功能)**:
1. 实现最近打开列表
2. 实现项目完整性验证
3. 实现用户界面优化

### 8.2 技术实现要点

1. **PathResolver**: 核心路径解析器,处理相对路径和绝对路径转换
2. **ResourceImporter**: 资源导入管理器,处理文件复制和路径生成
3. **PackageExporter**: 项目打包导出器,处理 ZIP 文件创建
4. **ProjectManager**: 项目管理器,统一管理项目生命周期

### 8.3 兼容性考虑

1. **向后兼容**: 支持打开旧版本的行为树文件(无项目文件夹结构)
2. **跨平台**: 处理 Windows/Linux/macOS 的路径分隔符差异
3. **编码**: 统一使用 UTF-8 编码,支持中文文件名

### 8.4 测试建议

1. **单元测试**: 测试 PathResolver 的路径转换功能
2. **集成测试**: 测试完整的资源导入和项目打包流程
3. **用户测试**: 邀请用户测试完整的使用流程,收集反馈

---

## 9. 总结

本设计方案为 AutoDoor 行为树系统提供了一套完整的项目工程文件管理方案,具有以下特点:

1. **简洁实用**: 避免过度设计,保持方案简单实用
2. **用户友好**: 保持用户导入文件的原始名称,减少用户认知负担
3. **可移植性强**: 使用相对路径引用,支持文件夹级别的完整移植
4. **自动化程度高**: 自动处理文件导入、备份和打包等操作
5. **易于实施**: 分阶段实施,优先级清晰,技术实现可行

该方案能够满足产品化分发、资源管理、可移植性和易用性等核心需求,为用户提供良好的使用体验。

---

**文档结束**
