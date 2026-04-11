# 开始节点实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现行为树的"开始"节点,作为根节点控制整个行为树的执行流程,支持重复执行次数控制,并具备不可删除的保护属性。

**Architecture:** 继承SequenceNode复用顺序执行逻辑,重写失败处理逻辑(失败后继续执行),添加重复执行控制。在节点层面添加保护标记,在画布和编辑器层面检查该标记以实现不可删除、不可复制、不可剪切的特性。

**Tech Stack:** Python 3.10+, CustomTkinter, Tkinter Canvas

---

## 第一阶段: 核心节点实现

### Task 1: 扩展节点基类添加保护属性

**Files:**
- Modify: `bt_core/nodes.py:15-30` (Node.__init__方法)
- Test: 无需测试(简单属性添加)

**Step 1: 读取Node类定义**

Run: Read file `bt_core/nodes.py` to understand current Node class structure

**Step 2: 在Node.__init__中添加_is_protected属性**

在`bt_core/nodes.py`的`Node.__init__`方法中,在`self._tick_count = 0`之后添加:

```python
self._is_protected = False  # 节点保护标记,防止被删除
```

**Step 3: 添加is_protected方法**

在`Node`类中添加公共方法:

```python
def is_protected(self) -> bool:
    """
    检查节点是否受保护(不可删除)
    
    Returns:
        bool: True表示受保护,False表示可删除
    """
    return self._is_protected
```

**Step 4: 验证修改**

Run: 检查代码语法是否正确
Expected: 无语法错误

**Step 5: Commit**

```bash
git add bt_core/nodes.py
git commit -m "feat(core): add node protection mechanism with is_protected property"
```

---

### Task 2: 创建StartNode类

**Files:**
- Modify: `bt_core/nodes.py` (在文件末尾添加StartNode类)
- Test: `tests/test_start_node.py` (创建测试文件)

**Step 1: 创建测试文件**

创建文件 `tests/test_start_node.py`:

```python
"""
StartNode单元测试
"""
import unittest
from bt_core.nodes import StartNode, NodeStatus
from bt_core.context import ExecutionContext
from bt_core.blackboard import Blackboard


class TestStartNode(unittest.TestCase):
    """StartNode测试类"""
    
    def test_create_start_node(self):
        """测试创建开始节点"""
        node = StartNode()
        self.assertEqual(node.NODE_TYPE, "StartNode")
        self.assertEqual(node.repeat_count, -1)
        self.assertTrue(node.is_protected())
    
    def test_repeat_count_default(self):
        """测试默认重复次数为-1(无限循环)"""
        node = StartNode()
        self.assertEqual(node.repeat_count, -1)
    
    def test_repeat_count_custom(self):
        """测试自定义重复次数"""
        from bt_core.config import NodeConfig
        config = NodeConfig()
        config.extra["repeat_count"] = 5
        node = StartNode(config=config)
        self.assertEqual(node.repeat_count, 5)
    
    def test_tick_no_children(self):
        """测试无子节点时返回SUCCESS"""
        node = StartNode()
        context = ExecutionContext()
        status = node.tick(context)
        self.assertEqual(status, NodeStatus.SUCCESS)
    
    def test_tick_with_running_child(self):
        """测试有RUNNING状态的子节点"""
        from bt_core.nodes import ActionNode
        
        class RunningAction(ActionNode):
            def _execute_action(self, context):
                return NodeStatus.RUNNING
        
        node = StartNode()
        child = RunningAction()
        node.add_child(child)
        
        context = ExecutionContext()
        status = node.tick(context)
        self.assertEqual(status, NodeStatus.RUNNING)
    
    def test_tick_failure_continues(self):
        """测试子节点失败后继续执行"""
        from bt_core.nodes import ActionNode
        
        class FailAction(ActionNode):
            def _execute_action(self, context):
                return NodeStatus.FAILURE
        
        class SuccessAction(ActionNode):
            def _execute_action(self, context):
                return NodeStatus.SUCCESS
        
        node = StartNode()
        fail_child = FailAction()
        success_child = SuccessAction()
        node.add_child(fail_child)
        node.add_child(success_child)
        
        context = ExecutionContext()
        status = node.tick(context)
        # 所有子节点执行完毕后应该返回RUNNING(因为默认无限循环)
        self.assertEqual(status, NodeStatus.RUNNING)


if __name__ == '__main__':
    unittest.main()
```

**Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_start_node.py -v`
Expected: FAIL with "StartNode not defined"

**Step 3: 在nodes.py中导入NodeStatus**

检查`bt_core/nodes.py`顶部是否已导入NodeStatus,如果没有则添加:

```python
from .status import NodeStatus
```

**Step 4: 实现StartNode类**

在`bt_core/nodes.py`文件末尾添加StartNode类:

```python
class StartNode(SequenceNode):
    """
    开始节点 - 行为树的根节点
    
    特性:
    - 继承SequenceNode的顺序执行逻辑
    - 失败后继续执行(不短路)
    - 支持重复执行次数控制
    - 不可删除、不可复制、不可剪切
    """
    NODE_TYPE = "StartNode"
    
    def __init__(self, node_id=None, config=None):
        super().__init__(node_id, config)
        self.repeat_count = self.config.get_int("repeat_count", -1)  # -1表示无限循环
        self._current_repeat = 0  # 当前重复次数
        self._is_protected = True  # 不可删除标记
    
    def tick(self, context: ExecutionContext) -> NodeStatus:
        """
        执行所有子节点,失败后继续执行
        
        与SequenceNode的区别:
        - SequenceNode: 任一子节点失败立即返回FAILURE
        - StartNode: 子节点失败后继续执行后续子节点
        
        Args:
            context: 执行上下文
            
        Returns:
            NodeStatus: 执行状态
        """
        if not self.children:
            return NodeStatus.SUCCESS
        
        # 执行所有子节点(不短路)
        has_running = False
        for child in self.children:
            if not child.config.enabled:
                continue
            
            status = child.tick(context)
            
            # 如果有子节点正在运行,记录状态但不中断执行
            if status == NodeStatus.RUNNING:
                has_running = True
        
        # 如果有子节点正在运行,返回RUNNING
        if has_running:
            return NodeStatus.RUNNING
        
        # 所有子节点执行完毕,处理重复逻辑
        self._current_repeat += 1
        
        if self.repeat_count == -1:
            # 无限循环模式
            self.reset()
            return NodeStatus.RUNNING
        elif self._current_repeat < self.repeat_count:
            # 继续重复
            self.reset()
            return NodeStatus.RUNNING
        else:
            # 达到重复次数,执行完成
            return NodeStatus.SUCCESS
    
    def reset(self) -> None:
        """重置节点状态"""
        super().reset()
        # 重置所有子节点
        for child in self.children:
            child.reset()
    
    def to_dict(self) -> dict:
        """
        序列化为字典
        
        Returns:
            Dict[str, Any]: 节点数据字典
        """
        data = super().to_dict()
        data["repeat_count"] = self.repeat_count
        data["_is_protected"] = self._is_protected
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "StartNode":
        """
        从字典反序列化
        
        Args:
            data: 节点数据字典
            
        Returns:
            StartNode: 节点实例
        """
        node = super().from_dict(data)
        node.repeat_count = data.get("repeat_count", -1)
        node._is_protected = data.get("_is_protected", True)
        return node
```

**Step 5: 运行测试验证通过**

Run: `python -m pytest tests/test_start_node.py -v`
Expected: PASS (所有测试通过)

**Step 6: Commit**

```bash
git add bt_core/nodes.py tests/test_start_node.py
git commit -m "feat(core): implement StartNode with failure-continue logic and repeat control"
```

---

### Task 3: 注册StartNode到节点注册中心

**Files:**
- Modify: `bt_core/registry.py`
- Test: `tests/test_registry.py` (添加测试)

**Step 1: 读取registry.py了解注册机制**

Run: Read file `bt_core/registry.py`

**Step 2: 在register_core_nodes函数中注册StartNode**

在`bt_core/registry.py`的`register_core_nodes()`函数中添加:

```python
from .nodes import StartNode

def register_core_nodes():
    """注册核心节点类型"""
    NodeRegistry.register("SequenceNode", SequenceNode)
    NodeRegistry.register("SelectorNode", SelectorNode)
    NodeRegistry.register("ParallelNode", ParallelNode)
    NodeRegistry.register("StartNode", StartNode)  # 新增
```

**Step 3: 添加注册测试**

在`tests/test_registry.py`中添加测试(如果文件不存在则创建):

```python
"""
节点注册中心测试
"""
import unittest
from bt_core.registry import NodeRegistry
from bt_core.nodes import StartNode


class TestNodeRegistry(unittest.TestCase):
    """节点注册中心测试"""
    
    def test_start_node_registered(self):
        """测试StartNode已注册"""
        node_class = NodeRegistry.get("StartNode")
        self.assertEqual(node_class, StartNode)
    
    def test_create_start_node_from_registry(self):
        """测试通过注册中心创建StartNode"""
        data = {
            "type": "StartNode",
            "id": "test_start",
            "name": "开始",
            "config": {"repeat_count": 5}
        }
        node = NodeRegistry.create_node(data)
        self.assertIsInstance(node, StartNode)
        self.assertEqual(node.repeat_count, 5)


if __name__ == '__main__':
    unittest.main()
```

**Step 4: 运行测试验证**

Run: `python -m pytest tests/test_registry.py::TestNodeRegistry::test_start_node_registered -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bt_core/registry.py tests/test_registry.py
git commit -m "feat(core): register StartNode to NodeRegistry"
```

---

## 第二阶段: UI集成

### Task 4: 更新主题系统添加开始节点颜色

**Files:**
- Modify: `bt_gui/theme.py`

**Step 1: 读取theme.py了解颜色配置**

Run: Read file `bt_gui/theme.py`

**Step 2: 在NODE_COLORS中添加start颜色**

在`bt_gui/theme.py`的`NODE_COLORS`字典中添加:

```python
NODE_COLORS = {
    "composite": "#1E40AF",    # 蓝色 - 复合节点
    "condition": "#BE185D",    # 粉色 - 条件节点
    "action": "#047857",       # 绿色 - 动作节点
    "decorator": "#B45309",    # 橙色 - 装饰器
    "start": "#F59E0B"         # 金色 - 开始节点(新增)
}
```

**Step 3: 验证修改**

Run: 检查Python语法
Expected: 无语法错误

**Step 4: Commit**

```bash
git add bt_gui/theme.py
git commit -m "feat(ui): add golden color for StartNode in theme"
```

---

### Task 5: 更新节点类型常量

**Files:**
- Modify: `bt_gui/bt_editor/constants.py`

**Step 1: 读取constants.py了解节点名称配置**

Run: Read file `bt_gui/bt_editor/constants.py`

**Step 2: 在NODE_TYPE_NAMES中添加StartNode**

在`bt_gui/bt_editor/constants.py`的`NODE_TYPE_NAMES`字典中添加:

```python
NODE_TYPE_NAMES = {
    "SequenceNode": "顺序",
    "SelectorNode": "选择",
    "ParallelNode": "并行",
    "StartNode": "开始",  # 新增
    # ... 其他节点类型
}
```

**Step 3: 验证修改**

Run: 检查Python语法
Expected: 无语法错误

**Step 4: Commit**

```bash
git add bt_gui/bt_editor/constants.py
git commit -m "feat(ui): add StartNode display name to constants"
```

---

### Task 6: 更新属性面板配置

**Files:**
- Modify: `bt_gui/bt_editor/property.py`

**Step 1: 读取property.py了解属性配置结构**

Run: Read file `bt_gui/bt_editor/property.py` to find PROPERTY_SCHEMAS

**Step 2: 在PROPERTY_SCHEMAS中添加StartNode配置**

在`bt_gui/bt_editor/property.py`的`PROPERTY_SCHEMAS`字典中添加:

```python
PROPERTY_SCHEMAS = {
    # ... 现有配置
    "StartNode": [
        {
            "key": "name",
            "label": "名称",
            "type": "text",
            "width": 120,
            "default": "开始",
            "editable": True
        },
        {
            "key": "repeat_count",
            "label": "重复次数",
            "type": "number",
            "width": 120,
            "default": -1,
            "min": -1,
            "tooltip": "-1表示无限循环,其他数字表示执行次数",
            "editable": True
        },
        {
            "key": "enabled",
            "label": "启用",
            "type": "bool",
            "default": True,
            "editable": True
        }
    ]
}
```

**Step 3: 验证修改**

Run: 检查Python语法
Expected: 无语法错误

**Step 4: Commit**

```bash
git add bt_gui/bt_editor/property.py
git commit -m "feat(ui): add property panel schema for StartNode"
```

---

### Task 7: 更新节点渲染逻辑

**Files:**
- Modify: `bt_gui/bt_editor/node_item.py`

**Step 1: 读取node_item.py了解节点渲染逻辑**

Run: Read file `bt_gui/bt_editor/node_item.py` to understand node rendering

**Step 2: 修改_get_category_color方法**

在`bt_gui/bt_editor/node_item.py`的`NodeItem`类中,找到`_get_category_color`方法并修改:

```python
def _get_category_color(self) -> str:
    """获取节点分类颜色"""
    if self.node_type == "StartNode":
        return Theme.NODE_COLORS["start"]
    
    # ... 其他节点类型的颜色判断
```

**Step 3: 修改_draw_node方法添加特殊图标**

在`bt_gui/bt_editor/node_item.py`的`NodeItem`类的`_draw_node`方法中,修改节点名称显示部分:

```python
# 绘制节点名称
display_name = self.node_name
if self.node_type == "StartNode":
    # 开始节点添加特殊图标
    display_name = "▶ " + display_name

self.canvas.create_text(
    x + 15, y + height / 2,
    text=display_name,
    fill=self._dark_colors['text_primary'],
    font=(Theme.FONTS['family'], 10),
    anchor="w",
    tags=("node_text", self.node_id)
)
```

**Step 4: 验证修改**

Run: 检查Python语法
Expected: 无语法错误

**Step 5: Commit**

```bash
git add bt_gui/bt_editor/node_item.py
git commit -m "feat(ui): add special rendering for StartNode with golden color and play icon"
```

---

## 第三阶段: 功能集成

### Task 8: 实现自动创建开始节点

**Files:**
- Modify: `bt_gui/bt_editor/editor.py`

**Step 1: 读取editor.py了解new_tree方法**

Run: Read file `bt_gui/bt_editor/editor.py` to find new_tree method

**Step 2: 在new_tree方法中添加自动创建逻辑**

在`bt_gui/bt_editor/editor.py`的`BehaviorTreeEditor`类的`new_tree`方法中添加:

```python
def new_tree(self):
    """新建项目时自动创建开始节点"""
    # 清空画布
    self.canvas.clear_canvas()
    
    # 导入StartNode
    from bt_core.nodes import StartNode
    
    # 创建开始节点
    start_node = StartNode()
    start_node.config.name = "开始"
    
    # 计算默认位置
    # 获取画布尺寸
    canvas_width = self.canvas.winfo_width()
    canvas_height = self.canvas.winfo_height()
    
    # 如果画布尺寸为0(尚未渲染),使用默认值
    if canvas_width <= 0:
        canvas_width = 800
    if canvas_height <= 0:
        canvas_height = 600
    
    # 左右居中
    x = canvas_width / 2
    
    # 上下位置偏顶部,预留顶部空间(约20%的高度)
    y = canvas_height * 0.2
    
    # 构建节点数据
    node_data = {
        "id": start_node.node_id,
        "type": "StartNode",
        "name": "开始",
        "enabled": True,
        "config": {
            "repeat_count": -1
        },
        "position": {
            "x": x,
            "y": y
        }
    }
    
    # 添加到画布
    self.canvas.add_node(node_data)
    
    # 清空撤销/重做栈
    self.command_manager.clear()
    
    # 重置文件路径
    self.file_path = None
```

**Step 3: 验证修改**

Run: 检查Python语法
Expected: 无语法错误

**Step 4: Commit**

```bash
git add bt_gui/bt_editor/editor.py
git commit -m "feat(editor): auto-create StartNode when creating new project"
```

---

### Task 9: 实现删除保护机制

**Files:**
- Modify: `bt_gui/bt_editor/canvas.py`

**Step 1: 读取canvas.py了解删除逻辑**

Run: Read file `bt_gui/bt_editor/canvas.py` to find delete method

**Step 2: 修改删除方法添加保护检查**

在`bt_gui/bt_editor/canvas.py`的`BehaviorTreeCanvas`类中,找到删除节点的方法(可能是`_delete_selected`或类似方法)并修改:

```python
def _delete_selected(self):
    """删除选中的节点"""
    from tkinter import messagebox
    
    nodes_to_delete = []
    protected_nodes = []
    
    for node_id in self.selected_nodes:
        node_item = self.nodes.get(node_id)
        if node_item:
            # 获取节点实例
            node = node_item.node
            if node and node.is_protected():
                # 记录受保护的节点
                protected_nodes.append(node_id)
                continue
            nodes_to_delete.append(node_id)
    
    # 如果有受保护的节点,显示提示
    if protected_nodes:
        messagebox.showwarning(
            "无法删除",
            "开始节点不可删除"
        )
    
    # 删除非保护节点
    if nodes_to_delete:
        command = RemoveNodesCommand(self, nodes_to_delete)
        self.command_manager.execute(command)
```

**Step 3: 验证修改**

Run: 检查Python语法
Expected: 无语法错误

**Step 4: Commit**

```bash
git add bt_gui/bt_editor/canvas.py
git commit -m "feat(canvas): prevent deletion of protected StartNode"
```

---

### Task 10: 实现复制/剪切保护机制

**Files:**
- Modify: `bt_gui/bt_editor/editor.py`

**Step 1: 读取editor.py了解复制/剪切方法**

Run: Read file `bt_gui/bt_editor/editor.py` to find copy and cut methods

**Step 2: 修改复制方法添加保护检查**

在`bt_gui/bt_editor/editor.py`的`BehaviorTreeEditor`类中,找到复制方法(可能是`_copy_selected`)并修改:

```python
def _copy_selected(self):
    """复制选中的节点"""
    nodes_to_copy = []
    
    for node_id in self.canvas.selected_nodes:
        node_item = self.canvas.nodes.get(node_id)
        if node_item:
            node = node_item.node
            if node and node.is_protected():
                # 跳过受保护的节点
                continue
            nodes_to_copy.append(node_id)
    
    if nodes_to_copy:
        # 复制节点数据到剪贴板
        self._clipboard_data = self.canvas.get_nodes_data(nodes_to_copy)
    else:
        self._clipboard_data = None
```

**Step 3: 修改剪切方法添加保护检查**

在同一个类中找到剪切方法(可能是`_cut_selected`)并修改:

```python
def _cut_selected(self):
    """剪切选中的节点"""
    nodes_to_cut = []
    
    for node_id in self.canvas.selected_nodes:
        node_item = self.canvas.nodes.get(node_id)
        if node_item:
            node = node_item.node
            if node and node.is_protected():
                # 跳过受保护的节点
                continue
            nodes_to_cut.append(node_id)
    
    if nodes_to_cut:
        # 复制节点数据到剪贴板
        self._clipboard_data = self.canvas.get_nodes_data(nodes_to_cut)
        # 删除节点
        command = RemoveNodesCommand(self.canvas, nodes_to_cut)
        self.command_manager.execute(command)
    else:
        self._clipboard_data = None
```

**Step 4: 验证修改**

Run: 检查Python语法
Expected: 无语法错误

**Step 5: Commit**

```bash
git add bt_gui/bt_editor/editor.py
git commit -m "feat(editor): prevent copy/cut of protected StartNode"
```

---

## 第四阶段: 测试验证

### Task 11: 创建集成测试

**Files:**
- Create: `tests/test_start_node_integration.py`

**Step 1: 创建集成测试文件**

创建文件 `tests/test_start_node_integration.py`:

```python
"""
StartNode集成测试
"""
import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bt_core.nodes import StartNode, ActionNode, NodeStatus
from bt_core.context import ExecutionContext
from bt_core.blackboard import Blackboard


class TestStartNodeIntegration(unittest.TestCase):
    """StartNode集成测试"""
    
    def test_start_node_protection(self):
        """测试开始节点保护属性"""
        node = StartNode()
        self.assertTrue(node.is_protected())
    
    def test_start_node_serialization(self):
        """测试开始节点序列化"""
        node = StartNode()
        node.repeat_count = 5
        
        # 序列化
        data = node.to_dict()
        self.assertEqual(data["repeat_count"], 5)
        self.assertTrue(data["_is_protected"])
        
        # 反序列化
        new_node = StartNode.from_dict(data)
        self.assertEqual(new_node.repeat_count, 5)
        self.assertTrue(new_node.is_protected())
    
    def test_start_node_with_multiple_children(self):
        """测试开始节点支持多个子节点"""
        class SuccessAction(ActionNode):
            def _execute_action(self, context):
                return NodeStatus.SUCCESS
        
        node = StartNode()
        for i in range(3):
            child = SuccessAction()
            node.add_child(child)
        
        self.assertEqual(len(node.children), 3)
        
        context = ExecutionContext()
        status = node.tick(context)
        self.assertEqual(status, NodeStatus.RUNNING)  # 默认无限循环
    
    def test_start_node_failure_continue(self):
        """测试开始节点失败后继续执行"""
        execution_order = []
        
        class TrackAction(ActionNode):
            def __init__(self, name, status):
                super().__init__()
                self.name = name
                self.status = status
            
            def _execute_action(self, context):
                execution_order.append(self.name)
                return self.status
        
        node = StartNode()
        node.add_child(TrackAction("first", NodeStatus.FAILURE))
        node.add_child(TrackAction("second", NodeStatus.SUCCESS))
        node.add_child(TrackAction("third", NodeStatus.FAILURE))
        
        context = ExecutionContext()
        node.tick(context)
        
        # 所有子节点都应该被执行
        self.assertEqual(execution_order, ["first", "second", "third"])
    
    def test_start_node_repeat_count(self):
        """测试开始节点重复次数控制"""
        execution_count = [0]
        
        class CountAction(ActionNode):
            def _execute_action(self, context):
                execution_count[0] += 1
                return NodeStatus.SUCCESS
        
        node = StartNode()
        node.repeat_count = 3
        node.add_child(CountAction())
        
        context = ExecutionContext()
        
        # 执行3次后应该返回SUCCESS
        for i in range(3):
            status = node.tick(context)
            if i < 2:
                self.assertEqual(status, NodeStatus.RUNNING)
            else:
                self.assertEqual(status, NodeStatus.SUCCESS)
        
        # 验证执行了3次
        self.assertEqual(execution_count[0], 3)


if __name__ == '__main__':
    unittest.main()
```

**Step 2: 运行集成测试**

Run: `python -m pytest tests/test_start_node_integration.py -v`
Expected: PASS (所有测试通过)

**Step 3: Commit**

```bash
git add tests/test_start_node_integration.py
git commit -m "test: add integration tests for StartNode"
```

---

### Task 12: 手动测试验证

**Files:**
- 无文件修改,仅手动测试

**Step 1: 启动应用程序**

Run: `python main.py`
Expected: 应用程序正常启动

**Step 2: 测试新建项目**

Action: 点击"新建"按钮或使用Ctrl+N快捷键
Expected: 
- 画布清空
- 自动创建一个"开始"节点
- 节点位置在画布居中偏上
- 节点显示金色边框和▶图标

**Step 3: 测试删除保护**

Action: 
1. 选中"开始"节点
2. 按Delete键或点击删除按钮
Expected: 
- 显示警告提示"开始节点不可删除"
- 节点未被删除

**Step 4: 测试复制保护**

Action:
1. 选中"开始"节点
2. 按Ctrl+C复制
3. 按Ctrl+V粘贴
Expected:
- 粘贴时没有创建新的"开始"节点

**Step 5: 测试属性编辑**

Action:
1. 选中"开始"节点
2. 在属性面板中修改"重复次数"为5
Expected:
- 属性面板正常显示
- 可以编辑名称和重复次数

**Step 6: 测试保存和加载**

Action:
1. 保存项目(Ctrl+S)
2. 关闭应用
3. 重新打开应用并加载项目
Expected:
- "开始"节点正常加载
- 属性值正确恢复

**Step 7: 记录测试结果**

创建测试报告文件 `tests/test_report_start_node.md`:

```markdown
# StartNode手动测试报告

## 测试环境
- 操作系统: Windows
- Python版本: 3.10+
- 测试日期: 2026-04-11

## 测试结果

### 1. 新建项目测试
- [ ] 自动创建开始节点
- [ ] 节点位置正确(居中偏上)
- [ ] 节点外观正确(金色边框+▶图标)

### 2. 删除保护测试
- [ ] 无法删除开始节点
- [ ] 显示正确的提示信息

### 3. 复制/剪切保护测试
- [ ] 无法复制开始节点
- [ ] 无法剪切开始节点

### 4. 属性编辑测试
- [ ] 属性面板正常显示
- [ ] 可以编辑名称
- [ ] 可以编辑重复次数

### 5. 保存/加载测试
- [ ] 保存项目成功
- [ ] 加载项目成功
- [ ] 节点属性正确恢复

## 发现的问题
(记录测试中发现的问题)

## 建议
(记录改进建议)
```

**Step 8: Commit测试报告**

```bash
git add tests/test_report_start_node.md
git commit -m "docs: add manual test report for StartNode"
```

---

## 完成检查清单

完成所有任务后,请检查以下内容:

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 手动测试全部通过
- [ ] 代码无语法错误
- [ ] 代码符合项目规范
- [ ] 所有修改已提交到git
- [ ] 文档已更新

---

**计划完成!**
