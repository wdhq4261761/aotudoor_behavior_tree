# TesseractOCR 替换为 RapidOCR 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将项目中使用的 Tesseract OCR 全面替换为 RapidOCR，提升识别速度和部署便捷性

**Architecture:** 保持现有 OCRManager 接口不变，仅替换底层实现。RapidOCR 基于 ONNX Runtime，无需外部依赖，打包体积更小，识别速度更快。

**Tech Stack:** 
- RapidOCR (rapidocr)
- ONNX Runtime (onnxruntime)
- PIL (Pillow)

---

## 当前实现分析

### 1. Tesseract OCR 使用情况

| 文件 | 用途 | 关键方法 |
|------|------|----------|
| `bt_utils/ocr_manager.py` | OCR管理器 | `recognize()`, `recognize_number()`, `get_all_text()` |
| `bt_nodes/conditions/ocr.py` | OCR检测节点 | `_check_condition()` |
| `bt_nodes/conditions/number.py` | 数字识别节点 | `_check_condition()` |
| `bt_core/context.py` | 执行上下文 | `perform_ocr()` |
| `bt_gui/settings_tab.py` | 设置界面 | Tesseract路径配置 |
| `autodoor_bt.spec` | 打包配置 | 包含tesseract目录 |
| `autodoor_bt_dd.spec` | DD版打包配置 | 包含tesseract目录 |

### 2. Tesseract OCR 依赖

```
pytesseract>=0.3.10
tesseract/  (约100MB运行时)
├── tesseract.exe
├── tessdata/
│   ├── eng.traineddata
│   ├── chi_sim.traineddata
│   └── ...
└── *.dll
```

### 3. RapidOCR 优势

| 特性 | Tesseract | RapidOCR |
|------|-----------|----------|
| 安装复杂度 | 需要外部运行时 | pip安装即可 |
| 打包体积 | ~100MB | ~20MB |
| 识别速度 | 较慢 | 更快 |
| 中文识别 | 一般 | 优秀 |
| 部署难度 | 高 | 低 |

---

## 替换方案设计

### 1. 接口兼容性设计

保持 `OCRManager` 类的公共接口不变，确保现有节点无需修改：

```python
class OCRManager:
    def recognize(self, image, keywords, language, preprocess_mode) -> Tuple[bool, Optional[Tuple[int, int]]]
    def recognize_number(self, image, language, preprocess_mode, extract_mode, extract_pattern, min_confidence) -> Tuple[bool, Optional[float]]
    def get_all_text(self, image, language, preprocess_mode, psm, oem) -> str
```

### 2. RapidOCR 集成设计

```python
from rapidocr import RapidOCR

class OCRManager:
    def __init__(self):
        self._engine = RapidOCR()
    
    def recognize(self, image, keywords=None, language="eng", preprocess_mode="normal"):
        # RapidOCR自动处理中英文
        result = self._engine(image)
        # 解析结果，返回关键词位置
        ...
```

### 3. 语言映射

| Tesseract语言代码 | RapidOCR支持 | 说明 |
|-------------------|--------------|------|
| eng | ✅ | 英文 |
| chi_sim | ✅ | 简体中文 |
| chi_tra | ✅ | 繁体中文 |
| 其他 | ⚠️ | 需要额外模型 |

### 4. 功能映射

| Tesseract功能 | RapidOCR实现 | 备注 |
|---------------|--------------|------|
| image_to_data | result.boxes + result.txts | 获取文本框和文本 |
| image_to_string | result.txts | 获取所有文本 |
| PSM模式 | 不支持 | RapidOCR自动处理 |
| OEM模式 | 不支持 | RapidOCR使用ONNX |
| 字符白名单 | 不支持 | 后处理过滤 |
| 图像预处理 | 保留现有逻辑 | 继续使用PIL预处理 |

---

## 实施任务

### Task 1: 更新依赖配置

**Files:**
- Modify: `requirements.txt`

**Step 1: 移除pytesseract依赖，添加rapidocr**

```txt
customtkinter>=5.2.0
Pillow>=10.0.0
pyautogui>=0.9.54
rapidocr>=1.3.0
onnxruntime>=1.15.0
pygame>=2.0.0
pynput>=1.7.6
opencv-python-headless>=4.5.0
numpy>=1.21.0
screeninfo>=0.6.7
pywin32>=305
PyYAML>=6.0
```

**Step 2: 验证依赖安装**

Run: `pip install -r requirements.txt`
Expected: 成功安装rapidocr和onnxruntime

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: replace pytesseract with rapidocr"
```

---

### Task 2: 重构OCRManager核心实现

**Files:**
- Modify: `bt_utils/ocr_manager.py`

**Step 1: 移除Tesseract相关导入和配置**

删除以下代码：
```python
import pytesseract
from pytesseract import Output

def get_tesseract_paths(app_root: str) -> List[str]:
    ...

def find_tesseract() -> Optional[str]:
    ...

class OCRManager:
    _tesseract_path: Optional[str] = None
    
    @classmethod
    def _auto_configure_tesseract(cls):
        ...
    
    @classmethod
    def set_tesseract_path(cls, path: str) -> None:
        ...
```

**Step 2: 添加RapidOCR导入和初始化**

```python
from rapidocr import RapidOCR
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Optional, List
import os
import re
import numpy as np


class OCRManager:
    """OCR管理器

    封装RapidOCR功能，提供文字识别和数字识别。
    支持图像预处理和多语言识别。
    使用单例模式。
    """
    _instance = None
    _initialized: bool = False
    _engine: Optional[RapidOCR] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._engine = RapidOCR()
```

**Step 3: 重构recognize方法**

```python
def recognize(self, image: Image.Image, keywords: str = None,
              language: str = "eng",
              preprocess_mode: str = "normal") -> Tuple[bool, Optional[Tuple[int, int]]]:
    """执行OCR识别

    Args:
        image: PIL.Image 图像
        keywords: 关键词（逗号分隔）
        language: OCR语言 (eng/chi_sim/chi_tra)
        preprocess_mode: 预处理模式 (normal/artistic)

    Returns:
        (是否找到, 位置坐标) 元组
    """
    try:
        processed = self._preprocess_image(image, language, preprocess_mode)
        
        img_array = np.array(processed)
        
        result = self._engine(img_array)
        
        if result is None or result.boxes is None:
            return False, None
        
        if keywords:
            keyword_list = [k.strip().lower() for k in keywords.split(",")]
            
            for i, text in enumerate(result.txts):
                if not text:
                    continue
                
                text_lower = text.lower()
                for keyword in keyword_list:
                    if keyword in text_lower:
                        box = result.boxes[i]
                        x = int((box[0] + box[2]) / 2)
                        y = int((box[1] + box[3]) / 2)
                        
                        if image.size != processed.size:
                            scale_x = image.size[0] / processed.size[0]
                            scale_y = image.size[1] / processed.size[1]
                            x = int(x * scale_x)
                            y = int(y * scale_y)
                        
                        return True, (x, y)
            
            return False, None
        
        return True, None
    
    except Exception as e:
        print(f"[WARN] OCR识别错误: {e}")
        return False, None
```

**Step 4: 重构recognize_number方法**

```python
def recognize_number(self, image: Image.Image, language: str = "eng",
                     preprocess_mode: str = "normal",
                     extract_mode: str = "无规则",
                     extract_pattern: str = "",
                     min_confidence: float = 0.5) -> Tuple[bool, Optional[float]]:
    """识别数字

    Args:
        image: PIL.Image 图像
        language: OCR语言
        preprocess_mode: 预处理模式 (normal/artistic)
        extract_mode: 提取模式 (无规则/x/y/自定义)
        extract_pattern: 自定义提取模式（使用*作为通配符）
        min_confidence: 最小置信度

    Returns:
        (是否识别成功, 数字值) 元组
    """
    try:
        processed = self._preprocess_image(image, language, preprocess_mode)
        
        img_array = np.array(processed)
        
        result = self._engine(img_array)
        
        if result is None or result.txts is None:
            return False, None
        
        all_text = " ".join(result.txts)
        
        extracted = self._extract_number(all_text, extract_mode, extract_pattern)
        
        if extracted is not None:
            return True, extracted
        
        return False, None
    
    except Exception as e:
        print(f"[WARN] OCR数字识别错误: {e}")
        return False, None
```

**Step 5: 重构get_all_text方法**

```python
def get_all_text(self, image: Image.Image, language: str = "eng",
                 preprocess_mode: str = "normal",
                 psm: int = None, oem: int = None) -> str:
    """获取所有识别文本
    
    Args:
        image: PIL.Image 图像
        language: OCR语言
        preprocess_mode: 预处理模式
        psm: PSM模式 (已废弃，RapidOCR自动处理)
        oem: OEM模式 (已废弃，RapidOCR使用ONNX)
        
    Returns:
        识别文本
    """
    try:
        processed = self._preprocess_image(image, language, preprocess_mode)
        
        img_array = np.array(processed)
        
        result = self._engine(img_array)
        
        if result is None or result.txts is None:
            return ""
        
        return "\n".join(result.txts)
    
    except Exception as e:
        print(f"[WARN] OCR文本识别错误: {e}")
        return ""
```

**Step 6: 移除_try_multi_psm方法**

删除此方法，RapidOCR不需要PSM模式。

**Step 7: 保留预处理方法**

保留以下方法不变：
- `_preprocess_chinese()`
- `_preprocess_standard()`
- `_preprocess_image()`
- `_extract_number()`

**Step 8: 测试OCRManager**

创建测试脚本 `test_ocr_manager.py`:

```python
from PIL import Image
from bt_utils.ocr_manager import OCRManager

def test_ocr_manager():
    ocr = OCRManager()
    
    img = Image.new('RGB', (200, 100), color='white')
    
    found, pos = ocr.recognize(img, keywords="test", language="eng")
    print(f"Recognize test: found={found}, pos={pos}")
    
    found, value = ocr.recognize_number(img, language="eng")
    print(f"Recognize number test: found={found}, value={value}")
    
    text = ocr.get_all_text(img, language="eng")
    print(f"Get all text test: text='{text}'")

if __name__ == "__main__":
    test_ocr_manager()
```

Run: `python test_ocr_manager.py`
Expected: 无错误输出

**Step 9: Commit**

```bash
git add bt_utils/ocr_manager.py
git commit -m "refactor: replace Tesseract with RapidOCR in OCRManager"
```

---

### Task 3: 更新设置界面

**Files:**
- Modify: `bt_gui/settings_tab.py`

**Step 1: 移除Tesseract路径配置**

删除以下代码：
```python
from bt_utils.ocr_manager import find_tesseract

self.tesseract_path = tk.StringVar(value=default_tesseract)

def _create_tesseract_section(self, parent):
    ...

def _browse_tesseract(self):
    ...
```

**Step 2: 添加RapidOCR信息显示**

```python
def _create_ocr_section(self, parent):
    """创建OCR信息区域"""
    tess_header = ctk.CTkFrame(parent, fg_color="transparent")
    tess_header.pack(fill="x", pady=(Theme.DIMENSIONS['spacing_md'], Theme.DIMENSIONS['spacing_xs']))
    
    create_section_title(tess_header, "OCR 引擎信息", level=1).pack(side="left")
    
    info_frame = ctk.CTkFrame(parent, fg_color=Theme.DARK_COLORS['bg_secondary'])
    info_frame.pack(fill="x", pady=Theme.DIMENSIONS['spacing_xs'])
    
    info_text = ctk.CTkLabel(
        info_frame,
        text="当前使用: RapidOCR\n基于ONNX Runtime，无需额外配置\n支持中英文识别",
        font=Theme.FONTS['body'],
        text_color=Theme.DARK_COLORS['text_secondary'],
        justify="left"
    )
    info_text.pack(padx=Theme.DIMENSIONS['spacing_md'], pady=Theme.DIMENSIONS['spacing_md'], anchor="w")
```

**Step 3: 更新_create_ui方法**

将 `_create_tesseract_section(scroll_frame)` 替换为 `_create_ocr_section(scroll_frame)`

**Step 4: 更新_save_settings方法**

移除 `tesseract_path` 的保存逻辑。

**Step 5: 更新_load_settings方法**

移除 `tesseract_path` 的加载逻辑。

**Step 6: Commit**

```bash
git add bt_gui/settings_tab.py
git commit -m "refactor: remove Tesseract path config, add RapidOCR info"
```

---

### Task 4: 更新打包配置

**Files:**
- Modify: `autodoor_bt.spec`
- Modify: `autodoor_bt_dd.spec`

**Step 1: 移除tesseract文件收集逻辑**

删除以下代码：
```python
tesseract_files = []
tesseract_dir = os.path.join(project_root, 'tesseract')

if os.path.exists(tesseract_dir):
    for root, _, files in os.walk(tesseract_dir):
        for file in files:
            file_path = os.path.join(root, file)
            dest_dir = os.path.join('tesseract', os.path.relpath(root, tesseract_dir))
            
            if (file == 'tesseract' or file == 'tesseract.exe'):
                tesseract_files.append((file_path, dest_dir))
                continue
            if file.endswith('.exe') and file != 'tesseract.exe':
                continue
            if file.endswith('.html'):
                continue
            if root.endswith('tessdata/configs') or root.endswith('tessdata/tessconfigs'):
                continue
            
            tesseract_files.append((file_path, dest_dir))
    print(f"Collected {len(tesseract_files)} tesseract files")
```

**Step 2: 更新data_files**

将 `+ tesseract_files` 从data_files中移除：

```python
data_files = [
    (os.path.join(project_root, 'assets/sounds/alarm.mp3'), 'assets/sounds'),
    (os.path.join(project_root, 'assets/sounds/temp_reversed.mp3'), 'assets/sounds'),
    (os.path.join(project_root, 'assets/icons/autodoor.ico'), 'assets/icons'),
    (os.path.join(project_root, 'assets/icons/autodoor.png'), 'assets/icons'),
    (os.path.join(project_root, 'config/settings.json'), 'config'),
]
```

**Step 3: 添加RapidOCR模型文件（如果需要）**

RapidOCR会自动下载模型，但为了离线使用，可以预先下载模型：

```python
rapidocr_models = []
rapidocr_dir = os.path.join(project_root, 'rapidocr_models')

if os.path.exists(rapidocr_dir):
    for root, _, files in os.walk(rapidocr_dir):
        for file in files:
            file_path = os.path.join(root, file)
            dest_dir = os.path.join('rapidocr_models', os.path.relpath(root, rapidocr_dir))
            rapidocr_models.append((file_path, dest_dir))
    print(f"Collected {len(rapidocr_models)} RapidOCR model files")

data_files = [
    ...
] + rapidocr_models
```

**Step 4: Commit**

```bash
git add autodoor_bt.spec autodoor_bt_dd.spec
git commit -m "refactor: remove Tesseract from build, add RapidOCR models"
```

---

### Task 5: 更新文档

**Files:**
- Modify: `README.md`
- Modify: `doc/01_架构文档.md`

**Step 1: 更新README.md**

将OCR引擎部分从：
```markdown
- OCR 引擎: Tesseract 5.x + pytesseract
```

改为：
```markdown
- OCR 引擎: RapidOCR (基于ONNX Runtime)
```

**Step 2: 更新架构文档**

更新技术栈部分：
```markdown
├── OCR 引擎:    RapidOCR + ONNX Runtime
```

更新基础设施层描述：
```markdown
│  │  OCR 管理器   │ │
│  │  OCRManager   │ │
│  │               │ │
│  └───────┬───────┘  │
│          │          │
│  ┌───────┴────────┐ │
│  │  RapidOCR      │ │
│  │  (ONNX)        │ │
│  └────────────────┘ │
```

**Step 3: Commit**

```bash
git add README.md doc/01_架构文档.md
git commit -m "docs: update OCR engine from Tesseract to RapidOCR"
```

---

### Task 6: 清理Tesseract运行时

**Files:**
- Delete: `tesseract/` 目录

**Step 1: 确认不再需要Tesseract**

检查代码中是否还有引用：
```bash
grep -r "tesseract" --include="*.py" .
grep -r "pytesseract" --include="*.py" .
```

Expected: 无输出（除了文档中的说明）

**Step 2: 删除tesseract目录**

```bash
rm -rf tesseract/
```

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove Tesseract runtime"
```

---

### Task 7: 测试验证

**Step 1: 运行单元测试**

如果有OCR相关的单元测试，运行测试：
```bash
python -m pytest tests/ -v -k ocr
```

Expected: 所有测试通过

**Step 2: 运行集成测试**

启动应用，测试OCR功能：
```bash
python main.py
```

测试项目：
1. 创建OCR检测节点，测试关键词识别
2. 创建数字识别节点，测试数字提取
3. 测试中英文识别
4. 测试图像预处理功能

**Step 3: 打包测试**

```bash
# 标准版
python -m PyInstaller autodoor_bt.spec --clean

# DD版
python -m PyInstaller autodoor_bt_dd.spec --clean
```

Expected: 
- 打包成功
- 打包体积减少约80MB
- 运行打包后的程序，OCR功能正常

**Step 4: Commit测试结果**

```bash
git add docs/test_results.md
git commit -m "test: verify RapidOCR integration"
```

---

## 风险与注意事项

### 1. 功能差异

| 功能 | Tesseract | RapidOCR | 处理方案 |
|------|-----------|----------|----------|
| PSM模式 | 支持 | 不支持 | RapidOCR自动处理，无需配置 |
| OEM模式 | 支持 | 不支持 | RapidOCR使用ONNX，固定引擎 |
| 字符白名单 | 支持 | 不支持 | 后处理过滤结果 |
| 自定义训练 | 支持 | 支持 | 使用PaddleOCR训练后转换 |

### 2. 性能对比

预期改进：
- 识别速度提升 2-5倍
- 打包体积减少 ~80MB
- 内存占用减少 ~50MB

### 3. 兼容性

- Python版本：3.7+
- 操作系统：Windows/Linux/macOS
- 架构：x64/ARM64

### 4. 回滚方案

如果RapidOCR出现严重问题，可以快速回滚：

```bash
git revert <commit-hash>
pip install pytesseract
```

恢复tesseract目录和打包配置。

---

## 实施时间估算

| 任务 | 预计时间 |
|------|----------|
| Task 1: 更新依赖 | 5分钟 |
| Task 2: 重构OCRManager | 30分钟 |
| Task 3: 更新设置界面 | 15分钟 |
| Task 4: 更新打包配置 | 10分钟 |
| Task 5: 更新文档 | 10分钟 |
| Task 6: 清理Tesseract | 5分钟 |
| Task 7: 测试验证 | 30分钟 |
| **总计** | **105分钟** |

---

## 成功标准

- [ ] 所有OCR功能正常工作
- [ ] 打包体积减少至少50MB
- [ ] 识别速度提升至少2倍
- [ ] 中英文识别准确率不低于Tesseract
- [ ] 无需用户配置OCR路径
- [ ] 所有单元测试通过
- [ ] 文档更新完整

---

## 后续优化

1. **模型优化**：根据实际场景微调模型
2. **GPU加速**：使用onnxruntime-gpu提升速度
3. **多语言支持**：添加更多语言模型
4. **结果缓存**：对相同图像缓存识别结果
5. **批量识别**：支持批量图像识别
