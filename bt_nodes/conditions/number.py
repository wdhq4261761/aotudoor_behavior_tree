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
            from config.settings_manager import get_default_value_key
            default_value_key = get_default_value_key()
        except ImportError:
            default_value_key = "last_number_value"
        
        self.value_key = self.config.get("value_key", default_value_key)

    def _check_condition(self, context) -> bool:
        print(f"[数字节点] _check_condition 被调用 - {self.name}")
        
        from bt_utils.ocr_manager import OCRManager
        
        if not OCRManager.is_available():
            reason = OCRManager.get_unavailable_reason()
            from bt_utils.log_manager import LogManager
            LogManager.instance().log_failure(
                node_type="数字条件节点",
                node_name=self.name,
                reason=f"OCR功能不可用: {reason}"
            )
            print(f"[数字节点] OCR功能不可用: {reason}")
            return False
        
        try:
            screenshot = context.get_screenshot(self.region)
            print(f"[数字节点] 获取截图成功 - 尺寸: {screenshot.size}")

            ocr = OCRManager()
            found, value, all_text = ocr.recognize_number(
                screenshot,
                language=self.language,
                preprocess_mode=self.preprocess_mode,
                extract_mode=self.extract_mode,
                extract_pattern=self.extract_pattern,
                min_confidence=self.min_confidence
            )
            
            print(f"[数字节点] OCR结果 - 找到: {found}, 数值: {value}, 文本: {all_text}")

            if found and value is not None:
                if self.save_value:
                    context.blackboard.set(self.value_key, value)

                if self.save_position and self.region:
                    center_x = (self.region[0] + self.region[2]) // 2
                    center_y = (self.region[1] + self.region[3]) // 2
                    context.blackboard.set(self.position_key, (center_x, center_y))

                from bt_utils.log_manager import LogManager
                LogManager.instance().log_success(
                    node_type="数字条件节点",
                    node_name=self.name
                )
                if all_text:
                    LogManager.instance().log_info(
                        node_type="数字条件节点",
                        node_name=self.name,
                        message=f"识别结果: {all_text}, 提取数值: {value}"
                    )

                if self.operator in self.OPERATORS:
                    result = self.OPERATORS[self.operator](value, self.target_value)
                    print(f"[数字节点] 比较: {value} {self.operator} {self.target_value} = {result}")
                    return result

            from bt_utils.log_manager import LogManager
            LogManager.instance().log_failure(
                node_type="数字条件节点",
                node_name=self.name,
                reason=f"未识别到数字"
            )
            if all_text:
                LogManager.instance().log_info(
                    node_type="数字条件节点",
                    node_name=self.name,
                    message=f"识别结果: {all_text}"
                )
            return False
        except Exception as e:
            print(f"[数字节点] 异常: {e}")
            import traceback
            traceback.print_exc()
            
            from bt_utils.log_manager import LogManager
            LogManager.instance().log_failure(
                node_type="数字条件节点",
                node_name=self.name,
                reason=f"执行错误: {str(e)}"
            )
            return False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["region"] = self.region
        data["config"]["compare_mode"] = self.compare_mode
        data["config"]["threshold"] = self.threshold
        data["config"]["language"] = self.language
        data["config"]["preprocess_mode"] = "艺术字" if self.preprocess_mode == "artistic" else "普通文本"
        data["config"]["extract_mode"] = self.extract_mode
        data["config"]["extract_pattern"] = self.extract_pattern
        data["config"]["min_confidence"] = int(self.min_confidence * 100)
        data["config"]["save_value"] = self.save_value
        data["config"]["value_key"] = self.value_key
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NumberConditionNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        
        if "name" in data:
            config.name = data["name"]
        if "description" in data:
            config.description = data["description"]
        if "enabled" in data:
            config.enabled = data["enabled"]
        
        node = cls(node_id=data.get("id"), config=config)
        node.region = config.get("region", None)
        node.compare_mode = config.get("compare_mode", ">=")
        node.operator = node.compare_mode
        node.threshold = config.get_float("threshold", 0)
        node.target_value = node.threshold
        node.language = config.get("language", "eng")
        preprocess_mode_display = config.get("preprocess_mode", "普通文本")
        node.preprocess_mode = "artistic" if preprocess_mode_display == "艺术字" else "normal"
        node.extract_mode = config.get("extract_mode", "无规则")
        node.extract_pattern = config.get("extract_pattern", "")
        node.min_confidence = config.get_float("min_confidence", 50) / 100.0
        node.save_value = config.get_bool("save_value", True)
        
        try:
            from config.settings_manager import get_default_value_key
            default_value_key = get_default_value_key()
        except ImportError:
            default_value_key = "last_number_value"
        
        node.value_key = config.get("value_key", default_value_key)
        return node
