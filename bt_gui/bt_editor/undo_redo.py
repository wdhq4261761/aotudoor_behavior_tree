from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass
class Command:
    description: str = ""
    
    def execute(self) -> bool:
        return True
    
    def undo(self) -> bool:
        return True
    
    def redo(self) -> bool:
        return self.execute()


@dataclass
class AddNodeCommand(Command):
    canvas: Any = None
    node_id: str = ""
    node_type: str = ""
    x: float = 0
    y: float = 0
    node_data: Dict[str, Any] = field(default_factory=dict)
    
    description: str = "添加节点"
    
    def execute(self) -> bool:
        if self.canvas and hasattr(self.canvas, 'add_node'):
            name = self.node_data.get('name', '')
            config = self.node_data.get('config', {})
            enabled = self.node_data.get('enabled', True)
            self.canvas.add_node(self.node_id, self.node_type, self.x, self.y, name, config, enabled)
            return True
        return False
    
    def undo(self) -> bool:
        if self.canvas and hasattr(self.canvas, 'remove_node'):
            self.canvas.remove_node(self.node_id)
            return True
        return False


@dataclass
class AddNodesCommand(Command):
    canvas: Any = None
    nodes_data: List[Dict[str, Any]] = field(default_factory=list)
    connections: List[tuple] = field(default_factory=list)
    new_node_ids: List[str] = field(default_factory=list)
    
    description: str = "批量添加节点"
    
    def execute(self) -> bool:
        if not self.canvas or not hasattr(self.canvas, 'add_node'):
            return False
        
        self.new_node_ids = []
        
        for node_data in self.nodes_data:
            node_id = node_data['id']
            self.canvas.add_node(
                node_id,
                node_data['type'],
                node_data['x'],
                node_data['y'],
                node_data.get('name', ''),
                node_data.get('config', {}),
                node_data.get('enabled', True)
            )
            self.new_node_ids.append(node_id)
        
        for parent_id, child_id in self.connections:
            if hasattr(self.canvas, 'add_connection'):
                self.canvas.add_connection(parent_id, child_id)
        
        return True
    
    def undo(self) -> bool:
        if not self.canvas or not hasattr(self.canvas, 'remove_node'):
            return False
        
        for node_id in self.new_node_ids:
            self.canvas.remove_node(node_id)
        
        return True


@dataclass
class RemoveNodeCommand(Command):
    canvas: Any = None
    node_id: str = ""
    node_data: Dict[str, Any] = field(default_factory=dict)
    connections: List[tuple] = field(default_factory=list)
    
    description: str = "删除节点"
    
    def execute(self) -> bool:
        if self.canvas and hasattr(self.canvas, 'remove_node'):
            if hasattr(self.canvas, 'nodes') and self.node_id in self.canvas.nodes:
                node = self.canvas.nodes[self.node_id]
                self.node_data = {
                    "id": node.node_id,
                    "type": node.node_type,
                    "x": node.x,
                    "y": node.y,
                    "name": getattr(node, 'name', ''),
                    "config": deepcopy(getattr(node, 'config', {})),
                    "enabled": getattr(node, 'enabled', True)
                }
                self.connections = [
                    c for c in self.canvas.connections 
                    if c[0] == self.node_id or c[1] == self.node_id
                ]
            self.canvas.remove_node(self.node_id)
            return True
        return False
    
    def undo(self) -> bool:
        if self.canvas and hasattr(self.canvas, 'add_node'):
            self.canvas.add_node(
                self.node_data["id"],
                self.node_data["type"],
                self.node_data["x"],
                self.node_data["y"],
                self.node_data.get("name", ""),
                self.node_data.get("config", {}),
                self.node_data.get("enabled", True)
            )
            for parent_id, child_id in self.connections:
                self.canvas.add_connection(parent_id, child_id)
            return True
        return False


@dataclass
class RemoveNodesCommand(Command):
    canvas: Any = None
    node_ids: List[str] = field(default_factory=list)
    nodes_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    connections: List[tuple] = field(default_factory=list)
    
    description: str = "批量删除节点"
    
    def execute(self) -> bool:
        if not self.canvas or not hasattr(self.canvas, 'remove_node'):
            return False
        
        self.nodes_data = {}
        self.connections = []
        
        node_set = set(self.node_ids)
        
        for node_id in self.node_ids:
            if node_id in self.canvas.nodes:
                node = self.canvas.nodes[node_id]
                self.nodes_data[node_id] = {
                    "id": node.node_id,
                    "type": node.node_type,
                    "x": node.x,
                    "y": node.y,
                    "name": getattr(node, 'name', ''),
                    "config": deepcopy(getattr(node, 'config', {})),
                    "enabled": getattr(node, 'enabled', True)
                }
        
        self.connections = [
            c for c in self.canvas.connections 
            if c[0] in node_set or c[1] in node_set
        ]
        
        for node_id in self.node_ids:
            self.canvas.remove_node(node_id)
        
        return True
    
    def undo(self) -> bool:
        if not self.canvas or not hasattr(self.canvas, 'add_node'):
            return False
        
        for node_id, node_data in self.nodes_data.items():
            self.canvas.add_node(
                node_id,
                node_data["type"],
                node_data["x"],
                node_data["y"],
                node_data.get("name", ""),
                node_data.get("config", {}),
                node_data.get("enabled", True)
            )
        
        for parent_id, child_id in self.connections:
            if parent_id in self.canvas.nodes and child_id in self.canvas.nodes:
                self.canvas.add_connection(parent_id, child_id)
        
        return True


@dataclass
class MoveNodeCommand(Command):
    canvas: Any = None
    node_id: str = ""
    old_x: float = 0
    old_y: float = 0
    new_x: float = 0
    new_y: float = 0
    
    description: str = "移动节点"
    
    def execute(self) -> bool:
        if self.canvas and hasattr(self.canvas, 'nodes') and self.node_id in self.canvas.nodes:
            node = self.canvas.nodes[self.node_id]
            node.move_to(self.new_x, self.new_y)
            if hasattr(self.canvas, '_redraw_connections'):
                self.canvas._redraw_connections()
            return True
        return False
    
    def undo(self) -> bool:
        if self.canvas and hasattr(self.canvas, 'nodes') and self.node_id in self.canvas.nodes:
            node = self.canvas.nodes[self.node_id]
            node.move_to(self.old_x, self.old_y)
            if hasattr(self.canvas, '_redraw_connections'):
                self.canvas._redraw_connections()
            return True
        return False


@dataclass
class MoveNodesCommand(Command):
    canvas: Any = None
    node_ids: List[str] = field(default_factory=list)
    old_positions: Dict[str, tuple] = field(default_factory=dict)
    new_positions: Dict[str, tuple] = field(default_factory=dict)
    
    description: str = "批量移动节点"
    
    def execute(self) -> bool:
        if not self.canvas or not hasattr(self.canvas, 'nodes'):
            return False
        
        for node_id, (new_x, new_y) in self.new_positions.items():
            if node_id in self.canvas.nodes:
                self.canvas.nodes[node_id].move_to(new_x, new_y)
        
        if hasattr(self.canvas, '_redraw_connections'):
            self.canvas._redraw_connections()
        
        return True
    
    def undo(self) -> bool:
        if not self.canvas or not hasattr(self.canvas, 'nodes'):
            return False
        
        for node_id, (old_x, old_y) in self.old_positions.items():
            if node_id in self.canvas.nodes:
                self.canvas.nodes[node_id].move_to(old_x, old_y)
        
        if hasattr(self.canvas, '_redraw_connections'):
            self.canvas._redraw_connections()
        
        return True


@dataclass
class AddConnectionCommand(Command):
    canvas: Any = None
    parent_id: str = ""
    child_id: str = ""
    
    description: str = "添加连线"
    
    def execute(self) -> bool:
        if self.canvas and hasattr(self.canvas, 'add_connection'):
            self.canvas.add_connection(self.parent_id, self.child_id)
            return True
        return False
    
    def undo(self) -> bool:
        if self.canvas and hasattr(self.canvas, 'connections'):
            self.canvas.connections = [
                c for c in self.canvas.connections 
                if not (c[0] == self.parent_id and c[1] == self.child_id)
            ]
            if hasattr(self.canvas, '_redraw_connections'):
                self.canvas._redraw_connections()
            return True
        return False


@dataclass
class RemoveConnectionCommand(Command):
    canvas: Any = None
    parent_id: str = ""
    child_id: str = ""
    
    description: str = "删除连线"
    
    def execute(self) -> bool:
        if self.canvas and hasattr(self.canvas, 'connections'):
            self.canvas.connections = [
                c for c in self.canvas.connections 
                if not (c[0] == self.parent_id and c[1] == self.child_id)
            ]
            if hasattr(self.canvas, '_redraw_connections'):
                self.canvas._redraw_connections()
            return True
        return False
    
    def undo(self) -> bool:
        if self.canvas and hasattr(self.canvas, 'add_connection'):
            self.canvas.add_connection(self.parent_id, self.child_id)
            return True
        return False


@dataclass
class SetPropertyCommand(Command):
    property_panel: Any = None
    node_id: str = ""
    property_key: str = ""
    old_value: Any = None
    new_value: Any = None
    
    description: str = "设置属性"
    
    def execute(self) -> bool:
        return True
    
    def undo(self) -> bool:
        if self.property_panel and hasattr(self.property_panel, 'on_change'):
            self.property_panel.on_change(self.node_id, self.property_key, self.old_value)
            return True
        return False


@dataclass
class ClearCanvasCommand(Command):
    canvas: Any = None
    nodes_backup: Dict[str, Any] = field(default_factory=dict)
    connections_backup: List[tuple] = field(default_factory=list)
    
    description: str = "清空画布"
    
    def execute(self) -> bool:
        if self.canvas:
            self.nodes_backup = {}
            self.connections_backup = []
            
            if hasattr(self.canvas, 'nodes'):
                for node_id, node in self.canvas.nodes.items():
                    self.nodes_backup[node_id] = {
                        "id": node.node_id,
                        "type": node.node_type,
                        "x": node.x,
                        "y": node.y,
                    }
            
            if hasattr(self.canvas, 'connections'):
                self.connections_backup = list(self.canvas.connections)
            
            if hasattr(self.canvas, 'clear_canvas'):
                self.canvas.clear_canvas()
            return True
        return False
    
    def undo(self) -> bool:
        if self.canvas and hasattr(self.canvas, 'add_node'):
            for node_id, node_data in self.nodes_backup.items():
                self.canvas.add_node(
                    node_data["id"],
                    node_data["type"],
                    node_data["x"],
                    node_data["y"]
                )
            for parent_id, child_id in self.connections_backup:
                self.canvas.add_connection(parent_id, child_id)
            return True
        return False


class CommandManager:
    def __init__(self, max_history: int = 100):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_history = max_history
        self._is_executing = False
    
    def execute(self, command: Command) -> bool:
        if self._is_executing:
            return False
        
        self._is_executing = True
        try:
            if command.execute():
                self.undo_stack.append(command)
                self.redo_stack.clear()
                
                if len(self.undo_stack) > self.max_history:
                    self.undo_stack.pop(0)
                
                return True
            return False
        finally:
            self._is_executing = False
    
    def undo(self) -> bool:
        if not self.can_undo():
            return False
        
        self._is_executing = True
        try:
            command = self.undo_stack.pop()
            if command.undo():
                self.redo_stack.append(command)
                return True
            self.undo_stack.append(command)
            return False
        finally:
            self._is_executing = False
    
    def redo(self) -> bool:
        if not self.can_redo():
            return False
        
        self._is_executing = True
        try:
            command = self.redo_stack.pop()
            if command.redo():
                self.undo_stack.append(command)
                return True
            self.redo_stack.append(command)
            return False
        finally:
            self._is_executing = False
    
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0
    
    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
    
    def get_undo_description(self) -> Optional[str]:
        if self.undo_stack:
            return self.undo_stack[-1].description
        return None
    
    def get_redo_description(self) -> Optional[str]:
        if self.redo_stack:
            return self.redo_stack[-1].description
        return None
