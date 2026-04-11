import tkinter as tk
import tkinter.font as tkFont
from typing import Dict, Optional
from enum import Enum
import math

from ..theme import Theme
from .constants import NODE_CATEGORY_MAP, NODE_DISPLAY_NAMES


class NodeExecutionStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    ABORTED = "aborted"


STATUS_COLORS = {
    NodeExecutionStatus.IDLE: None,
    NodeExecutionStatus.RUNNING: "#F59E0B",
    NodeExecutionStatus.SUCCESS: "#22C55E",
    NodeExecutionStatus.FAILURE: "#EF4444",
    NodeExecutionStatus.ABORTED: "#6B7280",
}

STATUS_ICONS = {
    NodeExecutionStatus.SUCCESS: "✓",
    NodeExecutionStatus.FAILURE: "✗",
    NodeExecutionStatus.RUNNING: "⋯",
    NodeExecutionStatus.ABORTED: "⊘",
}

PORT_RADIUS = 8


class NodeItem:
    def __init__(self, canvas: tk.Canvas, node_id: str, node_type: str, x: float, y: float, name: str = "", config: dict = None, enabled: bool = True, zoom: float = 1.0, pan_x: float = 0, pan_y: float = 0):
        self.canvas = canvas
        self.node_id = node_id
        self.node_type = node_type
        self.x = x
        self.y = y
        self.width = 140
        self.height = 56
        self.name = name
        self.config = config or {}
        self.enabled = enabled
        self._zoom = zoom
        self._pan_x = pan_x
        self._pan_y = pan_y
        
        self._status = NodeExecutionStatus.IDLE
        self._selected = False
        self._flash_state = False
        self._flash_job = None
        self._status_visible = False
        
        self._dark_colors = Theme.get_dark_colors()
        self._category = NODE_CATEGORY_MAP.get(node_type, "action")
        self._color_config = Theme.get_node_color(self._category)
        
        self._create_visuals()
    
    def set_zoom(self, zoom: float):
        self._zoom = zoom
    
    def set_pan(self, pan_x: float, pan_y: float):
        self._pan_x = pan_x
        self._pan_y = pan_y
    
    def _scale(self, value: float) -> float:
        return value * self._zoom
    
    def _transform_x(self, x: float) -> float:
        return x * self._zoom + self._pan_x
    
    def _transform_y(self, y: float) -> float:
        return y * self._zoom + self._pan_y
    
    def update_config(self, key: str, value) -> None:
        if key in ["name", "description", "enabled"]:
            old_value = getattr(self, key, None)
            setattr(self, key, value)
            
            if key == "name" and old_value != value:
                self.redraw()
        else:
            if self.config is None:
                self.config = {}
            self.config[key] = value
    
    def _create_visuals(self):
        shadow_offset = 3
        w = self._scale(self.width)
        h = self._scale(self.height)
        x = self._transform_x(self.x)
        y = self._transform_y(self.y)
        
        self.shadow = self.canvas.create_rectangle(
            x - w/2 + self._scale(shadow_offset),
            y - h/2 + self._scale(shadow_offset),
            x + w/2 + self._scale(shadow_offset),
            y + h/2 + self._scale(shadow_offset),
            fill="#000000",
            stipple="gray50",
            outline="",
            tags=("node_shadow", self.node_id)
        )
        
        self.rect = self.canvas.create_rectangle(
            x - w/2,
            y - h/2,
            x + w/2,
            y + h/2,
            fill=self._dark_colors['node_bg'],
            outline=self._dark_colors['node_border'],
            width=1,
            tags=("node", self.node_id)
        )
        
        self.color_bar = self.canvas.create_rectangle(
            x - w/2,
            y - h/2,
            x - w/2 + self._scale(4),
            y + h/2,
            fill=self._color_config['bg'],
            outline="",
            tags=("node_color", self.node_id)
        )
        
        display_name = self._get_display_name()
        self.text = self.canvas.create_text(
            x + self._scale(10),
            y,
            text=display_name,
            fill=self._dark_colors['text_primary'],
            font=("Microsoft YaHei", max(8, int(10 * self._zoom)), "bold"),
            anchor="center",
            tags=("node_text", self.node_id)
        )
        
        status_radius = self._scale(10)
        self.status_bg = self.canvas.create_oval(
            x + w/2 - self._scale(24),
            y - status_radius,
            x + w/2 - self._scale(4),
            y + status_radius,
            fill=self._dark_colors['bg_tertiary'],
            outline="",
            tags=("node_status_bg", self.node_id),
            state='hidden'
        )
        
        self.status_icon = self.canvas.create_text(
            x + w/2 - self._scale(14),
            y,
            text="",
            fill=self._dark_colors['text_secondary'],
            font=("Arial", max(8, int(10 * self._zoom)), "bold"),
            tags=("node_icon", self.node_id),
            state='hidden'
        )
        
        port_radius = self._scale(PORT_RADIUS)
        self.input_port = self.canvas.create_oval(
            x - port_radius,
            y - h/2 - port_radius,
            x + port_radius,
            y - h/2 + port_radius,
            fill=self._dark_colors['bg_tertiary'],
            outline=self._dark_colors['border'],
            width=2,
            tags=("node_port_in", self.node_id, "port")
        )
        
        self.output_port = self.canvas.create_oval(
            x - port_radius,
            y + h/2 - port_radius,
            x + port_radius,
            y + h/2 + port_radius,
            fill=self._color_config['bg'],
            outline=self._dark_colors['border'],
            width=2,
            tags=("node_port_out", self.node_id, "port")
        )
        
        self._update_outline()
    
    def _get_display_name(self) -> str:
        if self.name and self.name.strip():
            base_name = self.name.strip()
        else:
            base_name = NODE_DISPLAY_NAMES.get(self.node_type, self.node_type)
        
        # 为StartNode添加特殊图标
        if self.node_type == "StartNode":
            base_name = "▶ " + base_name
        
        available_width = self.width - 48
        scaled_available_width = self._scale(available_width)
        
        font_size = max(8, int(10 * self._zoom))
        font = tkFont.Font(family="Microsoft YaHei", size=font_size, weight="bold")
        
        text_width = font.measure(base_name)
        
        if text_width <= scaled_available_width:
            return base_name
        
        ellipsis = "..."
        ellipsis_width = font.measure(ellipsis)
        target_width = scaled_available_width - ellipsis_width
        
        if target_width <= 0:
            return ellipsis
        
        left, right = 0, len(base_name)
        while left < right:
            mid = (left + right + 1) // 2
            test_text = base_name[:mid]
            test_width = font.measure(test_text)
            
            if test_width <= target_width:
                left = mid
            else:
                right = mid - 1
        
        return base_name[:left] + ellipsis
    
    def redraw(self):
        self.canvas.delete(self.node_id)
        self._create_visuals()
    
    def move_to(self, x: float, y: float):
        self.x = x
        self.y = y
        self.redraw()
    
    def get_bounds(self) -> tuple:
        return (
            self.x - self.width/2, self.y - self.height/2,
            self.x + self.width/2, self.y + self.height/2
        )
    
    def contains_point(self, x: float, y: float) -> bool:
        x1, y1, x2, y2 = self.get_bounds()
        return x1 <= x <= x2 and y1 <= y <= y2
    
    def get_input_port_pos(self) -> tuple:
        return (self.x, self.y - self.height/2)
    
    def get_output_port_pos(self) -> tuple:
        return (self.x, self.y + self.height/2)
    
    def is_on_input_port(self, x: float, y: float) -> bool:
        px, py = self.get_input_port_pos()
        dist = math.sqrt((x - px)**2 + (y - py)**2)
        return dist <= PORT_RADIUS + 4
    
    def is_on_output_port(self, x: float, y: float) -> bool:
        px, py = self.get_output_port_pos()
        dist = math.sqrt((x - px)**2 + (y - py)**2)
        return dist <= PORT_RADIUS + 4
    
    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_outline()
    
    def highlight_port(self, port_type: str, highlight: bool = True):
        if port_type == "input":
            port = self.input_port
            color = self._dark_colors['node_selected'] if highlight else self._dark_colors['bg_tertiary']
        else:
            port = self.output_port
            color = self._dark_colors['node_selected'] if highlight else self._color_config['bg']
        
        self.canvas.itemconfig(port, outline=color, width=3 if highlight else 2)
    
    def set_status(self, status: NodeExecutionStatus):
        self._status = status
        
        if self._flash_job:
            self.canvas.after_cancel(self._flash_job)
            self._flash_job = None
        
        if status == NodeExecutionStatus.RUNNING:
            self._start_flashing()
        else:
            self._flash_state = False
            self._update_outline()
        
        icon = STATUS_ICONS.get(status, "")
        self.canvas.itemconfig(self.status_icon, text=icon)
        
        if status in (NodeExecutionStatus.SUCCESS, NodeExecutionStatus.FAILURE, NodeExecutionStatus.ABORTED):
            status_color = STATUS_COLORS[status]
            if status_color:
                self.canvas.itemconfig(self.status_bg, fill=status_color)
                self.canvas.itemconfig(self.status_icon, fill="#FFFFFF")
        elif status == NodeExecutionStatus.RUNNING:
            self.canvas.itemconfig(self.status_bg, fill=STATUS_COLORS[NodeExecutionStatus.RUNNING])
        else:
            self.canvas.itemconfig(self.status_bg, fill=self._dark_colors['bg_tertiary'])
            self.canvas.itemconfig(self.status_icon, fill=self._dark_colors['text_secondary'])
    
    def show_status_indicator(self):
        if not self._status_visible:
            self._status_visible = True
            self.canvas.itemconfig(self.status_bg, state='normal')
            self.canvas.itemconfig(self.status_icon, state='normal')
    
    def hide_status_indicator(self):
        if self._status_visible:
            self._status_visible = False
            self.canvas.itemconfig(self.status_bg, state='hidden')
            self.canvas.itemconfig(self.status_icon, state='hidden')
    
    def _start_flashing(self):
        self._flash_state = not self._flash_state
        self._update_outline()
        self._flash_job = self.canvas.after(400, self._start_flashing)
    
    def _update_outline(self):
        if self._status == NodeExecutionStatus.RUNNING:
            outline = "#F59E0B" if self._flash_state else "#FBBF24"
            width = 2
        elif self._selected:
            outline = self._dark_colors['node_selected']
            width = 2
        else:
            outline = self._dark_colors['node_border']
            width = 1
        
        self.canvas.itemconfig(self.rect, outline=outline, width=width)
    
    def reset_status(self):
        self._status = NodeExecutionStatus.IDLE
        if self._flash_job:
            self.canvas.after_cancel(self._flash_job)
            self._flash_job = None
        self._flash_state = False
        self._update_outline()
        self.canvas.itemconfig(self.status_icon, text="")
        self.canvas.itemconfig(self.status_bg, fill=self._dark_colors['bg_tertiary'])
        self.hide_status_indicator()
