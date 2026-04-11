import time
from bt_core.nodes import ActionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any
from bt_utils.log_manager import LogManager


class DelayNode(ActionNode):
    NODE_TYPE = "DelayNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.duration_ms = self.config.get_int("duration_ms", 1000)
        self._delay_start_time = None

    def _execute_action(self, context) -> NodeStatus:
        if self._delay_start_time is None:
            self._delay_start_time = time.time()

        elapsed = (time.time() - self._delay_start_time) * 1000

        if elapsed >= self.duration_ms:
            self._delay_start_time = None
            LogManager.instance().log_success(
                node_type="延时节点",
                node_name=self.name
            )
            return NodeStatus.SUCCESS

        return NodeStatus.RUNNING

    
    def abort(self, context) -> None:
        self._delay_start_time = None
        super().abort(context)

    def reset(self) -> None:
        super().reset()
        self._delay_start_time = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["duration_ms"] = self.duration_ms
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DelayNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.duration_ms = config.get_int("duration_ms", 1000)
        return node
