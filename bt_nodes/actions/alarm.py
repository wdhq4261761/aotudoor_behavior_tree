from bt_core.nodes import ActionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any, Optional
import time
import threading
from bt_utils.log_manager import LogManager


class AlarmNode(ActionNode):
    NODE_TYPE = "AlarmNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        
        from bt_utils.resource_manager import ResourceManager
        from config.settings_manager import SettingsManager
        
        default_sound = ResourceManager().get_alarm_sound_path()
        default_volume = SettingsManager().get("alarm_volume", 70)
        
        self.sound_path = self.config.get("sound_path", default_sound)
        self.volume = self.config.get_int("volume", default_volume)
        self.wait_complete = self.config.get_bool("wait_complete", True)
        self.repeat_count = self.config.get_int("repeat_count", 0)
        self.interval_ms = self.config.get_int("interval_ms", 0)
        self._abort_flag = False
        self._current_repeat = 0
        
        if "sound_path" not in self.config.extra:
            self.config.set("sound_path", default_sound)
        
        if "volume" not in self.config.extra:
            self.config.set("volume", default_volume)

    def _execute_action(self, context) -> NodeStatus:
        try:
            from bt_utils.alarm import AlarmPlayer
            player = AlarmPlayer()

            if self.repeat_count == -1:
                result = self._infinite_play(player, context)
            elif self.repeat_count > 0:
                result = self._finite_play(player, context)
            else:
                player.play(self.sound_path, self.volume, self.wait_complete)
                result = NodeStatus.SUCCESS
            
            if result == NodeStatus.SUCCESS:
                LogManager.instance().log_success(
                    node_type="报警节点",
                    node_name=self.name
                )
            elif result == NodeStatus.ABORTED:
                LogManager.instance().log_aborted(
                    node_type="报警节点",
                    node_name=self.name
                )
            
            return result

        except Exception as e:
            LogManager.instance().log_failure(
                node_type="报警节点",
                node_name=self.name,
                reason=str(e)
            )
            return NodeStatus.FAILURE

    def _finite_play(self, player, context) -> NodeStatus:
        while self._current_repeat < self.repeat_count:
            if self._abort_flag or not context.check_running():
                self._current_repeat = 0
                return NodeStatus.ABORTED
            
            player.play(self.sound_path, self.volume, self.wait_complete)
            self._current_repeat += 1
            
            if self._current_repeat < self.repeat_count and self.interval_ms > 0:
                time.sleep(self.interval_ms / 1000.0)
        
        self._current_repeat = 0
        return NodeStatus.SUCCESS

    def _infinite_play(self, player, context) -> NodeStatus:
        while context.check_running() and not self._abort_flag:
            player.play(self.sound_path, self.volume, self.wait_complete)
            
            if self.interval_ms > 0:
                time.sleep(self.interval_ms / 1000.0)
        
        self._abort_flag = False
        return NodeStatus.ABORTED

    def abort(self, context) -> None:
        self._abort_flag = True
        super().abort(context)

    def reset(self) -> None:
        super().reset()
        self._abort_flag = False
        self._current_repeat = 0

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["extra"]["sound_path"] = self.sound_path
        data["config"]["extra"]["volume"] = self.volume
        data["config"]["extra"]["wait_complete"] = self.wait_complete
        data["config"]["extra"]["repeat_count"] = self.repeat_count
        data["config"]["extra"]["interval_ms"] = self.interval_ms
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlarmNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.sound_path = config.get("sound_path", "")
        node.volume = config.get_int("volume", 70)
        node.wait_complete = config.get_bool("wait_complete", True)
        node.repeat_count = config.get_int("repeat_count", 0)
        node.interval_ms = config.get_int("interval_ms", 0)
        return node
