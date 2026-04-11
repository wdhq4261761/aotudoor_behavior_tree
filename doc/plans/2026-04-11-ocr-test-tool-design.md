# OCR测试工具设计文档

## 1 项目概述

### 1.1 项目目标

创建一个独立的OCR参数测试工具，用于微调AutoDoor行为树系统的OCR识别参数，提升中英文和数字的识别准确率。

### 1.2 核心需求

- 支持实时截图测试和图片文件加载
- 可视化参数调节（滑块控制）
- 实时预览预处理效果
- 识别准确率和速度统计
- 参数保存和加载
- 与现有OCR系统参数完全一致

### 1.3 技术栈

```
Python 3.10+
├── GUI框架: CustomTkinter
├── 图像处理: Pillow
├── OCR引擎: Tesseract 5.x + pytesseract
└── 截图: PIL.ImageGrab
```

---

## 2 系统架构

### 2.1 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    表现层 (Presentation)                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              OCRTestMainWindow (CTk)                    │ │
│  │  ┌──────────────┬──────────────┬──────────────┐       │ │
│  │  │ ScreenshotPanel│ ParamPanel  │ ResultPanel │       │ │
│  │  │              │              │              │       │ │
│  │  │ - 图像预览   │ - 参数调节   │ - 结果显示   │       │ │
│  │  │ - 区域选择   │ - 参数保存   │ - 性能统计   │       │ │
│  │  └──────────────┴──────────────┴──────────────┘       │ │
│  └────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    业务层 (Business)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  TestRunner  │  │ OCRTester    │  │ImagePreproc  │     │
│  │              │  │              │  │essor         │     │
│  │ - 执行测试   │  │ - OCR识别    │  │ - 图像预处理  │     │
│  │ - 性能统计   │  │ - 结果对比   │  │ - 参数应用   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                    基础设施层 (Infrastructure)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ScreenshotMgr │  │ParameterMgr  │  │ OCRManager   │     │
│  │              │  │              │  │ (复用现有)   │     │
│  │ - 全屏截图   │  │ - 参数保存   │  │              │     │
│  │ - 区域截图   │  │ - 参数加载   │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

```
autodoor_behavior_tree/
├── bt_utils/
│   ├── ocr_tester.py          # OCR测试器核心类
│   ├── image_preprocessor.py  # 图像预处理器
│   └── parameter_manager.py   # 参数管理器
│
├── bt_gui/
│   └── ocr_test_tool/
│       ├── __init__.py
│       ├── main_window.py     # 主窗口
│       ├── screenshot_panel.py # 截图面板
│       ├── param_panel.py     # 参数调节面板
│       ├── result_panel.py    # 结果展示面板
│       └── test_runner.py     # 测试执行器
│
├── config/
│   └── ocr_test_params.json   # 默认测试参数
│
└── ocr_test_tool.py           # 独立启动脚本
```

---

## 3 核心组件设计

### 3.1 图像预处理器 (ImagePreprocessor)

**职责:** 提供可配置参数的图像预处理功能

**关键方法:**

```python
class ImagePreprocessor:
    def preprocess_chinese(
        self,
        image: Image.Image,
        scale_factor: float = 2.5,
        median_filter_size: int = 3,
        contrast_enhance: float = 2.5,
        sharpness_enhance: float = 2.0,
        sharpness_iterations: int = 2,
        binary_threshold: int = 130
    ) -> Image.Image:
        """中文图像预处理"""
        
    def preprocess_standard(
        self,
        image: Image.Image,
        contrast_enhance: float = 1.5,
        sharpness_enhance: float = 1.5,
        binary_threshold: int = 128
    ) -> Image.Image:
        """标准图像预处理"""
        
    def preprocess_with_params(
        self,
        image: Image.Image,
        params: Dict[str, Any],
        language: str = "eng"
    ) -> Image.Image:
        """使用参数字典进行预处理"""
```

**预处理流程对比:**

| 步骤 | 中文预处理 | 标准预处理 |
|------|-----------|-----------|
| 放大 | 2.5倍 (尺寸<100时) | 无 |
| 中值滤波 | size=3 | 无 |
| 灰度转换 | ✓ | ✓ |
| 对比度增强 | 2.5倍 | 1.5倍 |
| 锐化 | 2.0倍×2次 | 1.5倍×1次 |
| 二值化 | 阈值130 | 阈值128 |

### 3.2 OCR测试器 (OCRTester)

**职责:** 执行OCR识别测试并评估结果

**关键方法:**

```python
class OCRTester:
    def test_text_recognition(
        self,
        image: Image.Image,
        keywords: str = None,
        language: str = "eng",
        params: Dict[str, Any] = None
    ) -> TestResult:
        """测试文本识别"""
        
    def test_number_recognition(
        self,
        image: Image.Image,
        language: str = "eng",
        params: Dict[str, Any] = None,
        extract_mode: str = "无规则"
    ) -> TestResult:
        """测试数字识别"""
        
    def calculate_accuracy(
        self,
        recognized: str,
        expected: str
    ) -> float:
        """计算识别准确率 (Levenshtein相似度)"""
        
    def measure_performance(
        self,
        test_func: Callable,
        iterations: int = 10
    ) -> PerformanceReport:
        """测量性能指标"""
```

**测试结果数据结构:**

```python
@dataclass
class TestResult:
    success: bool
    recognized_text: str
    confidence: float
    position: Optional[Tuple[int, int]]
    processing_time: float  # 毫秒
    preprocessed_image: Image.Image
    accuracy: Optional[float] = None  # 如果提供了预期结果
    error_message: Optional[str] = None
```

### 3.3 参数管理器 (ParameterManager)

**职责:** 管理OCR测试参数的保存、加载和对比

**关键方法:**

```python
class ParameterManager:
    def save_config(
        self,
        params: Dict[str, Any],
        filepath: str = None
    ) -> None:
        """保存参数配置"""
        
    def load_config(
        self,
        filepath: str = None
    ) -> Dict[str, Any]:
        """加载参数配置"""
        
    def get_default_params(self) -> Dict[str, Any]:
        """获取默认参数"""
        
    def compare_params(
        self,
        params1: Dict[str, Any],
        params2: Dict[str, Any]
    ) -> ComparisonReport:
        """对比两组参数"""
        
    def validate_params(
        self,
        params: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """验证参数有效性"""
```

**参数配置结构:**

```json
{
  "version": "1.0",
  "preprocessing": {
    "scale_factor": 2.5,
    "median_filter_size": 3,
    "contrast_enhance": 2.5,
    "sharpness_enhance": 2.0,
    "sharpness_iterations": 2,
    "binary_threshold": 130
  },
  "ocr": {
    "language": "chi_sim",
    "psm_modes": [7, 6, 11],
    "preprocess_mode": "artistic",
    "char_whitelist": "0123456789.-/:*"
  },
  "test": {
    "keywords": "",
    "expected_text": "",
    "expected_number": null,
    "test_iterations": 10
  }
}
```

### 3.4 测试执行器 (TestRunner)

**职责:** 协调测试流程，管理测试状态

**关键方法:**

```python
class TestRunner:
    def run_single_test(
        self,
        image: Image.Image,
        params: Dict[str, Any]
    ) -> TestResult:
        """执行单次测试"""
        
    def run_batch_tests(
        self,
        images: List[Image.Image],
        params: Dict[str, Any]
    ) -> List[TestResult]:
        """执行批量测试"""
        
    def run_comparison_test(
        self,
        image: Image.Image,
        params_list: List[Dict[str, Any]]
    ) -> ComparisonReport:
        """对比不同参数的测试结果"""
        
    def get_statistics(
        self,
        results: List[TestResult]
    ) -> StatisticsReport:
        """生成统计报告"""
```

---

## 4 GUI组件设计

### 4.1 主窗口 (OCRTestMainWindow)

**布局:**

```
┌────────────────────────────────────────────────────────────┐
│  工具栏: [截图] [区域截图] [加载图片] [保存配置] [加载配置] │
├──────────────────┬─────────────────┬──────────────────────┤
│                  │                 │                      │
│  截图面板        │  参数面板       │  结果面板            │
│  (40%)           │  (30%)          │  (30%)               │
│                  │                 │                      │
│  ┌────────────┐ │ ┌─────────────┐ │ ┌──────────────────┐ │
│  │ 原始图像   │ │ │预处理参数   │ │ │ 识别结果         │ │
│  └────────────┘ │ │ - 放大倍数  │ │ │ [文本框]         │ │
│  ┌────────────┐ │ │ - 中值滤波  │ │ │                  │ │
│  │ 预处理图像 │ │ │ - 对比度    │ │ ├──────────────────┤ │
│  └────────────┘ │ │ - 锐化      │ │ │ 性能统计         │ │
│                  │ │ - 二值化    │ │ │ - 耗时: XX ms    │ │
│  [开始测试]     │ ├─────────────┤ │ │ - 准确率: XX%    │ │
│                  │ │OCR参数      │ │ │ - 成功次数: X    │ │
│                  │ │ - 语言      │ │ ├──────────────────┤ │
│                  │ │ - PSM模式   │ │ │ 参数建议         │ │
│                  │ │ - 预处理模式│ │ │ [建议内容]       │ │
│                  │ ├─────────────┤ │ └──────────────────┘ │
│                  │ │测试参数     │ │                      │
│                  │ │ - 关键词    │ │                      │
│                  │ │ - 预期结果  │ │                      │
│                  │ └─────────────┘ │                      │
├──────────────────┴─────────────────┴──────────────────────┤
│  状态栏: 就绪 | 当前语言: chi_sim | 测试次数: 0           │
└────────────────────────────────────────────────────────────┘
```

**关键属性:**

```python
class OCRTestMainWindow(ctk.CTk):
    def __init__(self):
        self.screenshot_panel = ScreenshotPanel(self)
        self.param_panel = ParamPanel(self)
        self.result_panel = ResultPanel(self)
        self.test_runner = TestRunner()
        self.param_manager = ParameterManager()
        
        self.current_image: Optional[Image.Image] = None
        self.test_history: List[TestResult] = []
```

### 4.2 截图面板 (ScreenshotPanel)

**功能:**
- 显示原始图像
- 显示预处理后图像
- 支持区域选择
- 图像缩放适应

**关键方法:**

```python
class ScreenshotPanel(ctk.CTkFrame):
    def set_original_image(self, image: Image.Image) -> None:
        """设置原始图像"""
        
    def set_preprocessed_image(self, image: Image.Image) -> None:
        """设置预处理图像"""
        
    def clear_images(self) -> None:
        """清空图像"""
        
    def enable_region_selection(self) -> None:
        """启用区域选择模式"""
```

### 4.3 参数面板 (ParamPanel)

**功能:**
- 预处理参数滑块
- OCR参数选择
- 测试参数输入
- 参数预设选择

**参数控件映射:**

| 参数 | 控件类型 | 范围 | 默认值 |
|------|---------|------|--------|
| 放大倍数 | CTkSlider | 1.0-5.0 | 2.5 |
| 中值滤波大小 | CTkSlider | 1-7 | 3 |
| 对比度增强 | CTkSlider | 0.5-5.0 | 2.5 |
| 锐化强度 | CTkSlider | 0.5-5.0 | 2.0 |
| 锐化次数 | CTkSlider | 1-5 | 2 |
| 二值化阈值 | CTkSlider | 50-200 | 130 |
| 语言 | CTkOptionMenu | eng/chi_sim/chi_tra | chi_sim |
| PSM模式 | CTkOptionMenu | 6/7/11 | 7 |
| 预处理模式 | CTkOptionMenu | normal/artistic | artistic |

**关键方法:**

```python
class ParamPanel(ctk.CTkFrame):
    def get_params(self) -> Dict[str, Any]:
        """获取当前参数"""
        
    def set_params(self, params: Dict[str, Any]) -> None:
        """设置参数"""
        
    def reset_to_default(self) -> None:
        """重置为默认参数"""
        
    def on_param_change(self, callback: Callable) -> None:
        """参数变化回调"""
```

### 4.4 结果面板 (ResultPanel)

**功能:**
- 显示识别结果文本
- 显示性能统计
- 显示参数建议
- 测试历史记录

**关键方法:**

```python
class ResultPanel(ctk.CTkFrame):
    def display_result(self, result: TestResult) -> None:
        """显示测试结果"""
        
    def display_statistics(self, stats: StatisticsReport) -> None:
        """显示统计信息"""
        
    def display_suggestion(self, suggestion: str) -> None:
        """显示参数建议"""
        
    def clear(self) -> None:
        """清空结果"""
```

---

## 5 测试流程设计

### 5.1 单次测试流程

```
用户点击"开始测试"
    │
    ├── 1. 获取当前图像
    │       └── 如果无图像,提示用户先截图或加载
    │
    ├── 2. 获取当前参数
    │       └── 从ParamPanel读取所有参数
    │
    ├── 3. 执行预处理
    │       ├── 根据语言选择预处理方法
    │       ├── 应用自定义参数
    │       └── 更新预处理图像显示
    │
    ├── 4. 执行OCR识别
    │       ├── 记录开始时间
    │       ├── 调用OCRTester.test_text_recognition()
    │       └── 记录结束时间
    │
    ├── 5. 计算准确率
    │       ├── 如果提供了预期结果
    │       └── 计算Levenshtein相似度
    │
    ├── 6. 显示结果
    │       ├── 更新ResultPanel
    │       ├── 添加到测试历史
    │       └── 更新统计信息
    │
    └── 7. 生成参数建议
            ├── 分析测试结果
            └── 提供优化建议
```

### 5.2 性能测试流程

```
用户点击"性能测试"
    │
    ├── 1. 设置测试迭代次数 (默认10次)
    │
    ├── 2. 循环执行测试
    │       for i in range(iterations):
    │           ├── 执行OCR识别
    │           ├── 记录耗时
    │           └── 记录结果
    │
    ├── 3. 计算统计数据
    │       ├── 平均耗时
    │       ├── 最小/最大耗时
    │       ├── 成功率
    │       └── 平均准确率
    │
    └── 4. 生成报告
            ├── 显示统计图表
            └── 导出报告文件
```

---

## 6 参数优化策略

### 6.1 中文识别优化

**问题:** 中文文字笔画复杂,小字体识别困难

**优化策略:**
1. 增加放大倍数 (2.5-3.5倍)
2. 增强对比度 (2.0-3.0倍)
3. 多次锐化 (2-3次)
4. 调整二值化阈值 (120-140)

**测试建议:**
- 使用不同大小的中文字体测试
- 对比不同放大倍数的效果
- 测试不同对比度增强值

### 6.2 英文识别优化

**问题:** 英文字体多样,部分艺术字体识别困难

**优化策略:**
1. 适度放大 (1.5-2.0倍)
2. 中等对比度 (1.5-2.0倍)
3. 单次锐化 (1.0-1.5倍)
4. 标准二值化 (120-140)

**测试建议:**
- 测试不同字体类型
- 对比不同PSM模式
- 测试艺术字体预处理效果

### 6.3 数字识别优化

**问题:** 数字相似度高,容易混淆 (0/O, 1/l/I)

**优化策略:**
1. 使用数字白名单
2. 尝试不同PSM模式
3. 提高对比度
4. 降低二值化阈值

**测试建议:**
- 测试不同数字组合
- 对比有无白名单的效果
- 测试不同提取模式

---

## 7 准确率评估方法

### 7.1 文本相似度计算

使用Levenshtein距离计算相似度:

```python
def levenshtein_similarity(s1: str, s2: str) -> float:
    """计算Levenshtein相似度
    
    Args:
        s1: 字符串1
        s2: 字符串2
        
    Returns:
        相似度 (0.0-1.0)
    """
    if not s1 or not s2:
        return 0.0
    
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1.0 - (distance / max_len)
```

### 7.2 数字准确率计算

```python
def number_accuracy(recognized: float, expected: float) -> float:
    """计算数字识别准确率
    
    Args:
        recognized: 识别值
        expected: 预期值
        
    Returns:
        准确率 (0.0-1.0)
    """
    if expected == 0:
        return 1.0 if recognized == 0 else 0.0
    
    error = abs(recognized - expected) / abs(expected)
    return max(0.0, 1.0 - error)
```

### 7.3 关键词检测准确率

```python
def keyword_accuracy(recognized: str, keywords: List[str]) -> float:
    """计算关键词检测准确率
    
    Args:
        recognized: 识别文本
        keywords: 关键词列表
        
    Returns:
        准确率 (0.0-1.0)
    """
    if not keywords:
        return 1.0
    
    recognized_lower = recognized.lower()
    found_count = sum(1 for kw in keywords if kw.lower() in recognized_lower)
    return found_count / len(keywords)
```

---

## 8 性能指标

### 8.1 响应时间要求

| 操作 | 目标响应时间 |
|------|------------|
| 截图 | < 500ms |
| 预处理 | < 200ms |
| OCR识别 | < 2000ms |
| 参数更新 | < 100ms |
| 界面渲染 | < 50ms |

### 8.2 准确率目标

| 语言类型 | 目标准确率 |
|---------|-----------|
| 中文 | > 85% |
| 英文 | > 90% |
| 数字 | > 95% |

---

## 9 扩展性设计

### 9.1 插件式预处理

支持自定义预处理插件:

```python
class PreprocessorPlugin(ABC):
    @abstractmethod
    def process(self, image: Image.Image) -> Image.Image:
        """处理图像"""
        
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        
    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """获取参数"""
```

### 9.2 批量测试支持

支持批量导入测试图片:

```python
def batch_test(
    self,
    image_dir: str,
    params: Dict[str, Any]
) -> BatchTestReport:
    """批量测试
    
    Args:
        image_dir: 图片目录
        params: 测试参数
        
    Returns:
        批量测试报告
    """
```

### 9.3 自动化测试

支持自动化测试脚本:

```python
def run_automated_test(
    self,
    test_config: str
) -> AutomatedTestReport:
    """运行自动化测试
    
    Args:
        test_config: 测试配置文件路径
        
    Returns:
        自动化测试报告
    """
```

---

## 10 部署和使用

### 10.1 启动方式

**独立启动:**

```bash
python ocr_test_tool.py
```

**从主应用启动:**

```python
from bt_gui.ocr_test_tool.main_window import OCRTestMainWindow

app = OCRTestMainWindow()
app.mainloop()
```

### 10.2 配置文件

默认配置文件位置: `config/ocr_test_params.json`

用户可以保存自定义配置到任意位置。

### 10.3 测试报告

测试报告保存为JSON格式:

```json
{
  "timestamp": "2026-04-11T12:00:00",
  "test_type": "text_recognition",
  "params": {...},
  "results": [...],
  "statistics": {
    "avg_time": 1234.5,
    "avg_accuracy": 0.87,
    "success_rate": 0.9
  }
}
```

---

## 11 开发计划

### 11.1 开发阶段

**阶段1: 核心功能 (优先级: 高)**
- 图像预处理器
- OCR测试器
- 参数管理器
- 测试执行器

**阶段2: GUI界面 (优先级: 高)**
- 主窗口框架
- 截图面板
- 参数面板
- 结果面板

**阶段3: 测试和优化 (优先级: 高)**
- 单元测试
- 集成测试
- 性能优化

**阶段4: 扩展功能 (优先级: 中)**
- 批量测试
- 自动化测试
- 插件支持

### 11.2 验收标准

- ✅ 能够实时截图并测试
- ✅ 参数调节实时生效
- ✅ 准确显示预处理效果
- ✅ 正确统计性能指标
- ✅ 参数可保存和加载
- ✅ 与现有OCR系统参数一致

---

## 12 风险和限制

### 12.1 已知限制

1. **Tesseract依赖:** 需要正确安装Tesseract OCR
2. **语言包:** 需要下载对应语言的数据包
3. **性能瓶颈:** 图像预处理可能耗时较长
4. **准确率上限:** Tesseract本身识别能力有限

### 12.2 风险缓解

1. **依赖检查:** 启动时检查Tesseract是否可用
2. **错误处理:** 完善的异常处理和用户提示
3. **性能优化:** 使用缓存和异步处理
4. **参数建议:** 提供基于测试结果的参数优化建议

---

## 13 总结

本设计文档详细描述了OCR测试工具的架构、组件、流程和实现细节。该工具将帮助用户快速测试和优化OCR识别参数，提升中英文和数字的识别准确率。

**核心优势:**
- 独立运行，不影响现有系统
- 可视化参数调节，直观易用
- 实时预览，快速迭代
- 详细统计，科学优化
- 参数管理，便于复用

**下一步行动:**
1. 创建实现计划
2. 开发核心模块
3. 开发GUI界面
4. 测试验证
5. 文档完善
