from bt_core.nodes import ActionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any, Tuple, Optional
import time
from bt_utils.log_manager import LogManager


def _get_default_position_key() -> str:
    try:
        from bt_utils.config_manager import get_default_position_key
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
        self.duration = self.config.get_int("duration", 0)
        self.use_blackboard = self.config.get_bool("use_blackboard", False)
        self.position_key = self.config.get("position_key", _get_default_position_key())
        self.click_count = self.config.get_int("click_count", 1)
        self.click_interval = self.config.get_int("click_interval", 100)
        self._current_click = 0
        self._abort_flag = False

    def _execute_action(self, context) -> NodeStatus:
        try:
            click_position = self._get_position(context)
            
            if self.click_count == -1:
                result = self._infinite_click(context, click_position)
            else:
                result = self._finite_click(context, click_position)
            
            if result == NodeStatus.SUCCESS:
                LogManager.instance().log_success(
                    node_type="鼠标点击节点",
                    node_name=self.name
                )
            elif result == NodeStatus.ABORTED:
                LogManager.instance().log_aborted(
                    node_type="鼠标点击节点",
                    node_name=self.name
                )
            
            return result
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

    def _finite_click(self, context, position: Optional[Tuple[int, int]]) -> NodeStatus:
        while self._current_click < self.click_count:
            if self._abort_flag or not context.check_running():
                self._current_click = 0
                return NodeStatus.ABORTED
            
            context.execute_mouse_click(self.button, position, self.action, self.duration)
            self._current_click += 1
            
            if self._current_click < self.click_count and self.click_interval > 0:
                time.sleep(self.click_interval / 1000.0)
        
        self._current_click = 0
        return NodeStatus.SUCCESS

    def _infinite_click(self, context, position: Optional[Tuple[int, int]]) -> NodeStatus:
        while context.check_running() and not self._abort_flag:
            context.execute_mouse_click(self.button, position, self.action, self.duration)
            if self.click_interval > 0:
                time.sleep(self.click_interval / 1000.0)
        
        self._abort_flag = False
        return NodeStatus.ABORTED

    def abort(self, context) -> None:
        self._abort_flag = True
        super().abort(context)

    def reset(self) -> None:
        super().reset()
        self._current_click = 0
        self._abort_flag = False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["extra"]["button"] = self.button
        data["config"]["extra"]["position"] = self.position
        data["config"]["extra"]["action"] = self.action
        data["config"]["extra"]["duration"] = self.duration
        data["config"]["extra"]["use_blackboard"] = self.use_blackboard
        data["config"]["extra"]["position_key"] = self.position_key
        data["config"]["extra"]["click_count"] = self.click_count
        data["config"]["extra"]["click_interval"] = self.click_interval
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MouseClickNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.button = config.get("button", "left")
        node.position = config.get("position", None)
        node.action = config.get("action", "press")
        node.duration = config.get_int("duration", 0)
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
        self.relative = self.config.get_bool("relative", False)
        self.use_blackboard = self.config.get_bool("use_blackboard", False)
        self.position_key = self.config.get("position_key", _get_default_position_key())
        self.move_type = self.config.get("move_type", "move")
        self.drag_button = self.config.get("drag_button", "left")
        self.end_position: Optional[Tuple[int, int]] = self.config.get("end_position", None)
        self.use_blackboard_end = self.config.get_bool("use_blackboard_end", False)
        self.position_key_end = self.config.get("position_key_end", _get_default_position_key())
        self.drag_duration = self.config.get_int("drag_duration", 0)

    def _execute_action(self, context) -> NodeStatus:
        try:
            start_pos = self._get_start_position(context)
            
            if self.move_type == "drag":
                result = self._execute_drag(context, start_pos)
            else:
                result = self._execute_move(context, start_pos)
            
            if result == NodeStatus.SUCCESS:
                LogManager.instance().log_success(
                    node_type="鼠标移动节点",
                    node_name=self.name
                )
            elif result == NodeStatus.ABORTED:
                LogManager.instance().log_aborted(
                    node_type="鼠标移动节点",
                    node_name=self.name
                )
            
            return result
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="鼠标移动节点",
                node_name=self.name,
                reason=str(e)
            )
            return NodeStatus.FAILURE

    def _get_start_position(self, context) -> Tuple[int, int]:
        if self.use_blackboard:
            bb_position = context.blackboard.get(self.position_key)
            if bb_position:
                return bb_position
        return self.position

    def _get_end_position(self, context) -> Optional[Tuple[int, int]]:
        if self.use_blackboard_end:
            bb_position = context.blackboard.get(self.position_key_end)
            if bb_position:
                return bb_position
        return self.end_position

    def _execute_move(self, context, position: Tuple[int, int]) -> NodeStatus:
        context.execute_mouse_move(position, self.relative)
        return NodeStatus.SUCCESS

    def _execute_drag(self, context, start_pos: Tuple[int, int]) -> NodeStatus:
        end_pos = self._get_end_position(context)
        
        if not end_pos:
            LogManager.instance().log_failure(
                node_type="鼠标移动节点",
                node_name=self.name,
                reason="拖拽模式需要终点位置"
            )
            return NodeStatus.FAILURE

        try:
            context.execute_mouse_click(self.drag_button, start_pos, "down", 0)
            
            if self.drag_duration > 0:
                steps = max(10, self.drag_duration // 20)
                dx = (end_pos[0] - start_pos[0]) / steps
                dy = (end_pos[1] - start_pos[1]) / steps
                
                for i in range(1, steps + 1):
                    if not context.check_running():
                        return NodeStatus.ABORTED
                    
                    current_x = int(start_pos[0] + dx * i)
                    current_y = int(start_pos[1] + dy * i)
                    context.execute_mouse_move((current_x, current_y), relative=False)
                    time.sleep(self.drag_duration / 1000.0 / steps)
            else:
                context.execute_mouse_move(end_pos, relative=False)
            
            return NodeStatus.SUCCESS
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="鼠标移动节点",
                node_name=self.name,
                reason=f"拖拽错误: {e}"
            )
            return NodeStatus.FAILURE
        finally:
            context.execute_mouse_click(self.drag_button, end_pos or start_pos, "up", 0)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["extra"]["position"] = self.position
        data["config"]["extra"]["relative"] = self.relative
        data["config"]["extra"]["use_blackboard"] = self.use_blackboard
        data["config"]["extra"]["position_key"] = self.position_key
        data["config"]["extra"]["move_type"] = self.move_type
        data["config"]["extra"]["drag_button"] = self.drag_button
        data["config"]["extra"]["end_position"] = self.end_position
        data["config"]["extra"]["use_blackboard_end"] = self.use_blackboard_end
        data["config"]["extra"]["position_key_end"] = self.position_key_end
        data["config"]["extra"]["drag_duration"] = self.drag_duration
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MouseMoveNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.position = config.get("position", (0, 0))
        node.relative = config.get_bool("relative", False)
        node.use_blackboard = config.get_bool("use_blackboard", False)
        node.position_key = config.get("position_key", "last_detection_position")
        node.move_type = config.get("move_type", "move")
        node.drag_button = config.get("drag_button", "left")
        node.end_position = config.get("end_position", None)
        node.use_blackboard_end = config.get_bool("use_blackboard_end", False)
        node.position_key_end = config.get("position_key_end", "last_detection_position")
        node.drag_duration = config.get_int("drag_duration", 0)
        return node
