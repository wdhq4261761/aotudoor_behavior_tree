"""
测试子节点被多个父节点连接时的异常情况
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bt_core.nodes import SequenceNode, ActionNode, SelectorNode
from bt_core.config import NodeConfig
from bt_core.status import NodeStatus
from bt_core.context import ExecutionContext


class TestActionNode(ActionNode):
    """测试用的动作节点"""
    NODE_TYPE = "TestActionNode"
    
    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.execution_count = 0
    
    def _execute_action(self, context: ExecutionContext) -> NodeStatus:
        self.execution_count += 1
        print(f"[{self.name}] 执行次数: {self.execution_count}, 父节点: {self.parent.name if self.parent else 'None'}")
        return NodeStatus.SUCCESS


def test_multiple_parents():
    """测试一个子节点被多个父节点连接的情况"""
    print("\n" + "="*60)
    print("测试：子节点被多个父节点连接")
    print("="*60)
    
    # 创建节点
    action_node = TestActionNode(
        node_id="action_1",
        config=NodeConfig(name="共享动作节点")
    )
    
    sequence1 = SequenceNode(
        node_id="seq_1",
        config=NodeConfig(name="顺序节点1")
    )
    
    sequence2 = SequenceNode(
        node_id="seq_2",
        config=NodeConfig(name="顺序节点2")
    )
    
    selector = SelectorNode(
        node_id="selector_1",
        config=NodeConfig(name="选择节点")
    )
    
    # 第一次连接：sequence1 -> action_node
    print("\n1. 第一次连接: sequence1 -> action_node")
    sequence1.add_child(action_node)
    print(f"   action_node.parent = {action_node.parent.name}")
    print(f"   sequence1.children = {[c.name for c in sequence1.children]}")
    
    # 第二次连接：sequence2 -> action_node (同一个子节点)
    print("\n2. 第二次连接: sequence2 -> action_node (问题出现!)")
    sequence2.add_child(action_node)
    print(f"   action_node.parent = {action_node.parent.name}  <- 父节点被覆盖!")
    print(f"   sequence1.children = {[c.name for c in sequence1.children]}  <- 仍然保留引用!")
    print(f"   sequence2.children = {[c.name for c in sequence2.children]}")
    
    # 检查数据不一致
    print("\n3. 数据不一致检查:")
    print(f"   action_node.parent == sequence1? {action_node.parent == sequence1}")
    print(f"   action_node.parent == sequence2? {action_node.parent == sequence2}")
    print(f"   action_node in sequence1.children? {action_node in sequence1.children}")
    print(f"   action_node in sequence2.children? {action_node in sequence2.children}")
    
    if action_node.parent != sequence1 and action_node in sequence1.children:
        print("\n   [WARNING] 问题确认: action_node 在 sequence1.children 中，但 parent 指向 sequence2!")
    
    # 构建选择节点
    selector.add_child(sequence1)
    selector.add_child(sequence2)
    
    # 创建执行上下文
    context = ExecutionContext()
    
    # 执行行为树
    print("\n4. 执行行为树:")
    print("   选择节点会依次执行子节点...")
    
    result = selector.tick(context)
    print(f"\n   执行结果: {result}")
    print(f"   action_node 总执行次数: {action_node.execution_count}")
    
    # 重置并再次执行
    print("\n5. 重置后再次执行:")
    selector.reset()
    result = selector.tick(context)
    print(f"   执行结果: {result}")
    print(f"   action_node 总执行次数: {action_node.execution_count}")
    
    print("\n" + "="*60)
    print("结论:")
    print("="*60)
    print("[X] 子节点被多个父节点连接会导致数据不一致")
    print("[X] 子节点的 parent 引用会被后连接的父节点覆盖")
    print("[X] 先连接的父节点仍然保留对子节点的引用")
    print("[X] 这可能导致运行时状态混乱和不可预期的行为")
    print("="*60 + "\n")


def test_serialization_issue():
    """测试序列化/反序列化时的问题"""
    print("\n" + "="*60)
    print("测试：序列化/反序列化时的多父节点问题")
    print("="*60)
    
    from bt_core.serializer import Serializer
    
    # 创建节点
    action_node = TestActionNode(
        node_id="action_1",
        config=NodeConfig(name="共享动作节点")
    )
    
    sequence1 = SequenceNode(
        node_id="seq_1",
        config=NodeConfig(name="顺序节点1")
    )
    
    sequence2 = SequenceNode(
        node_id="seq_2",
        config=NodeConfig(name="顺序节点2")
    )
    
    # 建立连接
    sequence1.add_child(action_node)
    sequence2.add_child(action_node)
    
    print("\n序列化前:")
    print(f"  action_node.parent = {action_node.parent.name}")
    
    # 序列化
    data = Serializer.serialize(sequence1)
    print("\n序列化数据中的连接:")
    for conn in data.get("connections", []):
        print(f"  {conn['parent_id']} -> {conn['child_id']}")
    
    # 反序列化
    root, _, _ = Serializer.deserialize(data)
    
    print("\n反序列化后:")
    if root and root.children:
        child = root.children[0]
        print(f"  子节点: {child.name}")
        print(f"  子节点.parent: {child.parent.name if child.parent else 'None'}")
        print(f"  子节点.parent == root? {child.parent == root}")
    
    print("\n" + "="*60 + "\n")


def test_remove_child_issue():
    """测试移除子节点时的问题"""
    print("\n" + "="*60)
    print("测试：移除子节点时的问题")
    print("="*60)
    
    # 创建节点
    action_node = TestActionNode(
        node_id="action_1",
        config=NodeConfig(name="共享动作节点")
    )
    
    sequence1 = SequenceNode(
        node_id="seq_1",
        config=NodeConfig(name="顺序节点1")
    )
    
    sequence2 = SequenceNode(
        node_id="seq_2",
        config=NodeConfig(name="顺序节点2")
    )
    
    # 建立连接
    print("\n1. 建立连接:")
    sequence1.add_child(action_node)
    sequence2.add_child(action_node)
    print(f"   sequence1.children = {[c.name for c in sequence1.children]}")
    print(f"   sequence2.children = {[c.name for c in sequence2.children]}")
    print(f"   action_node.parent = {action_node.parent.name}")
    
    # 从 sequence1 移除
    print("\n2. 从 sequence1 移除子节点:")
    sequence1.remove_child(action_node)
    print(f"   sequence1.children = {[c.name for c in sequence1.children]}")
    print(f"   sequence2.children = {[c.name for c in sequence2.children]}")
    print(f"   action_node.parent = {action_node.parent}  <- 被设置为 None!")
    
    # 检查问题
    if action_node in sequence2.children and action_node.parent is None:
        print("\n   [WARNING] 问题: action_node 仍在 sequence2.children 中，但 parent 为 None!")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    test_multiple_parents()
    test_serialization_issue()
    test_remove_child_issue()
