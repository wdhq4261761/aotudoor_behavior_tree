from bt_core.nodes import ConditionNode
from bt_core.config import NodeConfig
from typing import Dict, Any, Tuple, Optional
from bt_utils.log_manager import LogManager


from bt_utils.ocr_manager import OCRManager


class OCRConditionNode(ConditionNode):
    NODE_TYPE = "OCRConditionNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.region: Optional[Tuple[int, int, int, int]] = self._parse_region(self.config.get("region", None))
        self.keywords = self.config.get("keywords", "")
        self.language = self.config.get("language", "eng")
        preprocess_display = self.config.get("preprocess_mode", "默认")
        self.preprocess_mode = "game" if preprocess_display == "游戏" else "normal"

        self.position_key = self.config.get("position_key", "last_detection_position")

    def _check_condition(self, context) -> bool:
        try:
            screenshot = context.get_screenshot(self.region)

            found, position, all_text = OCRManager.instance().recognize(
                screenshot, self.keywords, self.language, 
                preprocess_mode=self.preprocess_mode, region=self.region
            )

            if found:
                context.blackboard.set(self.position_key, position)
                LogManager.instance().log_success(
                    node_type="OCR检测节点",
                    node_name=self.name
                )
                return True
            else:
                reason = f"未找到关键词: {self.keywords}"
                if all_text:
                    reason += f"，识别到的文本: {all_text}"
                LogManager.instance().log_failure(
                    node_type="OCR检测节点",
                    node_name=self.name,
                    reason=reason
                )
                return False
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="OCR检测节点",
                node_name=self.name,
                reason=str(e)
            )
            return False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["region"] = list(self.region) if self.region else None
        data["config"]["keywords"] = self.keywords
        data["config"]["language"] = self.language
        data["config"]["preprocess_mode"] = "游戏" if self.preprocess_mode == "game" else "默认"
        data["config"]["position_key"] = self.position_key
        return data

