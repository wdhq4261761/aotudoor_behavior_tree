from bt_core.nodes import ActionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any
from bt_utils.log_manager import LogManager


class MouseScrollNode(ActionNode):
    NODE_TYPE = "MouseScrollNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.distance = self.config.get_int("distance", 5)
        self.clicks = self.config.get_int("clicks", 1)
        self.direction = self.config.get("direction", "向上")

    def _execute_action(self, context) -> NodeStatus:
        try:
            scroll_distance = self.distance
            scroll_direction = "垂直"
            
            if self.direction == "向上":
                scroll_distance = abs(self.distance)
                scroll_direction = "垂直"
            elif self.direction == "向下":
                scroll_distance = -abs(self.distance)
                scroll_direction = "垂直"
            elif self.direction == "向左":
                scroll_distance = -abs(self.distance)
                scroll_direction = "水平"
            elif self.direction == "向右":
                scroll_distance = abs(self.distance)
                scroll_direction = "水平"
            
            success = context.execute_mouse_scroll(scroll_distance, self.clicks, scroll_direction)
            
            if success:
                LogManager.instance().log_success(
                    node_type="鼠标滚轮节点",
                    node_name=self.name
                )
                return NodeStatus.SUCCESS
            else:
                LogManager.instance().log_failure(
                    node_type="鼠标滚轮节点",
                    node_name=self.name,
                    reason="滚轮执行失败"
                )
                return NodeStatus.FAILURE
                
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="鼠标滚轮节点",
                node_name=self.name,
                reason=str(e)
            )
            return NodeStatus.FAILURE

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["distance"] = self.distance
        data["config"]["clicks"] = self.clicks
        data["config"]["direction"] = self.direction
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MouseScrollNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.distance = config.get_int("distance", 5)
        node.clicks = config.get_int("clicks", 1)
        node.direction = config.get("direction", "向上")
        return node
