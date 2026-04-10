from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, field
import inspect


@dataclass
class ConsistencyIssue:
    level: str
    category: str
    node_type: str
    field: str
    message: str
    suggestion: str = ""


@dataclass
class ConsistencyReport:
    issues: List[ConsistencyIssue] = field(default_factory=list)
    node_types_checked: int = 0
    fields_checked: int = 0
    
    def add_issue(self, issue: ConsistencyIssue):
        self.issues.append(issue)
    
    def has_errors(self) -> bool:
        return any(i.level == "error" for i in self.issues)
    
    def has_warnings(self) -> bool:
        return any(i.level == "warning" for i in self.issues)
    
    def get_summary(self) -> str:
        errors = sum(1 for i in self.issues if i.level == "error")
        warnings = sum(1 for i in self.issues if i.level == "warning")
        infos = sum(1 for i in self.issues if i.level == "info")
        
        lines = [
            f"一致性检查完成:",
            f"  - 检查节点类型: {self.node_types_checked}",
            f"  - 检查字段: {self.fields_checked}",
            f"  - 错误: {errors}",
            f"  - 警告: {warnings}",
            f"  - 信息: {infos}",
        ]
        return "\n".join(lines)
    
    def get_detailed_report(self) -> str:
        lines = [self.get_summary(), ""]
        
        if self.issues:
            lines.append("详细问题列表:")
            lines.append("-" * 60)
            
            for issue in sorted(self.issues, key=lambda x: (x.level, x.category, x.node_type)):
                lines.append(f"[{issue.level.upper()}] {issue.category}")
                lines.append(f"  节点: {issue.node_type}")
                lines.append(f"  字段: {issue.field}")
                lines.append(f"  问题: {issue.message}")
                if issue.suggestion:
                    lines.append(f"  建议: {issue.suggestion}")
                lines.append("")
        
        return "\n".join(lines)


class ConsistencyChecker:
    GUI_NODE_TYPES: Set[str] = {
        "SequenceNode", "SelectorNode", "ParallelNode",
        "OCRConditionNode", "ImageConditionNode", "ColorConditionNode",
        "NumberConditionNode", "VariableConditionNode",
        "KeyPressNode", "MouseClickNode", "MouseMoveNode", "MouseScrollNode",
        "DelayNode", "SetVariableNode", "AlarmNode", "CodeNode", "ScriptNode",
    }
    
    GUI_NODE_SCHEMAS: Dict[str, List[Dict[str, Any]]] = {}
    
    ENGINE_NODE_PARAMS: Dict[str, Set[str]] = {}
    
    COMMON_DECORATOR_PARAMS: Set[str] = {
        "retry_count", "repeat_count", "timeout_ms",
        "invert", "check_interval_ms",
        "continue_on_failure", "child_interval",
    }
    
    IGNORED_PARAMS: Set[str] = {
        "name", "enabled", "id", "type", "children",
    }

    @classmethod
    def check_all(cls) -> ConsistencyReport:
        report = ConsistencyReport()
        
        cls._load_gui_definitions()
        cls._load_engine_implementations()
        
        cls._check_node_types(report)
        cls._check_field_consistency(report)
        
        return report
    
    @classmethod
    def _load_gui_definitions(cls):
        try:
            from bt_gui.bt_editor.constants import ALL_NODE_TYPES
            cls.GUI_NODE_TYPES = set(ALL_NODE_TYPES)
        except ImportError:
            pass
        
        try:
            from bt_gui.bt_editor.property import NODE_CONFIG_SCHEMAS
            cls.GUI_NODE_SCHEMAS = NODE_CONFIG_SCHEMAS
        except ImportError:
            pass
    
    @classmethod
    def _load_engine_implementations(cls):
        from bt_core.registry import NodeRegistry
        
        registered_types = NodeRegistry.list_types()
        
        for node_type, node_class in registered_types.items():
            params = cls._extract_node_params(node_class)
            cls.ENGINE_NODE_PARAMS[node_type] = params
    
    @classmethod
    def _extract_node_params(cls, node_class) -> Set[str]:
        params = set()
        
        try:
            source = inspect.getsource(node_class.__init__)
        except (TypeError, OSError):
            source = ""
        
        config_accesses = [
            "self.config.get(",
            "self.config[",
            'config.get("',
            "config['",
        ]
        
        for line in source.split('\n'):
            line = line.strip()
            for access in config_accesses:
                if access in line:
                    try:
                        if '"' in line:
                            start = line.find('"') + 1
                            end = line.find('"', start)
                            if start > 0 and end > start:
                                param_name = line[start:end]
                                params.add(param_name)
                        elif "'" in line:
                            start = line.find("'") + 1
                            end = line.find("'", start)
                            if start > 0 and end > start:
                                param_name = line[start:end]
                                params.add(param_name)
                    except (ValueError, IndexError):
                        pass
        
        try:
            for attr_name in dir(node_class):
                if not attr_name.startswith('_') and not callable(getattr(node_class, attr_name)):
                    attr = getattr(node_class, attr_name)
                    if not isinstance(attr, (classmethod, staticmethod, type)):
                        params.add(attr_name)
        except Exception:
            pass
        
        return params
    
    @classmethod
    def _check_node_types(cls, report: ConsistencyReport):
        report.node_types_checked = len(cls.GUI_NODE_TYPES)
        
        for node_type in cls.GUI_NODE_TYPES:
            if node_type not in cls.ENGINE_NODE_PARAMS:
                report.add_issue(ConsistencyIssue(
                    level="error",
                    category="节点类型缺失",
                    node_type=node_type,
                    field="-",
                    message=f"GUI定义了节点类型 '{node_type}'，但引擎层未注册对应实现",
                    suggestion=f"在 bt_nodes 中创建 {node_type} 类并注册到 NodeRegistry"
                ))
    
    @classmethod
    def _check_field_consistency(cls, report: ConsistencyReport):
        for node_type, schema_fields in cls.GUI_NODE_SCHEMAS.items():
            engine_params = cls.ENGINE_NODE_PARAMS.get(node_type, set())
            
            for field_def in schema_fields:
                field_key = field_def.get("key", "")
                report.fields_checked += 1
                
                if field_key in cls.IGNORED_PARAMS:
                    continue
                
                if field_key not in engine_params and field_key not in cls.COMMON_DECORATOR_PARAMS:
                    level = "warning"
                    if field_key in ["region", "position", "threshold"]:
                        level = "error"
                    
                    report.add_issue(ConsistencyIssue(
                        level=level,
                        category="参数未实现",
                        node_type=node_type,
                        field=field_key,
                        message=f"GUI定义了参数 '{field_key}'，但引擎节点可能未处理该参数",
                        suggestion=f"在 {node_type}.__init__ 中添加 self.{field_key} = self.config.get('{field_key}', ...)"
                    ))
        
        for node_type, engine_params in cls.ENGINE_NODE_PARAMS.items():
            schema_fields = cls.GUI_NODE_SCHEMAS.get(node_type, [])
            gui_field_keys = {f.get("key") for f in schema_fields}
            
            for param in engine_params:
                if param.startswith("_"):
                    continue
                if param in cls.IGNORED_PARAMS:
                    continue
                if param in cls.COMMON_DECORATOR_PARAMS:
                    continue
                
                if param not in gui_field_keys:
                    report.add_issue(ConsistencyIssue(
                        level="info",
                        category="参数未在GUI定义",
                        node_type=node_type,
                        field=param,
                        message=f"引擎节点使用了参数 '{param}'，但GUI schema中未定义",
                        suggestion=f"在 NODE_CONFIG_SCHEMAS['{node_type}'] 中添加 '{param}' 字段定义"
                    ))


def run_consistency_check() -> ConsistencyReport:
    return ConsistencyChecker.check_all()


def print_consistency_report():
    report = run_consistency_check()
    print(report.get_detailed_report())
    return report


if __name__ == "__main__":
    print_consistency_report()
