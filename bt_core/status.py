from enum import Enum


class NodeStatus(Enum):
    """节点执行状态枚举"""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"
    ABORTED = "aborted"
