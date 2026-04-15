import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERSION = "V1.1.7"

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
    except Exception:
        pass


def check_vcredist():
    """检查 Visual C++ Redistributable 运行时库"""
    try:
        import onnxruntime
        return True
    except ImportError as e:
        if "DLL load failed" in str(e) or "onnxruntime_pybind11_state" in str(e):
            return False
        raise
    except Exception:
        return False


def initialize_ocr():
    """初始化OCR引擎"""
    try:
        if not check_vcredist():
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            
            messagebox.showwarning(
                "缺少运行时库",
                "程序检测到缺少 Visual C++ Redistributable 运行时库。\n\n"
                "OCR 相关功能将无法使用。\n\n"
                "请下载并安装：\n"
                "https://aka.ms/vs/17/release/vc_redist.x64.exe\n\n"
                "安装后重启程序即可使用 OCR 功能。\n\n"
                "其他功能不受影响，可正常使用。"
            )
            
            root.destroy()
            
            from bt_utils.ocr_manager import OCRManager
            OCRManager.set_unavailable("缺少 Visual C++ Redistributable 运行时库")
            
            return False
        
        from bt_utils.ocr_manager import OCRManager
        OCRManager.initialize()
        return True
        
    except Exception as e:
        from bt_utils.ocr_manager import OCRManager
        OCRManager.set_unavailable(str(e))
        
        return False


def initialize_input():
    """初始化输入控制器（预加载DD虚拟键盘）"""
    try:
        from bt_utils.input_controller_factory import InputController
        # 预加载输入控制器，会自动加载DD虚拟键盘（如果启用）
        InputController()
        return True
    except Exception:
        return False


def main():
    ensure_workspace_exists()
    
    initialize_ocr()
    initialize_input()  # 预加载输入控制器
    
    register_all_nodes()
    
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = BehaviorTreeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
