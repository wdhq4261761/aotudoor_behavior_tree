from .ocr import OCRConditionNode
from .image import ImageConditionNode
from .color import ColorConditionNode
from .number import NumberConditionNode
from .variable import VariableConditionNode

from bt_core.registry import NodeRegistry

NodeRegistry.register("OCRConditionNode", OCRConditionNode)
NodeRegistry.register("ImageConditionNode", ImageConditionNode)
NodeRegistry.register("ColorConditionNode", ColorConditionNode)
NodeRegistry.register("NumberConditionNode", NumberConditionNode)
NodeRegistry.register("VariableConditionNode", VariableConditionNode)

__all__ = [
    "OCRConditionNode",
    "ImageConditionNode",
    "ColorConditionNode",
    "NumberConditionNode",
    "VariableConditionNode",
]
