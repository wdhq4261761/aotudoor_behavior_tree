from bt_core.nodes import ConditionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any, Tuple, Optional
from bt_utils.log_manager import LogManager


class NumberConditionNode(ConditionNode):
    NODE_TYPE = "NumberConditionNode"

    OPERATORS = {
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        raw_region = self.config.get("region", None)
        self.region: Optional[Tuple[int, int, int, int]] = self._parse_region(raw_region)
        self.compare_mode = self.config.get("compare_mode", ">=")
        self.threshold = self.config.get_float("threshold", 0)
        self.language = self.config.get("language", "eng")
        preprocess_mode_display = self.config.get("preprocess_mode", "普通文本")
        self.preprocess_mode = "artistic" if preprocess_mode_display == "艺术字" else "normal"
        self.extract_mode = self.config.get("extract_mode", "无规则")
        self.extract_pattern = self.config.get("extract_pattern", "")
        self.min_confidence = self.config.get_float("min_confidence", 50) / 100.0
        self.save_value = self.config.get_bool("save_value", True)
        
        try:
            from config.settings_manager import get_default_value_key
            default_value_key = get_default_value_key()
        except ImportError:
            default_value_key = "last_number_value"
        
        self.value_key = self.config.get("value_key", default_value_key)
        self.position_key = self.config.get("position_key", "last_detection_position")

    def _check_condition(self, context) -> bool:
        from bt_utils.ocr_manager import OCRManager
        
        if not OCRManager.is_available():
            LogManager.instance().log_failure(
                node_type="数字节点",
                node_name=self.name,
                reason="OCR不可用"
            )
            return False
        
        try:
            screenshot = context.get_screenshot(self.region)
            
            from bt_utils.ocr_manager import OCRManager
            ocr_manager = OCRManager.instance()
            
            found, value, all_text, position = ocr_manager.recognize_number_with_position(
                screenshot, 
                language=self.language
            )
            
            if found and value is not None:
                if self.save_value:
                    context.blackboard.set(self.value_key, value)
                
                if position:
                    abs_position = position
                    if self.region:
                        abs_position = (position[0] + self.region[0], position[1] + self.region[1])
                    context.blackboard.set(self.position_key, abs_position)
                
                operator_func = self.OPERATORS.get(self.compare_mode)
                if operator_func:
                    result = operator_func(value, self.threshold)
                    LogManager.instance().log_success(
                        node_type="数字节点",
                        node_name=self.name
                    )
                    return result
                else:
                    LogManager.instance().log_failure(
                        node_type="数字节点",
                        node_name=self.name,
                        reason=f"未知比较运算符: {self.compare_mode}"
                    )
                    return False
            else:
                reason = "未识别到数字"
                if all_text:
                    reason += f"，识别到的文本: {all_text}"
                LogManager.instance().log_failure(
                    node_type="数字节点",
                    node_name=self.name,
                    reason=reason
                )
                return False
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="数字节点",
                node_name=self.name,
                reason=str(e)
            )
            return False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["region"] = list(self.region) if self.region else None
        data["config"]["compare_mode"] = self.compare_mode
        data["config"]["threshold"] = self.threshold
        data["config"]["language"] = self.language
        data["config"]["preprocess_mode"] = "艺术字" if self.preprocess_mode == "artistic" else "普通文本"
        data["config"]["extract_mode"] = self.extract_mode
        data["config"]["extract_pattern"] = self.extract_pattern
        data["config"]["min_confidence"] = int(self.min_confidence * 100)
        data["config"]["save_value"] = self.save_value
        data["config"]["value_key"] = self.value_key
        data["config"]["position_key"] = self.position_key
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NumberConditionNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        return node
