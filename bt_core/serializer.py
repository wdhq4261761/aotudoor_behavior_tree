import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from .nodes import Node

CURRENT_VERSION = "2.0"


class Serializer:
    """行为树序列化器

    支持将行为树序列化为JSON/YAML/TEXT格式，
    以及从这些格式反序列化重建行为树。
    支持保存和恢复编辑器状态和画布配置。
    """

    @staticmethod
    def serialize(root_node: Node, metadata: Dict[str, Any] = None,
                  canvas_state: Dict[str, Any] = None,
                  editor_state: Dict[str, Any] = None) -> Dict[str, Any]:
        """序列化行为树为字典

        Args:
            root_node: 根节点
            metadata: 元数据
            canvas_state: 画布状态 (viewport/grid等)
            editor_state: 编辑器状态 (selected_node/clipboard等)

        Returns:
            字典表示
        """
        nodes = {}
        connections = []

        def collect_nodes(node: Node):
            nodes[node.node_id] = node.to_dict()
            for child in node.children:
                connections.append({
                    "parent_id": node.node_id,
                    "child_id": child.node_id
                })
                collect_nodes(child)

        if root_node:
            collect_nodes(root_node)

        result = {
            "version": CURRENT_VERSION,
            "format_type": "behavior_tree_standalone",
            "metadata": metadata or {
                "created_at": datetime.now().isoformat(),
                "modified_at": datetime.now().isoformat(),
                "app_version": "1.0.0",
            },
            "canvas": canvas_state or {},
            "root_node": root_node.node_id if root_node else None,
            "nodes": nodes,
            "connections": connections,
        }

        if editor_state:
            result["editor_state"] = editor_state

        return result

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> tuple:
        """从字典反序列化行为树

        Args:
            data: 字典数据

        Returns:
            (根节点, canvas_state, editor_state) 元组
        """
        from .registry import NodeRegistry

        nodes_data = data.get("nodes", {})
        connections = data.get("connections", [])
        root_id = data.get("root_node")
        canvas_state = data.get("canvas", {})
        editor_state = data.get("editor_state", {})

        if not root_id or not nodes_data:
            return None, canvas_state, editor_state

        nodes = {}
        for node_id, node_data in nodes_data.items():
            node = NodeRegistry.create_node(node_data)
            if node:
                nodes[node_id] = node

        for conn in connections:
            parent_id = conn["parent_id"]
            child_id = conn["child_id"]

            if parent_id in nodes and child_id in nodes:
                nodes[parent_id].add_child(nodes[child_id])

        return nodes.get(root_id), canvas_state, editor_state

    @staticmethod
    def deserialize_node_only(data: Dict[str, Any]) -> Node:
        """仅反序列化节点（兼容旧接口）

        Args:
            data: 字典数据

        Returns:
            根节点
        """
        node, _, _ = Serializer.deserialize(data)
        return node

    @staticmethod
    def save_to_file(root_node: Node, filepath: str, format: str = "json",
                     canvas_state: Dict[str, Any] = None,
                     editor_state: Dict[str, Any] = None) -> None:
        """保存行为树到文件

        Args:
            root_node: 根节点
            filepath: 文件路径
            format: 文件格式 (json/yaml/txt)
            canvas_state: 画布状态
            editor_state: 编辑器状态
        """
        data = Serializer.serialize(root_node, canvas_state=canvas_state, editor_state=editor_state)

        if format == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format in ("yaml", "yml"):
            try:
                import yaml
                with open(filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            except ImportError:
                raise ImportError("PyYAML is required for YAML format")
        elif format in ("txt", "bt"):
            text = Serializer._to_text_format(root_node)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)

    @staticmethod
    def load_from_file(filepath: str) -> tuple:
        """从文件加载行为树

        Args:
            filepath: 文件路径

        Returns:
            (根节点, canvas_state, editor_state) 元组
        """
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".json":
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Serializer.deserialize(data)
        elif ext in (".yaml", ".yml"):
            try:
                import yaml
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                return Serializer.deserialize(data)
            except ImportError:
                raise ImportError("PyYAML is required for YAML format")
        elif ext in (".txt", ".bt"):
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            node = Serializer._from_text_format(text)
            return node, {}, {}

        return None, {}, {}

    @staticmethod
    def load_node_from_file(filepath: str) -> Node:
        """仅加载节点（兼容旧接口）

        Args:
            filepath: 文件路径

        Returns:
            根节点
        """
        node, _, _ = Serializer.load_from_file(filepath)
        return node

    @staticmethod
    def _to_text_format(node: Node, indent: int = 0) -> str:
        """转换为文本格式

        Args:
            node: 节点
            indent: 缩进层级

        Returns:
            文本表示
        """
        lines = []
        prefix = "  " * indent
        lines.append(f"{prefix}{node.NODE_TYPE}: {node.config.name}")

        for child in node.children:
            lines.append(Serializer._to_text_format(child, indent + 1))

        return "\n".join(lines)

    @staticmethod
    def _from_text_format(text: str) -> Node:
        """从文本格式解析

        Args:
            text: 文本内容

        Returns:
            根节点
        """
        import re
        from .registry import NodeRegistry

        lines = text.strip().split('\n')
        if not lines:
            return None

        root = None
        parent_stack = []
        last_indent = -1

        for line in lines:
            if not line.strip() or line.startswith(';'):
                continue

            match = re.match(r'^(\s*)(\w+)', line)
            if not match:
                continue

            indent = len(match.group(1))
            node_type = match.group(2).strip()
            name = match.group(3).strip() if match else ""

            config = {}
            current_line = line.lstrip()

            while current_line and current_line.startswith(';'):
                if ':' in current_line:
                    key_part, value_part = current_line.split(':', 1)
                    key = key_part.strip()
                    value = value_part.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
                        value = int(value)
                    elif value.replace('.', '', 1).isdigit():
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                    config[key] = value

            node_data = {
                "id": f"node_{len(parent_stack)}_{indent}",
                "type": node_type,
                "name": name,
                "config": config
            }

            node = NodeRegistry.create_node(node_data)
            if node is None:
                continue

            while len(parent_stack) > indent + 1:
                parent_stack.pop()

            if parent_stack:
                parent_stack[-1].add_child(node)

            else:
                root = node
                parent_stack.append(node)

            last_indent = indent

        return root
