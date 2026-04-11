from bt_core.nodes import ActionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any
from bt_utils.log_manager import LogManager


class SetVariableNode(ActionNode):
    """设置变量节点

    操作黑板中的变量。

    Args:
        variable_name: 变量名
        variable_value: 变量值
        operation: 操作类型 (set/increment/delete)
    """
    NODE_TYPE = "SetVariableNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.variable_name = self.config.get("variable_name", "")
        self.variable_value = self.config.get("variable_value", "")
        self.operation = self.config.get("operation", "set")

    def _execute_action(self, context) -> NodeStatus:
        try:
            if not self.variable_name:
                LogManager.instance().log_failure(
                    node_type="变量节点",
                    node_name=self.name,
                    reason="未配置变量名"
                )
                return NodeStatus.FAILURE
            
            if self.operation == "set":
                context.blackboard.set(self.variable_name, self.variable_value)
            elif self.operation == "increment":
                context.blackboard.increment(self.variable_name, self.variable_value)
            elif self.operation == "delete":
                context.blackboard.delete(self.variable_name)
            
            LogManager.instance().log_success(
                node_type="变量节点",
                node_name=self.name
            )
            return NodeStatus.SUCCESS
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="变量节点",
                node_name=self.name,
                reason=str(e)
            )
            return NodeStatus.FAILURE

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["variable_name"] = self.variable_name
        data["config"]["variable_value"] = self.variable_value
        data["config"]["operation"] = self.operation
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SetVariableNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.variable_name = config.get("variable_name", "")
        node.variable_value = config.get("variable_value", "")
        node.operation = config.get("operation", "set")
        return node
