import customtkinter as ctk
from typing import Optional
import os
from tkinter import messagebox

from .theme import Theme, init_theme
from .bt_editor import BehaviorTreeEditor
from .script_tab import ScriptTab
from .settings_tab import SettingsTab
from config.settings_manager import SettingsManager


class BehaviorTreeApp(ctk.CTk):
    
    def __init__(self):
        init_theme()
        
        super().__init__()
        
        self._dark_colors = Theme.get_dark_colors()
        
        self._settings = SettingsManager.get_instance()
        
        self.title("行为树编辑器")
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
                    print(f"[OK] 已自动加载上次文件: {last_file}")
            except Exception as e:
                print(f"[WARN] 自动加载上次文件失败: {e}")
    
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
        
        self.main_tabview.set("🌲 行为树编辑器")
    
    def _setup_shortcuts(self):
        self.bind("<Control-z>", lambda e: self._undo())
        self.bind("<Control-y>", lambda e: self._redo())
        self.bind("<Control-s>", lambda e: self._save())
        self.bind("<Control-o>", lambda e: self._open())
        self.bind("<Control-n>", lambda e: self._new())
        self.bind("<Delete>", lambda e: self._delete())
        
        start_key = self._settings.get("shortcuts.start", "F10")
        stop_key = self._settings.get("shortcuts.stop", "F12")
        record_key = self._settings.get("shortcuts.record", "F11")
        
        self.bind(f"<{start_key}>", lambda e: self._start_behavior_tree())
        self.bind(f"<{stop_key}>", lambda e: self._stop_behavior_tree())
        self.bind(f"<{record_key}>", lambda e: self._toggle_recording())
    
    def _undo(self):
        if hasattr(self.behavior_tree, 'undo'):
            self.behavior_tree.undo()
    
    def _redo(self):
        if hasattr(self.behavior_tree, 'redo'):
            self.behavior_tree.redo()
    
    def _save(self):
        current_tab = self.main_tabview.get()
        if "行为树" in current_tab:
            if hasattr(self.behavior_tree, 'save_tree'):
                self.behavior_tree.save_tree()
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
        current_tab = self.main_tabview.get()
        if "行为树" in current_tab:
            if hasattr(self.behavior_tree, '_delete_selected'):
                self.behavior_tree._delete_selected()
    
    def _start_behavior_tree(self):
        """开始运行行为树"""
        if hasattr(self.behavior_tree, 'start_tree'):
            self.behavior_tree.start_tree()
    
    def _stop_behavior_tree(self):
        """停止运行行为树"""
        if hasattr(self.behavior_tree, 'stop_tree'):
            self.behavior_tree.stop_tree()
    
    def _toggle_recording(self):
        """切换录制状态"""
        if hasattr(self.script_editor, '_is_recording'):
            if self.script_editor._is_recording:
                self.script_editor._stop_recording()
            else:
                self.script_editor._start_recording()
    
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
