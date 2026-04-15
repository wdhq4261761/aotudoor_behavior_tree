# "DD按键"功能实现方法对比分析报告

## 一、概述

本报告对 `autodoor_behavior_tree` 和 `autodoor` 两个项目中"DD按键"（DD虚拟键盘）功能的实现方法进行全面梳理与对比分析。两个项目均实现了基于DD虚拟键盘的输入控制功能，但实现细节存在一定差异。

---

## 二、相关文件清单

### 2.1 autodoor_behavior_tree 项目

| 文件路径 | 功能说明 |
|---------|---------|
| `bt_utils/dd_input.py` | DD虚拟键盘输入控制器核心实现 |
| `bt_utils/hook_dd_input.py` | DD输入初始化钩子（设置环境变量） |
| `bt_utils/base_input.py` | 输入控制器抽象基类 |
| `bt_utils/input_controller.py` | 输入控制器（基于pyautogui） |
| `bt_utils/vk_mapping.py` | Windows虚拟键码映射表 |
| `hooks/hook_dd_input.py` | PyInstaller运行时钩子 |
| `build_dd.bat` | DD版本编译脚本 |
| `autodoor_bt_dd.spec` | PyInstaller DD版配置文件 |
| `bt_nodes/actions/keyboard.py` | 键盘动作节点 |
| `bt_nodes/actions/mouse.py` | 鼠标动作节点 |
| `bt_core/context.py` | 执行上下文（调用输入控制器） |

### 2.2 autodoor 项目

| 文件路径 | 功能说明 |
|---------|---------|
| `input/dd_input.py` | DD虚拟键盘输入控制器核心实现 |
| `input/controller.py` | 输入控制器工厂（统一调度） |
| `input/base.py` | 输入控制器抽象基类 |
| `input/pyautogui_input.py` | PyAutoGUI输入控制器实现 |
| `input/key_mapping.py` | 按键名称映射与DD键码 |
| `input/__init__.py` | 模块导出接口 |
| `hooks/hook_dd_input.py` | PyInstaller运行时钩子 |
| `build_dd.bat` | DD版本编译脚本 |
| `autodoor_dd.spec` | PyInstaller DD版配置文件 |
| `modules/input.py` | 统一按键执行器 |
| `core/controller.py` | 核心控制器 |

---

## 三、核心实现分析

### 3.1 DD虚拟键盘加载机制

#### 3.1.1 autodoor_behavior_tree 项目

```python
# bt_utils/dd_input.py - DLL加载逻辑
def _load_dd_dll(self) -> bool:
    possible_paths = []
    if self._dll_path:
        possible_paths.append(self._dll_path)
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths.extend([
        os.path.join(base_path, "DD64.dll"),
        os.path.join(base_path, "drivers", "DD64.dll"),
        os.path.join(base_path, "..", "drivers", "DD64.dll"),
        os.path.join(os.path.dirname(base_path), "drivers", "DD64.dll"),
    ])
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                self._dd_dll = ctypes.windll.LoadLibrary(path)
                result = self._dd_dll.DD_btn(0)
                if result == 1:
                    self._available = True
                    return True
            except Exception as e:
                continue
    
    return False
```

**特点：**
- 支持4个DLL路径搜索
- 使用`DD_btn(0)`验证DLL可用性
- 不支持PyInstaller打包后的路径解析（缺少`sys.frozen`检查）

#### 3.1.2 autodoor 项目

```python
# input/dd_input.py - DLL加载逻辑
def _load_dd_dll(self) -> bool:
    possible_paths = []
    if self._dll_path:
        possible_paths.append(self._dll_path)
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # 新增：支持PyInstaller打包后的路径
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    
    possible_paths.extend([
        os.path.join(base_path, "DD64.dll"),
        os.path.join(base_path, "drivers", "DD64.dll"),
        os.path.join(base_path, "..", "drivers", "DD64.dll"),
        os.path.join(os.path.dirname(base_path), "drivers", "DD64.dll"),
    ])
    
    # ... 后续逻辑相同
```

**特点：**
- 与autodoor_behavior_tree项目基本一致
- 新增对PyInstaller打包环境的支持（`sys.frozen`检查）
- 更好地支持编译后的可执行文件运行

---

### 3.2 键码转换机制

#### 3.2.1 统一VK_CODE_MAP

两个项目使用完全相同的Windows虚拟键码映射表：

```python
VK_CODE_MAP = {
    'backspace': 0x08,
    'tab': 0x09,
    'enter': 0x0D,
    'shift': 0x10,
    'control': 0x11,
    'ctrl': 0x11,
    'alt': 0x12,
    # ... 完整覆盖所有标准按键
    'a': 0x41, 'b': 0x42, ...,
    'f1': 0x70, 'f2': 0x71, ...,
    'numpad0': 0x60, ...,
}
```

#### 3.2.2 DD键码动态转换

两个项目均使用`DD_todc`函数动态将Windows VK码转换为DD码：

```python
def _get_dd_code(self, key: str) -> int:
    key_lower = key.lower()
    
    # 使用缓存优化性能
    if key_lower in self._vk_cache:
        return self._vk_cache[key_lower]
    
    vk_code = VK_CODE_MAP.get(key_lower)
    
    # 动态调用DD库函数转换
    if self._available and self._dd_dll:
        dd_code = self._dd_dll.DD_todc(vk_code)
        if dd_code > 0:
            self._vk_cache[key_lower] = dd_code
            return dd_code
    
    return 0
```

**特点：**
- 使用键码缓存提高重复按键性能
- 支持动态VK到DD码转换
- 对未知按键有错误处理机制

---

### 3.3 按键与鼠标操作接口

#### 3.3.1 键盘操作

| 操作 | DD函数 | autodoor_behavior_tree | autodoor |
|-----|-------|----------------------|----------|
| 按下按键 | `DD_key(dd_code, 1)` | ✅ key_down() | ✅ key_down() |
| 抬起按键 | `DD_key(dd_code, 2)` | ✅ key_up() | ✅ key_up() |
| 单次按键 | key_down + delay + key_up | ✅ press_key() | ✅ press_key() |

#### 3.3.2 鼠标操作

| 操作 | DD函数 | autodoor_behavior_tree | autodoor |
|-----|-------|----------------------|----------|
| 移动鼠标 | `DD_mov(x, y)` | ✅ mouse_move() | ✅ mouse_move() |
| 相对移动 | `DD_movR(dx, dy)` | ✅ mouse_move_relative() | ✅ mouse_move_relative() |
| 按下鼠标 | `DD_btn(1/4/16)` | ✅ mouse_down() | ✅ mouse_down() |
| 抬起鼠标 | `DD_btn(2/8/32)` | ✅ mouse_up() | ✅ mouse_up() |
| 鼠标点击 | mouse_down + mouse_up | ✅ mouse_click() | ✅ mouse_click() |
| 滚轮滚动 | `DD_whl(clicks)` | ✅ mouse_scroll() | ✅ mouse_scroll() |

**鼠标按键DD码对照表：**
```python
# 按下
btn_map = {'left': 1, 'right': 4, 'middle': 16}
# 抬起  
btn_map = {'left': 2, 'right': 8, 'middle': 32}
```

---

### 3.4 DD启用机制

#### 3.4.1 环境变量控制

两个项目均通过环境变量`AUTODOOR_USE_DD`控制是否启用DD：

```python
# hooks/hook_dd_input.py（两个项目相同）
import os
os.environ['AUTODOOR_USE_DD'] = '1'
```

#### 3.4.2 编译时配置

**autodoor_behavior_tree:**
```batch
# build_dd.bat
echo Starting PyInstaller build (DD version)...
pyinstaller autodoor_bt_dd.spec --clean
```

**autodoor:**
```batch
# build_dd.bat
set AUTODOOR_USE_DD=1
pyinstaller autodoor_dd.spec --noconfirm
```

#### 3.4.3 PyInstaller钩子配置

```python
# autodoor_bt_dd.spec / autodoor_dd.spec
runtime_hooks=['hooks/hook_dd_input.py'],

data_files = [
    # ...
    (os.path.join(project_root, 'drivers/DD64.dll'), 'drivers'),
]
```

---

### 3.5 输入控制器架构

#### 3.5.1 autodoor_behavior_tree 项目

```python
# bt_utils/input_controller.py
class InputController:
    """基于pyautogui的输入控制器"""
    
    def key_press(self, key: str, action: str = "press", duration: int = 0):
        if action == "press":
            pyautogui.press(key)
        elif action == "down":
            pyautogui.keyDown(key)
        elif action == "up":
            pyautogui.keyUp(key)
    
    def mouse_click(self, button: str = "left", position: tuple = None, ...):
        # 使用pyautogui实现
```

**特点：**
- 直接使用pyautogui实现
- 无工厂模式选择
- 不支持运行时切换到DD

#### 3.5.2 autodoor 项目

```python
# input/controller.py
USE_DD_INPUT = os.environ.get('AUTODOOR_USE_DD', '0') == '1'

class InputController:
    """输入控制器工厂（兼容层）"""
    
    def __init__(self, app=None, method: str = None):
        if method is None:
            if USE_DD_INPUT:
                method = 'dd'
            else:
                method = 'pyautogui'
        
        if method == 'dd':
            impl = _get_dd_input(self.app)
            if impl and impl.is_available:
                self._impl = impl
                return
        
        self._impl = _get_pyautogui_input(self.app)
    
    def press_key(self, key, delay=0, priority=0):
        with self.key_lock.acquire(priority):
            return self._impl.press_key(key, delay, priority)
```

**特点：**
- 工厂模式设计
- 支持DD和PyAutoGUI双方案
- 通过环境变量或参数选择实现
- 支持优先级锁（PriorityLock）
- 更好的运行时错误处理

---

### 3.6 行为树节点集成

#### 3.6.1 autodoor_behavior_tree 项目

```python
# bt_nodes/actions/keyboard.py
class KeyPressNode(ActionNode):
    def _execute_action(self, context) -> NodeStatus:
        context.execute_key_press(self.key, self.action, self.duration)
        return NodeStatus.SUCCESS

# bt_nodes/actions/mouse.py  
class MouseClickNode(ActionNode):
    def _execute_action(self, context) -> NodeStatus:
        context.execute_mouse_click(self.button, position, self.action, self.duration)
        return NodeStatus.SUCCESS
```

#### 3.6.2 执行上下文调用链

```python
# bt_core/context.py
def execute_key_press(self, key: str, action: str = "press", duration: int = 0):
    if self._input_controller is None:
        from bt_utils.input_controller import InputController
        self._input_controller = InputController()
    
    self._input_controller.key_press(key, action, duration)
```

---

## 四、对比分析总结

### 4.1 相同点

| 对比项 | 说明 |
|-------|------|
| 核心DD实现 | 两个项目的`dd_input.py`实现几乎完全相同 |
| VK键码映射 | 使用完全一致的`VK_CODE_MAP` |
| DD函数调用 | 均使用`DD_key`、`DD_btn`、`DD_mov`、`DD_whl`等函数 |
| 鼠标键码 | 相同的按键码映射规则 |
| 键码缓存 | 都实现了`_vk_cache`缓存机制 |
| 编译打包 | 均支持DD版的PyInstaller打包 |

### 4.2 差异点

| 差异项 | autodoor_behavior_tree | autodoor |
|-------|----------------------|----------|
| **PyInstaller兼容** | 不支持打包后路径解析 | 支持`sys._MEIPASS`路径 |
| **控制器架构** | 直接使用pyautogui | 工厂模式，支持DD/PyAutoGUI切换 |
| **优先级控制** | 无 | 支持`PriorityLock`优先级锁 |
| **错误处理** | 基础异常捕获 | 更完善的权限错误处理 |
| **模块结构** | 分散在bt_utils | 集中于input模块 |
| **日志输出** | 基础日志 | 统一的日志管理 |

---

## 五、技术选型分析

### 5.1 autodoor项目优势

1. **更好的扩展性**：工厂模式便于后续添加新的输入方式
2. **编译兼容性**：支持PyInstaller打包后的运行环境
3. **优先级控制**：解决多模块竞争输入的问题
4. **统一错误处理**：权限错误等特殊情况有专门处理

### 5.2 autodoor_behavior_tree项目特点

1. **简洁实现**：代码相对简洁直观
2. **行为树集成**：与BT节点系统深度集成
3. **DD专用**：通过编译选项生成DD专用版本

---

## 六、结论与建议

### 6.1 结论

两个项目在DD按键功能的核心实现上高度一致，均能有效实现基于DD虚拟键盘的输入控制。主要差异在于：

1. **autodoor项目**采用了更完善的工厂模式和运行时切换机制
2. **autodoor_behavior_tree项目**更侧重于行为树节点的集成

### 6.2 建议

如需将两个项目的DD功能统一，建议：

1. 将`autodoor`项目的`sys.frozen`路径解析逻辑合并到`autodoor_behavior_tree`项目
2. 考虑将`autodoor`的工厂模式引入`autodoor_behavior_tree`
3. 统一键码缓存和错误处理机制

---

**报告生成时间：** 2026-04-15

**分析版本：**
- autodoor_behavior_tree: 最新版
- autodoor: 最新版
