from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TYPE_CHECKING
import uuid

from .status import NodeStatus
from .config import NodeConfig

if TYPE_CHECKING:
    from .context import ExecutionContext


class Node(ABC):
    """节点抽象基类

    所有行为树节点的基类，定义了节点的通用接口和行为。

    Args:
        node_id: 节点唯一标识
        config: 节点配置
    """
    NODE_TYPE = "Node"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        self.node_id = node_id or str(uuid.uuid4())[:8]
        self.config = config or NodeConfig()
        self.name = self.config.name
        self.description = self.config.description
        self.enabled = self.config.enabled
        self.status = NodeStatus.SUCCESS
        self.children: List["Node"] = []
        self.parent: Optional["Node"] = None
        self._tick_count = 0
        self._retry_count = 0
        self._repeat_count = 0
        self._start_time: Optional[float] = None

    @abstractmethod
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """执行节点逻辑

        Args:
            context: 执行上下文

        Returns:
            节点执行状态
        """
        pass

    def _execute_with_decorators(self, context: "ExecutionContext", 
                                   execute_func: callable) -> NodeStatus:
        """带装饰参数执行节点逻辑

        Args:
            context: 执行上下文
            execute_func: 实际执行函数

        Returns:
            节点执行状态
        """
        if not self.config.enabled:
            return NodeStatus.SUCCESS

        if self.status != NodeStatus.RUNNING:
            context.notify_node_status(self.node_id, "running")

        if self._start_time is None:
            self._start_time = context.elapsed_time

        timeout_ms = self.config.timeout_ms
        if timeout_ms > 0:
            elapsed_ms = (context.elapsed_time - self._start_time) * 1000
            if elapsed_ms >= timeout_ms:
                self.status = NodeStatus.FAILURE
                context.notify_node_status(self.node_id, "failure")
                return NodeStatus.FAILURE

        status = execute_func(context)
        self.status = status

        retry_count = self.config.retry_count
        if status == NodeStatus.FAILURE and retry_count != 0:
            if retry_count == -1 or self._retry_count < retry_count:
                self._retry_count += 1
                self._reset_for_retry()
                return NodeStatus.RUNNING

        repeat_count = self.config.repeat_count
        if status == NodeStatus.SUCCESS and repeat_count != 0:
            if repeat_count == -1 or self._repeat_count < repeat_count:
                self._repeat_count += 1
                self._reset_for_repeat()
                return NodeStatus.RUNNING

        if status == NodeStatus.SUCCESS:
            context.notify_node_status(self.node_id, "success")
        elif status == NodeStatus.FAILURE:
            context.notify_node_status(self.node_id, "failure")

        return status

    def _reset_for_retry(self) -> None:
        """重试时重置状态（保留重试计数器）"""
        self.status = NodeStatus.SUCCESS
        self._tick_count = 0
        self._start_time = None
        for child in self.children:
            child.reset()

    def _reset_for_repeat(self) -> None:
        """重复执行时重置状态（保留重复计数器）"""
        self.status = NodeStatus.SUCCESS
        self._tick_count = 0
        self._retry_count = 0
        self._start_time = None
        for child in self.children:
            child.reset()

    def reset(self, reset_counters: bool = True) -> None:
        """重置节点状态

        Args:
            reset_counters: 是否重置计数器（重复执行时不应重置）
        """
        self.status = NodeStatus.SUCCESS
        self._tick_count = 0
        if reset_counters:
            self._retry_count = 0
            self._repeat_count = 0
        self._start_time = None
        for child in self.children:
            child.reset()

    def abort(self, context: "ExecutionContext") -> None:
        """中止节点执行

        当节点被外部中止时调用（如并行节点完成时中止其他RUNNING子节点）。

        Args:
            context: 执行上下文
        """
        self.reset()
        self.status = NodeStatus.ABORTED
        context.notify_node_status(self.node_id, "aborted")
        for child in self.children:
            child.abort(context)

    def add_child(self, child: "Node") -> None:
        """添加子节点

        Args:
            child: 子节点
        """
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: "Node") -> None:
        """移除子节点

        Args:
            child: 子节点
        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典

        Returns:
            字典表示
        """
        return {
            "id": self.node_id,
            "type": self.NODE_TYPE,
            "name": self.name,
            "enabled": self.enabled,
            "config": self.config.to_dict(),
            "children": [child.node_id for child in self.children],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """从字典反序列化

        Args:
            data: 字典数据

        Returns:
            节点实例
        """
        config = NodeConfig.from_dict(data.get("config", {}))
        
        if "name" in data:
            config.name = data["name"]
        if "description" in data:
            config.description = data["description"]
        if "enabled" in data:
            config.enabled = data["enabled"]
        
        node = cls(node_id=data.get("id"), config=config)
        return node


class CompositeNode(Node):
    """组合节点基类

    包含多个子节点的节点，按特定策略执行子节点。
    """
    NODE_TYPE = "CompositeNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.current_index = 0

    def reset(self, reset_counters: bool = True) -> None:
        """重置节点状态"""
        super().reset(reset_counters)
        self.current_index = 0


class SequenceNode(CompositeNode):
    NODE_TYPE = "SequenceNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.continue_on_failure = self.config.get_bool("continue_on_failure", False)
        self.child_interval = self.config.get_int("child_interval", 0)
        self._last_child_time = 0

    def tick(self, context: "ExecutionContext") -> NodeStatus:
        return self._execute_with_decorators(context, self._tick_internal)

    def _tick_internal(self, context: "ExecutionContext") -> NodeStatus:
        from bt_utils.log_manager import LogManager
        
        if not self.children:
            return NodeStatus.SUCCESS

        has_failure = False

        while self.current_index < len(self.children):
            child = self.children[self.current_index]

            if not child.config.enabled:
                self.current_index += 1
                continue

            if self.child_interval > 0:
                current_time = context.elapsed_time * 1000
                if current_time - self._last_child_time < self.child_interval:
                    return NodeStatus.RUNNING
                self._last_child_time = current_time

            status = child.tick(context)

            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING

            if status == NodeStatus.FAILURE:
                if self.continue_on_failure:
                    has_failure = True
                    self.current_index += 1
                    continue
                else:
                    self.current_index = 0
                    LogManager.instance().log_failure(
                        node_type="顺序节点",
                        node_name=self.name,
                        reason=f"子节点 '{child.name}' 执行失败"
                    )
                    return NodeStatus.FAILURE

            self.current_index += 1

        self.current_index = 0
        
        if has_failure:
            LogManager.instance().log_failure(
                node_type="顺序节点",
                node_name=self.name,
                reason="部分子节点执行失败（继续执行模式）"
            )
        else:
            LogManager.instance().log_success(
                node_type="顺序节点",
                node_name=self.name
            )
        
        return NodeStatus.FAILURE if has_failure else NodeStatus.SUCCESS

    def reset(self, reset_counters: bool = True) -> None:
        super().reset(reset_counters)
        self._last_child_time = 0


class SelectorNode(CompositeNode):
    NODE_TYPE = "SelectorNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.child_interval = self.config.get_int("child_interval", 0)
        self._last_child_time = 0

    def tick(self, context: "ExecutionContext") -> NodeStatus:
        return self._execute_with_decorators(context, self._tick_internal)

    def _tick_internal(self, context: "ExecutionContext") -> NodeStatus:
        from bt_utils.log_manager import LogManager
        
        if not self.children:
            LogManager.instance().log_failure(
                node_type="选择节点",
                node_name=self.name,
                reason="没有子节点"
            )
            return NodeStatus.FAILURE

        while self.current_index < len(self.children):
            child = self.children[self.current_index]

            if not child.config.enabled:
                self.current_index += 1
                continue

            if self.child_interval > 0:
                current_time = context.elapsed_time * 1000
                if current_time - self._last_child_time < self.child_interval:
                    return NodeStatus.RUNNING
                self._last_child_time = current_time

            status = child.tick(context)

            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING

            if status == NodeStatus.SUCCESS:
                self.current_index = 0
                LogManager.instance().log_success(
                    node_type="选择节点",
                    node_name=self.name
                )
                return NodeStatus.SUCCESS

            self.current_index += 1

        self.current_index = 0
        LogManager.instance().log_failure(
            node_type="选择节点",
            node_name=self.name,
            reason="所有子节点都执行失败"
        )
        return NodeStatus.FAILURE

    def reset(self, reset_counters: bool = True) -> None:
        super().reset(reset_counters)
        self._last_child_time = 0


class ParallelNode(CompositeNode):
    """并行节点

    同时执行所有子节点，根据策略决定成功条件。

    Args:
        success_policy: 成功策略，require_all（全部成功）或 require_one（任一成功）
    """
    NODE_TYPE = "ParallelNode"

    SUCCESS_POLICY_ALL = "require_all"
    SUCCESS_POLICY_ONE = "require_one"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.cached_statuses: Dict[int, NodeStatus] = {}
        self.success_policy = self.config.get("success_policy", self.SUCCESS_POLICY_ALL)

    def tick(self, context: "ExecutionContext") -> NodeStatus:
        return self._execute_with_decorators(context, self._tick_internal)

    def _tick_internal(self, context: "ExecutionContext") -> NodeStatus:
        if not self.children:
            return NodeStatus.SUCCESS

        success_count = 0
        failure_count = 0
        running_children = []
        enabled_count = 0

        for i, child in enumerate(self.children):
            if not child.config.enabled:
                continue

            enabled_count += 1

            if i in self.cached_statuses:
                status = self.cached_statuses[i]
                if status == NodeStatus.SUCCESS:
                    success_count += 1
                    continue
                elif status == NodeStatus.FAILURE:
                    failure_count += 1
                    continue

            status = child.tick(context)

            if status == NodeStatus.SUCCESS:
                self.cached_statuses[i] = NodeStatus.SUCCESS
                success_count += 1
            elif status == NodeStatus.FAILURE:
                self.cached_statuses[i] = NodeStatus.FAILURE
                failure_count += 1
            elif status == NodeStatus.RUNNING:
                running_children.append(child)

        if self.success_policy == self.SUCCESS_POLICY_ONE and success_count > 0:
            self._abort_running(context, running_children)
            return NodeStatus.SUCCESS

        if running_children:
            return NodeStatus.RUNNING

        if self.success_policy == self.SUCCESS_POLICY_ALL:
            return NodeStatus.SUCCESS if success_count == enabled_count else NodeStatus.FAILURE
        else:
            return NodeStatus.SUCCESS if success_count > 0 else NodeStatus.FAILURE

    def _abort_running(self, context: "ExecutionContext", children: List[Node]) -> None:
        """中止正在运行的子节点

        Args:
            context: 执行上下文
            children: 正在运行的子节点列表
        """
        for child in children:
            child.abort(context)

    def reset(self, reset_counters: bool = True) -> None:
        """重置节点状态"""
        super().reset(reset_counters)
        self.cached_statuses.clear()


class ConditionNode(Node):
    NODE_TYPE = "ConditionNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.invert = self.config.get_bool("invert", False)
        self.check_interval_ms = self.config.get_int("check_interval_ms", 300)
        self.save_position = self.config.get_bool("save_position", True)
        
        try:
            from bt_utils.config_manager import get_default_position_key
            default_position_key = get_default_position_key()
        except ImportError:
            default_position_key = "last_detection_position"
        
        self.position_key = self.config.get("position_key", default_position_key)
        self._last_check_time = 0
        self._child_index = 0

    def tick(self, context: "ExecutionContext") -> NodeStatus:
        return self._execute_with_decorators(context, self._tick_internal)

    def _tick_internal(self, context: "ExecutionContext") -> NodeStatus:
        current_time = context.elapsed_time * 1000
        if current_time - self._last_check_time < self.check_interval_ms:
            return self.status

        self._last_check_time = current_time
        result = self._check_condition(context)

        if self.invert:
            result = not result

        status = NodeStatus.SUCCESS if result else NodeStatus.FAILURE
        self.status = status

        if status == NodeStatus.SUCCESS and self.children:
            return self._execute_children(context)

        return status

    @abstractmethod
    def _check_condition(self, context: "ExecutionContext") -> bool:
        """检测条件是否满足

        Args:
            context: 执行上下文

        Returns:
            条件是否满足
        """
        pass

    def _execute_children(self, context: "ExecutionContext") -> NodeStatus:
        """执行子节点

        Args:
            context: 执行上下文

        Returns:
            执行状态
        """
        while self._child_index < len(self.children):
            child = self.children[self._child_index]
            status = child.tick(context)
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            if status != NodeStatus.SUCCESS:
                self._child_index = 0
                return status
            
            self._child_index += 1
        
        self._child_index = 0
        return NodeStatus.SUCCESS

    def reset(self, reset_counters: bool = True) -> None:
        super().reset(reset_counters)
        self._last_check_time = 0
        self._child_index = 0


class ActionNode(Node):
    """动作节点基类

    执行特定动作，动作成功后可选执行子节点。
    """
    NODE_TYPE = "ActionNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self._child_index = 0

    def tick(self, context: "ExecutionContext") -> NodeStatus:
        return self._execute_with_decorators(context, self._tick_internal)

    def _tick_internal(self, context: "ExecutionContext") -> NodeStatus:
        status = self._execute_action(context)
        self.status = status

        if status == NodeStatus.SUCCESS and self.children:
            return self._execute_children(context)

        return status

    @abstractmethod
    def _execute_action(self, context: "ExecutionContext") -> NodeStatus:
        """执行动作

        Args:
            context: 执行上下文

        Returns:
            执行状态
        """
        pass

    def _execute_children(self, context: "ExecutionContext") -> NodeStatus:
        """执行子节点

        Args:
            context: 执行上下文

        Returns:
            执行状态
        """
        while self._child_index < len(self.children):
            child = self.children[self._child_index]
            status = child.tick(context)
            
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
            
            if status != NodeStatus.SUCCESS:
                self._child_index = 0
                return status
            
            self._child_index += 1
        
        self._child_index = 0
        return NodeStatus.SUCCESS

    def reset(self, reset_counters: bool = True) -> None:
        super().reset(reset_counters)
        self._child_index = 0
