from bt_core.nodes import ConditionNode
from bt_core.config import NodeConfig
from bt_utils.log_manager import LogManager
from typing import Dict, Any, Optional


class VariableConditionNode(ConditionNode):
    """变量判断节点

    检查黑板中变量的值是否满足条件。
    支持自动类型推断和多种运算符。

    Args:
        variable_name: 变量名
        operator: 比较运算符 (==, !=, >, >=, <, <=, contains, not_contains, exists, not_exists)
        compare_value: 比较值
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
        self.compare_value = self.config.get("compare_value", "")

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
                result = value is not None
                if result:
                    LogManager.instance().log_success(
                        node_type="变量条件节点",
                        node_name=self.name
                    )
                else:
                    LogManager.instance().log_failure(
                        node_type="变量条件节点",
                        node_name=self.name,
                        reason=f"变量 '{self.variable_name}' 不存在"
                    )
                return result

            if self.operator == "not_exists":
                result = value is None
                if result:
                    LogManager.instance().log_success(
                        node_type="变量条件节点",
                        node_name=self.name
                    )
                else:
                    LogManager.instance().log_failure(
                        node_type="变量条件节点",
                        node_name=self.name,
                        reason=f"变量 '{self.variable_name}' 存在，值为: {value}"
                    )
                return result

            if value is None:
                LogManager.instance().log_failure(
                    node_type="变量条件节点",
                    node_name=self.name,
                    reason=f"变量 '{self.variable_name}' 不存在"
                )
                return False

            inferred_target = self._infer_type(value, self.compare_value)

            if self.operator in self.OPERATORS:
                result = self.OPERATORS[self.operator](value, inferred_target)
                if result:
                    LogManager.instance().log_success(
                        node_type="变量条件节点",
                        node_name=self.name
                    )
                else:
                    LogManager.instance().log_failure(
                        node_type="变量条件节点",
                        node_name=self.name,
                        reason=f"比较: {value} {self.operator} {inferred_target} = False"
                    )
                return result

            LogManager.instance().log_failure(
                node_type="变量条件节点",
                node_name=self.name,
                reason=f"未知运算符: {self.operator}"
            )
            return False
        except Exception as e:
            LogManager.instance().log_failure(
                node_type="变量条件节点",
                node_name=self.name,
                reason=f"执行错误: {str(e)}"
            )
            return False

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["variable_name"] = self.variable_name
        data["config"]["operator"] = self.operator
        data["config"]["compare_value"] = self.compare_value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VariableConditionNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.variable_name = config.get("variable_name", "")
        node.operator = config.get("operator", "==")
        node.compare_value = config.get("compare_value", "")
        return node
