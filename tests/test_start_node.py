"""
StartNode单元测试
"""
import unittest
from bt_core.nodes import StartNode, NodeStatus, ActionNode
from bt_core.context import ExecutionContext
from bt_core.blackboard import Blackboard


class TestStartNode(unittest.TestCase):
    """StartNode测试类"""
    
    def test_create_start_node(self):
        """测试创建开始节点"""
        node = StartNode()
        self.assertEqual(node.NODE_TYPE, "StartNode")
        self.assertTrue(node.is_protected())
    
    def test_tick_no_children(self):
        """测试无子节点时返回SUCCESS"""
        node = StartNode()
        context = ExecutionContext()
        status = node.tick(context)
        self.assertEqual(status, NodeStatus.SUCCESS)
    
    def test_tick_with_running_child(self):
        """测试有RUNNING状态的子节点"""
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
        # 所有子节点执行完毕后应该返回SUCCESS
        self.assertEqual(status, NodeStatus.SUCCESS)


if __name__ == '__main__':
    unittest.main()
