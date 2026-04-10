import os
from bt_core.nodes import ActionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any


class ScriptNode(ActionNode):
    NODE_TYPE = "ScriptNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.script_path = self.config.get("script_path", "")
        self.loop = self.config.get_bool("loop", False)

    def _execute_action(self, context) -> NodeStatus:
        try:
            if not os.path.exists(self.script_path):
                return NodeStatus.FAILURE

            from bt_utils.script_executor import ScriptExecutor
            executor = ScriptExecutor()

            with open(self.script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            executor.run_script(content, self.loop)

            return NodeStatus.SUCCESS
        except Exception as e:
            print(f"[WARN] ScriptNode错误: {e}")
            return NodeStatus.FAILURE

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["extra"]["script_path"] = self.script_path
        data["config"]["extra"]["loop"] = self.loop
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScriptNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.script_path = config.get("script_path", "")
        node.loop = config.get_bool("loop", False)
        return node
