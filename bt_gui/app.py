import customtkinter as ctk
from typing import Optional
import os
import json

from .theme import Theme, init_theme
from .bt_editor import BehaviorTreeEditor
from .script_tab import ScriptTab
from .settings_tab import SettingsTab
from bt_utils.config_manager import ConfigManager


class BehaviorTreeApp(ctk.CTk):
    CONFIG_FILE_NAME = "bt_editor_config.json"
    
    def __init__(self):
        init_theme()
        
        super().__init__()
        
        self._dark_colors = Theme.get_dark_colors()
        
        self._config_path = self._get_config_path()
        
        self.title("行为树编辑器")
        self.geometry("1280x800")
        self.minsize(800, 600)
        
        self.configure(fg_color=self._dark_colors['bg_primary'])
        
        self._set_icon()
        
        self._load_config()
        
        self._create_ui()
        self._setup_shortcuts()
        
        self._restore_last_file()
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _get_config_path(self) -> str:
        """获取配置文件路径"""
        config_dir = os.path.join(os.path.expanduser("~"), ".autodoor_bt")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, self.CONFIG_FILE_NAME)
    
    def _load_config(self):
        """加载配置"""
        if os.path.exists(self._config_path):
            ConfigManager.load_from_file(self._config_path)
    
    def _save_config(self):
        """保存配置"""
        try:
            if hasattr(self, 'behavior_tree') and self.behavior_tree:
                file_path = self.behavior_tree.file_path
                if file_path:
                    ConfigManager.set_last_file_path(file_path)
            
            ConfigManager.save_to_file(self._config_path)
        except Exception as e:
            print(f"[WARN] 保存配置失败: {e}")
    
    def _restore_last_file(self):
        """恢复上次打开的文件"""
        last_file = ConfigManager.get_last_file_path()
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
    
    def _on_close(self):
        self._save_config()
        if hasattr(self, 'behavior_tree') and self.behavior_tree:
            self.behavior_tree.destroy()
        self.destroy()


def create_app() -> BehaviorTreeApp:
    return BehaviorTreeApp()
