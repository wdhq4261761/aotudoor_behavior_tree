import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os

from .theme import Theme
from .widgets import CardFrame, AnimatedButton, NumericEntry, create_divider


def center_window_on_parent(window, parent):
    window.update_idletasks()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    x = parent_x + (parent_width - window_width) // 2
    y = parent_y + (parent_height - window_height) // 2
    window.geometry(f"+{x}+{y}")

def askyesno_centered(parent, title, message):
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)
    
    result = [False]
    
    frame = ctk.CTkFrame(dialog, fg_color='transparent')
    frame.pack(fill='both', expand=True, padx=20, pady=15)
    
    label = ctk.CTkLabel(frame, text=message, font=Theme.get_font('base'), wraplength=300)
    label.pack(pady=(0, 15))
    
    btn_frame = ctk.CTkFrame(frame, fg_color='transparent')
    btn_frame.pack(fill='x')
    
    def on_yes():
        result[0] = True
        dialog.destroy()
    
    def on_no():
        result[0] = False
        dialog.destroy()
    
    yes_btn = ctk.CTkButton(btn_frame, text='是', width=80, command=on_yes,
                            fg_color=Theme.COLORS['success'], hover_color='#16A34A')
    yes_btn.pack(side='left', padx=10, expand=True)
    
    no_btn = ctk.CTkButton(btn_frame, text='否', width=80, command=on_no,
                           fg_color=Theme.COLORS['error'], hover_color='#DC2626')
    no_btn.pack(side='left', padx=10, expand=True)
    
    dialog.protocol("WM_DELETE_WINDOW", on_no)
    
    center_window_on_parent(dialog, parent)
    
    dialog.wait_window()
    return result[0]


class ScriptTab(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        self.file_path = None
        self._modified = False
        self.script_original_content = ""
        
        self._dark_colors = Theme.get_dark_colors()
        self.configure(fg_color=self._dark_colors['bg_primary'], corner_radius=0)
        
        self._init_variables()
        self._create_ui()
    
    def _init_variables(self):
        self.key_var = tk.StringVar(value="1")
        self.key_type = tk.StringVar(value="KeyDown")
        self.key_count = tk.IntVar(value=1)
        
        self.delay_var = tk.StringVar(value="250")
        
        self.mouse_button_var = tk.StringVar(value="Left")
        self.mouse_action_var = tk.StringVar(value="Down")
        self.mouse_count_var = tk.IntVar(value=1)
        
        self.combo_key_var = tk.StringVar(value="1")
        self.combo_key_delay = tk.StringVar(value="2500")
        self.combo_after_delay = tk.StringVar(value="300")
        
        self.script_file_path_var = tk.StringVar(value="未保存")
    
    def _create_ui(self):
        main_container = ctk.CTkFrame(self, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=Theme.DIMENSIONS['spacing_md'], pady=Theme.DIMENSIONS['spacing_md'])
        
        left_frame = ctk.CTkFrame(main_container, fg_color='transparent')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, Theme.DIMENSIONS['spacing_sm']))
        
        self._create_key_command_card(left_frame)
        self._create_delay_command_card(left_frame)
        self._create_mouse_command_card(left_frame)
        self._create_combo_key_card(left_frame)
        self._create_control_card(left_frame)
        
        right_frame = ctk.CTkFrame(main_container, width=400)
        right_frame.pack(side='left', fill='both', expand=True)
        right_frame.pack_propagate(False)
        
        self._create_editor_tabview(right_frame)
    
    def _create_key_command_card(self, parent):
        key_card = CardFrame(parent)
        key_card.pack(fill='x', pady=(0, Theme.DIMENSIONS['spacing_sm']))
        
        key_header = ctk.CTkFrame(key_card, fg_color='transparent')
        key_header.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_md'], Theme.DIMENSIONS['spacing_xs']))
        ctk.CTkLabel(key_header, text='按键命令', font=Theme.get_font('base'), text_color=self._dark_colors['text_primary']).pack(side='left')
        
        create_divider(key_card)
        
        key_row = ctk.CTkFrame(key_card, fg_color='transparent')
        key_row.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_xs'], Theme.DIMENSIONS['spacing_md']))
        
        ctk.CTkLabel(key_row, text='按键:', font=Theme.get_font('xs'), text_color=self._dark_colors['text_secondary']).pack(side='left')
        
        self.key_entry = ctk.CTkEntry(key_row, width=50, height=24, state='disabled',
                                       textvariable=self.key_var,
                                       fg_color=self._dark_colors['bg_tertiary'],
                                       text_color=self._dark_colors['text_primary'])
        self.key_entry.pack(side='left', padx=(Theme.DIMENSIONS['spacing_xs'], Theme.DIMENSIONS['spacing_xs']))
        
        self.set_key_btn = AnimatedButton(key_row, text='修改', font=Theme.get_font('xs'), width=40, height=24, 
                                          corner_radius=Theme.DIMENSIONS['button_corner_radius'],
                                          fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                                          command=self._start_key_listening)
        self.set_key_btn.pack(side='left', padx=(0, Theme.DIMENSIONS['spacing_md']))
        
        ctk.CTkLabel(key_row, text='类型:', font=Theme.get_font('xs'), text_color=self._dark_colors['text_secondary']).pack(side='left', padx=(0, Theme.DIMENSIONS['spacing_xs']))
        
        from .widgets import create_bordered_option_menu
        create_bordered_option_menu(key_row, values=["KeyDown", "KeyUp"], variable=self.key_type, width=80, height=24)
        
        self.insert_key_btn = AnimatedButton(key_row, text='插入', font=Theme.get_font('xs'), width=50, height=24,
                                             corner_radius=Theme.DIMENSIONS['button_corner_radius'], 
                                             fg_color=Theme.COLORS['success'],
                                             hover_color='#16A34A',
                                             command=self._insert_key_command)
        self.insert_key_btn.pack(side='left', padx=(Theme.DIMENSIONS['spacing_sm'], 0))
    
    def _create_delay_command_card(self, parent):
        delay_card = CardFrame(parent)
        delay_card.pack(fill='x', pady=(0, Theme.DIMENSIONS['spacing_sm']))
        
        delay_header = ctk.CTkFrame(delay_card, fg_color='transparent')
        delay_header.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_md'], Theme.DIMENSIONS['spacing_xs']))
        ctk.CTkLabel(delay_header, text='延迟命令', font=Theme.get_font('base'), text_color=self._dark_colors['text_primary']).pack(side='left')
        
        create_divider(delay_card)
        
        delay_row = ctk.CTkFrame(delay_card, fg_color='transparent')
        delay_row.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_xs'], Theme.DIMENSIONS['spacing_md']))
        
        ctk.CTkLabel(delay_row, text='延迟(ms):', font=Theme.get_font('xs'), text_color=self._dark_colors['text_secondary']).pack(side='left')
        self.delay_entry = NumericEntry(delay_row, textvariable=self.delay_var, width=60, height=24)
        self.delay_entry.pack(side='left', padx=(Theme.DIMENSIONS['spacing_xs'], Theme.DIMENSIONS['spacing_sm']))
        
        self.insert_delay_btn = AnimatedButton(delay_row, text='插入', font=Theme.get_font('xs'), width=50, height=24,
                                               corner_radius=Theme.DIMENSIONS['button_corner_radius'], 
                                               fg_color=Theme.COLORS['success'],
                                               hover_color='#16A34A',
                                               command=self._insert_delay_command)
        self.insert_delay_btn.pack(side='left')
    
    def _create_mouse_command_card(self, parent):
        mouse_card = CardFrame(parent)
        mouse_card.pack(fill='x', pady=(0, Theme.DIMENSIONS['spacing_sm']))
        
        mouse_header = ctk.CTkFrame(mouse_card, fg_color='transparent')
        mouse_header.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_md'], Theme.DIMENSIONS['spacing_xs']))
        ctk.CTkLabel(mouse_header, text='鼠标命令', font=Theme.get_font('base'), text_color=self._dark_colors['text_primary']).pack(side='left')
        
        create_divider(mouse_card)
        
        mouse_row = ctk.CTkFrame(mouse_card, fg_color='transparent')
        mouse_row.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_xs'], Theme.DIMENSIONS['spacing_sm']))
        
        ctk.CTkLabel(mouse_row, text='按键:', font=Theme.get_font('xs'), text_color=self._dark_colors['text_secondary']).pack(side='left', padx=(0, Theme.DIMENSIONS['spacing_xs']))
        
        from .widgets import create_bordered_option_menu
        create_bordered_option_menu(mouse_row, values=["Left", "Right", "Middle"],
                                    variable=self.mouse_button_var, width=60, height=24)
        
        ctk.CTkLabel(mouse_row, text='操作:', font=Theme.get_font('xs'), text_color=self._dark_colors['text_secondary']).pack(side='left', padx=(Theme.DIMENSIONS['spacing_sm'], Theme.DIMENSIONS['spacing_xs']))
        create_bordered_option_menu(mouse_row, values=["Down", "Up"],
                                    variable=self.mouse_action_var, width=60, height=24)
        
        self.insert_mouse_click_btn = AnimatedButton(mouse_row, text='插入', font=Theme.get_font('xs'), width=50, height=24,
                                                     corner_radius=Theme.DIMENSIONS['button_corner_radius'], 
                                                     fg_color=Theme.COLORS['success'],
                                                     hover_color='#16A34A',
                                                     command=self._insert_mouse_click_command)
        self.insert_mouse_click_btn.pack(side='left', padx=(Theme.DIMENSIONS['spacing_sm'], 0))
        
        mouse_row2 = ctk.CTkFrame(mouse_card, fg_color='transparent')
        mouse_row2.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(0, Theme.DIMENSIONS['spacing_md']))
        
        self.select_coordinate_btn = AnimatedButton(mouse_row2, text='选择坐标点', font=Theme.get_font('xs'),
                                                    height=24, corner_radius=Theme.DIMENSIONS['button_corner_radius'],
                                                    fg_color=Theme.COLORS['primary'],
                                                    hover_color=Theme.COLORS['primary_hover'],
                                                    command=self._select_coordinate)
        self.select_coordinate_btn.pack(fill='x')
    
    def _create_combo_key_card(self, parent):
        combo_card = CardFrame(parent)
        combo_card.pack(fill='x', pady=(0, Theme.DIMENSIONS['spacing_sm']))
        
        combo_header = ctk.CTkFrame(combo_card, fg_color='transparent')
        combo_header.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_md'], Theme.DIMENSIONS['spacing_xs']))
        ctk.CTkLabel(combo_header, text='组合按键', font=Theme.get_font('base'), text_color=self._dark_colors['text_primary']).pack(side='left')
        
        create_divider(combo_card)
        
        combo_row = ctk.CTkFrame(combo_card, fg_color='transparent')
        combo_row.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_xs'], Theme.DIMENSIONS['spacing_md']))
        
        ctk.CTkLabel(combo_row, text='按键:', font=Theme.get_font('xs'), text_color=self._dark_colors['text_secondary']).pack(side='left')
        
        self.combo_key_entry = ctk.CTkEntry(combo_row, width=50, height=24, state='disabled',
                                            textvariable=self.combo_key_var,
                                            fg_color=self._dark_colors['bg_tertiary'],
                                            text_color=self._dark_colors['text_primary'])
        self.combo_key_entry.pack(side='left', padx=(Theme.DIMENSIONS['spacing_xs'], Theme.DIMENSIONS['spacing_xs']))
        
        self.set_combo_key_btn = AnimatedButton(combo_row, text='修改', font=Theme.get_font('xs'), width=40, height=24, 
                                                corner_radius=Theme.DIMENSIONS['button_corner_radius'],
                                                fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                                                command=self._start_combo_key_listening)
        self.set_combo_key_btn.pack(side='left', padx=(0, Theme.DIMENSIONS['spacing_sm']))
        
        ctk.CTkLabel(combo_row, text='按键延迟(ms):', font=Theme.get_font('xs'), text_color=self._dark_colors['text_secondary']).pack(side='left')
        combo_delay_entry = NumericEntry(combo_row, textvariable=self.combo_key_delay, width=50, height=24)
        combo_delay_entry.pack(side='left', padx=(Theme.DIMENSIONS['spacing_xs'], Theme.DIMENSIONS['spacing_sm']))
        
        ctk.CTkLabel(combo_row, text='抬起延迟(ms):', font=Theme.get_font('xs'), text_color=self._dark_colors['text_secondary']).pack(side='left')
        combo_after_entry = NumericEntry(combo_row, textvariable=self.combo_after_delay, width=50, height=24)
        combo_after_entry.pack(side='left', padx=(Theme.DIMENSIONS['spacing_xs'], Theme.DIMENSIONS['spacing_sm']))
        
        self.insert_combo_btn = AnimatedButton(combo_row, text='插入', font=Theme.get_font('xs'), width=50, height=24,
                                               corner_radius=Theme.DIMENSIONS['button_corner_radius'], 
                                               fg_color=Theme.COLORS['success'],
                                               hover_color='#16A34A',
                                               command=self._insert_combo_command)
        self.insert_combo_btn.pack(side='left')
    
    def _create_control_card(self, parent):
        control_card = CardFrame(parent)
        control_card.pack(fill='x', pady=(0, Theme.DIMENSIONS['spacing_sm']))
        
        control_header = ctk.CTkFrame(control_card, fg_color='transparent')
        control_header.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_md'], Theme.DIMENSIONS['spacing_xs']))
        ctk.CTkLabel(control_header, text='脚本控制', font=Theme.get_font('base'), text_color=self._dark_colors['text_primary']).pack(side='left')
        
        create_divider(control_card)
        
        file_path_row = ctk.CTkFrame(control_card, fg_color='transparent')
        file_path_row.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_xs'], Theme.DIMENSIONS['spacing_xs']))
        
        ctk.CTkLabel(file_path_row, text='当前文件:', font=Theme.get_font('xs'), text_color=self._dark_colors['text_secondary']).pack(side='left')
        self.script_file_path_label = ctk.CTkLabel(file_path_row, textvariable=self.script_file_path_var, 
                                                   font=Theme.get_font('xs'), 
                                                   text_color=self._dark_colors['text_muted'],
                                                   anchor='w')
        self.script_file_path_label.pack(side='left', padx=(Theme.DIMENSIONS['spacing_xs'], 0), fill='x', expand=True)
        
        control_row1 = ctk.CTkFrame(control_card, fg_color='transparent')
        control_row1.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(Theme.DIMENSIONS['spacing_xs'], Theme.DIMENSIONS['spacing_sm']))
        
        self.record_btn = AnimatedButton(control_row1, text='开始录制', font=Theme.get_font('xs'),
                                         height=24, corner_radius=Theme.DIMENSIONS['button_corner_radius'], 
                                         fg_color=Theme.COLORS['success'],
                                         hover_color='#16A34A',
                                         command=self._start_recording)
        self.record_btn.pack(side='left', fill='x', expand=True, padx=(0, Theme.DIMENSIONS['spacing_xs']))
        
        self.stop_record_btn = AnimatedButton(control_row1, text='停止录制', font=Theme.get_font('xs'),
                                              height=24, corner_radius=Theme.DIMENSIONS['button_corner_radius'], 
                                              fg_color=Theme.COLORS['error'],
                                              hover_color='#DC2626',
                                              command=self._stop_recording)
        self.stop_record_btn.configure(state='disabled')
        self.stop_record_btn.pack(side='left', fill='x', expand=True)
        
        control_row2 = ctk.CTkFrame(control_card, fg_color='transparent')
        control_row2.pack(fill='x', padx=Theme.DIMENSIONS['spacing_md'], pady=(0, Theme.DIMENSIONS['spacing_md']))
        
        new_btn = AnimatedButton(control_row2, text='新建', font=Theme.get_font('xs'),
                                 height=24, corner_radius=Theme.DIMENSIONS['button_corner_radius'], 
                                 fg_color='transparent', text_color=Theme.COLORS['primary'],
                                 border_width=1, border_color=Theme.COLORS['primary'], hover_color=self._dark_colors['border'],
                                 command=self._new_script)
        new_btn.pack(side='left', fill='x', expand=True, padx=(0, Theme.DIMENSIONS['spacing_xs']))
        
        open_btn = AnimatedButton(control_row2, text='打开', font=Theme.get_font('xs'), height=24, 
                                  corner_radius=Theme.DIMENSIONS['button_corner_radius'],
                                  fg_color=Theme.COLORS['primary'], hover_color=Theme.COLORS['primary_hover'],
                                  command=self._load_script)
        open_btn.pack(side='left', fill='x', expand=True, padx=(0, Theme.DIMENSIONS['spacing_xs']))
        
        save_btn = AnimatedButton(control_row2, text='保存', font=Theme.get_font('xs'), height=24, 
                                  corner_radius=Theme.DIMENSIONS['button_corner_radius'],
                                  fg_color=Theme.COLORS['success'], hover_color='#16A34A',
                                  command=self._save_script)
        save_btn.pack(side='left', fill='x', expand=True)
    
    def _create_editor_tabview(self, parent):
        self.script_tabview = ctk.CTkTabview(parent)
        self.script_tabview.pack(fill='both', expand=True, padx=Theme.DIMENSIONS['spacing_xs'], pady=Theme.DIMENSIONS['spacing_xs'])
        
        editor_tab = self.script_tabview.add('脚本编辑')
        
        editor_content = ctk.CTkFrame(editor_tab, fg_color='transparent')
        editor_content.pack(fill='both', expand=True, padx=Theme.DIMENSIONS['spacing_xs'], pady=Theme.DIMENSIONS['spacing_xs'])
        
        self.script_text = ctk.CTkTextbox(editor_content, font=('Consolas', 10))
        self.script_text.pack(fill='both', expand=True)
        
        clear_btn = AnimatedButton(editor_content, text='清空', font=Theme.get_font('xs'), width=80, height=22,
                                   fg_color=self._dark_colors['bg_tertiary'], text_color=self._dark_colors['text_primary'],
                                   border_width=1, border_color=self._dark_colors['border'],
                                   corner_radius=Theme.DIMENSIONS['button_corner_radius'],
                                   hover_color=self._dark_colors['border'],
                                   command=self._clear_script)
        clear_btn.pack(side='right', pady=(Theme.DIMENSIONS['spacing_xs'], 0))
        
        def on_script_modified(event):
            if self.script_text.edit_modified():
                self._modified = True
                self.script_text.edit_modified(False)
        
        self.script_text.bind("<<Modified>>", on_script_modified)
    
    def _start_key_listening(self):
        self.set_key_btn.configure(text="请按键...", fg_color=Theme.COLORS['warning'])
        
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
            }
            
            if key_name in key_mappings:
                key_name = key_mappings[key_name]
            elif len(key_name) == 1:
                key_name = key_name.lower()
            
            self.key_var.set(key_name)
            self.set_key_btn.configure(text="修改", fg_color=Theme.COLORS['primary'])
            
            toplevel = self.winfo_toplevel()
            toplevel.unbind("<KeyPress>")
            
            return "break"
        
        toplevel = self.winfo_toplevel()
        toplevel.bind("<KeyPress>", on_key_press)
        
        def reset_listening():
            try:
                self.set_key_btn.configure(text="修改", fg_color=Theme.COLORS['primary'])
                toplevel.unbind("<KeyPress>")
            except Exception:
                pass
        
        self.after(10000, reset_listening)
    
    def _start_combo_key_listening(self):
        self.set_combo_key_btn.configure(text="请按键...", fg_color=Theme.COLORS['warning'])
        
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
            }
            
            if key_name in key_mappings:
                key_name = key_mappings[key_name]
            elif len(key_name) == 1:
                key_name = key_name.lower()
            
            self.combo_key_var.set(key_name)
            self.set_combo_key_btn.configure(text="修改", fg_color=Theme.COLORS['primary'])
            
            toplevel = self.winfo_toplevel()
            toplevel.unbind("<KeyPress>")
            
            return "break"
        
        toplevel = self.winfo_toplevel()
        toplevel.bind("<KeyPress>", on_key_press)
        
        def reset_listening():
            try:
                self.set_combo_key_btn.configure(text="修改", fg_color=Theme.COLORS['primary'])
                toplevel.unbind("<KeyPress>")
            except Exception:
                pass
        
        self.after(10000, reset_listening)
    
    def _insert_key_command(self):
        key = self.key_var.get().strip()
        key_type = self.key_type.get()
        count = self.key_count.get()
        
        if not key:
            messagebox.showwarning("警告", "请输入按键名称！")
            return
        
        if count < 1:
            messagebox.showwarning("警告", "请输入有效的执行次数！")
            return
        
        command = f'{key_type} "{key}", {count}\n'
        self.script_text.insert(tk.INSERT, command)
        self.script_text.see(tk.END)
    
    def _insert_delay_command(self):
        delay = self.delay_var.get().strip()
        
        if not delay.isdigit() or int(delay) < 0:
            messagebox.showwarning("警告", "请输入有效的延迟时间！")
            return
        
        command = f"Delay {delay}\n"
        self.script_text.insert(tk.INSERT, command)
        self.script_text.see(tk.END)
    
    def _insert_mouse_click_command(self):
        button = self.mouse_button_var.get()
        action = self.mouse_action_var.get()
        count = self.mouse_count_var.get()
        
        if count < 1:
            messagebox.showwarning("警告", "请输入有效的执行次数！")
            return
        
        mouse_command = f"{button}{action} {count}\n"
        self.script_text.insert(tk.INSERT, mouse_command)
        self.script_text.see(tk.END)
    
    def _insert_combo_command(self):
        key = self.combo_key_var.get().strip()
        key_delay = self.combo_key_delay.get().strip()
        after_delay = self.combo_after_delay.get().strip()
        
        if not key:
            messagebox.showwarning("警告", "请输入按键名称！")
            return
        
        if not key_delay.isdigit() or int(key_delay) < 0:
            messagebox.showwarning("警告", "请输入有效的按键延迟时间！")
            return
        
        if not after_delay.isdigit() or int(after_delay) < 0:
            messagebox.showwarning("警告", "请输入有效的抬起后延迟时间！")
            return
        
        combo_command = f'Delay {key_delay}\nKeyDown "{key}", 1\nDelay {after_delay}\nKeyUp "{key}", 1\n'
        self.script_text.insert(tk.INSERT, combo_command)
        self.script_text.see(tk.END)
    
    def _select_coordinate(self):
        try:
            import screeninfo
            
            monitors = screeninfo.get_monitors()
            min_x = min(monitor.x for monitor in monitors)
            min_y = min(monitor.y for monitor in monitors)
            max_x = max(monitor.x + monitor.width for monitor in monitors)
            max_y = max(monitor.y + monitor.height for monitor in monitors)
        except ImportError:
            messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。")
            return
        except Exception:
            min_x, min_y, max_x, max_y = 0, 0, 1920, 1080
        
        self.coordinate_window = tk.Toplevel(self.winfo_toplevel())
        self.coordinate_window.overrideredirect(True)
        self.coordinate_window.geometry(f"{max_x - min_x}x{max_y - min_y}+{min_x}+{min_y}")
        self.coordinate_window.attributes("-alpha", 0.3)
        self.coordinate_window.attributes("-topmost", True)
        self.coordinate_window.configure(cursor="crosshair")
        
        self.coordinate_canvas = tk.Canvas(self.coordinate_window, bg="white", highlightthickness=0)
        self.coordinate_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.coordinate_canvas.bind("<Button-1>", self._on_coordinate_select)
        self.coordinate_window.bind("<Escape>", lambda e: self.coordinate_window.destroy())
        
        self.coordinate_window.focus_set()
    
    def _on_coordinate_select(self, event):
        abs_x = event.x_root
        abs_y = event.y_root
        
        self.coordinate_window.destroy()
        
        coordinate_command = f"MoveTo {abs_x}, {abs_y}\n"
        self.script_text.insert(tk.INSERT, coordinate_command)
        self.script_text.see(tk.END)
    
    def _start_recording(self):
        self.record_btn.configure(state='disabled')
        self.stop_record_btn.configure(state='normal')
        messagebox.showinfo("提示", "录制功能需要keyboard库支持")
    
    def _stop_recording(self):
        self.record_btn.configure(state='normal')
        self.stop_record_btn.configure(state='disabled')
    
    def _check_script_modified(self):
        if self._modified:
            return askyesno_centered(self.winfo_toplevel(), "保存确认", "当前脚本已修改，是否保存？")
        return True
    
    def _new_script(self):
        if not self._check_script_modified():
            return
        
        self.script_text.delete(1.0, tk.END)
        self.script_file_path_var.set("未保存")
        self.file_path = None
        self._modified = False
        self.script_original_content = ""
    
    def _clear_script(self):
        if askyesno_centered(self.winfo_toplevel(), "确认", "确定要清空当前脚本吗？"):
            self.script_text.delete(1.0, tk.END)
            self.script_file_path_var.set("未保存")
            self._modified = False
    
    def _save_script(self):
        current_path = self.script_file_path_var.get()
        if current_path and current_path != "未保存":
            file_path = current_path
        else:
            initial_dir = None
            if self.file_path:
                initial_dir = os.path.dirname(self.file_path)
            
            file_path = filedialog.asksaveasfilename(
                initialdir=initial_dir,
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                title="保存脚本"
            )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.script_text.get(1.0, tk.END))
                self.script_file_path_var.set(file_path)
                self.file_path = file_path
                self.script_file_path_label.configure(text=os.path.basename(file_path))
                self._modified = False
                self.script_original_content = self.script_text.get(1.0, tk.END)
                messagebox.showinfo("成功", f"脚本已保存到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存脚本失败: {str(e)}")
    
    def _load_script(self):
        if not self._check_script_modified():
            return
        
        initial_dir = None
        if self.file_path:
            initial_dir = os.path.dirname(self.file_path)
        
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="打开脚本"
        )
        
        if file_path:
            try:
                encodings = ['utf-8', 'gbk', 'gb2312', 'ansi']
                content = None
                
                for encoding in encodings:
                    try:
                        with open(file_path, "r", encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    messagebox.showerror("错误", "无法读取文件，编码不支持！")
                    return
                
                self.script_text.delete(1.0, tk.END)
                self.script_text.insert(1.0, content)
                self.script_file_path_var.set(file_path)
                self.file_path = file_path
                self.script_file_path_label.configure(text=os.path.basename(file_path))
                self._modified = False
                self.script_original_content = content
                messagebox.showinfo("成功", f"脚本已从: {file_path} 加载")
            except Exception as e:
                messagebox.showerror("错误", f"加载脚本失败: {str(e)}")
    
    def get_script_content(self) -> str:
        return self.script_text.get("1.0", "end-1c")
    
    def set_script_content(self, content: str):
        self.script_text.delete("1.0", "end")
        self.script_text.insert("1.0", content)
