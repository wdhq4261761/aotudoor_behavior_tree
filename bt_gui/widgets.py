import customtkinter as ctk
import tkinter as tk
from .theme import Theme


class NumericEntry(ctk.CTkEntry):
    def __init__(self, master, textvariable=None, **kwargs):
        self._valid = True
        self._textvariable = textvariable
        
        if textvariable is not None:
            try:
                current_value = textvariable.get()
                if current_value == '' or current_value is None:
                    if isinstance(textvariable, tk.DoubleVar):
                        textvariable.set(0.0)
                    elif isinstance(textvariable, tk.IntVar):
                        textvariable.set(0)
                    else:
                        textvariable.set('0')
            except tk.TclError:
                if isinstance(textvariable, tk.DoubleVar):
                    textvariable.set(0.0)
                elif isinstance(textvariable, tk.IntVar):
                    textvariable.set(0)
                else:
                    textvariable.set('0')
        
        super().__init__(master, textvariable=textvariable, **kwargs)
        
        try:
            self._orig_value = self.get()
        except tk.TclError:
            self._orig_value = '0'
        
        self.bind('<KeyRelease>', self._validate)
        self.bind('<FocusOut>', self._on_focus_out)
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<KeyPress>', self._on_key_press)
    
    def _on_key_press(self, event):
        if event.keysym in ('BackSpace', 'Delete', 'Tab', 'Return', 'Escape', 'Left', 'Right'):
            return
        
        if event.char == '' and event.keysym not in ('BackSpace', 'Delete'):
            return
        
        if event.char.isdigit() or event.char == '-':
            return
        
        if event.keysym not in ('BackSpace', 'Delete', 'Tab'):
            return 'break'
    
    def _on_focus_in(self, event=None):
        try:
            value = self.get()
            if value == '0' or value == '0.0':
                self.delete(0, 'end')
            self._orig_value = self.get()
        except tk.TclError:
            self._orig_value = '0'
    
    def _on_focus_out(self, event=None):
        try:
            value = self.get()
            if value == '' or value == '-':
                if self._textvariable:
                    if isinstance(self._textvariable, tk.DoubleVar):
                        self._textvariable.set(0.0)
                    elif isinstance(self._textvariable, tk.IntVar):
                        self._textvariable.set(0)
                    else:
                        self._textvariable.set('0')
                else:
                    self.delete(0, 'end')
                    self.insert(0, '0')
            self._validate(event)
        except tk.TclError:
            if self._textvariable:
                if isinstance(self._textvariable, tk.DoubleVar):
                    self._textvariable.set(0.0)
                elif isinstance(self._textvariable, tk.IntVar):
                    self._textvariable.set(0)
                else:
                    self._textvariable.set('0')
    
    def _validate(self, event=None):
        try:
            value = self.get()
            if value == '' or value == '-':
                self._valid = True
                self.configure(border_color=Theme.COLORS['border'])
                return
            
            try:
                float(value)
                self._valid = True
                self.configure(border_color=Theme.COLORS['success'])
            except ValueError:
                self._valid = False
                self.configure(border_color=Theme.COLORS['error'])
                restore_value = self._orig_value if self._orig_value and self._orig_value not in ('', '-') else '0'
                self.delete(0, 'end')
                self.insert(0, restore_value)
                self._valid = True
                self.configure(border_color=Theme.COLORS['border'])
        except tk.TclError:
            self._valid = True
            self.configure(border_color=Theme.COLORS['border'])
    
    def get_value(self, default=0):
        try:
            val = self.get()
            if val == '' or val == '-':
                return default
            return float(val)
        except (ValueError, tk.TclError):
            return default


class CardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        dark_colors = Theme.get_dark_colors()
        kwargs.setdefault('corner_radius', Theme.DIMENSIONS['card_corner_radius'])
        kwargs.setdefault('border_width', 1)
        kwargs.setdefault('border_color', dark_colors['border'])
        kwargs.setdefault('fg_color', dark_colors['card_bg'])
        super().__init__(master, **kwargs)


class AnimatedButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        self._press_color = kwargs.pop('press_color', None)
        self._original_fg = kwargs.get('fg_color', Theme.COLORS['primary'])
        self._original_hover = kwargs.get('hover_color', Theme.COLORS['primary_hover'])
        
        if self._press_color is None:
            if isinstance(self._original_fg, str) and self._original_fg not in ['transparent']:
                self._press_color = self._darken_color(self._original_fg, 0.2)
            else:
                self._press_color = self._original_hover
        
        super().__init__(master, **kwargs)
        
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<Leave>', self._on_leave)
    
    def _darken_color(self, hex_color, factor):
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            r = int(r * (1 - factor))
            g = int(g * (1 - factor))
            b = int(b * (1 - factor))
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return hex_color
    
    def _on_press(self, event):
        if self._original_fg not in ['transparent']:
            self.configure(fg_color=self._press_color)
    
    def _on_release(self, event):
        if self._original_fg not in ['transparent']:
            self.configure(fg_color=self._original_fg)
    
    def _on_leave(self, event=None):
        if self._original_fg not in ['transparent']:
            self.configure(fg_color=self._original_fg)


def create_section_title(parent, text, level=1):
    dark_colors = Theme.get_dark_colors()
    if level == 1:
        font = Theme.get_font('lg')
        text_color = dark_colors['text_primary']
    elif level == 2:
        font = Theme.get_font('base')
        text_color = dark_colors['text_primary']
    else:
        font = Theme.get_font('sm')
        text_color = dark_colors['text_secondary']
    
    return ctk.CTkLabel(parent, text=text, font=font, text_color=text_color)


def create_divider(parent, height=1, pady=4):
    dark_colors = Theme.get_dark_colors()
    divider = ctk.CTkFrame(parent, height=height, fg_color=dark_colors['border'])
    divider.pack(fill='x', pady=pady)
    return divider


def create_bordered_option_menu(parent, values, variable=None, width=70, height=24):
    dark_colors = Theme.get_dark_colors()
    border_frame = ctk.CTkFrame(parent, fg_color=dark_colors['border'], corner_radius=6)
    border_frame.pack(side='left')
    
    inner_frame = ctk.CTkFrame(border_frame, fg_color=dark_colors['bg_tertiary'], corner_radius=5)
    inner_frame.pack(padx=1, pady=1)
    
    menu = ctk.CTkOptionMenu(inner_frame, values=values, variable=variable,
                            width=width, height=height,
                            fg_color=dark_colors['bg_tertiary'], text_color=dark_colors['text_primary'],
                            button_color=Theme.COLORS['primary'],
                            button_hover_color=Theme.COLORS['primary_hover'],
                            dropdown_fg_color=dark_colors['bg_secondary'], dropdown_text_color=dark_colors['text_primary'],
                            dropdown_hover_color=dark_colors['border'],
                            corner_radius=5)
    menu.pack(padx=0, pady=0)
    
    return menu, border_frame
