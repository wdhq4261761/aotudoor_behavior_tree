from .keyboard import KeyPressNode
from .mouse import MouseClickNode, MouseMoveNode
from .scroll import MouseScrollNode
from .delay import DelayNode
from .variable import SetVariableNode
from .script import ScriptNode
from .code import CodeNode
from .alarm import AlarmNode

from bt_core.registry import NodeRegistry

NodeRegistry.register("KeyPressNode", KeyPressNode)
NodeRegistry.register("MouseClickNode", MouseClickNode)
NodeRegistry.register("MouseMoveNode", MouseMoveNode)
NodeRegistry.register("MouseScrollNode", MouseScrollNode)
NodeRegistry.register("DelayNode", DelayNode)
NodeRegistry.register("SetVariableNode", SetVariableNode)
NodeRegistry.register("ScriptNode", ScriptNode)
NodeRegistry.register("CodeNode", CodeNode)
NodeRegistry.register("AlarmNode", AlarmNode)

__all__ = [
    "KeyPressNode",
    "MouseClickNode",
    "MouseMoveNode",
    "MouseScrollNode",
    "DelayNode",
    "SetVariableNode",
    "ScriptNode",
    "CodeNode",
    "AlarmNode",
]
