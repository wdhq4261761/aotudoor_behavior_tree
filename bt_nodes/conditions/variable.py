from bt_core.nodes import ConditionNode
from bt_core.config import NodeConfig
from typing import Dict, Any, Optional


class VariableConditionNode(ConditionNode):
    """变量判断节点

    检查黑板中变量的值是否满足条件。
    支持自动类型推断和多种运算符。

    Args:
        variable_name: 变量名
        operator: 比较运算符 (==, !=, >, >=, <, <=, contains, not_contains, exists, not_exists)
        target_value: 目标值
    """
    NODE_TYPE = "VariableConditionNode"

    OPERATORS = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">": lambda a, b: a > b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else False,
        ">=": lambda a, b: a >= b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else False,
        "<": lambda a, b: a < b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else False,
        "<=": lambda a, b: a <= b if isinstance(a, (int, float)) and isinstance(b, (int, float)) else False,
        "contains": lambda a, b: b in a if isinstance(a, str) and isinstance(b, str) else False,
        "not_contains": lambda a, b: b not in a if isinstance(a, str) and isinstance(b, str) else True,
        "exists": lambda a, b: a is not None,
        "not_exists": lambda a, b: a is None,
    }

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.variable_name = self.config.get("variable_name", "")
        self.operator = self.config.get("operator", "==")
        self.target_value = self.config.get("target_value", "")

    def _infer_type(self, value: Any, target: Any) -> Any:
        """类型推断

        根据变量值类型自动转换目标值类型。

        Args:
            value: 变量值
            target: 目标值

        Returns:
            转换后的目标值
        """
        if value is None:
            return target

        if isinstance(value, bool):
            if isinstance(target, str):
                target_lower = target.lower().strip()
                if target_lower in ("true", "1", "yes", "是"):
                    return True
                elif target_lower in ("false", "0", "no", "否"):
                    return False
            return bool(target)

        if isinstance(value, int):
            try:
                return int(float(target))
            except (ValueError, TypeError):
                return target

        if isinstance(value, float):
            try:
                return float(target)
            except (ValueError, TypeError):
                return target

        if isinstance(value, str):
            return str(target)

        return target

    def _check_condition(self, context) -> bool:
        try:
            value = context.blackboard.get(self.variable_name)

            if self.operator == "exists":
                return value is not None

            if self.operator == "not_exists":
                return value is None

            inferred_target = self._infer_type(value, self.target_value)

            if self.operator in self.OPERATORS:
                return self.OPERATORS[self.operator](value, inferred_target)

            return False
        except Exception as e:
            print(f"[WARN] VariableConditionNode错误: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["extra"]["variable_name"] = self.variable_name
        data["config"]["extra"]["operator"] = self.operator
        data["config"]["extra"]["target_value"] = self.target_value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VariableConditionNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.variable_name = config.get("variable_name", "")
        node.operator = config.get("operator", "==")
        node.target_value = config.get("target_value", "")
        return node
