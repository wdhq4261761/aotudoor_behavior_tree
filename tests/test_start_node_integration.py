"""
StartNode集成测试
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bt_core.nodes import StartNode, ActionNode, NodeStatus
from bt_core.context import ExecutionContext
from bt_core.blackboard import Blackboard
from bt_core.registry import NodeRegistry


class TestStartNodeIntegration(unittest.TestCase):
    """StartNode集成测试"""
    
    def test_start_node_protection(self):
        """测试开始节点保护属性"""
        node = StartNode()
        self.assertTrue(node.is_protected())
    
    def test_start_node_serialization(self):
        """测试开始节点序列化"""
        node = StartNode()
        
        # 序列化
        data = node.to_dict()
        self.assertTrue(data["_is_protected"])
        
        # 反序列化
        new_node = StartNode.from_dict(data)
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
        self.assertEqual(status, NodeStatus.SUCCESS)
    
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
    
    def test_start_node_registered(self):
        """测试StartNode已注册到注册中心"""
        node_class = NodeRegistry.get("StartNode")
        self.assertEqual(node_class, StartNode)


if __name__ == '__main__':
    unittest.main()
