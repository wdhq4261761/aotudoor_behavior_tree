import os
import threading
from bt_core.nodes import ActionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any, Optional


class ScriptNode(ActionNode):
    NODE_TYPE = "ScriptNode"
    
    _executor_pool: Dict[str, Any] = {}
    _pool_lock = threading.Lock()

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.script_path = self.config.get("script_path", "")
        self.loop = self.config.get_bool("loop", False)
        self._executor: Optional[Any] = None
        self._script_started = False
        self._aborted = False
        self._lock = threading.Lock()
        self._script_content: Optional[str] = None

    def _get_or_create_executor(self) -> Any:
        from bt_utils.script_executor import ScriptExecutor
        
        with ScriptNode._pool_lock:
            if self.node_id not in ScriptNode._executor_pool:
                ScriptNode._executor_pool[self.node_id] = ScriptExecutor()
                return ScriptNode._executor_pool[self.node_id]
            
            executor = ScriptNode._executor_pool[self.node_id]
            
            if executor.is_running:
                ScriptNode._executor_pool[self.node_id] = ScriptExecutor()
                return ScriptNode._executor_pool[self.node_id]
            
            return executor
    
    @classmethod
    def cleanup_executor_pool(cls) -> None:
        with cls._pool_lock:
            to_remove = []
            for node_id, executor in cls._executor_pool.items():
                if not executor.is_running:
                    to_remove.append(node_id)
            
            for node_id in to_remove:
                del cls._executor_pool[node_id]
    
    @classmethod
    def clear_executor_pool(cls) -> None:
        with cls._pool_lock:
            for executor in cls._executor_pool.values():
                if executor.is_running:
                    try:
                        executor.stop_script()
                    except Exception:
                        pass
            cls._executor_pool.clear()

    def _execute_action(self, context) -> NodeStatus:
        from bt_utils.log_manager import LogManager
        
        with self._lock:
            self._aborted = False
        
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
            
            if not self._script_started:
                if not os.path.exists(absolute_script_path):
                    LogManager.instance().log_failure(
                        node_type="脚本节点",
                        node_name=self.name,
                        reason=f"脚本文件不存在: {absolute_script_path}"
                    )
                    return NodeStatus.FAILURE

                with open(absolute_script_path, 'r', encoding='utf-8') as f:
                    self._script_content = f.read()
                
                if not self._script_content.strip():
                    LogManager.instance().log_failure(
                        node_type="脚本节点",
                        node_name=self.name,
                        reason="脚本内容为空"
                    )
                    return NodeStatus.FAILURE
                
                self._executor = self._get_or_create_executor()
                use_loop = self.loop and self.config.repeat_count == 0
                self._executor.run_script(self._script_content, loop=use_loop)
                self._script_started = True
                
                LogManager.instance().log_info(
                     node_type="脚本节点",
                    node_name=self.name,
                    message=f"开始执行脚本 {script_path}"
                )
                return NodeStatus.RUNNING
            
            with self._lock:
                if self._aborted:
                    return NodeStatus.FAILURE
            
            if self._executor and self._executor.is_running:
                if not context.check_running():
                    self._executor.stop_script()
                    return NodeStatus.ABORTED
                return NodeStatus.RUNNING
            
            self._script_started = False
            self._executor = None
            self._script_content = None
            
            LogManager.instance().log_success(
                node_type="脚本节点",
                node_name=self.name
            )
            return NodeStatus.SUCCESS
            
        except Exception as e:
            with self._lock:
                if self._aborted:
                    return NodeStatus.FAILURE
            
            LogManager.instance().log_failure(
                node_type="脚本节点",
                node_name=self.name,
                reason=f"执行异常: {str(e)}"
            )
            return NodeStatus.FAILURE

    def abort(self, context) -> None:
        with self._lock:
            self._aborted = True
        
        if self._executor is not None:
            try:
                if hasattr(self._executor, 'stop_script'):
                    self._executor.stop_script()
            except Exception:
                pass
        self._executor = None
        self._script_started = False
        self._script_content = None
        super().abort(context)
    
    def reset(self, reset_counters: bool = True) -> None:
        with self._lock:
            if self._executor and self._executor.is_running:
                try:
                    self._executor.stop_script()
                except Exception:
                    pass
            
            with ScriptNode._pool_lock:
                if self.node_id in ScriptNode._executor_pool:
                    del ScriptNode._executor_pool[self.node_id]
            
            self._executor = None
            self._script_started = False
            self._aborted = False
            self._script_content = None
        super().reset(reset_counters=reset_counters)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["script_path"] = self.script_path
        data["config"]["loop"] = self.loop
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScriptNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.script_path = config.get("script_path", "")
        node.loop = config.get_bool("loop", False)
        return node
