from bt_core.nodes import ConditionNode
from bt_core.config import NodeConfig
from typing import Dict, Any, Tuple, Optional
from bt_utils.log_manager import LogManager


class ColorConditionNode(ConditionNode):
    NODE_TYPE = "ColorConditionNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        raw_color = self.config.get("target_color", (255, 0, 0))
        self.target_color: Tuple[int, int, int] = self._parse_color(raw_color)
        raw_region = self.config.get("region", None)
        self.region: Optional[Tuple[int, int, int, int]] = self._parse_region(raw_region)
        self.tolerance = self.config.get_int("tolerance", 10)

    def _check_condition(self, context) -> bool:
        try:
            screenshot = context.get_screenshot(self.region)

            from bt_utils.image_processor import ImageProcessor
            found, position = ImageProcessor.find_color(
                screenshot, self.target_color, self.tolerance
            )

            if found and position:
                context.blackboard.set(self.position_key, position)
                LogManager.instance().log_success(
                    node_type="颜色检测节点",
                    node_name=self.name
                )
                return True
            else:
                LogManager.instance().log_failure(
                    node_type="颜色检测节点",
                    node_name=self.name,
                    reason=f"未找到目标颜色: {self.target_color}"
                )
                return False
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="颜色检测节点",
                node_name=self.name,
                reason=str(e)
            )
            return False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["target_color"] = list(self.target_color) if self.target_color else [255, 0, 0]
        data["config"]["region"] = list(self.region) if self.region else None
        data["config"]["tolerance"] = self.tolerance
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColorConditionNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        return node
