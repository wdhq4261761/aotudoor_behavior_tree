import threading
import time
from typing import Optional, Callable, Dict, Any

from .nodes import Node, NodeStatus
from .context import ExecutionContext


class BehaviorTreeEngine:
    """行为树执行引擎

    负责行为树的加载、执行、暂停、停止等生命周期管理。
    执行在独立线程中进行，支持状态回调通知。

    Args:
        root_node: 行为树根节点
    """

    def __init__(self, root_node: Node = None):
        self.root_node = root_node
        self.context: Optional[ExecutionContext] = None
        self._running = False
        self._paused = False
        self._thread: Optional[threading.Thread] = None
        self._tick_interval = 0.01
        self._on_status_change: Optional[Callable] = None
        self._on_node_status: Optional[Callable] = None
        self._lock = threading.Lock()

    def load_tree(self, data: Dict[str, Any]) -> None:
        """从字典数据加载行为树

        Args:
            data: 行为树字典数据
        """
        from .serializer import Serializer
        result = Serializer.deserialize(data)
        if isinstance(result, tuple):
            self.root_node = result[0]
        else:
            self.root_node = result

    def load_from_file(self, filepath: str) -> None:
        """从文件加载行为树

        Args:
            filepath: 文件路径
        """
        from .serializer import Serializer
        result = Serializer.load_from_file(filepath)
        if isinstance(result, tuple):
            self.root_node = result[0]
        else:
            self.root_node = result

    def save_to_file(self, filepath: str, format: str = "json") -> None:
        """保存行为树到文件

        Args:
            filepath: 文件路径
            format: 文件格式 (json/yaml/txt)
        """
        from .serializer import Serializer
        Serializer.save_to_file(self.root_node, filepath, format)

    def start(self, context: ExecutionContext = None) -> None:
        """启动执行

        Args:
            context: 执行上下文，为None时自动创建
        """
        with self._lock:
            if self._running:
                return

            self.context = context or ExecutionContext()
            self._running = True
            self._paused = False

            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

            if self._on_status_change:
                self._on_status_change("running")

    def stop(self) -> None:
        """停止执行"""
        with self._lock:
            self._running = False
            self._paused = False

            if self.context:
                self.context._is_running = False

            if self.root_node and self.context:
                self.root_node.abort(self.context)
            elif self.root_node:
                self.root_node.reset()

            from bt_nodes.actions.script import ScriptNode
            ScriptNode.clear_executor_pool()

            if self._on_status_change:
                self._on_status_change("stopped")

    def pause(self) -> None:
        """暂停执行"""
        self._paused = True
        if self._on_status_change:
            self._on_status_change("paused")

    def resume(self) -> None:
        """恢复执行"""
        self._paused = False
        if self._on_status_change:
            self._on_status_change("running")

    def get_status(self) -> Dict[str, Any]:
        """获取执行状态

        Returns:
            状态字典
        """
        return {
            "running": self._running,
            "paused": self._paused,
            "elapsed_time": self.context.elapsed_time if self.context else 0,
            "tick_count": self.context.tick_count if self.context else 0,
        }

    def _run_loop(self) -> None:
        """执行循环"""
        start_time = time.time()

        while self._running:
            if self._paused:
                time.sleep(0.1)
                continue

            self.context.elapsed_time = time.time() - start_time
            self.context.tick_count += 1

            if self.root_node:
                status = self.root_node.tick(self.context)

                if self._on_node_status:
                    self._on_node_status(self.root_node.node_id, status.value)

                if status != NodeStatus.RUNNING:
                    self._running = False
                    if self._on_status_change:
                        self._on_status_change("completed", status)

            time.sleep(self._tick_interval)
