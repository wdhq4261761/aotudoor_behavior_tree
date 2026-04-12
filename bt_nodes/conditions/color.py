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
        self.min_pixels = self.config.get_int("min_pixels", 1)

    def _check_condition(self, context) -> bool:
        try:
            screenshot = context.get_screenshot(self.region)

            from bt_utils.image_processor import ImageProcessor
            found, position, match_count = ImageProcessor.find_color_with_count(
                screenshot, self.target_color, self.tolerance
            )

            if found and position and match_count >= self.min_pixels:
                if self.region:
                    position = (position[0] + self.region[0], position[1] + self.region[1])
                context.blackboard.set(self.position_key, position)
                LogManager.instance().log_success(
                    node_type="颜色检测节点",
                    node_name=self.name,
                    message=f"匹配像素数: {match_count}"
                )
                return True
            else:
                reason = f"未找到目标颜色: {self.target_color}"
                if found and match_count < self.min_pixels:
                    reason = f"匹配像素数({match_count})小于最小阈值({self.min_pixels})"
                LogManager.instance().log_failure(
                    node_type="颜色检测节点",
                    node_name=self.name,
                    reason=reason
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
        data["config"]["min_pixels"] = self.min_pixels
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColorConditionNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        return node
