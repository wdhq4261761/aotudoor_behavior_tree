import os
import customtkinter as ctk
from tkinter import filedialog
from ..theme import Theme


class NewProjectDialog(ctk.CTkToplevel):
    """新建项目对话框"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.result = None
        
        self.title("新建项目")
        self.geometry("500x400")
        self.resizable(False, False)
        
        self.transient(master)
        self.grab_set()
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(fg_color=self._dark_colors['bg_primary'])
        
        self._create_ui()
        
        self._center_window()
    
    def _center_window(self):
        """将窗口居中"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_ui(self):
        """创建界面"""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="创建新项目",
            font=("Arial", 18, "bold"),
            text_color=self._dark_colors['text_primary']
        )
        title_label.pack(pady=(0, 20))
        
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="x", pady=10)
        
        name_label = ctk.CTkLabel(
            form_frame,
            text="项目名称:",
            font=("Arial", 12),
            text_color=self._dark_colors['text_primary']
        )
        name_label.grid(row=0, column=0, sticky="w", pady=5)
        
        self.name_entry = ctk.CTkEntry(
            form_frame,
            width=350,
            height=35,
            placeholder_text="输入项目名称"
        )
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        location_label = ctk.CTkLabel(
            form_frame,
            text="保存位置:",
            font=("Arial", 12),
            text_color=self._dark_colors['text_primary']
        )
        location_label.grid(row=1, column=0, sticky="w", pady=5)
        
        location_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        location_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        self.location_entry = ctk.CTkEntry(
            location_frame,
            width=270,
            height=35,
            placeholder_text="选择项目保存位置"
        )
        self.location_entry.pack(side="left", fill="x", expand=True)
        
        browse_button = ctk.CTkButton(
            location_frame,
            text="浏览...",
            width=70,
            height=35,
            command=self._browse_location
        )
        browse_button.pack(side="left", padx=(10, 0))
        
        desc_label = ctk.CTkLabel(
            form_frame,
            text="项目描述:",
            font=("Arial", 12),
            text_color=self._dark_colors['text_primary']
        )
        desc_label.grid(row=2, column=0, sticky="w", pady=5)
        
        self.desc_entry = ctk.CTkEntry(
            form_frame,
            width=350,
            height=35,
            placeholder_text="可选，输入项目描述"
        )
        self.desc_entry.grid(row=2, column=1, padx=10, pady=5)
        
        script_label = ctk.CTkLabel(
            form_frame,
            text="导入脚本:",
            font=("Arial", 12),
            text_color=self._dark_colors['text_primary']
        )
        script_label.grid(row=3, column=0, sticky="w", pady=5)
        
        script_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        script_frame.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        self.script_entry = ctk.CTkEntry(
            script_frame,
            width=270,
            height=35,
            placeholder_text="可选，选择要导入的旧脚本"
        )
        self.script_entry.pack(side="left", fill="x", expand=True)
        
        browse_script_button = ctk.CTkButton(
            script_frame,
            text="浏览...",
            width=70,
            height=35,
            command=self._browse_script
        )
        browse_script_button.pack(side="left", padx=(10, 0))
        
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        
        create_button = ctk.CTkButton(
            button_frame,
            text="创建",
            width=100,
            height=35,
            fg_color=self._dark_colors['primary'],
            hover_color=self._dark_colors['primary_hover'],
            text_color="white",
            font=("Arial", 12, "bold"),
            command=self._on_create
        )
        create_button.pack(side="left", padx=10)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="取消",
            width=100,
            height=35,
            fg_color=self._dark_colors['bg_tertiary'],
            hover_color=self._dark_colors['border'],
            text_color=self._dark_colors['text_primary'],
            font=("Arial", 12),
            command=self._on_cancel
        )
        cancel_button.pack(side="left", padx=10)
        
        self.name_entry.focus()
    
    def _browse_location(self):
        """浏览保存位置"""
        location = filedialog.askdirectory(title="选择项目保存位置")
        if location:
            self.location_entry.delete(0, "end")
            self.location_entry.insert(0, location)
    
    def _browse_script(self):
        """浏览脚本文件"""
        script_path = filedialog.askopenfilename(
            title="选择要导入的脚本",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if script_path:
            self.script_entry.delete(0, "end")
            self.script_entry.insert(0, script_path)
    
    def _on_create(self):
        """创建项目"""
        name = self.name_entry.get().strip()
        location = self.location_entry.get().strip()
        description = self.desc_entry.get().strip()
        script_path = self.script_entry.get().strip()
        
        if not name:
            from tkinter import messagebox
            messagebox.showwarning("提示", "请输入项目名称")
            return
        
        if not location:
            from tkinter import messagebox
            messagebox.showwarning("提示", "请选择保存位置")
            return
        
        self.result = {
            "name": name,
            "location": location,
            "description": description,
            "script_path": script_path if script_path else None
        }
        
        self.destroy()
    
    def _on_cancel(self):
        """取消"""
        self.result = None
        self.destroy()
