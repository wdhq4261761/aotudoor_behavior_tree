from bt_core.nodes import ActionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any
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
        self._abort_flag = False
        
        if "sound_path" not in self.config.extra:
            self.config.set("sound_path", default_sound)
        
        if "volume" not in self.config.extra:
            self.config.set("volume", default_volume)

    def _execute_action(self, context) -> NodeStatus:
        try:
            from bt_utils.alarm import AlarmPlayer
            player = AlarmPlayer()

            resolved_sound_path = context.resolve_path(self.sound_path)
            player.play(resolved_sound_path, self.volume, self.wait_complete)
            
            LogManager.instance().log_success(
                node_type="报警节点",
                node_name=self.name
            )
            
            return NodeStatus.SUCCESS

        except Exception as e:
            LogManager.instance().log_failure(
                node_type="报警节点",
                node_name=self.name,
                reason=str(e)
            )
            return NodeStatus.FAILURE

    def abort(self, context) -> None:
        self._abort_flag = True
        from bt_utils.alarm import AlarmPlayer
        AlarmPlayer().stop()
        super().abort(context)

    def reset(self, reset_counters: bool = True) -> None:
        super().reset(reset_counters=reset_counters)
        self._abort_flag = False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["sound_path"] = self.sound_path
        data["config"]["volume"] = self.volume
        data["config"]["wait_complete"] = self.wait_complete
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlarmNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        return node
