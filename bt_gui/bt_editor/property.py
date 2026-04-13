from typing import Any, Callable, Dict, Optional, List
import os

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

from ..theme import Theme
from .constants import CONDITION_NODES, ACTION_NODES, COMPOSITE_NODES


NODE_CONFIG_SCHEMAS = {
    "OCRConditionNode": [
        {"key": "region", "label": "检测区域", "type": "region"},
        {"key": "keywords", "label": "关键词", "type": "text"},
        {"key": "language", "label": "语言", "type": "select", "options": ["eng", "chi_sim", "chi_tra"], "default": "chi_sim"},
        {"key": "preprocess_mode", "label": "图像预处理", "type": "select", "options": ["默认", "游戏"], "default": "默认"},
        {"key": "position_key", "label": "位置变量名", "type": "text", "default": "last_detection_position"},
    ],
    "ImageConditionNode": [
        {"key": "region", "label": "检测区域", "type": "region"},
        {"key": "template_path", "label": "模板路径", "type": "screenshot", "width": 120, "filetypes": [("图像文件", "*.png *.jpg *.jpeg *.bmp"), ("所有文件", "*.*")]},
        {"key": "threshold", "label": "匹配阈值(%)", "type": "number", "min": 0, "max": 100, "default": 80},
        {"key": "position_key", "label": "位置变量名", "type": "text", "default": "last_detection_position"},
    ],
    "ColorConditionNode": [
        {"key": "region", "label": "检测区域", "type": "region"},
        {"key": "target_color", "label": "目标颜色", "type": "color"},
        {"key": "tolerance", "label": "容差", "type": "number", "min": 0, "max": 100, "default": 10},
        {"key": "min_pixels", "label": "最小像素数", "type": "number", "min": 1, "default": 1},
        {"key": "position_key", "label": "位置变量名", "type": "text", "default": "last_detection_position"},
    ],
    "NumberConditionNode": [
        {"key": "region", "label": "检测区域", "type": "region"},
        {"key": "preprocess_mode", "label": "预处理模式", "type": "select", "options": ["普通文本", "艺术字"], "default": "普通文本"},
        {"key": "extract_mode", "label": "提取模式", "type": "select", "options": ["无规则", "x/y", "自定义"], "default": "无规则"},
        {"key": "extract_pattern", "label": "自定义模式", "type": "text"},
        {"key": "compare_mode", "label": "比较模式", "type": "select", "options": ["<", "<=", ">", ">=", "==", "!="], "default": "=="},
        {"key": "threshold", "label": "比较值", "type": "number", "default": 0},
        {"key": "min_confidence", "label": "置信度阈值(%)", "type": "number", "min": 0, "max": 100, "default": 50},
        {"key": "value_key", "label": "值变量名", "type": "text", "default": "last_number_value"},
        {"key": "position_key", "label": "位置变量名", "type": "text", "default": "last_detection_position"},
    ],
    "VariableConditionNode": [
        {"key": "variable_name", "label": "变量名", "type": "text"},
        {"key": "operator", "label": "运算符", "type": "select", "options": ["==", "!=", ">", "<", ">=", "<=", "exists", "not_exists", "contains", "not_contains"], "default": "=="},
        {"key": "compare_value", "label": "比较值", "type": "text"},
    ],
    "KeyPressNode": [
        {"key": "key", "label": "按键", "type": "key"},
        {"key": "action", "label": "动作", "type": "select", "options": ["press", "down", "up"], "default": "press"},
        {"key": "duration", "label": "按住时长(ms)", "type": "number", "default": 0},
    ],
    "MouseClickNode": [
        {"key": "button", "label": "按钮", "type": "select", "options": ["left", "right", "middle"], "default": "left"},
        {"key": "action", "label": "动作", "type": "select", "options": ["press", "down", "up"], "default": "press"},
        {"key": "duration", "label": "按住时长(ms)", "type": "number", "default": 100},
        {"key": "position", "label": "位置", "type": "position"},
        {"key": "use_blackboard", "label": "点击最近检测点", "type": "bool", "default": False},
        {"key": "position_key", "label": "位置变量名", "type": "text", "default": "last_detection_position"},
        {"key": "click_count", "label": "点击次数(-1无限)", "type": "number", "min": -1, "max": 10, "default": 1},
        {"key": "click_interval", "label": "点击间隔(ms)", "type": "number", "default": 100},
    ],
    "MouseMoveNode": [
        {"key": "position", "label": "位置(拖拽时为起点)", "type": "position"},
        {"key": "use_blackboard", "label": "移动到最近检测点", "type": "bool", "default": False},
        {"key": "position_key", "label": "黑板变量名", "type": "text", "default": "last_detection_position"},
        {"key": "relative", "label": "相对移动", "type": "bool", "default": False},
        {"key": "smooth", "label": "平滑移动", "type": "bool", "default": True},
        {"key": "move_type", "label": "移动类型", "type": "select", "options": ["移动", "拖拽"], "default": "移动"},
        {"key": "drag_button", "label": "拖拽按钮", "type": "select", "options": ["left", "right", "middle"], "default": "left"},
        {"key": "end_position", "label": "拖拽终点", "type": "position"},
        {"key": "use_blackboard_end", "label": "终点使用黑板位置", "type": "bool", "default": False},
        {"key": "position_key_end", "label": "终点位置变量名", "type": "text", "default": ""},
        {"key": "drag_duration", "label": "拖拽时长(ms)", "type": "number", "default": 0},
    ],
    "MouseScrollNode": [
        {"key": "distance", "label": "滚动距离", "type": "number", "default": 5},
        {"key": "clicks", "label": "滚动次数", "type": "number", "default": 1},
        {"key": "direction", "label": "滚动方向", "type": "select", "options": ["向上", "向下", "向左", "向右"], "default": "向上"},
    ],
    "DelayNode": [
        {"key": "duration_ms", "label": "延时时长(ms)", "type": "number", "default": 1000},
    ],
    "SetVariableNode": [
        {"key": "variable_name", "label": "变量名", "type": "text"},
        {"key": "operation", "label": "操作", "type": "select", "options": ["set", "increment", "delete", "clear"], "default": "set"},
        {"key": "value", "label": "值", "type": "text"},
    ],
    "ScriptNode": [
        {"key": "script_path", "label": "脚本路径", "type": "file", "width": 120, "filetypes": [("所有文件", "*.*")]},
        {"key": "loop", "label": "循环执行", "type": "bool", "default": False},
    ],
    "CodeNode": [
        {"key": "code_path", "label": "代码路径", "type": "file", "width": 120, "filetypes": [("所有文件", "*.*")]},
        {"key": "code_type", "label": "代码类型", "type": "select", "options": ["auto", "python", "batch", "powershell"], "default": "auto"},
        {"key": "args", "label": "命令行参数", "type": "text"},
        {"key": "wait_complete", "label": "等待执行完成", "type": "bool", "default": True},
    ],
    "AlarmNode": [
        {"key": "sound_path", "label": "音频文件", "type": "file", "width": 120, "filetypes": [("所有文件", "*.*")]},
        {"key": "volume", "label": "音量(0-100,空用全局)", "type": "number", "min": 0, "max": 100, "default": 70},
        {"key": "wait_complete", "label": "等待播放完成", "type": "bool", "default": True},
    ],
    "ParallelNode": [
        {"key": "success_policy", "label": "成功策略", "type": "select", "options": ["require_all", "require_one"], "default": "require_all"},
    ],
    "SequenceNode": [
        {"key": "child_interval", "label": "子节点间隔(ms)", "type": "number", "min": 0, "default": 0},
        {"key": "continue_on_failure", "label": "失败后继续执行", "type": "bool", "default": False},
    ],
    "SelectorNode": [
        {"key": "child_interval", "label": "子节点间隔(ms)", "type": "number", "min": 0, "default": 0},
    ],
}

CONDITION_DECORATOR_FIELDS = [
    {"key": "invert", "label": "结果取反", "type": "bool", "default": False},
    {"key": "retry_count", "label": "失败重试次数(-1无限)", "type": "number", "min": -1, "default": 0},
    {"key": "timeout_ms", "label": "超时时间(ms,0不限)", "type": "number", "min": 0, "default": 0},
    {"key": "check_interval_ms", "label": "检测间隔(ms)", "type": "number", "min": 30, "default": 300},
]

ACTION_DECORATOR_FIELDS = [
    {"key": "repeat_count", "label": "重复次数(0不重复,-1无限)", "type": "number", "min": -1, "default": 0},
    {"key": "repeat_interval_ms", "label": "重复间隔(ms)", "type": "number", "min": 0, "default": 100},
    {"key": "timeout_ms", "label": "超时时间(ms,0不限)", "type": "number", "min": 0, "default": 0},
]

COMPOSITE_DECORATOR_FIELDS = [
    {"key": "retry_count", "label": "失败重试次数(-1无限)", "type": "number", "min": -1, "default": 0},
    {"key": "repeat_count", "label": "重复次数(0不重复,-1无限)", "type": "number", "min": -1, "default": 0},
    {"key": "repeat_interval_ms", "label": "重复间隔(ms)", "type": "number", "min": 0, "default": 100},
    {"key": "timeout_ms", "label": "超时时间(ms,0不限)", "type": "number", "min": 0, "default": 0},
]


class FieldWidget(ctk.CTkFrame):
    def __init__(self, master, label: str, key: str, on_change: Callable, **kwargs):
        super().__init__(master, **kwargs)
        self.label = label
        self.key = key
        self.on_change = on_change
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(fg_color="transparent")
        
        self._create_label()
    
    def _create_label(self):
        self.label_widget = ctk.CTkLabel(
            self,
            text=self.label,
            font=Theme.get_font('sm'),
            text_color=self._dark_colors['text_secondary'],
            anchor="w"
        )
        self.label_widget.pack(fill="x", pady=(Theme.DIMENSIONS['spacing_sm'], Theme.DIMENSIONS['spacing_xs']))
    
    def set_value(self, value: Any):
        pass
    
    def get_value(self) -> Any:
        return None


class TextField(FieldWidget):
    def __init__(self, master, label: str, key: str, on_change: Callable, **kwargs):
        super().__init__(master, label, key, on_change, **kwargs)
        self._create_widget()
    
    def _create_widget(self):
        self.var = tk.StringVar()
        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.var,
            font=Theme.get_font('sm'),
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['bg_tertiary'],
            border_color=self._dark_colors['border'],
            text_color=self._dark_colors['text_primary'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius']
        )
        self.entry.pack(fill="x")
        self.entry.bind("<FocusOut>", lambda e: self.on_change(self.key, self.var.get()))
        self.entry.bind("<Return>", self._on_return)
    
    def _on_return(self, event):
        self.on_change(self.key, self.var.get())
        self.entry.selection_clear()
        self.master.focus_set()
        return "break"
    
    def set_value(self, value: Any):
        self.var.set(str(value or ""))
    
    def get_value(self) -> Any:
        return self.var.get()


class NumberField(FieldWidget):
    def __init__(self, master, label: str, key: str, on_change: Callable, 
                 min_val: float = None, max_val: float = None, step: float = 1, default: float = None, **kwargs):
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.default = default
        super().__init__(master, label, key, on_change, **kwargs)
        self._create_widget()
    
    def _create_widget(self):
        self.var = tk.StringVar()
        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.var,
            font=Theme.get_font('sm'),
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['bg_tertiary'],
            border_color=self._dark_colors['border'],
            text_color=self._dark_colors['text_primary'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius']
        )
        self.entry.pack(fill="x")
        self.entry.bind("<FocusOut>", lambda e: self._on_change())
        self.entry.bind("<Return>", self._on_return)
    
    def _on_change(self):
        try:
            value = float(self.var.get()) if "." in self.var.get() else int(self.var.get())
            if self.min_val is not None:
                value = max(self.min_val, value)
            if self.max_val is not None:
                value = min(self.max_val, value)
            self.on_change(self.key, value)
        except ValueError:
            pass
    
    def _on_return(self, event):
        self._on_change()
        self.entry.selection_clear()
        self.master.focus_set()
        return "break"
    
    def set_value(self, value: Any):
        if value is not None:
            self.var.set(str(value))
        elif self.default is not None:
            self.var.set(str(self.default))
        elif self.min_val is not None:
            self.var.set(str(self.min_val))
        else:
            self.var.set("0")
    
    def get_value(self) -> Any:
        try:
            value = float(self.var.get()) if "." in self.var.get() else int(self.var.get())
            if self.min_val is not None:
                value = max(self.min_val, value)
            if self.max_val is not None:
                value = min(self.max_val, value)
            return value
        except ValueError:
            if self.default is not None:
                return self.default
            elif self.min_val is not None:
                return self.min_val
            else:
                return 0


class SelectField(FieldWidget):
    def __init__(self, master, label: str, key: str, on_change: Callable, options: List[str] = None, **kwargs):
        self.options = options or []
        super().__init__(master, label, key, on_change, **kwargs)
        self._create_widget()
    
    def _create_widget(self):
        self.var = tk.StringVar(value=self.options[0] if self.options else "")
        self.menu = ctk.CTkOptionMenu(
            self,
            variable=self.var,
            values=self.options,
            font=Theme.get_font('sm'),
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['bg_tertiary'],
            button_color=self._dark_colors['border'],
            button_hover_color=self._dark_colors['node_selected'],
            text_color=self._dark_colors['text_primary'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            command=lambda choice: self.on_change(self.key, choice)
        )
        self.menu.pack(fill="x")
    
    def set_value(self, value: Any):
        if value in self.options:
            self.var.set(str(value))
    
    def get_value(self) -> Any:
        return self.var.get()


class BoolField(FieldWidget):
    def __init__(self, master, label: str, key: str, on_change: Callable, **kwargs):
        super().__init__(master, label, key, on_change, **kwargs)
        self._create_widget()
    
    def _create_widget(self):
        self.var = tk.BooleanVar(value=True)
        self.switch = ctk.CTkSwitch(
            self,
            text="",
            variable=self.var,
            width=44,
            progress_color=self._dark_colors['primary'],
            button_color=self._dark_colors['text_primary'],
            button_hover_color=self._dark_colors['text_secondary'],
            command=lambda: self.on_change(self.key, self.var.get())
        )
        self.switch.pack(anchor="w")
    
    def set_value(self, value: Any):
        self.var.set(bool(value))
    
    def get_value(self) -> Any:
        return self.var.get()


class RegionField(FieldWidget):
    def __init__(self, master, label: str, key: str, on_change: Callable, app, **kwargs):
        self.app = app
        super().__init__(master, label, key, on_change, **kwargs)
        self._create_widget()
    
    def _create_widget(self):
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.var = tk.StringVar(value="未选择")
        
        self.entry = ctk.CTkEntry(
            input_frame,
            textvariable=self.var,
            font=Theme.get_font('sm'),
            height=Theme.DIMENSIONS['input_height'],
            width=120,
            fg_color=self._dark_colors['bg_tertiary'],
            border_color=self._dark_colors['border'],
            text_color=self._dark_colors['text_primary'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            state="disabled"
        )
        self.entry.pack(side="left", padx=(0, Theme.DIMENSIONS['spacing_xs']))
        
        self.btn = ctk.CTkButton(
            input_frame,
            text="选择",
            font=Theme.get_font('sm'),
            width=60,
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['primary'],
            hover_color=self._dark_colors['primary_hover'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            command=self._start_selection
        )
        self.btn.pack(side="right")
    
    def _start_selection(self):
        import time
        try:
            import screeninfo
            
            self.app.iconify()
            
            time.sleep(0.2)
            
            monitors = screeninfo.get_monitors()
            min_x = min(monitor.x for monitor in monitors)
            min_y = min(monitor.y for monitor in monitors)
            max_x = max(monitor.x + monitor.width for monitor in monitors)
            max_y = max(monitor.y + monitor.height for monitor in monitors)
            
            select_window = tk.Toplevel(self.app)
            select_window.geometry(f"{max_x - min_x}x{max_y - min_y}+{min_x}+{min_y}")
            select_window.overrideredirect(True)
            select_window.attributes("-alpha", 0.3)
            select_window.attributes("-topmost", True)
            select_window.configure(cursor="cross", bg=self._dark_colors['primary'])
            
            canvas = tk.Canvas(select_window, bg=self._dark_colors['primary'], highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            start_x_abs = [0]
            start_y_abs = [0]
            start_x_rel = [0]
            start_y_rel = [0]
            rect = [None]
            
            def on_mouse_down(event):
                start_x_abs[0] = event.x_root
                start_y_abs[0] = event.y_root
                start_x_rel[0] = event.x_root - min_x
                start_y_rel[0] = event.y_root - min_y
                rect[0] = None
            
            def on_mouse_drag(event):
                current_x_rel = event.x_root - min_x
                current_y_rel = event.y_root - min_y
                if rect[0]:
                    canvas.delete(rect[0])
                rect[0] = canvas.create_rectangle(
                    start_x_rel[0], start_y_rel[0], current_x_rel, current_y_rel,
                    outline="#FFFFFF", width=2, fill=""
                )
            
            def on_mouse_up(event):
                end_x_abs = event.x_root
                end_y_abs = event.y_root
                
                if abs(end_x_abs - start_x_abs[0]) < 10 or abs(end_y_abs - start_y_abs[0]) < 10:
                    messagebox.showwarning("警告", "选择的区域太小，请重新选择")
                    select_window.destroy()
                    self.app.deiconify()
                    return
                
                region = (
                    min(start_x_abs[0], end_x_abs),
                    min(start_y_abs[0], end_y_abs),
                    max(start_x_abs[0], end_x_abs),
                    max(start_y_abs[0], end_y_abs)
                )
                
                self.var.set(f"{region[0]},{region[1]},{region[2]},{region[3]}")
                self.on_change(self.key, list(region))
                
                select_window.destroy()
                self.app.deiconify()
            
            def on_escape(e):
                select_window.destroy()
                self.app.deiconify()
            
            canvas.bind("<Button-1>", on_mouse_down)
            canvas.bind("<B1-Motion>", on_mouse_drag)
            canvas.bind("<ButtonRelease-1>", on_mouse_up)
            select_window.bind("<Escape>", on_escape)
            select_window.focus_set()
            
        except ImportError:
            self.app.deiconify()
            messagebox.showerror("错误", "screeninfo库未安装，无法支持区域选择。\n请运行 'pip install screeninfo' 安装该库。")
        except Exception as e:
            self.app.deiconify()
            messagebox.showerror("错误", f"区域选择失败: {str(e)}")
    
    def set_value(self, value: Any):
        if isinstance(value, (list, tuple)) and len(value) == 4:
            self.var.set(f"{value[0]},{value[1]},{value[2]},{value[3]}")
        else:
            self.var.set(str(value or "未选择"))
    
    def get_value(self) -> Any:
        return self.var.get()


class FileField(FieldWidget):
    def __init__(self, master, label: str, key: str, on_change: Callable, 
                 filetypes: List[tuple] = None, app=None, width: int = None, **kwargs):
        self.filetypes = filetypes or [("所有文件", "*.*")]
        self.full_path = ""
        self.app = app
        self._width = width
        super().__init__(master, label, key, on_change, **kwargs)
        self._create_widget()
    
    def _create_widget(self):
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.var = tk.StringVar(value="")
        
        entry_kwargs = {
            "textvariable": self.var,
            "font": Theme.get_font('sm'),
            "height": Theme.DIMENSIONS['input_height'],
            "fg_color": self._dark_colors['bg_tertiary'],
            "border_color": self._dark_colors['border'],
            "text_color": self._dark_colors['text_primary'],
            "corner_radius": Theme.DIMENSIONS['button_corner_radius'],
            "state": "disabled"
        }
        if self._width:
            entry_kwargs["width"] = self._width
        
        self.entry = ctk.CTkEntry(input_frame, **entry_kwargs)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, Theme.DIMENSIONS['spacing_xs']))
        
        self.btn = ctk.CTkButton(
            input_frame,
            text="浏览",
            font=Theme.get_font('sm'),
            width=60,
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['primary'],
            hover_color=self._dark_colors['primary_hover'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            command=self._browse
        )
        self.btn.pack(side="right")
    
    def _get_project_root(self):
        if self.app and hasattr(self.app, 'behavior_tree'):
            editor = self.app.behavior_tree
            if hasattr(editor, 'project_root') and editor.project_root:
                return editor.project_root
        return None
    
    def _get_editor(self):
        if self.app and hasattr(self.app, 'behavior_tree'):
            return self.app.behavior_tree
        return None
    
    def _prompt_create_project(self):
        from tkinter import messagebox
        result = messagebox.askyesno(
            "提示",
            "请先创建或打开项目，才能导入资源文件。\n\n是否现在创建新项目？"
        )
        if result:
            editor = self._get_editor()
            if editor and hasattr(editor, '_on_new_project_dialog'):
                editor._on_new_project_dialog()
        return result
    
    def _browse(self):
        project_root = self._get_project_root()
        
        if not project_root:
            self._prompt_create_project()
            return
        
        initial_dir = None
        if self.full_path:
            abs_full_path = self.full_path
            if self.full_path.startswith("./"):
                abs_full_path = os.path.normpath(os.path.join(project_root, self.full_path[2:]))
            if os.path.exists(abs_full_path):
                initial_dir = os.path.dirname(abs_full_path)
        else:
            if os.path.exists(project_root):
                initial_dir = project_root
        
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="选择文件",
            filetypes=self.filetypes
        )
        
        if not file_path:
            return
        
        from bt_utils.resource_service import ResourceService
        
        old_path = self.full_path if self.full_path else None
        
        resource_type = ResourceService.RESOURCE_TYPE_MAP.get(self.key)
        
        relative_path = ResourceService.import_single_file_to_project(
            file_path,
            project_root,
            resource_type=resource_type,
            old_path=old_path
        )
        
        if relative_path:
            self.full_path = relative_path
            filename = relative_path.split("/")[-1]
            self.var.set(filename)
            self.on_change(self.key, relative_path)
        else:
            self.full_path = file_path
            filename = file_path.split("/")[-1].split("\\")[-1]
            self.var.set(filename)
            self.on_change(self.key, file_path)
    
    def set_value(self, value: Any):
        if value:
            self.full_path = str(value)
            filename = str(value).split("/")[-1].split("\\")[-1]
            self.var.set(filename)
        else:
            self.var.set("")
    
    def get_value(self) -> Any:
        return self.full_path


class ScreenshotField(FieldWidget):
    def __init__(self, master, label: str, key: str, on_change: Callable, 
                 filetypes: List[tuple] = None, app=None, width: int = None, **kwargs):
        self.filetypes = filetypes or [("所有文件", "*.*")]
        self.full_path = ""
        self.app = app
        self._width = width
        super().__init__(master, label, key, on_change, **kwargs)
        self._create_widget()
    
    def _create_widget(self):
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.var = tk.StringVar(value="")
        
        entry_kwargs = {
            "textvariable": self.var,
            "font": Theme.get_font('sm'),
            "height": Theme.DIMENSIONS['input_height'],
            "fg_color": self._dark_colors['bg_tertiary'],
            "border_color": self._dark_colors['border'],
            "text_color": self._dark_colors['text_primary'],
            "corner_radius": Theme.DIMENSIONS['button_corner_radius'],
            "state": "disabled"
        }
        if self._width:
            entry_kwargs["width"] = self._width
        
        self.entry = ctk.CTkEntry(input_frame, **entry_kwargs)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, Theme.DIMENSIONS['spacing_xs']))
        
        self.browse_btn = ctk.CTkButton(
            input_frame,
            text="浏览",
            font=Theme.get_font('sm'),
            width=50,
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['primary'],
            hover_color=self._dark_colors['primary_hover'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            command=self._browse
        )
        self.browse_btn.pack(side="right")
        
        screenshot_frame = ctk.CTkFrame(self, fg_color="transparent")
        screenshot_frame.pack(fill="x", pady=(Theme.DIMENSIONS['spacing_xs'], 0))
        
        self.screenshot_btn = ctk.CTkButton(
            screenshot_frame,
            text="截图",
            font=Theme.get_font('sm'),
            width=50,
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['info'],
            hover_color=self._dark_colors['info_hover'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            command=self._take_screenshot
        )
        self.screenshot_btn.pack(side="left")
    
    def _browse(self):
        project_root = self._get_project_root()
        
        if not project_root:
            from tkinter import messagebox
            result = messagebox.askyesno(
                "提示",
                "请先创建或打开项目，才能导入资源文件。\n\n是否现在创建新项目？"
            )
            if result:
                if self.app and hasattr(self.app, 'behavior_tree'):
                    editor = self.app.behavior_tree
                    if hasattr(editor, '_on_new_project_dialog'):
                        editor._on_new_project_dialog()
            return
        
        initial_dir = None
        if self.full_path:
            abs_full_path = self.full_path
            if self.full_path.startswith("./"):
                abs_full_path = os.path.normpath(os.path.join(project_root, self.full_path[2:]))
            if os.path.exists(abs_full_path):
                initial_dir = os.path.dirname(abs_full_path)
        else:
            if os.path.exists(project_root):
                initial_dir = project_root
        
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="选择文件",
            filetypes=self.filetypes
        )
        
        if not file_path:
            return
        
        from bt_utils.resource_service import ResourceService
        
        old_path = self.full_path if self.full_path else None
        
        resource_type = ResourceService.RESOURCE_TYPE_MAP.get(self.key)
        
        relative_path = ResourceService.import_single_file_to_project(
            file_path,
            project_root,
            resource_type=resource_type,
            old_path=old_path
        )
        
        if relative_path:
            self.full_path = relative_path
            filename = relative_path.split("/")[-1]
            self.var.set(filename)
            self.on_change(self.key, relative_path)
        else:
            self.full_path = file_path
            filename = file_path.split("/")[-1].split("\\")[-1]
            self.var.set(filename)
            self.on_change(self.key, file_path)
    
    def _take_screenshot(self):
        import os
        from tkinter import messagebox
        
        try:
            if not self.app:
                messagebox.showerror("错误", "应用实例未初始化")
                return
            
            app_dir = self._get_project_root()
            if not app_dir:
                self.app.deiconify()
                messagebox.showerror("错误", "请先保存项目，再进行截图操作")
                return
            
            image_dir = os.path.join(app_dir, "images", "templates")
            
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            
            self.app._screenshot_callback = self._save_screenshot
            self._start_screenshot_selection()
            
        except Exception as e:
            if self.app:
                self.app.deiconify()
            messagebox.showerror("错误", f"截图失败: {str(e)}")
    
    def _start_screenshot_selection(self):
        import time
        try:
            import screeninfo
            
            self.app.iconify()
            
            time.sleep(0.2)
            
            monitors = screeninfo.get_monitors()
            min_x = min(monitor.x for monitor in monitors)
            min_y = min(monitor.y for monitor in monitors)
            max_x = max(monitor.x + monitor.width for monitor in monitors)
            max_y = max(monitor.y + monitor.height for monitor in monitors)
            
            select_window = tk.Toplevel(self.app)
            select_window.geometry(f"{max_x - min_x}x{max_y - min_y}+{min_x}+{min_y}")
            select_window.overrideredirect(True)
            select_window.attributes("-alpha", 0.3)
            select_window.attributes("-topmost", True)
            select_window.configure(cursor="cross", bg=self._dark_colors['primary'])
            
            canvas = tk.Canvas(select_window, bg=self._dark_colors['primary'], highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            start_x_abs = [0]
            start_y_abs = [0]
            start_x_rel = [0]
            start_y_rel = [0]
            rect = [None]
            
            def on_mouse_down(event):
                start_x_abs[0] = event.x_root
                start_y_abs[0] = event.y_root
                start_x_rel[0] = event.x_root - min_x
                start_y_rel[0] = event.y_root - min_y
                rect[0] = None
            
            def on_mouse_drag(event):
                current_x_rel = event.x_root - min_x
                current_y_rel = event.y_root - min_y
                if rect[0]:
                    canvas.delete(rect[0])
                rect[0] = canvas.create_rectangle(
                    start_x_rel[0], start_y_rel[0], current_x_rel, current_y_rel,
                    outline="#FFFFFF", width=2, fill=""
                )
            
            def on_mouse_up(event):
                end_x_abs = event.x_root
                end_y_abs = event.y_root
                
                select_window.destroy()
                
                if abs(end_x_abs - start_x_abs[0]) < 10 or abs(end_y_abs - start_y_abs[0]) < 10:
                    self.app.deiconify()
                    messagebox.showwarning("警告", "选择的区域太小，请重新选择")
                    return
                
                region = (
                    min(start_x_abs[0], end_x_abs),
                    min(start_y_abs[0], end_y_abs),
                    max(start_x_abs[0], end_x_abs),
                    max(start_y_abs[0], end_y_abs)
                )
                
                if hasattr(self.app, '_screenshot_callback') and callable(self.app._screenshot_callback):
                    self.app._screenshot_callback(region)
            
            def on_escape(e):
                select_window.destroy()
                self.app.deiconify()
            
            canvas.bind("<Button-1>", on_mouse_down)
            canvas.bind("<B1-Motion>", on_mouse_drag)
            canvas.bind("<ButtonRelease-1>", on_mouse_up)
            select_window.bind("<Escape>", on_escape)
            select_window.focus_set()
            
        except ImportError:
            self.app.deiconify()
            messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。\n请运行 'pip install screeninfo' 安装该库。")
        except Exception as e:
            self.app.deiconify()
            messagebox.showerror("错误", f"区域选择失败: {str(e)}")
    
    def _save_screenshot(self, region):
        import os
        import time
        from tkinter import messagebox
        
        try:
            project_root = self._get_project_root()
            if not project_root:
                self.app.deiconify()
                messagebox.showerror("错误", "请先保存项目，再进行截图操作")
                return
            
            image_dir = os.path.join(project_root, "images", "templates")
            
            if not os.path.exists(image_dir):
                os.makedirs(image_dir)
            
            time.sleep(0.2)
            
            from bt_utils.screenshot import ScreenshotManager
            screenshot = ScreenshotManager().get_region_screenshot(region)
            
            self.app.deiconify()
            
            if not screenshot:
                messagebox.showerror("错误", "无法获取截图区域")
                return
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"template_{timestamp}.png"
            save_path = os.path.join(image_dir, filename)
            
            screenshot.save(save_path)
            
            from bt_utils.path_resolver import PathResolver
            resolver = PathResolver(project_root)
            relative_path = resolver.to_relative(save_path)
            
            self.full_path = relative_path
            self.var.set(filename)
            self.on_change(self.key, relative_path)
            
            messagebox.showinfo("成功", f"截图已保存到:\n{relative_path}")
            
        except Exception as e:
            self.app.deiconify()
            messagebox.showerror("错误", f"保存截图失败: {str(e)}")
    
    def _get_project_root(self):
        if self.app and hasattr(self.app, 'behavior_tree'):
            editor = self.app.behavior_tree
            if hasattr(editor, 'project_root') and editor.project_root:
                return editor.project_root
            
            if hasattr(editor, 'file_path') and editor.file_path:
                project_root = self._find_project_root(editor.file_path)
                if project_root:
                    return project_root
        
        return None
    
    def _find_project_root(self, file_path: str):
        """向上查找项目根目录"""
        import os
        current_dir = os.path.dirname(file_path)
        
        while current_dir:
            project_json_path = os.path.join(current_dir, "project.json")
            if os.path.exists(project_json_path):
                return current_dir
            
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                break
            current_dir = parent_dir
        
        return None
    
    def set_value(self, value: Any):
        if value:
            self.full_path = str(value)
            filename = str(value).split("/")[-1].split("\\")[-1]
            self.var.set(filename)
        else:
            self.var.set("")
    
    def get_value(self) -> Any:
        return self.full_path


class KeyField(FieldWidget):
    def __init__(self, master, label: str, key: str, on_change: Callable, **kwargs):
        self._listening = False
        super().__init__(master, label, key, on_change, **kwargs)
        self._create_widget()
    
    def _create_widget(self):
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.var = tk.StringVar(value="")
        
        self.entry = ctk.CTkEntry(
            input_frame,
            textvariable=self.var,
            font=Theme.get_font('sm'),
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['bg_tertiary'],
            border_color=self._dark_colors['border'],
            text_color=self._dark_colors['text_primary'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            state="disabled"
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, Theme.DIMENSIONS['spacing_xs']))
        
        self.btn = ctk.CTkButton(
            input_frame,
            text="修改",
            font=Theme.get_font('sm'),
            width=60,
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['primary'],
            hover_color=self._dark_colors['primary_hover'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            command=self._start_listening
        )
        self.btn.pack(side="right")
    
    def _start_listening(self):
        if self._listening:
            return
        
        self._listening = True
        self.btn.configure(text="请按键...", fg_color=self._dark_colors['warning'])
        
        def on_key_press(event):
            try:
                if not self._listening:
                    return
                
                key_name = event.keysym
                
                key_mappings = {
                    "Control_L": "ctrl", "Control_R": "ctrl",
                    "Alt_L": "alt", "Alt_R": "alt",
                    "Shift_L": "shift", "Shift_R": "shift",
                    "Super_L": "win", "Super_R": "win",
                    "Return": "enter", "BackSpace": "backspace",
                    "Tab": "tab", "Escape": "escape",
                    "space": "space", "Delete": "delete",
                    "Insert": "insert", "Home": "home",
                    "End": "end", "Prior": "pageup",
                    "Next": "pagedown", "Up": "up",
                    "Down": "down", "Left": "left",
                    "Right": "right",
                }
                
                if key_name in key_mappings:
                    key_name = key_mappings[key_name]
                elif len(key_name) == 1:
                    key_name = key_name.lower()
                
                self.var.set(key_name)
                self.on_change(self.key, key_name)
                
                self._listening = False
                if self.winfo_exists():
                    self.btn.configure(text="修改", fg_color=self._dark_colors['primary'])
                
                toplevel = self.winfo_toplevel()
                toplevel.unbind("<KeyPress>")
                
                return "break"
            except Exception:
                pass
        
        toplevel = self.winfo_toplevel()
        toplevel.bind("<KeyPress>", on_key_press)
        self._key_press_binding = on_key_press
        
        def reset_listening():
            if self._listening:
                self._listening = False
                try:
                    if self.winfo_exists():
                        self.btn.configure(text="修改", fg_color=self._dark_colors['primary'])
                except Exception:
                    pass
                try:
                    toplevel = self.winfo_toplevel()
                    toplevel.unbind("<KeyPress>")
                except Exception:
                    pass
        
        self.after(10000, reset_listening)
    
    def set_value(self, value: Any):
        self.var.set(str(value or ""))
    
    def get_value(self) -> Any:
        return self.var.get()


class PositionField(FieldWidget):
    def __init__(self, master, label: str, key: str, on_change: Callable, app, **kwargs):
        self.app = app
        super().__init__(master, label, key, on_change, **kwargs)
        self._create_widget()
    
    def _create_widget(self):
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.var = tk.StringVar(value="未选择")
        
        self.entry = ctk.CTkEntry(
            input_frame,
            textvariable=self.var,
            font=Theme.get_font('sm'),
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['bg_tertiary'],
            border_color=self._dark_colors['border'],
            text_color=self._dark_colors['text_primary'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius']
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, Theme.DIMENSIONS['spacing_xs']))
        self.entry.bind("<FocusOut>", lambda e: self._parse_and_change())
        
        self.btn = ctk.CTkButton(
            input_frame,
            text="获取",
            font=Theme.get_font('sm'),
            width=60,
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['primary'],
            hover_color=self._dark_colors['primary_hover'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            command=self._pick_position
        )
        self.btn.pack(side="right")
    
    def _parse_and_change(self):
        try:
            parts = self.var.get().replace(" ", "").split(",")
            if len(parts) >= 2:
                value = [int(parts[0]), int(parts[1])]
                self.on_change(self.key, value)
        except (ValueError, AttributeError):
            pass
    
    def _pick_position(self):
        import time
        try:
            import screeninfo
            
            self.app.iconify()
            
            time.sleep(0.2)
            
            monitors = screeninfo.get_monitors()
            min_x = min(monitor.x for monitor in monitors)
            min_y = min(monitor.y for monitor in monitors)
            max_x = max(monitor.x + monitor.width for monitor in monitors)
            max_y = max(monitor.y + monitor.height for monitor in monitors)
            
            select_window = tk.Toplevel(self.app)
            select_window.geometry(f"{max_x - min_x}x{max_y - min_y}+{min_x}+{min_y}")
            select_window.overrideredirect(True)
            select_window.attributes("-alpha", 0.2)
            select_window.attributes("-topmost", True)
            select_window.configure(cursor="crosshair", bg=self._dark_colors['primary'])
            
            label = tk.Label(
                select_window, 
                text="点击选择位置", 
                font=("Microsoft YaHei", 24), 
                bg=self._dark_colors['primary'], 
                fg="#FFFFFF"
            )
            label.place(relx=0.5, rely=0.5, anchor="center")
            
            def on_click(event):
                x, y = event.x_root, event.y_root
                self.var.set(f"{x}, {y}")
                self.on_change(self.key, [x, y])
                select_window.destroy()
                self.app.deiconify()
            
            def on_escape(e):
                select_window.destroy()
                self.app.deiconify()
            
            select_window.bind("<Button-1>", on_click)
            select_window.bind("<Escape>", on_escape)
            select_window.focus_set()
            
        except ImportError:
            self.app.deiconify()
            messagebox.showerror("错误", "screeninfo库未安装，无法支持位置选择。\n请运行 'pip install screeninfo' 安装该库。")
        except Exception as e:
            self.app.deiconify()
            messagebox.showerror("错误", f"位置选择失败: {str(e)}")
    
    def set_value(self, value: Any):
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            self.var.set(f"{value[0]}, {value[1]}")
        else:
            self.var.set(str(value or "未选择"))
    
    def get_value(self) -> Any:
        try:
            parts = self.var.get().replace(" ", "").split(",")
            if len(parts) >= 2:
                return [int(parts[0]), int(parts[1])]
            return None
        except (ValueError, AttributeError):
            return None


class ColorField(FieldWidget):
    def __init__(self, master, label: str, key: str, on_change: Callable, app, **kwargs):
        self.app = app
        self._current_color = "#808080"
        super().__init__(master, label, key, on_change, **kwargs)
        self._create_widget()
    
    def _create_widget(self):
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x")
        
        self.var = tk.StringVar(value="未选择")
        self._rgb_value = None
        
        self.preview = ctk.CTkFrame(
            input_frame,
            width=32,
            height=32,
            fg_color=self._current_color,
            corner_radius=Theme.DIMENSIONS['button_corner_radius']
        )
        self.preview.pack(side="left", padx=(0, Theme.DIMENSIONS['spacing_xs']))
        
        self.entry = ctk.CTkEntry(
            input_frame,
            textvariable=self.var,
            font=Theme.get_font('sm'),
            height=Theme.DIMENSIONS['input_height'],
            width=100,
            fg_color=self._dark_colors['bg_tertiary'],
            border_color=self._dark_colors['border'],
            text_color=self._dark_colors['text_primary'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            state="disabled"
        )
        self.entry.pack(side="left", padx=(0, Theme.DIMENSIONS['spacing_xs']))
        
        self.btn = ctk.CTkButton(
            input_frame,
            text="选择",
            font=Theme.get_font('sm'),
            width=60,
            height=Theme.DIMENSIONS['input_height'],
            fg_color=self._dark_colors['primary'],
            hover_color=self._dark_colors['primary_hover'],
            corner_radius=Theme.DIMENSIONS['button_corner_radius'],
            command=self._pick_color
        )
        self.btn.pack(side="right")
    
    def _pick_color(self):
        from bt_gui.widgets import create_color_picker
        
        def on_color_picked(rgb):
            r, g, b = rgb
            self.var.set(f"RGB({r}, {g}, {b})")
            self._current_color = f"#{r:02x}{g:02x}{b:02x}"
            self._rgb_value = [r, g, b]
            self.preview.configure(fg_color=self._current_color)
            self.on_change(self.key, self._rgb_value)
        
        create_color_picker(self.app, on_color_picked)
    
    def set_value(self, value: Any):
        if isinstance(value, (list, tuple)) and len(value) >= 3:
            r, g, b = int(value[0]), int(value[1]), int(value[2])
            self.var.set(f"RGB({r}, {g}, {b})")
            self._current_color = f"#{r:02x}{g:02x}{b:02x}"
            self._rgb_value = [r, g, b]
            self.preview.configure(fg_color=self._current_color)
        else:
            self.var.set(str(value or "未选择"))
            self._rgb_value = None
    
    def get_value(self) -> Any:
        return self._rgb_value


class PropertyPanel(ctk.CTkFrame):
    def __init__(self, master, app, on_change: Optional[Callable[[str, str, Any], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.on_change = on_change
        
        self.current_node_id: Optional[str] = None
        self.current_node_type: Optional[str] = None
        self.widgets: Dict[str, FieldWidget] = {}
        self._is_loading: bool = False
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(
            fg_color=self._dark_colors['sidebar_bg'],
            corner_radius=0,
            width=Theme.DIMENSIONS['property_width']
        )
        
        self._create_ui()
        self._bind_click_event()
    
    def is_loading(self) -> bool:
        return self._is_loading
    
    def _bind_click_event(self):
        def on_click(event):
            focused = self.focus_get()
            if focused:
                widget_type = str(type(focused).__name__)
                if widget_type in ("CTkEntry", "Entry"):
                    self.focus_set()
        
        self.bind("<Button-1>", on_click)
        self.header_frame.bind("<Button-1>", on_click)
        self.title_label.bind("<Button-1>", on_click)
        self.node_type_label.bind("<Button-1>", on_click)
        self.separator.bind("<Button-1>", on_click)
        self.content_frame.bind("<Button-1>", on_click)
    
    def force_save_current_field(self):
        """强制保存当前焦点控件的值"""
        focused = self.focus_get()
        if not focused:
            return
        
        for key, widget in self.widgets.items():
            if not hasattr(widget, 'entry'):
                continue
            
            try:
                entry_widget = widget.entry
                
                if entry_widget == focused:
                    self._save_widget_value(widget)
                    return
                
                if hasattr(entry_widget, '_entry'):
                    if entry_widget._entry == focused:
                        self._save_widget_value(widget)
                        return
                
                if hasattr(entry_widget, 'winfo_children'):
                    for child in entry_widget.winfo_children():
                        if child == focused:
                            self._save_widget_value(widget)
                            return
            except Exception:
                pass
    
    def _save_widget_value(self, widget):
        """保存控件的值"""
        if hasattr(widget, 'on_change') and hasattr(widget, 'var'):
            try:
                widget.on_change(widget.key, widget.var.get())
            except Exception:
                pass
    
    def _create_ui(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=Theme.DIMENSIONS['spacing_md'])
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="属性面板",
            font=Theme.get_font('lg'),
            text_color=self._dark_colors['text_primary']
        )
        self.title_label.pack(side="left")
        
        self.node_type_label = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=Theme.get_font('sm'),
            text_color=self._dark_colors['text_muted']
        )
        self.node_type_label.pack(side="right")
        
        self.separator = ctk.CTkFrame(
            self,
            height=1,
            fg_color=self._dark_colors['border']
        )
        self.separator.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'])
        
        self.content_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=self._dark_colors['bg_tertiary'],
            scrollbar_button_hover_color=self._dark_colors['border']
        )
        self.content_frame.pack(fill="both", expand=True, padx=Theme.DIMENSIONS['spacing_md'], pady=Theme.DIMENSIONS['spacing_sm'])
        
        self._show_empty()
    
    def _show_empty(self):
        self._clear_content()
        self.title_label.configure(text="属性面板")
        self.node_type_label.configure(text="")
        
        empty_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        empty_frame.pack(expand=True)
        
        empty_icon = ctk.CTkLabel(
            empty_frame,
            text="◇",
            font=("Arial", 32),
            text_color=self._dark_colors['border']
        )
        empty_icon.pack(pady=(Theme.DIMENSIONS['spacing_xl'], Theme.DIMENSIONS['spacing_md']))
        
        empty_text = ctk.CTkLabel(
            empty_frame,
            text="请选择一个节点\n查看和编辑属性",
            font=Theme.get_font('sm'),
            text_color=self._dark_colors['text_muted'],
            justify="center"
        )
        empty_text.pack()
    
    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.widgets.clear()
    
    def save_and_clear(self):
        self.current_node_id = None
        self.current_node_type = None
        self._show_empty()
    
    def load_node(self, node_id: str, node_type: str, node_data: Dict[str, Any]):
        self._is_loading = True
        
        try:
            self.current_node_id = node_id
            self.current_node_type = node_type
            
            self._clear_content()
            
            display_name = node_type.replace("Node", "").replace("Condition", "").replace("Action", "")
            self.title_label.configure(text="节点属性")
            self.node_type_label.configure(text=display_name)
            
            self._create_base_fields(node_data)
            
            schema = NODE_CONFIG_SCHEMAS.get(node_type, [])
            if schema:
                self._create_section_title("配置参数")
                for field in schema:
                    value = node_data.get("config", {}).get(field["key"])
                    self._create_field(field, value)
            
            decorator_fields = []
            if node_type in CONDITION_NODES:
                decorator_fields = CONDITION_DECORATOR_FIELDS
            elif node_type in ACTION_NODES:
                decorator_fields = ACTION_DECORATOR_FIELDS
            elif node_type in COMPOSITE_NODES or node_type == "StartNode":
                decorator_fields = COMPOSITE_DECORATOR_FIELDS
            
            if decorator_fields:
                self._create_section_title("装饰参数")
                for field in decorator_fields:
                    self._create_field(field, node_data.get("config", {}).get(field["key"]))
        finally:
            self._is_loading = False
    
    def _create_section_title(self, title: str):
        section_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        section_frame.pack(fill="x", pady=(Theme.DIMENSIONS['spacing_lg'], Theme.DIMENSIONS['spacing_sm']))
        
        section_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=Theme.get_font('sm'),
            text_color=self._dark_colors['text_primary']
        )
        section_label.pack(side="left")
        
        section_line = ctk.CTkFrame(
            section_frame,
            height=1,
            fg_color=self._dark_colors['border']
        )
        section_line.pack(side="left", fill="x", expand=True, padx=(Theme.DIMENSIONS['spacing_sm'], 0))
    
    def _create_base_fields(self, node_data: Dict[str, Any]):
        self._create_section_title("基本信息")
        
        name_field = TextField(
            self.content_frame,
            label="名称",
            key="name",
            on_change=self._on_field_change
        )
        name_field.set_value(node_data.get("name", ""))
        name_field.pack(fill="x", pady=Theme.DIMENSIONS['spacing_xs'])
        self.widgets["name"] = name_field
        
        enabled_field = BoolField(
            self.content_frame,
            label="启用",
            key="enabled",
            on_change=self._on_field_change
        )
        enabled_field.set_value(node_data.get("enabled", True))
        enabled_field.pack(fill="x", pady=Theme.DIMENSIONS['spacing_xs'])
        self.widgets["enabled"] = enabled_field
    
    def _create_field(self, field: Dict[str, Any], value: Any):
        field_type = field.get("type", "text")
        key = field["key"]
        label = field["label"]
        
        field_widget = None
        
        if field_type == "text":
            field_widget = TextField(self.content_frame, label, key, self._on_field_change)
        elif field_type == "number":
            field_widget = NumberField(
                self.content_frame, label, key, self._on_field_change,
                min_val=field.get("min"), max_val=field.get("max"), step=field.get("step", 1),
                default=field.get("default")
            )
        elif field_type == "select":
            field_widget = SelectField(
                self.content_frame, label, key, self._on_field_change,
                options=field.get("options", [])
            )
        elif field_type == "bool":
            field_widget = BoolField(self.content_frame, label, key, self._on_field_change)
        elif field_type == "region":
            field_widget = RegionField(self.content_frame, label, key, self._on_field_change, self.app)
        elif field_type == "file":
            field_widget = FileField(
                self.content_frame, label, key, self._on_field_change,
                filetypes=field.get("filetypes", [("所有文件", "*.*")]),
                app=self.app,
                width=field.get("width")
            )
        elif field_type == "screenshot":
            field_widget = ScreenshotField(
                self.content_frame, label, key, self._on_field_change,
                filetypes=field.get("filetypes", [("所有文件", "*.*")]),
                app=self.app,
                width=field.get("width")
            )
        elif field_type == "key":
            field_widget = KeyField(self.content_frame, label, key, self._on_field_change)
        elif field_type == "position":
            field_widget = PositionField(self.content_frame, label, key, self._on_field_change, self.app)
        elif field_type == "color":
            field_widget = ColorField(self.content_frame, label, key, self._on_field_change, self.app)
        
        if field_widget:
            field_widget.set_value(value)
            field_widget.pack(fill="x", pady=Theme.DIMENSIONS['spacing_xs'])
            self.widgets[key] = field_widget
    
    def _on_field_change(self, key: str, value: Any):
        if self.on_change and self.current_node_id:
            self.on_change(self.current_node_id, key, value)
