import customtkinter as ctk
from typing import Optional
import os
from tkinter import messagebox

from .theme import Theme, init_theme
from .bt_editor import BehaviorTreeEditor
from .script_tab import ScriptTab
from .settings_tab import SettingsTab
from config.settings_manager import SettingsManager


def _get_app_title() -> str:
    """获取应用标题，包含版本号"""
    try:
        from main import VERSION
        return f"autodoor - 行为树 {VERSION}"
    except ImportError:
        return "autodoor - 行为树"


class BehaviorTreeApp(ctk.CTk):
    
    def __init__(self):
        init_theme()
        
        super().__init__()
        
        self._dark_colors = Theme.get_dark_colors()
        
        self._settings = SettingsManager.get_instance()
        
        self.title(_get_app_title())
        self.geometry("1280x800")
        self.minsize(800, 600)
        
        self.configure(fg_color=self._dark_colors['bg_primary'])
        
        self._set_icon()
        
        self._create_ui()
        self._setup_shortcuts()
        
        self._restore_last_file()
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _restore_last_file(self):
        """恢复上次打开的文件"""
        last_file = self._settings.get_last_file_path()
        if last_file and os.path.exists(last_file):
            try:
                if hasattr(self, 'behavior_tree') and self.behavior_tree:
                    self.behavior_tree.load_tree(last_file)
                    self._update_window_title()
            except Exception:
                pass
    
    def _update_window_title(self):
        """更新窗口标题，显示项目名称"""
        project_name = None
        if hasattr(self.behavior_tree, 'project_root') and self.behavior_tree.project_root:
            project_name = os.path.basename(self.behavior_tree.project_root)
        
        if project_name:
            try:
                from main import VERSION
                self.title(f"autodoor - 行为树 {VERSION} - {project_name}")
            except ImportError:
                self.title(f"autodoor - 行为树 - {project_name}")
        else:
            self.title(_get_app_title())
    
    def _set_icon(self):
        """设置应用图标"""
        try:
            from bt_utils.resource_manager import get_resource_manager
            rm = get_resource_manager()
            icon_path = rm.get_icon_path()
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            print(f"[WARN] 设置图标失败: {e}")
    
    def _create_ui(self):
        self._create_tabview()
    
    def _create_tabview(self):
        self.main_tabview = ctk.CTkTabview(
            self,
            fg_color=self._dark_colors['bg_primary'],
            segmented_button_fg_color=self._dark_colors['bg_secondary'],
            segmented_button_selected_color=self._dark_colors['primary'],
            segmented_button_selected_hover_color=self._dark_colors['primary_hover'],
            segmented_button_unselected_color=self._dark_colors['bg_tertiary'],
            segmented_button_unselected_hover_color=self._dark_colors['border']
        )
        self.main_tabview.pack(fill="both", expand=True, padx=Theme.DIMENSIONS['spacing_sm'], pady=Theme.DIMENSIONS['spacing_sm'])
        
        bt_tab = self.main_tabview.add("🌲 行为树编辑器")
        script_tab = self.main_tabview.add("📝 脚本录制")
        settings_tab = self.main_tabview.add("⚙ 设置")
        
        self.behavior_tree = BehaviorTreeEditor(bt_tab, self)
        self.behavior_tree.pack(fill="both", expand=True)
        
        self.script_editor = ScriptTab(script_tab, self)
        self.script_editor.pack(fill="both", expand=True)
        
        self.settings = SettingsTab(settings_tab, self)
        self.settings.pack(fill="both", expand=True)
        
        saved_settings = self._settings.get_all_settings()
        if saved_settings:
            self.settings.load_settings(saved_settings)
        
        self.main_tabview.set("🌲 行为树编辑器")
    
    def _setup_shortcuts(self):
        shortcuts = [
            ("<Control-z>", self._undo),
            ("<Control-y>", self._redo),
            ("<Control-Shift-Z>", self._redo),
            ("<Control-s>", self._save),
            ("<Control-Shift-S>", lambda: self._save(save_as=True)),
            ("<Control-o>", self._open),
            ("<Control-n>", self._new),
            ("<Delete>", self._delete),
            ("<BackSpace>", self._delete),
            ("<Control-c>", self._copy),
            ("<Control-v>", self._paste),
            ("<Control-x>", self._cut),
            ("<Control-d>", self._duplicate),
        ]
        
        for key, callback in shortcuts:
            self.bind(key, lambda e, cb=callback: self._handle_shortcut(e, cb))
    
    def _handle_shortcut(self, event, callback):
        if callable(callback):
            callback()
        return "break"
    
    def _undo(self):
        if hasattr(self.behavior_tree, 'undo'):
            self.behavior_tree.undo()
    
    def _redo(self):
        if hasattr(self.behavior_tree, 'redo'):
            self.behavior_tree.redo()
    
    def _save(self, save_as=False):
        current_tab = self.main_tabview.get()
        if "行为树" in current_tab:
            if hasattr(self.behavior_tree, 'save_tree'):
                self.behavior_tree.save_tree(save_as=save_as)
        elif "脚本" in current_tab:
            if hasattr(self.script_editor, '_save_script'):
                self.script_editor._save_script()
    
    def _open(self):
        current_tab = self.main_tabview.get()
        if "行为树" in current_tab:
            if hasattr(self.behavior_tree, 'load_tree'):
                self.behavior_tree.load_tree()
        elif "脚本" in current_tab:
            if hasattr(self.script_editor, '_load_script'):
                self.script_editor._load_script()
    
    def _new(self):
        current_tab = self.main_tabview.get()
        if "行为树" in current_tab:
            if hasattr(self.behavior_tree, 'new_tree'):
                self.behavior_tree.new_tree()
        elif "脚本" in current_tab:
            if hasattr(self.script_editor, '_new_script'):
                self.script_editor._new_script()
    
    def _delete(self):
        focused = self.focus_get()
        if focused:
            widget_type = str(type(focused).__name__)
            if widget_type in ("CTkEntry", "Entry", "CTkTextbox", "Text"):
                return
        current_tab = self.main_tabview.get()
        if "行为树" in current_tab:
            if hasattr(self.behavior_tree, '_delete_selected'):
                self.behavior_tree._delete_selected()
    
    def _copy(self):
        current_tab = self.main_tabview.get()
        if "行为树" in current_tab:
            if hasattr(self.behavior_tree, '_copy_selected'):
                self.behavior_tree._copy_selected()
    
    def _paste(self):
        current_tab = self.main_tabview.get()
        if "行为树" in current_tab:
            if hasattr(self.behavior_tree, '_paste_selected'):
                self.behavior_tree._paste_selected()
    
    def _cut(self):
        current_tab = self.main_tabview.get()
        if "行为树" in current_tab:
            if hasattr(self.behavior_tree, '_cut_selected'):
                self.behavior_tree._cut_selected()
    
    def _duplicate(self):
        current_tab = self.main_tabview.get()
        if "行为树" in current_tab:
            if hasattr(self.behavior_tree, '_duplicate_selected'):
                self.behavior_tree._duplicate_selected()
    
    def _on_close(self):
        if hasattr(self, 'behavior_tree') and self.behavior_tree:
            file_path = self.behavior_tree.file_path
            if file_path:
                self._settings.set_last_file_path(file_path)
            
            if hasattr(self.behavior_tree, '_modified') and self.behavior_tree._modified:
                result = messagebox.askyesnocancel(
                    "未保存的改动",
                    "当前项目有未保存的改动。\n\n是否保存？"
                )
                
                if result is None:
                    return
                elif result:
                    self.behavior_tree.save_tree()
            
            self.behavior_tree.destroy()
        
        self._settings.save_settings()
        self.destroy()


def create_app() -> BehaviorTreeApp:
    return BehaviorTreeApp()
