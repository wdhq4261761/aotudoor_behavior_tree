import os
from PIL import Image
from bt_core.nodes import ConditionNode
from bt_core.config import NodeConfig
from typing import Dict, Any, Tuple, Optional
from bt_utils.log_manager import LogManager


class ImageConditionNode(ConditionNode):
    NODE_TYPE = "ImageConditionNode"

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.template_path = self.config.get("template_path", "")
        raw_region = self.config.get("region", None)
        self.region: Optional[Tuple[int, int, int, int]] = self._parse_region(raw_region)
        self.threshold = self.config.get_float("threshold", 0.8)

        self._template_image = None

        self._last_template_path = None

        self._last_template_mtime = 0

    def _check_condition(self, context) -> bool:
        try:
            if not self.template_path:
                LogManager.instance().log_failure(
                    node_type="图像检测节点",
                    node_name=self.name,
                    reason="模板路径为空"
                )
                return False

            absolute_template_path = self.template_path
            if self.template_path.startswith("./"):
                if hasattr(context, 'resolve_path'):
                    absolute_template_path = context.resolve_path(self.template_path)
                elif hasattr(context, 'project_root'):
                    absolute_template_path = os.path.join(context.project_root, self.template_path[2:])
            else:
                absolute_template_path = os.path.abspath(self.template_path)
            if not os.path.exists(absolute_template_path):
                LogManager.instance().log_failure(
                    node_type="图像检测节点",
                    node_name=self.name,
                    reason=f"模板文件不存在: {absolute_template_path}"
                )
                return False
            if self._template_image is None or self._last_template_path != absolute_template_path:
                self._template_image = Image.open(absolute_template_path)
                self._last_template_path = absolute_template_path
                self._last_template_mtime = os.path.getmtime(absolute_template_path)
            screenshot = context.get_screenshot(self.region)
            from bt_utils.image_processor import ImageProcessor
            found, position = ImageProcessor.find_template(
                screenshot, self._template_image, self.threshold
            )
            if found and position:
                if self.region:
                    position = (position[0] + self.region[0], position[1] + self.region[1])
                context.blackboard.set(self.position_key, position)
                LogManager.instance().log_success(
                    node_type="图像检测节点",
                    node_name=self.name
                )
                return True
            else:
                LogManager.instance().log_failure(
                    node_type="图像检测节点",
                    node_name=self.name,
                    reason="未找到匹配的图像"
                )
                return False
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="图像检测节点",
                node_name=self.name,
                reason=str(e)
            )
            return False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["template_path"] = self.template_path
        data["config"]["region"] = list(self.region) if self.region else None
        data["config"]["threshold"] = self.threshold
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageConditionNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        return node
