from bt_core.nodes import ActionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any, Tuple, Optional


class MouseScrollNode(ActionNode):
    NODE_TYPE = "MouseScrollNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.amount = self.config.get_int("amount", 1)
        self.position: Optional[Tuple[int, int]] = self.config.get("position", None)
        self.use_blackboard = self.config.get_bool("use_blackboard", False)
        self.position_key = self.config.get("position_key", "last_detection_position")

    def _execute_action(self, context) -> NodeStatus:
        try:
            scroll_position = self.position

            if self.use_blackboard:
                bb_position = context.blackboard.get(self.position_key)
                if bb_position:
                    scroll_position = bb_position

            if scroll_position:
                context.execute_mouse_move(scroll_position, relative=False)

            context.execute_mouse_scroll(self.amount, scroll_position)
            return NodeStatus.SUCCESS
        except Exception as e:
            print(f"[WARN] MouseScrollNode错误: {e}")
            return NodeStatus.FAILURE

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["extra"]["amount"] = self.amount
        data["config"]["extra"]["position"] = self.position
        data["config"]["extra"]["use_blackboard"] = self.use_blackboard
        data["config"]["extra"]["position_key"] = self.position_key
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MouseScrollNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.amount = config.get_int("amount", 1)
        node.position = config.get("position", None)
        node.use_blackboard = config.get_bool("use_blackboard", False)
        node.position_key = config.get("position_key", "last_detection_position")
        return node
