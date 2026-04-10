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
        from bt_utils.log_manager import LogManager
        
        try:
            script_path = self.script_path
            
            if not script_path:
                LogManager.instance().log_failure(
                    node_type="脚本节点",
                    node_name=self.name,
                    reason="脚本路径为空"
                )
                return NodeStatus.FAILURE
            
            absolute_script_path = script_path
            
            if script_path.startswith("./"):
                if hasattr(context, 'resolve_path') and context.resolve_path:
                    absolute_script_path = context.resolve_path(script_path)
                elif hasattr(context, 'project_root'):
                    project_root = context.project_root
                    absolute_script_path = os.path.join(project_root, script_path[2:])
            else:
                if not os.path.isabs(script_path):
                    absolute_script_path = os.path.abspath(script_path)
            
            if not os.path.exists(absolute_script_path):
                LogManager.instance().log_failure(
                    node_type="脚本节点",
                    node_name=self.name,
                    reason=f"脚本文件不存在: {absolute_script_path}"
                )
                return NodeStatus.FAILURE
            
            from bt_utils.script_executor import ScriptExecutor
            executor = ScriptExecutor()
            
            with open(absolute_script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            executor.run_script(content, context)
            
            LogManager.instance().log_success(
                node_type="脚本节点",
                node_name=self.name
            )
            return NodeStatus.SUCCESS
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="脚本节点",
                node_name=self.name,
                reason=f"执行异常: {str(e)}"
            )
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
