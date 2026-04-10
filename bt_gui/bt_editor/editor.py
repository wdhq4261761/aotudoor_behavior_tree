import customtkinter as ctk
from tkinter import messagebox
import json
import os
from typing import Optional, Dict, Any, List
from copy import deepcopy

from ..theme import Theme
from .canvas import BehaviorTreeCanvas
from .palette import NodePalette
from .property import PropertyPanel
from .toolbar import EditorToolbar
from .constants import NODE_DISPLAY_NAMES
from .log_panel import LogPanel
from .undo_redo import (
    CommandManager, AddNodeCommand, AddNodesCommand, RemoveNodeCommand,
    RemoveNodesCommand, MoveNodeCommand, MoveNodesCommand, AddConnectionCommand,
    ClearCanvasCommand
)
from bt_core.engine import BehaviorTreeEngine
from bt_core.context import ExecutionContext
from bt_core.serializer import Serializer
from bt_core.status import NodeStatus
from bt_utils.auto_save import AutoSaveManager
from bt_utils.crash_recovery import CrashRecoveryHandler


class BehaviorTreeEditor(ctk.CTkFrame):
    AUTOSAVE_INTERVAL = 60000
    BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backup")
    RECOVERY_DIR = os.path.join(os.path.dirname(__file__), "recovery")

    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.file_path: Optional[str] = None
        self._node_counter = 0
        self._modified = False
        
        self.engine: Optional[BehaviorTreeEngine] = None
        self.context: Optional[ExecutionContext] = None
        self._is_running = False
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(fg_color=self._dark_colors['bg_primary'], corner_radius=0)
        
        self.command_manager = CommandManager()
        self._clipboard_data = None
        
        self._autosave_manager: Optional[AutoSaveManager] = None
        self._init_autosave()
        
        self._create_ui()
        self._bind_events()
        
        self._check_crash_recovery()
    
    def _create_ui(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        self._create_toolbar()
        self._create_main_area()
    
    def _create_toolbar(self):
        self.toolbar = EditorToolbar(
            self.main_container,
            self.app,
            on_new=self.new_tree,
            on_load=self.load_tree,
            on_save=self.save_tree,
            on_undo=self.undo,
            on_redo=self.redo,
            on_clear=self.clear_canvas,
            on_reset_view=self.reset_view,
            on_start=self._start_running,
            on_stop=self._stop_running
        )
        self.toolbar.pack(fill="x")
    
    def _create_main_area(self):
        self.main_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.main_area.pack(fill="both", expand=True)
        
        self._create_palette()
        self._create_canvas()
        self._create_property_panel()
        
        self._create_log_panel()
    
    def _create_log_panel(self):
        self.log_panel = LogPanel(self.main_container)
        self.log_panel.pack(fill="x", side="bottom")
    
    def _create_palette(self):
        self.palette = NodePalette(
            self.main_area,
            on_node_add=self._on_node_add_from_palette
        )
        self.palette.pack(side="left", fill="y")
    
    def _create_canvas(self):
        self.canvas_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.canvas_frame.pack(side="left", fill="both", expand=True)
        
        self.canvas = BehaviorTreeCanvas(
            self.canvas_frame,
            self.app,
            on_node_select=self._on_node_select,
            on_node_move=self._on_node_move,
            on_nodes_move=self._on_nodes_move,
            on_connection_add=self._on_connection_add,
            on_node_deselect=self._on_node_deselect,
            property_panel=None
        )
        self.canvas.pack(fill="both", expand=True)
        
        self.property_panel = PropertyPanel(
            self.main_area,
            self.app,
            on_change=self._on_property_change
        )
        self.property_panel.pack(side="right", fill="y")
        
        self.canvas.property_panel = self.property_panel
        
        self._init_autosave()
        self._start_autosave()
    
    def _create_property_panel(self):
        pass
    
    def _bind_events(self):
        shortcuts = [
            ("<Control-z>", self.undo),
            ("<Control-y>", self.redo),
            ("<Control-Shift-Z>", self.redo),
            ("<Control-s>", lambda: self.save_tree()),
            ("<Control-Shift-S>", lambda: self.save_tree(save_as=True)),
            ("<Control-o>", lambda: self.load_tree()),
            ("<Control-n>", lambda: self.new_tree()),
            ("<Delete>", self._on_delete_key),
            ("<BackSpace>", self._on_delete_key),
            ("<Control-c>", self._copy_selected),
            ("<Control-v>", self._paste_selected),
            ("<Control-x>", self._cut_selected),
            ("<Control-d>", self._duplicate_selected),
        ]
        
        def make_handler(cb, key):
            def handler(e):
                if key in ("<Delete>", "<BackSpace>"):
                    focused = self.winfo_toplevel().focus_get()
                    if focused:
                        widget_type = str(type(focused).__name__)
                        if widget_type in ("CTkEntry", "Entry", "CTkTextbox", "Text"):
                            return None
                if callable(cb):
                    cb()
                return "break"
            return handler
        
        root = self.winfo_toplevel()
        for key, callback in shortcuts:
            handler = make_handler(callback, key)
            root.bind(key, handler)
        
        self._bind_run_shortcuts()
    
    def _bind_run_shortcuts(self):
        """绑定运行快捷键（从设置读取）"""
        root = self.winfo_toplevel()
        
        start_key = "F10"
        stop_key = "F12"
        
        try:
            if hasattr(self.app, 'settings') and hasattr(self.app.settings, 'get_settings'):
                settings = self.app.settings.get_settings()
                shortcuts = settings.get("shortcuts", {})
                start_key = shortcuts.get("start", "F10")
                stop_key = shortcuts.get("stop", "F12")
        except Exception:
            pass
        
        def format_key(key: str) -> str:
            key = key.strip()
            if key.startswith("<") and key.endswith(">"):
                return key
            return f"<{key}>"
        
        start_key_formatted = format_key(start_key)
        stop_key_formatted = format_key(stop_key)
        
        root.bind(start_key_formatted, lambda e: self._start_running())
        root.bind(stop_key_formatted, lambda e: self._stop_running())
        
        self._start_shortcut = start_key_formatted
        self._stop_shortcut = stop_key_formatted
    
    def update_run_shortcuts(self, start_key: str, stop_key: str):
        """更新运行快捷键"""
        root = self.winfo_toplevel()
        
        if hasattr(self, '_start_shortcut'):
            root.unbind(self._start_shortcut)
        if hasattr(self, '_stop_shortcut'):
            root.unbind(self._stop_shortcut)
        
        def format_key(key: str) -> str:
            key = key.strip()
            if key.startswith("<") and key.endswith(">"):
                return key
            return f"<{key}>"
        
        start_key_formatted = format_key(start_key)
        stop_key_formatted = format_key(stop_key)
        
        root.bind(start_key_formatted, lambda e: self._start_running())
        root.bind(stop_key_formatted, lambda e: self._stop_running())
        
        self._start_shortcut = start_key_formatted
        self._stop_shortcut = stop_key_formatted
    
    def _on_delete_key(self):
        """处理删除键，避免在输入框中误删节点"""
        focused = self.winfo_toplevel().focus_get()
        if focused:
            widget_type = str(type(focused).__name__)
            if widget_type in ("CTkEntry", "Entry", "CTkTextbox", "Text"):
                return None
        self._delete_selected()
        return "break"
    
    def _on_node_add_from_palette(self, node_type: str):
        self._node_counter += 1
        node_id = f"node_{self._node_counter}"
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        x = (canvas_width / 2 - self.canvas.pan_x) / self.canvas.zoom
        y = (canvas_height / 3 - self.canvas.pan_y) / self.canvas.zoom
        
        offset = 0
        for existing_node in self.canvas.nodes.values():
            if abs(existing_node.x - x) < 160 and abs(existing_node.y - y) < 70:
                offset += 80
        
        x += offset
        
        name = NODE_DISPLAY_NAMES.get(node_type, node_type)
        
        command = AddNodeCommand(
            canvas=self.canvas,
            node_id=node_id,
            node_type=node_type,
            x=x,
            y=y,
            node_data={'name': name}
        )
        command.description = f"添加{name}"
        
        self.command_manager.execute(command)
        self._update_toolbar()
        self._set_modified(True)
    
    def _on_node_select(self, node_id: str, node_type: str):
        node = self.canvas.nodes.get(node_id)
        if node:
            node_data = {
                "id": node_id,
                "type": node_type,
                "name": node.name,
                "config": node.config,
                "enabled": node.enabled
            }
            self.property_panel.load_node(node_id, node_type, node_data)
    
    def _on_node_deselect(self):
        self.property_panel.save_and_clear()
    
    def _on_node_move(self, node_id: str, old_x: float, old_y: float, new_x: float, new_y: float):
        command = MoveNodeCommand(
            canvas=self.canvas,
            node_id=node_id,
            old_x=old_x,
            old_y=old_y,
            new_x=new_x,
            new_y=new_y
        )
        self.command_manager.undo_stack.append(command)
        self._update_toolbar()
        self._set_modified(True)
    
    def _on_nodes_move(self, old_positions: Dict[str, tuple], new_positions: Dict[str, tuple]):
        command = MoveNodesCommand(
            canvas=self.canvas,
            node_ids=list(new_positions.keys()),
            old_positions=old_positions,
            new_positions=new_positions
        )
        self.command_manager.undo_stack.append(command)
        self._update_toolbar()
        self._set_modified(True)
    
    def _on_connection_add(self, parent_id: str, child_id: str):
        command = AddConnectionCommand(
            canvas=self.canvas,
            parent_id=parent_id,
            child_id=child_id
        )
        self.command_manager.undo_stack.append(command)
        self._update_toolbar()
        self._set_modified(True)
    
    def _on_property_change(self, node_id: str, key: str, value: Any):
        if node_id not in self.canvas.nodes:
            return
        
        node = self.canvas.nodes[node_id]
        if key in ["name", "enabled"]:
            setattr(node, key, value)
            if key == "name":
                self.canvas.redraw_node(node_id)
        else:
            if node.config is None:
                node.config = {}
            node.config[key] = value
        self._set_modified(True)
    
    def _delete_selected(self):
        if self.canvas.selected_nodes:
            self._delete_nodes(self.canvas.selected_nodes)
        elif self.canvas.selected_node:
            self._delete_node(self.canvas.selected_node)
        elif self.canvas.selected_connection:
            self.canvas.remove_selected_connection()
            self._set_modified(True)
    
    def _delete_node(self, node_id: str):
        command = RemoveNodeCommand(canvas=self.canvas, node_id=node_id)
        self.command_manager.execute(command)
        self._update_toolbar()
        self._set_modified(True)
    
    def _delete_nodes(self, node_ids: List[str]):
        command = RemoveNodesCommand(canvas=self.canvas, node_ids=list(node_ids))
        self.command_manager.execute(command)
        self._update_toolbar()
        self._set_modified(True)
    
    def _copy_selected(self):
        if self.canvas.selected_nodes:
            self._clipboard_data = self.canvas._copy_selected_nodes_to_clipboard()
        elif self.canvas.selected_node:
            self._clipboard_data = self.canvas._copy_selected_nodes_to_clipboard()
    
    def _paste_selected(self):
        if not self._clipboard_data:
            return
        
        from copy import deepcopy
        
        clipboard_data = self._clipboard_data
        nodes_data = clipboard_data.get('nodes', [])
        relative_positions = clipboard_data.get('relative_positions', {})
        connections = clipboard_data.get('connections', [])
        
        if not nodes_data:
            return
        
        paste_offset_x, paste_offset_y = self._calculate_paste_offset()
        
        if len(nodes_data) == 1:
            node_data = nodes_data[0]
            self._node_counter += 1
            new_id = f"node_{self._node_counter}"
            
            rel_x, rel_y = relative_positions.get(node_data['id'], (0, 0))
            
            command = AddNodeCommand(
                canvas=self.canvas,
                node_id=new_id,
                node_type=node_data['type'],
                x=rel_x + paste_offset_x,
                y=rel_y + paste_offset_y,
                node_data={
                    'name': node_data.get('name', ''),
                    'config': deepcopy(node_data.get('config', {})),
                    'enabled': node_data.get('enabled', True)
                }
            )
            command.description = f"粘贴 {node_data.get('name', '节点')}"
            self.command_manager.execute(command)
            
            self._select_new_nodes([new_id])
            self._set_modified(True)
            self._update_toolbar()
        else:
            id_map = {}
            new_nodes_data = []
            
            for node_data in nodes_data:
                old_id = node_data['id']
                self._node_counter += 1
                new_id = f"node_{self._node_counter}"
                id_map[old_id] = new_id
                
                rel_x, rel_y = relative_positions.get(old_id, (0, 0))
                
                new_nodes_data.append({
                    'id': new_id,
                    'type': node_data['type'],
                    'x': rel_x + paste_offset_x,
                    'y': rel_y + paste_offset_y,
                    'name': node_data.get('name', ''),
                    'config': deepcopy(node_data.get('config', {})),
                    'enabled': node_data.get('enabled', True)
                })
            
            new_connections = []
            for old_parent, old_child in connections:
                new_parent = id_map.get(old_parent)
                new_child = id_map.get(old_child)
                if new_parent and new_child:
                    new_connections.append((new_parent, new_child))
            
            command = AddNodesCommand(
                canvas=self.canvas,
                nodes_data=new_nodes_data,
                connections=new_connections,
                description=f"粘贴 {len(new_nodes_data)} 个节点"
            )
            self.command_manager.execute(command)
            
            new_ids = [n['id'] for n in new_nodes_data]
            self._select_new_nodes(new_ids)
            
            self._set_modified(True)
            self._update_toolbar()
    
    def _calculate_paste_offset(self) -> tuple:
        base_offset_x = 50
        base_offset_y = 50
        
        additional_offset = 0
        for existing_node in self.canvas.nodes.values():
            if abs(existing_node.x - base_offset_x) < 160 and abs(existing_node.y - base_offset_y) < 70:
                additional_offset += 80
        
        return base_offset_x + additional_offset, base_offset_y + additional_offset
    
    def _select_new_nodes(self, node_ids: List[str]):
        """选中新节点"""
        self.canvas._deselect_all()
        
        for node_id in node_ids:
            if node_id in self.canvas.nodes:
                self.canvas.selected_nodes.append(node_id)
                self.canvas.nodes[node_id].set_selected(True)
        
        if self.canvas.selected_nodes:
            self.canvas.selected_node = self.canvas.selected_nodes[0]
            if len(self.canvas.selected_nodes) == 1:
                node = self.canvas.nodes[self.canvas.selected_node]
                if self.canvas.on_node_select:
                    self.canvas.on_node_select(self.canvas.selected_node, node.node_type)
    
    def _cut_selected(self):
        self._copy_selected()
        self._delete_selected()
    
    def _duplicate_selected(self):
        self._copy_selected()
        self._paste_selected()
    
    def undo(self):
        if self.command_manager.can_undo():
            self.command_manager.undo()
            self._update_toolbar()
            self._set_modified(True)
    
    def redo(self):
        if self.command_manager.can_redo():
            self.command_manager.redo()
            self._update_toolbar()
            self._set_modified(True)
    
    def _update_toolbar(self):
        self.toolbar.update_undo_redo(
            self.command_manager.can_undo(),
            self.command_manager.can_redo(),
            self.command_manager.get_undo_description(),
            self.command_manager.get_redo_description()
        )
    
    def new_tree(self):
        if self._modified:
            if not messagebox.askyesno("确认", "当前文件未保存，是否继续新建？"):
                return
        
        self.clear_canvas()
        self.file_path = None
        self._set_modified(False)
        self.toolbar.set_file_path(None)
    
    def load_tree(self, file_path: Optional[str] = None):
        if not file_path:
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="打开行为树",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.clear_canvas()
            self.canvas.load_tree(data)
            self.file_path = file_path
            self._set_modified(False)
            self.toolbar.set_file_path(file_path)
            
            from bt_utils.config_manager import ConfigManager
            ConfigManager.set_last_file_path(file_path)
            
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败: {str(e)}")
    
    def save_tree(self, file_path: Optional[str] = None, save_as: bool = False):
        if not file_path:
            if not self.file_path or save_as:
                from tkinter import filedialog
                file_path = filedialog.asksaveasfilename(
                    title="保存行为树",
                    defaultextension=".json",
                    filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
                )
            else:
                file_path = self.file_path
        
        if not file_path:
            return
        
        try:
            data = self.canvas.get_tree_data()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.file_path = file_path
            self._set_modified(False)
            self.toolbar.set_file_path(file_path)
            
            from bt_utils.config_manager import ConfigManager
            ConfigManager.set_last_file_path(file_path)
            
        except Exception as e:
            messagebox.showerror("错误", f"保存文件失败: {str(e)}")
    
    def clear_canvas(self):
        if self.canvas.nodes:
            if not messagebox.askyesno("确认", "确定要清空画布吗？"):
                return
        
        self.canvas.clear_canvas()
        self.command_manager.clear()
        self._update_toolbar()
        self._set_modified(False)
    
    def reset_view(self):
        self.canvas.reset_view()
    
    def _start_running(self):
        if self.engine and self.engine._running:
            return
        
        if self.property_panel:
            self.property_panel.force_save_current_field()

        tree_data = self.canvas.get_tree_data()
        result = Serializer.deserialize(tree_data)
        
        if isinstance(result, tuple):
            root_node = result[0]
        else:
            root_node = result
        
        if not root_node:
            messagebox.showwarning("警告", "行为树为空，无法运行")
            return

        self._play_start_sound()

        self.canvas.show_all_status_indicators()
        
        self.context = ExecutionContext()
        self.context._on_node_status = self._on_node_status
        
        self.engine = BehaviorTreeEngine(root_node)
        self.engine._on_status_change = self._on_engine_status_change
        self.engine._on_node_status = self._on_node_status
        
        self.engine.start(self.context)
        self.toolbar.set_running(True)

    def _stop_running(self):
        if self.engine:
            self.engine.stop()
            self.engine = None
            self.context = None
        
        self._play_stop_sound()
        
        self.canvas.after(100, self._clear_status_after_stop)
        self.toolbar.set_running(False)
    
    def _clear_status_after_stop(self):
        """延迟清除状态，确保引擎完全停止"""
        self.canvas.clear_all_node_status()

    def _play_start_sound(self):
        try:
            from bt_utils.alarm import AlarmPlayer
            player = AlarmPlayer()
            player.play(volume=70, wait_complete=False)
        except Exception:
            pass

    def _play_stop_sound(self):
        try:
            from bt_utils.resource_manager import get_resource_manager
            rm = get_resource_manager()
            reversed_path = rm.get_stop_sound_path()
            
            if reversed_path:
                from bt_utils.alarm import AlarmPlayer
                player = AlarmPlayer()
                player.play(sound_path=reversed_path, volume=70, wait_complete=False)
        except Exception:
            pass

    def _on_node_status(self, node_id: str, status: str):
        from .node_item import NodeExecutionStatus
        status_map = {
            "running": NodeExecutionStatus.RUNNING,
            "success": NodeExecutionStatus.SUCCESS,
            "failure": NodeExecutionStatus.FAILURE,
            "aborted": NodeExecutionStatus.ABORTED,
            "idle": NodeExecutionStatus.IDLE,
        }
        node_status = status_map.get(status, NodeExecutionStatus.IDLE)
        self.after(0, lambda: self.canvas.set_node_status(node_id, node_status))

    def _on_engine_status_change(self, status: str, node_status: NodeStatus = None):
        if status == "completed":
            self.toolbar.set_running(False)
    
    def _set_modified(self, modified: bool):
        self._modified = modified
    
    def get_tree_data(self) -> Dict[str, Any]:
        return self.canvas.get_tree_data()
    
    def set_tree_data(self, data: Dict[str, Any]):
        self.canvas.load_tree(data)
    
    def _init_autosave(self):
        self._autosave_manager = AutoSaveManager(
            get_data_func=self.canvas.get_tree_data if hasattr(self, 'canvas') else lambda: {},
            on_save_callback=self._on_autosave_complete,
            autosave_dir=self.BACKUP_DIR,
            get_file_path_func=lambda: self.file_path
        )
        
        self._crash_recovery_handler = CrashRecoveryHandler(
            get_data_func=self.canvas.get_tree_data if hasattr(self, 'canvas') else lambda: {},
            recovery_dir=self.RECOVERY_DIR,
            log_func=print
        )
        self._crash_recovery_handler.install()
        
    def _start_autosave(self):
        if self._autosave_manager:
            self._autosave_manager.start()
    
    def _on_autosave_complete(self, success: bool):
        if not success:
            print("[WARN] 自动保存失败")
    
    def on_content_changed(self):
        if self._autosave_manager:
            self._autosave_manager.on_content_changed()
    
    def _check_crash_recovery(self):
        if not hasattr(self, '_crash_recovery_handler'):
            return
        
        if not self._crash_recovery_handler.has_crash_recovery():
            return
        
        crash_info = self._crash_recovery_handler.get_latest_crash_info()
        if not crash_info:
            return
        
        result = messagebox.askyesno(
            "崩溃恢复",
            f"检测到上次未正常关闭的会话:\n"
            f"时间: {crash_info.get('crash_time', '未知')}\n"
            f"异常: {crash_info.get('crash_type', '未知')}\n\n"
            f"是否恢复该会话？"
        )
        
        if result:
            data = self._crash_recovery_handler.load_crash_file(crash_info["path"])
            if data:
                self.canvas.load_tree(data)
                self._set_modified(True)
                print("[OK] 已自动恢复上次未保存的会话")
        
        self._crash_recovery_handler.delete_crash_file(crash_info["path"])
    
    def destroy(self):
        if self._autosave_manager:
            self._autosave_manager.stop()
            self._autosave_manager.save_now()
        
        if hasattr(self, '_crash_recovery_handler'):
            self._crash_recovery_handler.uninstall()
        
        if hasattr(self, 'log_panel') and self.log_panel:
            self.log_panel.destroy()
        
        super().destroy()
