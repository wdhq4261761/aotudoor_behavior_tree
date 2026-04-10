import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERSION = "v1.0.1"

import customtkinter as ctk
from bt_gui.app import BehaviorTreeApp
from bt_core.registry import register_all_nodes


def ensure_workspace_exists():
    """确保workspace文件夹存在"""
    from config.settings_manager import SettingsManager
    
    settings_manager = SettingsManager()
    saved_path = settings_manager.get("default_project_path", "")
    
    if saved_path and os.path.exists(saved_path):
        return
    
    workspace_dir = SettingsManager.get_default_workspace_path()
    
    try:
        os.makedirs(workspace_dir, exist_ok=True)
    except Exception as e:
        print(f"[WARN] 无法创建workspace文件夹: {e}")


def main():
    ensure_workspace_exists()
    
    register_all_nodes()
    
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = BehaviorTreeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
