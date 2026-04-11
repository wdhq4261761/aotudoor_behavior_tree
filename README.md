# AutoDoor 行为树系统

<div align="center">

一个独立的可视化行为树编辑与执行框架，面向 Windows 平台的自动化场景

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

</div>

***

## 📖 项目简介

AutoDoor 行为树系统是一个功能完整的可视化行为树编辑与执行框架，专为 Windows 平台的自动化场景设计（游戏辅助、RPA 流程等）。系统提供图形化编辑器、丰富的节点类型、脚本录制、OCR 识别、DD 虚拟键盘等能力，支持标准版与 DD 游戏版两种打包模式。

### ✨ 核心特性

| 特性              | 说明                                     |
| --------------- | -------------------------------------- |
| 🎨 **可视化编辑器**   | 基于 CustomTkinter 的节点式编辑器，支持拖拽、连线、缩放、框选 |
| ⚙️ **行为树引擎**    | 独立线程执行，支持启动/暂停/停止/恢复                   |
| 🧩 **16 种内置节点** | 3 种复合节点 + 5 种条件节点 + 8 种动作节点            |
| 📊 **黑板系统**     | 观察者模式的数据共享机制，节点间解耦通信                   |
| 💾 **序列化**      | JSON/YAML/TXT 多格式持久化，版本化数据结构           |
| ↩️ **撤销/重做**    | Command 模式，支持 100 步历史                  |
| 🎮 **DD 虚拟键盘**  | 游戏级硬件模拟输入，绕过大多数输入检测                    |
| 👁️ **OCR 集成**  | 内嵌 RapidOCR，支持中英文识别，速度更快         |
| 📝 **脚本录制**     | TXT 脚本录制与回放                            |
| 📦 **双版打包**     | 标准版 (PyAutoGUI) 与游戏版 (DD64.dll)        |

***

## **联系作者**

QQ群：298117299 进群密码：autodoor
B站主页：https://space.bilibili.com/263150759

***

## 🛠️ 技术栈

```
Python 3.10+
├── GUI 框架:    CustomTkinter + Tkinter Canvas
├── 图像处理:    Pillow, OpenCV, imagehash
├── OCR 引擎:    Tesseract 5.x + pytesseract
├── 输入模拟:    PyAutoGUI (标准版) / DD64.dll (游戏版)
├── 音频播放:    pygame.mixer
├── 打包工具:    PyInstaller
└── CI/CD:       GitHub Actions
```

***

## 🏗️ 系统架构

### 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    表现层 (Presentation)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 行为树    │  │ 脚本录制  │  │  设置    │              │
│  │ 编辑器    │  │  标签页   │  │  标签页  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
├─────────────────────────────────────────────────────────┤
│                    应用层 (Application)                   │
│  ┌──────────────────────────────────────────┐           │
│  │         BehaviorTreeEditor               │           │
│  │  (编辑器编排: 工具栏/画布/面板/撤销重做)  │           │
│  └──────────────────────────────────────────┘           │
├─────────────────────────────────────────────────────────┤
│                    领域层 (Domain)                        │
│  ┌────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐   │
│  │ 节点   │ │ 执行引擎  │ │  黑板    │ │  序列化器  │   │
│  │ 模型   │ │  Engine   │ │Blackboard│ │ Serializer│   │
│  └────────┘ └──────────┘ └──────────┘ └───────────┘   │
├─────────────────────────────────────────────────────────┤
│                  基础设施层 (Infrastructure)              │
│  ┌──────────┐ ┌────────────┐ ┌───────────┐             │
│  │ 输入控制  │ │ 截图管理器  │ │ OCR 管理器 │             │
│  │InputCtrl │ │Screenshot  │ │OCRManager │             │
│  └──────────┘ └────────────┘ └───────────┘             │
└─────────────────────────────────────────────────────────┘
```

### 模块结构

```
autodoor_behavior_tree/
├── main.py                    # 应用入口
├── bt_core/                   # 核心领域层
│   ├── nodes.py               # 节点抽象与实现
│   ├── engine.py              # 行为树执行引擎
│   ├── blackboard.py          # 黑板系统
│   ├── context.py             # 执行上下文
│   ├── serializer.py          # 序列化/反序列化
│   ├── registry.py            # 节点类型注册中心
│   ├── config.py              # 节点配置数据类
│   └── status.py              # 节点状态枚举
├── bt_nodes/                  # 具体节点实现
│   ├── actions/               # 动作节点
│   │   ├── keyboard.py        #   按键节点
│   │   ├── mouse.py           #   鼠标节点
│   │   ├── delay.py           #   延时节点
│   │   ├── variable.py        #   变量节点
│   │   ├── script.py          #   脚本节点
│   │   ├── code.py            #   代码节点
│   │   └── alarm.py           #   报警节点
│   └── conditions/            # 条件节点
│       ├── ocr.py             #   OCR检测节点
│       ├── image.py           #   图像匹配节点
│       ├── color.py           #   颜色检测节点
│       ├── number.py          #   数字比较节点
│       └── variable.py        #   变量判断节点
├── bt_gui/                    # GUI 表现层
│   ├── app.py                 #   主应用窗口
│   ├── theme.py               #   主题与样式
│   ├── widgets.py             #   通用组件
│   ├── script_tab.py          #   脚本录制标签页
│   ├── settings_tab.py        #   设置标签页
│   └── bt_editor/             #   行为树编辑器
│       ├── editor.py          #     编辑器主控
│       ├── canvas.py          #     画布（节点/连线/交互）
│       ├── node_item.py       #     节点视觉项
│       ├── palette.py         #     节点面板
│       ├── property.py        #     属性面板
│       ├── toolbar.py         #     工具栏
│       ├── undo_redo.py       #     撤销/重做系统
│       └── constants.py       #     节点类型常量
├── bt_utils/                  # 基础设施层
│   ├── input_controller.py    #   PyAutoGUI 输入控制
│   ├── dd_input.py            #   DD 虚拟键盘控制
│   ├── screenshot.py          #   截图管理器
│   ├── ocr_manager.py         #   OCR 管理器
│   ├── alarm.py               #   报警播放器
│   ├── image_processor.py     #   图像处理工具
│   ├── recorder.py            #   脚本录制器
│   ├── script_executor.py     #   脚本执行器
│   ├── resource_manager.py    #   资源管理器
│   └── ...
├── config/                    # 配置管理
│   ├── settings.json          #   默认设置
│   └── settings_manager.py    #   设置管理器
├── drivers/                   # 驱动文件
│   └── DD64.dll               #   DD虚拟键盘驱动
├── tesseract/                 # Tesseract OCR 完整运行时
├── assets/                    # 资源文件
│   ├── icons/                 #   图标
│   └── sounds/                #   音效
└── ...
```

***

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本
- Windows 操作系统
- Tesseract OCR 5.x（可选，用于 OCR 功能）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python main.py
```

### 打包应用

**标准版打包：**

```bash
build_standard.bat
```

**游戏版打包（包含 DD 虚拟键盘）：**

```bash
build_dd.bat
```

***

## 🧩 节点类型

### 复合节点 (Composite Nodes)

| 节点               | 说明                           |
| ---------------- | ---------------------------- |
| **SequenceNode** | 顺序节点 - 按顺序执行子节点，所有子节点成功才返回成功 |
| **SelectorNode** | 选择节点 - 按顺序执行子节点，任一成功即返回成功    |
| **ParallelNode** | 并行节点 - 同时执行所有子节点，根据策略决定成功条件  |

### 条件节点 (Condition Nodes)

| 节点                        | 说明                          |
| ------------------------- | --------------------------- |
| **OCRConditionNode**      | OCR 检测节点 - 检测屏幕指定区域是否包含目标文字 |
| **ImageConditionNode**    | 图像匹配节点 - 检测屏幕是否匹配目标图像模板     |
| **ColorConditionNode**    | 颜色检测节点 - 检测屏幕指定区域是否包含目标颜色   |
| **NumberConditionNode**   | 数字比较节点 - 识别屏幕数字并与目标值比较      |
| **VariableConditionNode** | 变量判断节点 - 判断黑板变量值是否满足条件      |

### 动作节点 (Action Nodes)

| 节点                  | 说明                 |
| ------------------- | ------------------ |
| **KeyPressNode**    | 按键节点 - 执行键盘按键操作    |
| **MouseClickNode**  | 鼠标点击节点 - 执行鼠标点击操作  |
| **MouseMoveNode**   | 鼠标移动节点 - 移动鼠标到指定位置 |
| **DelayNode**       | 延时节点 - 等待指定时间      |
| **SetVariableNode** | 设置变量节点 - 设置/修改黑板变量 |
| **ScriptNode**      | 脚本节点 - 执行外部脚本文件    |
| **CodeNode**        | 代码节点 - 执行外部程序      |
| **AlarmNode**       | 报警节点 - 播放报警音效      |

***

## 🎯 核心功能

### 1. 可视化编辑器

- **节点拖拽**：从节点面板拖拽节点到画布
- **连线操作**：从输出端口拖拽到输入端口创建连线
- **框选移动**：框选多个节点批量移动
- **缩放平移**：滚轮缩放，右键拖拽平移画布
- **属性编辑**：选中节点后在属性面板编辑配置

### 2. 行为树执行

- **独立线程**：行为树在独立线程中执行，不阻塞 UI
- **状态可视化**：实时显示节点执行状态（成功/失败/运行中）
- **暂停恢复**：支持暂停和恢复执行
- **黑板系统**：节点间通过黑板共享数据

### 3. 撤销/重做系统

- 支持 100 步历史记录
- 所有编辑操作均可撤销/重做
- Command 模式实现

### 4. 自动保存与崩溃恢复

- 定时自动保存（默认 30 秒）
- 启动时自动恢复上次编辑状态
- 静默恢复，无需用户确认

***

## ⌨️ 快捷键

| 快捷键                       | 功能          |
| ------------------------- | ----------- |
| `Ctrl+Z`                  | 撤销          |
| `Ctrl+Y` / `Ctrl+Shift+Z` | 重做          |
| `Ctrl+S`                  | 保存          |
| `Ctrl+Shift+S`            | 另存为         |
| `Ctrl+O`                  | 打开          |
| `Ctrl+N`                  | 新建          |
| `Ctrl+C`                  | 复制选中节点      |
| `Ctrl+V`                  | 粘贴节点        |
| `Ctrl+X`                  | 剪切节点        |
| `Ctrl+D`                  | 复制并粘贴（快速复制） |
| `Delete` / `Backspace`    | 删除选中        |
| `Space`                   | 开始/停止运行     |
| `Escape`                  | 停止运行        |

***

## 🔧 配置管理

### 默认配置结构

```json
{
  "tesseract_path": "",
  "alarm_sound_path": "",
  "alarm_volume": 70,
  "shortcuts": {
    "start": "F10",
    "stop": "F12",
    "record": "F11"
  },
  "behavior_tree": {
    "tick_interval": 50,
    "auto_save_interval": 30,
    "default_format": "json"
  },
  "ui": {
    "theme": "dark",
    "language": "zh_CN",
    "font_size": 10
  }
}
```

***

## 📦 打包与部署

### 双版打包

| 版本  | Spec 文件               | 输出名称                       | 特殊包含                        |
| --- | --------------------- | -------------------------- | --------------------------- |
| 标准版 | `autodoor_bt.spec`    | `autodoor-bt-{ver}-normal` | tesseract, assets, config   |
| 游戏版 | `autodoor_bt_dd.spec` | `autodoor-bt-{ver}-game`   | +DD64.dll, +hook\_dd\_input |

### GitHub Actions CI/CD

项目包含 GitHub Actions 工作流配置，支持自动构建和发布：

1. 触发条件：push tag / manual dispatch
2. 版本号提取：从 main.py 的 VERSION 变量
3. 模块验证：检查关键依赖
4. 双版构建：PyInstaller --clean
5. 发布：创建 GitHub Release + 上传产物

***

## 🔌 扩展开发

### 添加自定义节点

1. 创建节点类，继承 `ActionNode` 或 `ConditionNode`
2. 实现 `tick()` / `_execute_action()` / `_check_condition()` 方法
3. 实现 `to_dict()` 和 `from_dict()` 方法
4. 在 `__init__.py` 中注册到 `NodeRegistry`
5. 在 `constants.py` 中添加显示名称和分类
6. 在 `property.py` 中添加配置 Schema

### 示例：自定义动作节点

```python
from bt_core.nodes import ActionNode, NodeStatus
from bt_core.registry import NodeRegistry

class CustomActionNode(ActionNode):
    NODE_TYPE = "CustomAction"
    
    def _execute_action(self, context):
        # 实现自定义逻辑
        return NodeStatus.SUCCESS
    
    def to_dict(self):
        data = super().to_dict()
        # 添加自定义序列化逻辑
        return data
    
    @classmethod
    def from_dict(cls, data):
        node = super().from_dict(data)
        # 添加自定义反序列化逻辑
        return node

# 注册节点
NodeRegistry.register("CustomAction", CustomActionNode)
```

***

## 📄 序列化格式

### JSON 数据结构（v2.0）

```json
{
  "version": "2.0",
  "format_type": "behavior_tree_standalone",
  "metadata": {
    "created_at": "2026-04-09T12:00:00",
    "modified_at": "2026-04-09T12:00:00",
    "app_version": "1.0.0"
  },
  "root_node": "node_1",
  "nodes": {
    "node_1": {
      "id": "node_1",
      "type": "SequenceNode",
      "config": { "name": "顺序", "enabled": true, "extra": {} },
      "children": ["node_2", "node_3"]
    }
  },
  "connections": [
    { "parent_id": "node_1", "child_id": "node_2" },
    { "parent_id": "node_1", "child_id": "node_3" }
  ]
}
```

***

## 🐛 故障排除

### OCR 无法使用

1. 确保已安装 Tesseract OCR 5.x
2. 检查 `tesseract/` 目录是否包含完整的运行时
3. 查看日志确认 Tesseract 路径是否正确检测

### DD 虚拟键盘无法使用

1. 确保 `drivers/DD64.dll` 文件存在
2. 检查是否有足够的系统权限
3. 尝试使用管理员权限运行

### 快捷键不生效

1. 确保应用窗口处于活动状态
2. 检查是否有其他应用占用了相同快捷键
3. 删除快捷键在输入框获得焦点时不触发（这是预期行为）

***

## 📚 文档

- [架构文档](doc/01_架构文档.md) - 系统架构和核心组件设计
- [详细实现方法](doc/02_详细实现方法.md) - 节点实现和关键机制
- [技术图表与伪代码](doc/03_技术图表与伪代码.md) - 类图、流程图和算法

***

## 📝 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

***

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

***

<div align="center">

**Made with ❤️ by Flown王砖家**

</div>
