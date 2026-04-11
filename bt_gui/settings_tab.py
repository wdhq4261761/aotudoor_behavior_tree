import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os

from .theme import Theme
from .widgets import CardFrame, AnimatedButton, create_section_title, create_divider
from bt_utils.resource_manager import ResourceManager


class SettingsTab(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(fg_color=self._dark_colors['bg_primary'], corner_radius=0)
        
        self._init_variables()
        self._create_ui()
    
    def _init_variables(self):
        default_alarm_sound = ResourceManager().get_alarm_sound_path()
        if not os.path.exists(default_alarm_sound):
            default_alarm_sound = ""
        
        self.alarm_sound_path = tk.StringVar(value=default_alarm_sound)
        self.alarm_volume = tk.IntVar(value=70)
        self.alarm_volume_str = tk.StringVar(value="70")
        
        default_project_path = self._get_default_project_path()
        self.default_project_path = tk.StringVar(value=default_project_path)
        
        self.start_shortcut_var = tk.StringVar(value="F10")
        self.stop_shortcut_var = tk.StringVar(value="F12")
        self.record_hotkey_var = tk.StringVar(value="F11")
    
    def _get_default_project_path(self) -> str:
        """获取默认项目保存路径
        
        Returns:
            默认项目保存路径
        """
        from config.settings_manager import SettingsManager
        settings_manager = SettingsManager()
        saved_path = settings_manager.get("default_project_path", "")
        
        if saved_path and os.path.exists(saved_path):
            return saved_path
        
        return SettingsManager.get_default_workspace_path()
    
    def _create_ui(self):
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=Theme.DIMENSIONS['spacing_md'], pady=Theme.DIMENSIONS['spacing_md'])
        
        self._create_project_section(scroll_frame)
        self._create_ocr_section(scroll_frame)
        self._create_alarm_section(scroll_frame)
        self._create_shortcut_section(scroll_frame)
    
    def _create_project_section(self, parent):
        project_frame = CardFrame(parent)
        project_frame.pack(fill="x", pady=(0, Theme.DIMENSIONS['spacing_md']))
        
        project_header = ctk.CTkFrame(project_frame, fg_color="transparent")
        project_header.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_md'], Theme.DIMENSIONS['spacing_sm']))
        create_section_title(project_header, "项目设置", level=1).pack(side="left")
        
        create_divider(project_frame)
        
        project_row = ctk.CTkFrame(project_frame, fg_color="transparent")
        project_row.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_sm'], Theme.DIMENSIONS['spacing_md']))
        
        ctk.CTkLabel(project_row, text="默认保存位置:", font=Theme.get_font("sm"), text_color=self._dark_colors['text_secondary']).pack(side="left")
        
        self.project_path_entry = ctk.CTkEntry(
            project_row, 
            textvariable=self.default_project_path, 
            height=28, 
            state="disabled",
            fg_color=self._dark_colors['bg_tertiary'],
            text_color=self._dark_colors['text_primary']
        )
        self.project_path_entry.pack(side="left", fill="x", expand=True, padx=(Theme.DIMENSIONS['spacing_sm'], Theme.DIMENSIONS['spacing_sm']))
        
        self.browse_project_btn = AnimatedButton(
            project_row, 
            text="浏览", 
            font=Theme.get_font("xs"), 
            width=50, 
            height=28,
            corner_radius=Theme.DIMENSIONS['button_corner_radius'], 
            fg_color=Theme.COLORS['primary'],
            hover_color=Theme.COLORS['primary_hover'],
            command=self._browse_project_path
        )
        self.browse_project_btn.pack(side="left")
    
    def _create_ocr_section(self, parent):
        """创建OCR信息区域"""
        ocr_frame = CardFrame(parent)
        ocr_frame.pack(fill="x", pady=(0, Theme.DIMENSIONS['spacing_md']))
        
        ocr_header = ctk.CTkFrame(ocr_frame, fg_color="transparent")
        ocr_header.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_md'], Theme.DIMENSIONS['spacing_sm']))
        create_section_title(ocr_header, "OCR 引擎信息", level=1).pack(side="left")
        
        create_divider(ocr_frame)
        
        info_frame = ctk.CTkFrame(ocr_frame, fg_color=self._dark_colors['bg_secondary'])
        info_frame.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_sm'], Theme.DIMENSIONS['spacing_md']))
        
        info_text = ctk.CTkLabel(
            info_frame,
            text="当前使用: RapidOCR\n基于ONNX Runtime，无需额外配置\n支持中英文识别，识别速度更快",
            font=Theme.get_font("sm"),
            text_color=self._dark_colors['text_secondary'],
            justify="left"
        )
        info_text.pack(padx=Theme.DIMENSIONS['spacing_md'], pady=Theme.DIMENSIONS['spacing_md'], anchor="w")
    
    def _create_alarm_section(self, parent):
        alarm_frame = CardFrame(parent)
        alarm_frame.pack(fill="x", pady=(0, Theme.DIMENSIONS['spacing_md']))
        
        alarm_header = ctk.CTkFrame(alarm_frame, fg_color="transparent")
        alarm_header.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_md'], Theme.DIMENSIONS['spacing_sm']))
        create_section_title(alarm_header, "报警设置", level=1).pack(side="left")
        
        create_divider(alarm_frame)
        
        alarm_row1 = ctk.CTkFrame(alarm_frame, fg_color="transparent")
        alarm_row1.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=Theme.DIMENSIONS['spacing_sm'])
        
        ctk.CTkLabel(alarm_row1, text="声音:", font=Theme.get_font("sm"), text_color=self._dark_colors['text_secondary']).pack(side="left")
        
        alarm_sound_entry = ctk.CTkEntry(
            alarm_row1, 
            textvariable=self.alarm_sound_path, 
            height=28, 
            state="disabled",
            fg_color=self._dark_colors['bg_tertiary'],
            text_color=self._dark_colors['text_primary']
        )
        alarm_sound_entry.pack(side="left", fill="x", expand=True, padx=(Theme.DIMENSIONS['spacing_sm'], Theme.DIMENSIONS['spacing_sm']))
        
        alarm_sound_btn = AnimatedButton(
            alarm_row1, 
            text="浏览", 
            font=Theme.get_font("xs"), 
            width=50, 
            height=28,
            corner_radius=Theme.DIMENSIONS['button_corner_radius'], 
            fg_color=Theme.COLORS['primary'],
            hover_color=Theme.COLORS['primary_hover'],
            command=self._browse_alarm_sound
        )
        alarm_sound_btn.pack(side="left")
        
        alarm_row2 = ctk.CTkFrame(alarm_frame, fg_color="transparent")
        alarm_row2.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_sm'], Theme.DIMENSIONS['spacing_md']))
        
        ctk.CTkLabel(alarm_row2, text="音量:", font=Theme.get_font("sm"), text_color=self._dark_colors['text_secondary']).pack(side="left")
        
        def update_volume_display(*args):
            self.alarm_volume_str.set(str(self.alarm_volume.get()))
        
        self.alarm_volume.trace_add("write", update_volume_display)
        
        volume_slider = ctk.CTkSlider(
            alarm_row2, 
            from_=0, 
            to=100, 
            variable=self.alarm_volume, 
            width=200,
            progress_color=Theme.COLORS['primary'],
            button_color=Theme.COLORS['text_primary']
        )
        volume_slider.pack(side="left", padx=(Theme.DIMENSIONS['spacing_sm'], Theme.DIMENSIONS['spacing_sm']))
        
        volume_label = ctk.CTkLabel(
            alarm_row2, 
            textvariable=self.alarm_volume_str, 
            font=Theme.get_font("sm"), 
            width=40,
            text_color=self._dark_colors['text_primary']
        )
        volume_label.pack(side="left")
    
    def _create_shortcut_section(self, parent):
        shortcut_frame = CardFrame(parent)
        shortcut_frame.pack(fill="x", pady=(0, Theme.DIMENSIONS['spacing_md']))
        
        shortcut_header = ctk.CTkFrame(shortcut_frame, fg_color="transparent")
        shortcut_header.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_md'], Theme.DIMENSIONS['spacing_sm']))
        create_section_title(shortcut_header, "快捷键设置", level=1).pack(side="left")
        
        create_divider(shortcut_frame)
        
        shortcuts = [
            ("开始运行:", "F10", self.start_shortcut_var),
            ("停止运行:", "F12", self.stop_shortcut_var),
            ("录制按钮:", "F11", self.record_hotkey_var)
        ]
        
        for label, default, var in shortcuts:
            row = ctk.CTkFrame(shortcut_frame, fg_color="transparent")
            row.pack(fill="x", padx=Theme.DIMENSIONS['spacing_md'], pady=Theme.DIMENSIONS['spacing_sm'])
            
            ctk.CTkLabel(row, text=label, font=Theme.get_font("sm"), text_color=self._dark_colors['text_secondary']).pack(side="left")
            
            entry = ctk.CTkEntry(
                row, 
                textvariable=var, 
                width=80, 
                height=24, 
                state="disabled",
                fg_color=self._dark_colors['bg_tertiary'],
                text_color=self._dark_colors['text_primary']
            )
            entry.pack(side="left", padx=(Theme.DIMENSIONS['spacing_sm'], Theme.DIMENSIONS['spacing_xs']))
            
            btn = AnimatedButton(
                row, 
                text="修改", 
                font=Theme.get_font("xs"), 
                width=40, 
                height=24, 
                corner_radius=Theme.DIMENSIONS['button_corner_radius'],
                fg_color=Theme.COLORS['primary'], 
                hover_color=Theme.COLORS['primary_hover']
            )
            btn.configure(command=lambda e=entry, b=btn: self._start_key_listening(e, b))
            btn.pack(side="left")
        
        ctk.CTkFrame(shortcut_frame, height=6, fg_color="transparent").pack()
    
    def _browse_project_path(self):
        folder_path = filedialog.askdirectory(
            title="选择默认项目保存位置"
        )
        if folder_path:
            self.default_project_path.set(folder_path)
            self._ensure_workspace_exists()
    
    def _ensure_workspace_exists(self):
        """确保workspace文件夹存在"""
        workspace_path = self.default_project_path.get()
        if workspace_path:
            try:
                os.makedirs(workspace_path, exist_ok=True)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建workspace文件夹: {str(e)}")
    
    def _browse_alarm_sound(self):
        file_path = filedialog.askopenfilename(
            title="选择报警声音文件",
            filetypes=[("音频文件", "*.mp3 *.wav *.ogg"), ("所有文件", "*.*")]
        )
        if file_path:
            self.alarm_sound_path.set(file_path)
    
    def _start_key_listening(self, entry, btn):
        btn.configure(text="请按键...", fg_color=Theme.COLORS['warning'])
        
        def on_key_press(event):
            key_name = event.keysym
            
            key_mappings = {
                "Control_L": "ctrl", "Control_R": "ctrl",
                "Alt_L": "alt", "Alt_R": "alt",
                "Shift_L": "shift", "Shift_R": "shift",
                "Super_L": "win", "Super_R": "win",
                "Return": "enter", "BackSpace": "backspace",
                "Tab": "tab", "Escape": "escape",
                "space": "space", "Delete": "delete",
                "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4",
                "F5": "F5", "F6": "F6", "F7": "F7", "F8": "F8",
                "F9": "F9", "F10": "F10", "F11": "F11", "F12": "F12",
            }
            
            if key_name in key_mappings:
                key_name = key_mappings[key_name]
            elif len(key_name) == 1:
                key_name = key_name.upper()
            
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.insert(0, key_name)
            entry.configure(state="disabled")
            
            btn.configure(text="修改", fg_color=Theme.COLORS['primary'])
            
            toplevel = self.winfo_toplevel()
            toplevel.unbind("<KeyPress>")
            
            self._update_editor_shortcuts()
            
            return "break"
        
        toplevel = self.winfo_toplevel()
        toplevel.bind("<KeyPress>", on_key_press)
        
        def reset_listening():
            try:
                btn.configure(text="修改", fg_color=Theme.COLORS['primary'])
                toplevel.unbind("<KeyPress>")
            except Exception:
                pass
        
        self.after(10000, reset_listening)
    
    def _update_editor_shortcuts(self):
        """更新编辑器的快捷键绑定"""
        try:
            if hasattr(self.app, 'behavior_tree') and hasattr(self.app.behavior_tree, 'update_run_shortcuts'):
                start_key = self.start_shortcut_var.get()
                stop_key = self.stop_shortcut_var.get()
                record_key = self.record_hotkey_var.get()
                self.app.behavior_tree.update_run_shortcuts(start_key, stop_key, record_key)
        except Exception:
            pass
    
    def get_settings(self):
        return {
            "alarm_sound_path": self.alarm_sound_path.get(),
            "alarm_volume": self.alarm_volume.get(),
            "default_project_path": self.default_project_path.get(),
            "shortcuts": {
                "start": self.start_shortcut_var.get(),
                "stop": self.stop_shortcut_var.get(),
                "record": self.record_hotkey_var.get()
            }
        }
    
    def load_settings(self, settings):
        default_alarm_sound = ResourceManager().get_alarm_sound_path()
        if not os.path.exists(default_alarm_sound):
            default_alarm_sound = ""
        
        default_project_path = self._get_default_project_path()
        
        if "alarm_sound_path" in settings and settings["alarm_sound_path"]:
            if os.path.exists(settings["alarm_sound_path"]):
                self.alarm_sound_path.set(settings["alarm_sound_path"])
            else:
                self.alarm_sound_path.set(default_alarm_sound)
        else:
            self.alarm_sound_path.set(default_alarm_sound)
        
        if "alarm_volume" in settings:
            self.alarm_volume.set(settings["alarm_volume"])
            self.alarm_volume_str.set(str(settings["alarm_volume"]))
        
        if "default_project_path" in settings and settings["default_project_path"]:
            if os.path.exists(settings["default_project_path"]):
                self.default_project_path.set(settings["default_project_path"])
            else:
                self.default_project_path.set(default_project_path)
        else:
            self.default_project_path.set(default_project_path)
        
        self._ensure_workspace_exists()
        
        if "shortcuts" in settings:
            shortcuts = settings["shortcuts"]
            if "start" in shortcuts:
                self.start_shortcut_var.set(shortcuts["start"])
            if "stop" in shortcuts:
                self.stop_shortcut_var.set(shortcuts["stop"])
            if "record" in shortcuts:
                self.record_hotkey_var.set(shortcuts["record"])
