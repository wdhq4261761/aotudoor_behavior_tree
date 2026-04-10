from typing import Dict, Type, Any, Optional

from .nodes import Node


class NodeRegistry:
    _node_types: Dict[str, Type[Node]] = {}

    @classmethod
    def register(cls, node_type: str, node_class: Type[Node]) -> None:
        cls._node_types[node_type] = node_class

    @classmethod
    def unregister(cls, node_type: str) -> None:
        if node_type in cls._node_types:
            del cls._node_types[node_type]

    @classmethod
    def get(cls, node_type: str) -> Optional[Type[Node]]:
        return cls._node_types.get(node_type)

    @classmethod
    def create_node(cls, data: Dict[str, Any]) -> Optional[Node]:
        node_type = data.get("type", "")
        node_class = cls.get(node_type)

        if node_class is None:
            return None

        return node_class.from_dict(data)

    @classmethod
    def list_types(cls) -> Dict[str, Type[Node]]:
        return dict(cls._node_types)


def register_core_nodes():
    from .nodes import SequenceNode, SelectorNode, ParallelNode

    NodeRegistry.register("SequenceNode", SequenceNode)
    NodeRegistry.register("SelectorNode", SelectorNode)
    NodeRegistry.register("ParallelNode", ParallelNode)


def register_all_nodes():
    from .nodes import SequenceNode, SelectorNode, ParallelNode
    
    NodeRegistry.register("SequenceNode", SequenceNode)
    NodeRegistry.register("SelectorNode", SelectorNode)
    NodeRegistry.register("ParallelNode", ParallelNode)
    
    from bt_nodes.actions.keyboard import KeyPressNode
    from bt_nodes.actions.mouse import MouseClickNode, MouseMoveNode
    from bt_nodes.actions.scroll import MouseScrollNode
    from bt_nodes.actions.delay import DelayNode
    from bt_nodes.actions.variable import SetVariableNode
    from bt_nodes.actions.script import ScriptNode
    from bt_nodes.actions.code import CodeNode
    from bt_nodes.actions.alarm import AlarmNode
    
    NodeRegistry.register("KeyPressNode", KeyPressNode)
    NodeRegistry.register("MouseClickNode", MouseClickNode)
    NodeRegistry.register("MouseMoveNode", MouseMoveNode)
    NodeRegistry.register("MouseScrollNode", MouseScrollNode)
    NodeRegistry.register("DelayNode", DelayNode)
    NodeRegistry.register("SetVariableNode", SetVariableNode)
    NodeRegistry.register("ScriptNode", ScriptNode)
    NodeRegistry.register("CodeNode", CodeNode)
    NodeRegistry.register("AlarmNode", AlarmNode)
    
    from bt_nodes.conditions.ocr import OCRConditionNode
    from bt_nodes.conditions.image import ImageConditionNode
    from bt_nodes.conditions.color import ColorConditionNode
    from bt_nodes.conditions.number import NumberConditionNode
    from bt_nodes.conditions.variable import VariableConditionNode
    
    NodeRegistry.register("OCRConditionNode", OCRConditionNode)
    NodeRegistry.register("ImageConditionNode", ImageConditionNode)
    NodeRegistry.register("ColorConditionNode", ColorConditionNode)
    NodeRegistry.register("NumberConditionNode", NumberConditionNode)
    NodeRegistry.register("VariableConditionNode", VariableConditionNode)
