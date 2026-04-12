from bt_core.nodes import ActionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any, Tuple, Optional
import time
from bt_utils.log_manager import LogManager


def _get_default_position_key() -> str:
    try:
        from config.settings_manager import get_default_position_key
        return get_default_position_key()
    except ImportError:
        return "last_detection_position"


class MouseClickNode(ActionNode):
    NODE_TYPE = "MouseClickNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.button = self.config.get("button", "left")
        self.position: Optional[Tuple[int, int]] = self.config.get("position", None)
        self.action = self.config.get("action", "press")
        self.duration = self.config.get_int("duration", 100)
        self.use_blackboard = self.config.get_bool("use_blackboard", False)
        self.position_key = self.config.get("position_key", _get_default_position_key())
        self.click_count = self.config.get_int("click_count", 1)
        self.click_interval = self.config.get_int("click_interval", 100)
        self._current_click = 0
        self._last_click_time: Optional[float] = None
        self._abort_flag = False
        self._click_started = False

    def _execute_action(self, context) -> NodeStatus:
        try:
            click_position = self._get_position(context)
            
            if not self._click_started:
                self._click_started = True
                self._current_click = 0
                self._last_click_time = None
            
            if self._abort_flag or not context.check_running():
                self._reset_click_state()
                LogManager.instance().log_aborted(
                    node_type="鼠标点击节点",
                    node_name=self.name
                )
                return NodeStatus.ABORTED
            
            if self.click_count == -1:
                return self._non_blocking_infinite_click(context, click_position)
            else:
                return self._non_blocking_finite_click(context, click_position)
            
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="鼠标点击节点",
                node_name=self.name,
                reason=str(e)
            )
            return NodeStatus.FAILURE

    def _get_position(self, context) -> Optional[Tuple[int, int]]:
        if self.use_blackboard:
            bb_position = context.blackboard.get(self.position_key)
            if bb_position:
                return bb_position
        return self.position

    def _non_blocking_finite_click(self, context, position: Optional[Tuple[int, int]]) -> NodeStatus:
        current_time = time.time() * 1000
        
        if self._last_click_time is not None and self.click_interval > 0:
            elapsed = current_time - self._last_click_time
            if elapsed < self.click_interval:
                return NodeStatus.RUNNING
        
        if self._current_click < self.click_count:
            if self._abort_flag or not context.check_running():
                self._reset_click_state()
                return NodeStatus.ABORTED
            
            context.execute_mouse_click(self.button, position, self.action, self.duration)
            self._current_click += 1
            self._last_click_time = time.time() * 1000
            
            if self._current_click < self.click_count:
                return NodeStatus.RUNNING
        
        self._reset_click_state()
        LogManager.instance().log_success(
            node_type="鼠标点击节点",
            node_name=self.name
        )
        return NodeStatus.SUCCESS

    def _non_blocking_infinite_click(self, context, position: Optional[Tuple[int, int]]) -> NodeStatus:
        current_time = time.time() * 1000
        
        if self._last_click_time is not None and self.click_interval > 0:
            elapsed = current_time - self._last_click_time
            if elapsed < self.click_interval:
                return NodeStatus.RUNNING
        
        if self._abort_flag or not context.check_running():
            self._reset_click_state()
            LogManager.instance().log_aborted(
                node_type="鼠标点击节点",
                node_name=self.name
            )
            return NodeStatus.ABORTED
        
        context.execute_mouse_click(self.button, position, self.action, self.duration)
        self._current_click += 1
        self._last_click_time = time.time() * 1000
        
        return NodeStatus.RUNNING

    def _reset_click_state(self) -> None:
        self._current_click = 0
        self._last_click_time = None
        self._abort_flag = False
        self._click_started = False

    def abort(self, context) -> None:
        self._abort_flag = True
        self._reset_click_state()
        super().abort(context)

    def reset(self) -> None:
        self._reset_click_state()
        super().reset()

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["button"] = self.button
        data["config"]["position"] = self.position
        data["config"]["action"] = self.action
        data["config"]["duration"] = self.duration
        data["config"]["use_blackboard"] = self.use_blackboard
        data["config"]["position_key"] = self.position_key
        data["config"]["click_count"] = self.click_count
        data["config"]["click_interval"] = self.click_interval
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MouseClickNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.button = config.get("button", "left")
        node.position = config.get("position", None)
        node.action = config.get("action", "press")
        node.duration = config.get_int("duration", 100)
        node.use_blackboard = config.get_bool("use_blackboard", False)
        node.position_key = config.get("position_key", "last_detection_position")
        node.click_count = config.get_int("click_count", 1)
        node.click_interval = config.get_int("click_interval", 100)
        return node


class MouseMoveNode(ActionNode):
    NODE_TYPE = "MouseMoveNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.position: Tuple[int, int] = self.config.get("position", (0, 0))
        self.use_blackboard = self.config.get_bool("use_blackboard", False)
        self.position_key = self.config.get("position_key", _get_default_position_key())
        self.relative = self.config.get_bool("relative", False)
        self.smooth = self.config.get_bool("smooth", True)
        self.move_type = self.config.get("move_type", "移动")
        self.drag_button = self.config.get("drag_button", "left")
        self.end_position: Optional[Tuple[int, int]] = self.config.get("end_position", None)
        self.use_blackboard_end = self.config.get_bool("use_blackboard_end", False)
        self.position_key_end = self.config.get("position_key_end", "")
        self.drag_duration = self.config.get_int("drag_duration", 0)

    def _execute_action(self, context) -> NodeStatus:
        try:
            move_position = self.position
            
            if self.use_blackboard:
                bb_position = context.blackboard.get(self.position_key)
                if bb_position:
                    move_position = bb_position
            
            if not move_position:
                LogManager.instance().log_failure(
                    node_type="鼠标移动节点",
                    node_name=self.name,
                    reason="未指定位置"
                )
                return NodeStatus.FAILURE
            
            if self.move_type == "拖拽":
                return self._execute_drag(context, move_position)
            else:
                return self._execute_move(context, move_position)
                
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="鼠标移动节点",
                node_name=self.name,
                reason=str(e)
            )
            try:
                context.execute_mouse_click(self.drag_button, None, "up", 0)
            except Exception:
                pass
            return NodeStatus.FAILURE

    def _execute_move(self, context, position: Tuple[int, int]) -> NodeStatus:
        context.execute_mouse_move(position, self.relative, self.smooth)
        LogManager.instance().log_success(
            node_type="鼠标移动节点",
            node_name=self.name,
            message=f"{'平滑' if self.smooth else '直接'}移动到 {position}"
        )
        return NodeStatus.SUCCESS

    def _execute_drag(self, context, start_pos: Tuple[int, int]) -> NodeStatus:
        drag_end_position = self.end_position
        
        if self.use_blackboard_end:
            bb_position = context.blackboard.get(self.position_key_end)
            if bb_position:
                drag_end_position = bb_position
        
        if not drag_end_position:
            LogManager.instance().log_failure(
                node_type="鼠标移动节点",
                node_name=self.name,
                reason="未指定拖拽终点"
            )
            return NodeStatus.FAILURE
        
        context.execute_mouse_move(start_pos, relative=False)
        time.sleep(0.05)
        
        context.execute_mouse_click(self.drag_button, start_pos, "down", 0)
        time.sleep(0.05)
        
        if self.drag_duration > 0:
            steps = max(10, self.drag_duration // 50)
            dx = (drag_end_position[0] - start_pos[0]) / steps
            dy = (drag_end_position[1] - start_pos[1]) / steps
            
            for i in range(steps):
                if not context.check_running():
                    context.execute_mouse_click(self.drag_button, drag_end_position, "up", 0)
                    return NodeStatus.ABORTED
                
                current_x = int(start_pos[0] + dx * (i + 1))
                current_y = int(start_pos[1] + dy * (i + 1))
                context.execute_mouse_move((current_x, current_y), relative=False)
                time.sleep(self.drag_duration / 1000.0 / steps)
        else:
            steps = 20
            dx = (drag_end_position[0] - start_pos[0]) / steps
            dy = (drag_end_position[1] - start_pos[1]) / steps
            
            for i in range(steps):
                if not context.check_running():
                    context.execute_mouse_click(self.drag_button, drag_end_position, "up", 0)
                    return NodeStatus.ABORTED
                
                current_x = int(start_pos[0] + dx * (i + 1))
                current_y = int(start_pos[1] + dy * (i + 1))
                context.execute_mouse_move((current_x, current_y), relative=False)
                time.sleep(0.02)
        
        time.sleep(0.05)
        context.execute_mouse_click(self.drag_button, drag_end_position, "up", 0)
        
        LogManager.instance().log_success(
            node_type="鼠标移动节点",
            node_name=self.name,
            message=f"从 {start_pos} 拖拽到 {drag_end_position}"
        )
        return NodeStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["position"] = self.position
        data["config"]["use_blackboard"] = self.use_blackboard
        data["config"]["position_key"] = self.position_key
        data["config"]["relative"] = self.relative
        data["config"]["smooth"] = self.smooth
        data["config"]["move_type"] = self.move_type
        data["config"]["drag_button"] = self.drag_button
        data["config"]["end_position"] = self.end_position
        data["config"]["use_blackboard_end"] = self.use_blackboard_end
        data["config"]["position_key_end"] = self.position_key_end
        data["config"]["drag_duration"] = self.drag_duration
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MouseMoveNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.position = config.get("position", (0, 0))
        node.use_blackboard = config.get_bool("use_blackboard", False)
        node.position_key = config.get("position_key", "last_detection_position")
        node.relative = config.get_bool("relative", False)
        node.smooth = config.get_bool("smooth", True)
        node.move_type = config.get("move_type", "移动")
        node.drag_button = config.get("drag_button", "left")
        node.end_position = config.get("end_position", None)
        node.use_blackboard_end = config.get_bool("use_blackboard_end", False)
        node.position_key_end = config.get("position_key_end", "")
        node.drag_duration = config.get_int("drag_duration", 0)
        return node
