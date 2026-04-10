import tkinter as tk
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Callable
import math

from ..theme import Theme
from .constants import NODE_CATEGORY_MAP, NODE_DISPLAY_NAMES
from .node_item import NodeItem, NodeExecutionStatus


class BehaviorTreeCanvas(ctk.CTkFrame):
    def __init__(self, master, app, on_node_select: Optional[Callable] = None,
                 on_node_move: Optional[Callable] = None,
                 on_nodes_move: Optional[Callable] = None,
                 on_connection_add: Optional[Callable] = None,
                 on_node_deselect: Optional[Callable] = None,
                 property_panel: Optional[Any] = None,
                 **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.property_panel = property_panel
        
        self._node_counter = 0
        
        self.nodes: Dict[str, NodeItem] = {}
        self.connections: List[tuple] = []
        self.connection_items: Dict[tuple, int] = {}
        self.selected_node: Optional[str] = None
        self.selected_nodes: List[str] = []
        self.selected_connection: Optional[tuple] = None
        self.on_node_select = on_node_select
        self.on_node_move = on_node_move
        self.on_nodes_move = on_nodes_move
        self.on_connection_add = on_connection_add
        self.on_node_deselect = on_node_deselect
        
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        self.grid_enabled = True
        self.grid_size = 20
        
        self._dragging = False
        self._drag_node: Optional[str] = None
        self._drag_start = (0, 0)
        self._drag_start_pos = (0, 0)
        self._drag_start_positions: Dict[str, tuple] = {}
        
        self._panning = False
        self._pan_start = (0, 0)
        self._pan_start_offset = (0, 0)
        
        self._right_panning = False
        self._right_pan_start = (0, 0)
        self._right_pan_start_offset = (0, 0)
        self._right_pan_moved = False
        self._right_pan_threshold = 5
        
        self._selecting = False
        self._selection_start = (0, 0)
        self._selection_box = None
        self._selection_append = False
        
        self._connecting = False
        self._connect_start_node: Optional[str] = None
        self._temp_line = None
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(fg_color=self._dark_colors['canvas_bg'], corner_radius=0)
        
        self._create_canvas()
        self._bind_events()
    
    def _create_canvas(self):
        self.canvas = tk.Canvas(
            self,
            bg=self._dark_colors['canvas_bg'],
            highlightthickness=0,
            cursor="arrow"
        )
        self.canvas.pack(fill="both", expand=True)
        
        self._draw_grid()
    
    def _draw_grid(self):
        if not self.grid_enabled:
            self.canvas.delete("grid")
            return

        grid_color = self._dark_colors['canvas_grid']

        self.canvas.delete("grid")

        width = self.canvas.winfo_width() or 800
        height = self.canvas.winfo_height() or 600

        offset_x = int(self.pan_x) % self.grid_size
        offset_y = int(self.pan_y) % self.grid_size

        for x in range(-self.grid_size + offset_x, width + self.grid_size, self.grid_size):
            self.canvas.create_line(
                x, 0, x, height,
                fill=grid_color,
                tags="grid"
            )

        for y in range(-self.grid_size + offset_y, height + self.grid_size, self.grid_size):
            self.canvas.create_line(
                0, y, width, y,
                fill=grid_color,
                tags="grid"
            )

        self.canvas.tag_lower("grid")

    def set_grid_enabled(self, enabled: bool) -> None:
        self.grid_enabled = enabled
        self._draw_grid()

    def set_grid_size(self, size: int) -> None:
        self.grid_size = max(10, min(100, size))
        self._draw_grid()

    def get_grid_config(self) -> dict:
        return {
            "enabled": self.grid_enabled,
            "size": self.grid_size
        }
    
    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_scroll)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<B3-Motion>", self._on_right_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_right_release)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Control-Button-1>", self._on_ctrl_click)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Motion>", self._on_motion)
    
    def _on_resize(self, event):
        self._draw_grid()
    
    def _on_motion(self, event):
        x = (self.canvas.canvasx(event.x) - self.pan_x) / self.zoom
        y = (self.canvas.canvasy(event.y) - self.pan_y) / self.zoom
        
        for node_id, node in self.nodes.items():
            if node.is_on_output_port(x, y) or node.is_on_input_port(x, y):
                self.canvas.config(cursor="hand2")
                return
        
        self.canvas.config(cursor="arrow")
    
    def _on_click(self, event):
        if self.property_panel:
            self.property_panel.force_save_current_field()
        
        x = (self.canvas.canvasx(event.x) - self.pan_x) / self.zoom
        y = (self.canvas.canvasy(event.y) - self.pan_y) / self.zoom
        
        for node_id, node in self.nodes.items():
            if node.is_on_output_port(x, y):
                self._start_connecting(node_id, x, y)
                return
            
            if node.is_on_input_port(x, y):
                return
            
            if node.contains_point(x, y):
                if node_id in self.selected_nodes:
                    self._dragging = True
                    self._drag_node = node_id
                    self._drag_start = (x - node.x, y - node.y)
                    self._drag_start_pos = (node.x, node.y)
                    self._drag_start_positions = {}
                    for nid in self.selected_nodes:
                        if nid in self.nodes:
                            n = self.nodes[nid]
                            self._drag_start_positions[nid] = (n.x, n.y)
                else:
                    self._select_node(node_id)
                    self._dragging = True
                    self._drag_node = node_id
                    self._drag_start = (x - node.x, y - node.y)
                    self._drag_start_pos = (node.x, node.y)
                    self._drag_start_positions = {node_id: (node.x, node.y)}
                return
        
        clicked_connection = self._find_connection_at(x, y)
        if clicked_connection:
            self._select_connection(clicked_connection)
            return
        
        self._deselect_all()
        self._selecting = True
        self._selection_start = (x, y)
        self._selection_append = False
    
    def _on_ctrl_click(self, event):
        x = (self.canvas.canvasx(event.x) - self.pan_x) / self.zoom
        y = (self.canvas.canvasy(event.y) - self.pan_y) / self.zoom
        
        for node_id, node in self.nodes.items():
            if node.contains_point(x, y):
                if node_id in self.selected_nodes:
                    self.selected_nodes.remove(node_id)
                    node.set_selected(False)
                else:
                    self.selected_nodes.append(node_id)
                    node.set_selected(True)
                return
    
    def _start_connecting(self, node_id: str, x: float, y: float):
        self._connecting = True
        self._connect_start_node = node_id
        
        node = self.nodes[node_id]
        start_x, start_y = node.get_output_port_pos()
        
        self._temp_line = self.canvas.create_line(
            start_x * self.zoom + self.pan_x, start_y * self.zoom + self.pan_y,
            x * self.zoom + self.pan_x, y * self.zoom + self.pan_y,
            fill=self._dark_colors.get('connection_line', '#666666'),
            width=2,
            dash=(5, 3),
            arrow=tk.LAST,
            tags="temp_connection"
        )
        
        node.highlight_port("output", True)
        self.canvas.config(cursor="crosshair")
    
    def _update_connecting_line(self, x: float, y: float):
        if self._connecting and self._temp_line and self._connect_start_node:
            node = self.nodes[self._connect_start_node]
            start_x, start_y = node.get_output_port_pos()
            
            self.canvas.coords(self._temp_line, 
                start_x * self.zoom + self.pan_x, start_y * self.zoom + self.pan_y,
                x * self.zoom + self.pan_x, y * self.zoom + self.pan_y)
    
    def _finish_connecting(self, target_node_id: str):
        if self._connect_start_node and self._connect_start_node != target_node_id:
            self.add_connection(self._connect_start_node, target_node_id)
            if self.on_connection_add:
                self.on_connection_add(self._connect_start_node, target_node_id)
        
        self._cancel_connecting()
    
    def _cancel_connecting(self):
        if self._temp_line:
            self.canvas.delete(self._temp_line)
            self._temp_line = None
        
        if self._connect_start_node and self._connect_start_node in self.nodes:
            node = self.nodes[self._connect_start_node]
            node.highlight_port("output", False)
        
        self._connecting = False
        self._connect_start_node = None
        self.canvas.config(cursor="arrow")
    
    def _on_drag(self, event):
        x = (self.canvas.canvasx(event.x) - self.pan_x) / self.zoom
        y = (self.canvas.canvasy(event.y) - self.pan_y) / self.zoom
        
        if self._connecting:
            self._update_connecting_line(x, y)
            
            for node_id, node in self.nodes.items():
                if node_id != self._connect_start_node:
                    if node.is_on_input_port(x, y):
                        node.highlight_port("input", True)
                    else:
                        node.highlight_port("input", False)
            return
        
        if self._selecting:
            self._update_selection_box(x, y)
            return
        
        if self._dragging and self._drag_node:
            if self.property_panel and self.property_panel.is_loading():
                return
            
            dx = x - self._drag_start[0] - self._drag_start_pos[0]
            dy = y - self._drag_start[1] - self._drag_start_pos[1]
            
            if len(self.selected_nodes) > 1 and self._drag_start_positions:
                for node_id in self.selected_nodes:
                    if node_id in self.nodes and node_id in self._drag_start_positions:
                        start_x, start_y = self._drag_start_positions[node_id]
                        self.nodes[node_id].move_to(start_x + dx, start_y + dy)
            else:
                node = self.nodes[self._drag_node]
                node.move_to(x - self._drag_start[0], y - self._drag_start[1])
            
            self._redraw_connections()
            return
        
        if self._panning:
            dx = event.x - self._pan_start[0]
            dy = event.y - self._pan_start[1]
            self.pan_x = self._pan_start_offset[0] + dx
            self.pan_y = self._pan_start_offset[1] + dy
            self._redraw_all()
            self._draw_grid()
    
    def _on_release(self, event):
        x = (self.canvas.canvasx(event.x) - self.pan_x) / self.zoom
        y = (self.canvas.canvasy(event.y) - self.pan_y) / self.zoom
        
        if self._connecting:
            for node_id, node in self.nodes.items():
                if node_id != self._connect_start_node and node.is_on_input_port(x, y):
                    self._finish_connecting(node_id)
                    return
            
            self._cancel_connecting()
            return
        
        if self._selecting:
            self._finish_selection(x, y)
            return
        
        if self._dragging and self._drag_node:
            if len(self.selected_nodes) > 1 and self._drag_start_positions and self.on_nodes_move:
                old_positions = {}
                new_positions = {}
                for node_id in self.selected_nodes:
                    if node_id in self.nodes and node_id in self._drag_start_positions:
                        node = self.nodes[node_id]
                        old_positions[node_id] = self._drag_start_positions[node_id]
                        new_positions[node_id] = (node.x, node.y)
                
                self.on_nodes_move(old_positions, new_positions)
            elif self.on_node_move:
                node = self.nodes[self._drag_node]
                self.on_node_move(
                    self._drag_node,
                    self._drag_start_pos[0], self._drag_start_pos[1],
                    node.x, node.y
                )
        
        self._dragging = False
        self._drag_node = None
        self._panning = False
    
    def _on_scroll(self, event):
        mouse_x = event.x
        mouse_y = event.y
        
        canvas_x_before = (mouse_x - self.pan_x) / self.zoom
        canvas_y_before = (mouse_y - self.pan_y) / self.zoom
        
        if event.delta > 0:
            new_zoom = self.zoom * 1.1
        else:
            new_zoom = self.zoom / 1.1
        
        new_zoom = max(0.25, min(4.0, new_zoom))
        
        self.pan_x = mouse_x - canvas_x_before * new_zoom
        self.pan_y = mouse_y - canvas_y_before * new_zoom
        self.zoom = new_zoom
        
        self._redraw_all()
        self._draw_grid()
    
    def _on_right_click(self, event):
        self._right_panning = True
        self._right_pan_start = (event.x, event.y)
        self._right_pan_start_offset = (self.pan_x, self.pan_y)
        self._right_pan_moved = False
    
    def _on_right_drag(self, event):
        if not self._right_panning:
            return
        
        dx = event.x - self._right_pan_start[0]
        dy = event.y - self._right_pan_start[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        if not self._right_pan_moved and distance >= self._right_pan_threshold:
            self._right_pan_moved = True
        
        if self._right_pan_moved:
            self.pan_x = self._right_pan_start_offset[0] + dx
            self.pan_y = self._right_pan_start_offset[1] + dy
            self._redraw_all()
            self._draw_grid()
    
    def _on_right_release(self, event):
        if not self._right_panning:
            return
        
        self._right_panning = False
        
        if not self._right_pan_moved:
            self._show_context_menu(event)
    
    def _show_context_menu(self, event):
        x = (self.canvas.canvasx(event.x) - self.pan_x) / self.zoom
        y = (self.canvas.canvasy(event.y) - self.pan_y) / self.zoom
        
        menu = tk.Menu(self, tearoff=0, bg=self._dark_colors['bg_secondary'], 
                       fg=self._dark_colors['text_primary'],
                       activebackground=self._dark_colors['bg_tertiary'])
        
        if self.selected_nodes:
            menu.add_command(label=f"删除 {len(self.selected_nodes)} 个节点", 
                           command=lambda: self._delete_selected_nodes())
            menu.add_command(label=f"复制 {len(self.selected_nodes)} 个节点", 
                           command=self._copy_selected_nodes_to_clipboard)
        elif self.selected_node:
            menu.add_command(label="删除节点", command=lambda: self.remove_node(self.selected_node))
            menu.add_command(label="复制节点", command=lambda: self._copy_node(self.selected_node))
        elif self.selected_connection:
            menu.add_command(label="删除连线", command=self.remove_selected_connection)
        
        if menu.index("end") is not None:
            menu.post(event.x_root, event.y_root)
    
    def _on_double_click(self, event):
        x = (self.canvas.canvasx(event.x) - self.pan_x) / self.zoom
        y = (self.canvas.canvasy(event.y) - self.pan_y) / self.zoom
        
        for node_id, node in self.nodes.items():
            if node.contains_point(x, y):
                self._edit_node_properties(node_id)
                return
    
    def _select_node(self, node_id: str):
        self._deselect_all()
        self.selected_node = node_id
        self.selected_nodes = [node_id]
        node = self.nodes[node_id]
        node.set_selected(True)
        
        if self.on_node_select:
            self.on_node_select(node_id, node.node_type)
    
    def _select_node_add(self, node_id: str):
        if node_id not in self.nodes:
            return
        
        if node_id not in self.selected_nodes:
            self.selected_nodes.append(node_id)
            self.nodes[node_id].set_selected(True)
        
        if self.selected_nodes:
            self.selected_node = self.selected_nodes[0]
    
    def _deselect_all(self):
        if self.on_node_deselect and self.selected_node:
            self.on_node_deselect()
        self.selected_node = None
        self.selected_nodes = []
        for node in self.nodes.values():
            node.set_selected(False)
        self._deselect_connection()
    
    def _find_connection_at(self, x: float, y: float) -> Optional[tuple]:
        for conn_key, line_id in self.connection_items.items():
            coords = self.canvas.coords(line_id)
            if len(coords) >= 4:
                for i in range(0, len(coords) - 2, 2):
                    x1, y1 = (coords[i] - self.pan_x) / self.zoom, (coords[i + 1] - self.pan_y) / self.zoom
                    x2, y2 = (coords[i + 2] - self.pan_x) / self.zoom, (coords[i + 3] - self.pan_y) / self.zoom
                    
                    dist = self._point_to_line_distance(x, y, x1, y1, x2, y2)
                    if dist < 10:
                        return conn_key
        return None
    
    def _point_to_line_distance(self, px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
        line_len_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if line_len_sq == 0:
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
        
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_len_sq))
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)
    
    def _select_connection(self, conn_key: tuple):
        self._deselect_all()
        self.selected_connection = conn_key
        
        if conn_key in self.connection_items:
            line_id = self.connection_items[conn_key]
            self.canvas.itemconfig(line_id, fill=self._dark_colors.get('node_selected', '#FFD700'), width=3)
    
    def _deselect_connection(self):
        if self.selected_connection and self.selected_connection in self.connection_items:
            line_id = self.connection_items[self.selected_connection]
            self.canvas.itemconfig(line_id, fill=self._dark_colors['connection_line'], width=2)
        self.selected_connection = None
    
    def remove_selected_connection(self):
        if self.selected_connection:
            conn_key = self.selected_connection
            if conn_key in self.connections:
                self.connections.remove(conn_key)
            if conn_key in self.connection_items:
                self.canvas.delete(self.connection_items[conn_key])
                del self.connection_items[conn_key]
            self.selected_connection = None
            self._redraw_connections()
    
    def _show_add_dialog(self, x: float, y: float):
        pass
    
    def _edit_node_properties(self, node_id: str):
        pass
    
    def _copy_node(self, node_id: str):
        pass
    
    def add_node(self, node_id: str, node_type: str, x: float, y: float, name: str = "", config: dict = None, enabled: bool = True) -> NodeItem:
        if not name:
            name = NODE_DISPLAY_NAMES.get(node_type, node_type)
        
        node = NodeItem(self.canvas, node_id, node_type, x, y, name, config, enabled, self.zoom, self.pan_x, self.pan_y)
        self.nodes[node_id] = node
        return node
    
    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.reset_status()
            self.canvas.delete(node.node_id)
            del self.nodes[node_id]
            
            if node_id == self.selected_node:
                self.selected_node = None
            
            if node_id in self.selected_nodes:
                self.selected_nodes.remove(node_id)
            
            self.connections = [
                c for c in self.connections 
                if c[0] != node_id and c[1] != node_id
            ]
            self._redraw_connections()
    
    def redraw_node(self, node_id: str):
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.redraw()
    
    def add_connection(self, parent_id: str, child_id: str):
        if parent_id in self.nodes and child_id in self.nodes:
            if not any(c[0] == parent_id and c[1] == child_id for c in self.connections):
                self.connections.append((parent_id, child_id))
                self._redraw_connections()
    
    def _redraw_connections(self):
        self.canvas.delete("connection")
        self.canvas.delete("connection_order")
        self.connection_items.clear()
        
        parent_child_order: Dict[str, int] = {}
        
        for parent_id, child_id in self.connections:
            if parent_id not in parent_child_order:
                parent_child_order[parent_id] = 0
            else:
                parent_child_order[parent_id] += 1
            
            order_num = parent_child_order[parent_id] + 1
            
            if parent_id in self.nodes and child_id in self.nodes:
                parent = self.nodes[parent_id]
                child = self.nodes[child_id]
                
                start_x, start_y = parent.get_output_port_pos()
                end_x, end_y = child.get_input_port_pos()
                
                start_x = start_x * self.zoom + self.pan_x
                start_y = start_y * self.zoom + self.pan_y
                end_x = end_x * self.zoom + self.pan_x
                end_y = end_y * self.zoom + self.pan_y
                
                mid_y = (start_y + end_y) / 2
                
                is_selected = self.selected_connection == (parent_id, child_id)
                line_color = self._dark_colors.get('node_selected', '#FFD700') if is_selected else self._dark_colors['connection_line']
                line_width = 3 if is_selected else 2
                
                line_id = self.canvas.create_line(
                    start_x, start_y,
                    start_x, mid_y,
                    end_x, mid_y,
                    end_x, end_y,
                    fill=line_color,
                    width=line_width,
                    smooth=True,
                    arrow=tk.LAST,
                    arrowshape=(10, 12, 5),
                    tags="connection"
                )
                
                self.connection_items[(parent_id, child_id)] = line_id
                
                if order_num > 1 or len([c for c in self.connections if c[0] == parent_id]) > 1:
                    order_text = self.canvas.create_text(
                        end_x + 15,
                        end_y - 15,
                        text=str(order_num),
                        fill=self._dark_colors['text_secondary'],
                        font=("Arial", max(8, int(10 * self.zoom)), "bold"),
                        tags="connection_order"
                    )
        
        self.canvas.tag_lower("connection_order")
        self.canvas.tag_lower("connection")
        self.canvas.tag_lower("grid")
    
    def _scale(self, value: float) -> float:
        return value * self.zoom
    
    def _redraw_all(self):
        for node in self.nodes.values():
            node.set_zoom(self.zoom)
            node.set_pan(self.pan_x, self.pan_y)
            node.redraw()
        self._redraw_connections()
    
    def clear_canvas(self):
        self.canvas.delete("all")
        self.nodes.clear()
        self.connections.clear()
        self.connection_items.clear()
        self.selected_node = None
        self.selected_nodes = []
        self.selected_connection = None
        self._dragging = False
        self._drag_node = None
        self._drag_start = (0, 0)
        self._drag_start_pos = (0, 0)
        self._panning = False
        self._pan_start = (0, 0)
        self._pan_start_offset = (0, 0)
        self._right_panning = False
        self._right_pan_start = (0, 0)
        self._right_pan_start_offset = (0, 0)
        self._right_pan_moved = False
        self._selecting = False
        self._selection_start = (0, 0)
        self._selection_box = None
        self._selection_append = False
        self._connecting = False
        self._connect_start_node = None
        self._connect_start_pos = None
        self._connect_line = None
        self._draw_grid()
    
    def reset_view(self):
        if not self.nodes:
            self.zoom = 1.0
            self.pan_x = 0
            self.pan_y = 0
            self._redraw_all()
            self._draw_grid()
            return
        
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        for node in self.nodes.values():
            x = node.x
            y = node.y
            w = node.width
            h = node.height
            
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x + w)
            max_y = max(max_y, y + h)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 800
            canvas_height = 600
        
        nodes_width = max_x - min_x
        nodes_height = max_y - min_y
        
        padding = 100
        zoom_x = (canvas_width - 2 * padding) / nodes_width if nodes_width > 0 else 1.0
        zoom_y = (canvas_height - 2 * padding) / nodes_height if nodes_height > 0 else 1.0
        
        self.zoom = min(zoom_x, zoom_y, 1.0)
        self.zoom = max(0.25, min(4.0, self.zoom))
        
        self.pan_x = canvas_width / 2 - center_x * self.zoom
        self.pan_y = canvas_height / 2 - center_y * self.zoom
        
        self._redraw_all()
        self._draw_grid()
    
    def set_node_status(self, node_id: str, status: NodeExecutionStatus):
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.show_status_indicator()
            node.set_status(status)
    
    def show_all_status_indicators(self):
        for node in self.nodes.values():
            node.show_status_indicator()
    
    def hide_all_status_indicators(self):
        for node in self.nodes.values():
            node.hide_status_indicator()
    
    def reset_all_status(self):
        for node in self.nodes.values():
            node.reset_status()
    
    def clear_all_node_status(self):
        for node in self.nodes.values():
            node.hide_status_indicator()
            node.reset_status()
    
    def _is_node_visible(self, node: NodeItem) -> bool:
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600

        node_left = node.x * self.zoom + self.pan_x
        node_top = node.y * self.zoom + self.pan_y
        node_right = (node.x + node.width) * self.zoom + self.pan_x
        node_bottom = (node.y + node.height) * self.zoom + self.pan_y

        margin = 50

        return not (
            node_right < -margin or
            node_left > canvas_width + margin or
            node_bottom < -margin or
            node_top > canvas_height + margin
        )

    def get_visible_nodes(self) -> List[str]:
        visible = []
        for node_id, node in self.nodes.items():
            if self._is_node_visible(node):
                visible.append(node_id)
        return visible

    def load_tree(self, tree_data: Dict[str, Any]):
        self.clear_canvas()
        
        nodes_data = tree_data.get("nodes", {})
        root_id = tree_data.get("root_node")
        
        if not nodes_data:
            return
        
        canvas_state = tree_data.get("canvas", {})
        if canvas_state:
            viewport = canvas_state.get("viewport", {})
            if viewport:
                self.zoom = viewport.get("zoom", 1.0)
                self.pan_x = viewport.get("offset_x", 0)
                self.pan_y = viewport.get("offset_y", 0)
        
        has_positions = any("position" in node_data for node_data in nodes_data.values())
        
        if not has_positions:
            positions = self._auto_layout(nodes_data, root_id)
        else:
            positions = {}
        
        for node_id, node_data in nodes_data.items():
            node_type = node_data.get("type", "Node")
            config = node_data.get("config", {})
            
            name = node_data.get("name", "")
            if not name:
                name = config.get("name", "")
            
            enabled = node_data.get("enabled", None)
            if enabled is None:
                enabled = config.get("enabled", True)
            
            if "position" in node_data:
                x = node_data["position"].get("x", 200)
                y = node_data["position"].get("y", 100)
            elif node_id in positions:
                x, y = positions[node_id]
            else:
                x, y = 200, 100
            
            self.add_node(node_id, node_type, x, y, name, config, enabled)
        
        for node_id, node_data in nodes_data.items():
            children = node_data.get("children", [])
            for child_info in children:
                if isinstance(child_info, dict):
                    child_id = child_info.get("id", "")
                else:
                    child_id = child_info
                if child_id:
                    self.add_connection(node_id, child_id)
        
            if "child" in node_data:
                self.add_connection(node_id, node_data["child"])
        
        if root_id and root_id in self.nodes:
            self.root_node = root_id
        
        self._redraw_all()
        
        editor_state = tree_data.get("editor_state", {})
        if editor_state:
            selected_node = editor_state.get("selected_node")
            if selected_node and selected_node in self.nodes:
                self._select_node(selected_node)
    
    def _auto_layout(self, nodes_data: Dict, root_id: str) -> Dict[str, tuple]:
        positions = {}
        node_width = 180
        node_height = 80
        h_gap = 50
        v_gap = 100
        
        def get_children(node_id):
            node_data = nodes_data.get(node_id, {})
            children = node_data.get("children", [])
            result = []
            for child in children:
                if isinstance(child, dict):
                    result.append(child.get("id", ""))
                else:
                    result.append(child)
            return [c for c in result if c]
        
        def calc_subtree_width(node_id):
            children = get_children(node_id)
            if not children:
                return node_width
            total = 0
            for child in children:
                total += calc_subtree_width(child)
            return max(total, node_width)
        
        def layout_node(node_id, x, y):
            positions[node_id] = (x, y)
            children = get_children(node_id)
            if children:
                total_width = sum(calc_subtree_width(c) for c in children)
                current_x = x - total_width / 2
                for child in children:
                    child_width = calc_subtree_width(child)
                    layout_node(child, current_x + child_width / 2, y + node_height + v_gap)
                    current_x += child_width
        
        if root_id:
            layout_node(root_id, 400, 100)
        
        return positions
    
    def get_tree_data(self) -> Dict[str, Any]:
        nodes_data = {}
        
        for node_id, node in self.nodes.items():
            nodes_data[node_id] = {
                "id": node_id,
                "type": node.node_type,
                "name": getattr(node, 'name', ''),
                "enabled": getattr(node, 'enabled', True),
                "config": getattr(node, 'config', {}),
                "position": {
                    "x": node.x,
                    "y": node.y
                }
            }
        
        for parent_id, child_id in self.connections:
            if parent_id in nodes_data:
                if "children" not in nodes_data[parent_id]:
                    nodes_data[parent_id]["children"] = []
                nodes_data[parent_id]["children"].append(child_id)
        
        root_id = None
        all_children = {c for _, c in self.connections}
        for node_id in self.nodes:
            if node_id not in all_children:
                root_id = node_id
                break
        
        return {
            "version": "2.0",
            "format_type": "behavior_tree_editor",
            "canvas": {
                "name": "未命名",
                "description": "",
                "viewport": {
                    "zoom": self.zoom,
                    "offset_x": self.pan_x,
                    "offset_y": self.pan_y
                }
            },
            "root_node": root_id,
            "nodes": nodes_data,
            "connections": [{"parent_id": p, "child_id": c} for p, c in self.connections]
        }
    
    def _delete_selected_nodes(self):
        if not self.selected_nodes:
            return
        
        for node_id in list(self.selected_nodes):
            if node_id in self.nodes:
                self.remove_node(node_id)
    
    def _copy_selected_nodes_to_clipboard(self):
        if not self.selected_nodes:
            return None
        
        import copy
        
        min_x = min(self.nodes[nid].x for nid in self.selected_nodes if nid in self.nodes)
        min_y = min(self.nodes[nid].y for nid in self.selected_nodes if nid in self.nodes)
        
        nodes_data = []
        relative_positions = {}
        
        for node_id in self.selected_nodes:
            if node_id not in self.nodes:
                continue
            node = self.nodes[node_id]
            nodes_data.append({
                'id': node_id,
                'type': node.node_type,
                'name': node.name,
                'config': copy.deepcopy(node.config) if node.config else {},
                'enabled': node.enabled
            })
            relative_positions[node_id] = (node.x - min_x, node.y - min_y)
        
        connections = [
            (parent_id, child_id)
            for parent_id, child_id in self.connections
            if parent_id in self.selected_nodes and child_id in self.selected_nodes
        ]
        
        return {
            'nodes': nodes_data,
            'connections': connections,
            'relative_positions': relative_positions
        }
    
    def paste_nodes(self, clipboard_data: Dict[str, Any], offset_x: float = 50, offset_y: float = 50) -> List[str]:
        if not clipboard_data or not clipboard_data.get('nodes'):
            return []
        
        import copy
        
        nodes_data = clipboard_data['nodes']
        connections = clipboard_data.get('connections', [])
        relative_positions = clipboard_data.get('relative_positions', {})
        
        id_map = {}
        new_node_ids = []
        
        for node_data in nodes_data:
            old_id = node_data['id']
            self._node_counter += 1
            new_id = f"node_{self._node_counter}"
            id_map[old_id] = new_id
            
            rel_x, rel_y = relative_positions.get(old_id, (0, 0))
            new_x = rel_x + offset_x
            new_y = rel_y + offset_y
            
            self.add_node(
                new_id,
                node_data['type'],
                new_x, new_y,
                node_data.get('name', ''),
                node_data.get('config', {}),
                node_data.get('enabled', True)
            )
            new_node_ids.append(new_id)
        
        for old_parent, old_child in connections:
            new_parent = id_map.get(old_parent)
            new_child = id_map.get(old_child)
            if new_parent and new_child:
                self.add_connection(new_parent, new_child)
        
        return new_node_ids
    
    def _update_selection_box(self, x: float, y: float):
        if self._selection_box:
            self.canvas.delete(self._selection_box)
        
        start_x, start_y = self._selection_start
        
        screen_start_x = start_x * self.zoom + self.pan_x
        screen_start_y = start_y * self.zoom + self.pan_y
        screen_end_x = x * self.zoom + self.pan_x
        screen_end_y = y * self.zoom + self.pan_y
        
        self._selection_box = self.canvas.create_rectangle(
            screen_start_x, screen_start_y,
            screen_end_x, screen_end_y,
            outline=self._dark_colors.get('node_selected', '#FFD700'),
            width=2,
            dash=(5, 3),
            tags="selection_box"
        )
    
    def _finish_selection(self, x: float, y: float):
        if self._selection_box:
            self.canvas.delete(self._selection_box)
            self._selection_box = None
        
        selected_ids = self._get_nodes_in_selection_box(
            self._selection_start[0], self._selection_start[1],
            x, y
        )
        
        if not self._selection_append:
            self._deselect_all()
        
        for node_id in selected_ids:
            if node_id not in self.selected_nodes:
                self.selected_nodes.append(node_id)
                self.nodes[node_id].set_selected(True)
        
        if self.selected_nodes:
            self.selected_node = self.selected_nodes[0]
            if self.on_node_select and len(self.selected_nodes) == 1:
                node = self.nodes[self.selected_node]
                self.on_node_select(self.selected_node, node.node_type)
        
        self._selecting = False
    
    def _get_nodes_in_selection_box(self, x1: float, y1: float, 
                                     x2: float, y2: float) -> List[str]:
        selected = []
        
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        
        for node_id, node in self.nodes.items():
            nx1, ny1, nx2, ny2 = node.get_bounds()
            
            if not (nx2 < min_x or nx1 > max_x or 
                    ny2 < min_y or ny1 > max_y):
                selected.append(node_id)
        
        return selected
