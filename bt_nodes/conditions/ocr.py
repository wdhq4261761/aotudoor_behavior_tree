from bt_core.nodes import ConditionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any, Tuple, Optional
from bt_utils.log_manager import LogManager


class OCRConditionNode(ConditionNode):
    """OCR检测节点

    使用OCR检测屏幕区域中是否包含指定关键词。

    Args:
        region: 检测区域 (left, top, right, bottom)
        keywords: 关键词（逗号分隔）
        language: OCR语言
    """
    NODE_TYPE = "OCRConditionNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.region: Optional[Tuple[int, int, int, int]] = self.config.get("region", None)
        self.keywords = self.config.get("keywords", "")
        self.language = self.config.get("language", "eng")

    def _check_condition(self, context) -> bool:
        try:
            screenshot = context.get_screenshot(self.region)
            found, position = context.perform_ocr(screenshot, self.keywords, self.language)

            if found and position:
                context.blackboard.set(self.position_key, position)
                LogManager.instance().log_success(
                    node_type="OCR检测节点",
                    node_name=self.name
                )
                return True
            else:
                LogManager.instance().log_failure(
                    node_type="OCR检测节点",
                    node_name=self.name,
                    reason=f"未找到关键词: {self.keywords}"
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
        data["config"]["extra"]["region"] = self.region
        data["config"]["extra"]["keywords"] = self.keywords
        data["config"]["extra"]["language"] = self.language
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OCRConditionNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.region = config.get("region", None)
        node.keywords = config.get("keywords", "")
        node.language = config.get("language", "eng")
        return node
