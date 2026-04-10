from bt_core.nodes import ConditionNode
from bt_core.config import NodeConfig
from typing import Dict, Any, Tuple, Optional


class NumberConditionNode(ConditionNode):
    NODE_TYPE = "NumberConditionNode"

    OPERATORS = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
    }

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.region: Optional[Tuple[int, int, int, int]] = self.config.get("region", None)
        self.compare_mode = self.config.get("compare_mode", ">=")
        self.operator = self.compare_mode
        self.threshold = self.config.get_float("threshold", 0)
        self.target_value = self.threshold
        self.language = self.config.get("language", "eng")
        preprocess_mode_display = self.config.get("preprocess_mode", "普通文本")
        self.preprocess_mode = "artistic" if preprocess_mode_display == "艺术字" else "normal"
        self.extract_mode = self.config.get("extract_mode", "无规则")
        self.extract_pattern = self.config.get("extract_pattern", "")
        self.min_confidence = self.config.get_float("min_confidence", 50) / 100.0
        self.save_value = self.config.get_bool("save_value", True)
        
        try:
            from bt_utils.config_manager import get_default_value_key
            default_value_key = get_default_value_key()
        except ImportError:
            default_value_key = "last_number_value"
        
        self.value_key = self.config.get("value_key", default_value_key)

    def _check_condition(self, context) -> bool:
        try:
            screenshot = context.get_screenshot(self.region)

            from bt_utils.ocr_manager import OCRManager
            ocr = OCRManager()
            found, value = ocr.recognize_number(
                screenshot,
                language=self.language,
                preprocess_mode=self.preprocess_mode,
                extract_mode=self.extract_mode,
                extract_pattern=self.extract_pattern,
                min_confidence=self.min_confidence
            )

            if found and value is not None:
                if self.save_value:
                    context.blackboard.set(self.value_key, value)

                if self.save_position and self.region:
                    center_x = (self.region[0] + self.region[2]) // 2
                    center_y = (self.region[1] + self.region[3]) // 2
                    context.blackboard.set(self.position_key, (center_x, center_y))

                if self.operator in self.OPERATORS:
                    return self.OPERATORS[self.operator](value, self.target_value)

            return False
        except Exception as e:
            print(f"[WARN] NumberConditionNode错误: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["extra"]["region"] = self.region
        data["config"]["extra"]["operator"] = self.operator
        data["config"]["extra"]["target_value"] = self.target_value
        data["config"]["extra"]["language"] = self.language
        data["config"]["extra"]["preprocess_mode"] = self.preprocess_mode
        data["config"]["extra"]["extract_mode"] = self.extract_mode
        data["config"]["extra"]["extract_pattern"] = self.extract_pattern
        data["config"]["extra"]["min_confidence"] = self.min_confidence
        data["config"]["extra"]["save_value"] = self.save_value
        data["config"]["extra"]["value_key"] = self.value_key
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NumberConditionNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.region = config.get("region", None)
        node.operator = config.get("operator", ">=")
        node.target_value = config.get_float("target_value", 0)
        node.language = config.get("language", "eng")
        node.preprocess_mode = config.get("preprocess_mode", "normal")
        node.extract_mode = config.get("extract_mode", "无规则")
        node.extract_pattern = config.get("extract_pattern", "")
        node.min_confidence = config.get_float("min_confidence", 0.5)
        node.save_value = config.get_bool("save_value", True)
        node.value_key = config.get("value_key", "last_number_value")
        return node
