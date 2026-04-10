import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERSION = "v1.0.0"

import customtkinter as ctk
from bt_gui.app import BehaviorTreeApp
from bt_core.registry import register_all_nodes


def main():
    register_all_nodes()
    
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = BehaviorTreeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
