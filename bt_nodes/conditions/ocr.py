from bt_core.nodes import ConditionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any, Tuple, Optional
from bt_utils.log_manager import LogManager


class OCRConditionNode(ConditionNode):
    """OCR检测节点

    使用OCR检测屏幕区域中是否包含指定关键词。

    Args:
        region: 检测区域
        keywords: 关键词（逗号分隔）
        language: OCR语言
    """
    NODE_TYPE = "OCRConditionNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.region: Optional[Tuple[int, int, int, int]] = self.config.get("region", None)
        self.keywords = self.config.get("keywords", "")
        self.language = self.config.get("language", "eng")

    def tick(self, context: "ExecutionContext") -> NodeStatus:
        print(f"[OCR节点] tick 被调用 - {self.name}")
        result = super().tick(context)
        print(f"[OCR节点] tick 返回 - {self.name}, 状态: {result}")
        return result

    def _check_condition(self, context) -> bool:
        print(f"[OCR节点] _check_condition 被调用 - {self.name}")
        
        from bt_utils.ocr_manager import OCRManager
        
        if not OCRManager.is_available():
            reason = OCRManager.get_unavailable_reason()
            LogManager.instance().log_failure(
                node_type="OCR检测节点",
                node_name=self.name,
                reason=f"OCR功能不可用: {reason}"
            )
            print(f"[OCR节点] OCR功能不可用: {reason}")
            return False
        
        LogManager.instance().log_info(
            node_type="OCR检测节点",
            node_name=self.name,
            message=f"开始检测 - 区域: {self.region}, 关键词: {self.keywords}, 语言: {self.language}"
        )
        
        try:
            screenshot = context.get_screenshot(self.region)
            print(f"[OCR节点] 获取截图成功 - 尺寸: {screenshot.size}")
            
            LogManager.instance().log_info(
                node_type="OCR检测节点",
                node_name=self.name,
                message=f"获取截图成功 - 尺寸: {screenshot.size}"
            )
            
            found, position, all_text = context.perform_ocr(
                screenshot, self.keywords, self.language, region=self.region
            )
            print(f"[OCR节点] OCR结果 - 找到: {found}, 位置: {position}, 文本: {all_text}")

            if found and position:
                context.blackboard.set(self.position_key, position)
                LogManager.instance().log_success(
                    node_type="OCR检测节点",
                    node_name=self.name
                )
                if all_text:
                    LogManager.instance().log_info(
                        node_type="OCR检测节点",
                        node_name=self.name,
                        message=f"识别结果: {all_text}"
                    )
                LogManager.instance().log_info(
                    node_type="OCR检测节点",
                    node_name=self.name,
                    message=f"找到关键词，位置: {position}"
                )
                return True
            else:
                LogManager.instance().log_failure(
                    node_type="OCR检测节点",
                    node_name=self.name,
                    reason=f"未找到关键词: {self.keywords}"
                )
                if all_text:
                    LogManager.instance().log_info(
                        node_type="OCR检测节点",
                        node_name=self.name,
                        message=f"识别结果: {all_text}"
                    )
                return False
        except Exception as e:
            print(f"[OCR节点] 异常: {e}")
            import traceback
            traceback.print_exc()
            
            LogManager.instance().log_failure(
                node_type="OCR检测节点",
                node_name=self.name,
                reason=str(e)
            )
            return False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["region"] = self.region
        data["config"]["keywords"] = self.keywords
        data["config"]["language"] = self.language
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OCRConditionNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        
        if "name" in data:
            config.name = data["name"]
        if "description" in data:
            config.description = data["description"]
        if "enabled" in data:
            config.enabled = data["enabled"]
        
        node = cls(node_id=data.get("id"), config=config)
        node.region = config.get("region", None)
        node.keywords = config.get("keywords", "")
        node.language = config.get("language", "eng")
        
        return node
