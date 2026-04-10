import customtkinter as ctk
from typing import List
from bt_utils.log_manager import LogManager, LogEntry


class LogPanel(ctk.CTkFrame):
    MAX_LINES = 500
    FLUSH_INTERVAL = 200
    MIN_HEIGHT = 100
    MAX_HEIGHT = 600
    DEFAULT_HEIGHT = 120
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self._log_lines: List[str] = []
        self._auto_scroll = True
        self._is_expanded = False
        self._flush_timer = None
        self._current_height = self.DEFAULT_HEIGHT
        self._resizing = False
        self._resize_start_y = 0
        self._resize_start_height = 0
        
        self._create_ui()
        self._bind_events()
        self._start_flush_timer()
    
    def _create_ui(self):
        self._resize_handle = self._create_resize_handle()
        self._toolbar = self._create_toolbar()
    
    def _create_resize_handle(self) -> ctk.CTkFrame:
        handle = ctk.CTkFrame(
            self, 
            height=6, 
            fg_color=("gray70", "gray30"),
            cursor="sb_v_double_arrow"
        )
        handle.pack(fill="x", side="top")
        
        handle.bind("<Button-1>", self._on_resize_start)
        handle.bind("<B1-Motion>", self._on_resize_drag)
        handle.bind("<ButtonRelease-1>", self._on_resize_end)
        handle.bind("<Enter>", self._on_handle_enter)
        handle.bind("<Leave>", self._on_handle_leave)
        
        return handle
    
    def _create_toolbar(self) -> ctk.CTkFrame:
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", pady=2)
        
        left_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        left_frame.pack(side="left", padx=5)
        
        self._clear_btn = ctk.CTkButton(
            left_frame, text="清空", width=60, height=24,
            command=self._on_clear
        )
        self._clear_btn.pack(side="left")
        
        self._auto_scroll_var = ctk.BooleanVar(value=True)
        self._auto_scroll_cb = ctk.CTkCheckBox(
            left_frame, text="自动滚动", width=80,
            variable=self._auto_scroll_var
        )
        self._auto_scroll_cb.pack(side="left", padx=5)
        
        self._title_label = ctk.CTkLabel(
            toolbar, 
            text="运行日志",
            font=("", 12, "bold")
        )
        self._title_label.pack(side="left", expand=True)
        
        self._toggle_btn = ctk.CTkButton(
            toolbar, text="▼展开", width=60, height=24,
            command=self._on_toggle
        )
        self._toggle_btn.pack(side="right", padx=5)
        
        return toolbar
    
    def _create_text_area(self):
        height = max(self.MIN_HEIGHT, self._current_height)
        self._text_area = ctk.CTkTextbox(self, height=height, wrap="word")
        self._text_area.pack(fill="both", expand=True)
    
    def _bind_events(self):
        pass
    
    def _on_handle_enter(self, event):
        self._resize_handle.configure(fg_color=("gray50", "gray50"))
    
    def _on_handle_leave(self, event):
        if not self._resizing:
            self._resize_handle.configure(fg_color=("gray70", "gray30"))
    
    def _on_resize_start(self, event):
        self._resizing = True
        self._resize_start_y = event.y_root
        self._resize_start_height = self._current_height
        self._resize_handle.configure(fg_color=("gray50", "gray50"))
    
    def _on_resize_drag(self, event):
        if not self._resizing:
            return
        
        delta_y = self._resize_start_y - event.y_root
        new_height = self._resize_start_height + delta_y
        new_height = max(self.MIN_HEIGHT, min(self.MAX_HEIGHT, new_height))
        
        if abs(new_height - self._current_height) > 5:
            self._current_height = new_height
            
            if hasattr(self, '_text_area') and self._text_area:
                self._text_area.configure(height=new_height)
                self.update_idletasks()
    
    def _on_resize_end(self, event):
        self._resizing = False
        self._resize_handle.configure(fg_color=("gray70", "gray30"))
    
    def _on_scroll(self, event):
        if self._auto_scroll_var.get():
            self._auto_scroll_var.set(False)
    
    def _on_clear(self):
        self._log_lines.clear()
        if hasattr(self, '_text_area') and self._text_area:
            self._text_area.delete("1.0", "end")
        LogManager.instance().clear()
    
    def _on_toggle(self):
        if self._is_expanded:
            if hasattr(self, '_text_area') and self._text_area:
                self._text_area.pack_forget()
            self._toggle_btn.configure(text="▼展开")
            self._is_expanded = False
        else:
            if self._current_height < self.MIN_HEIGHT:
                self._current_height = self.DEFAULT_HEIGHT
            
            if not hasattr(self, '_text_area') or not self._text_area:
                self._create_text_area()
            else:
                self._text_area.configure(height=self._current_height)
                self._text_area.pack(fill="both", expand=True)
            self._toggle_btn.configure(text="▲折叠")
            self._is_expanded = True
    
    def _start_flush_timer(self):
        self._flush_timer = self.after(self.FLUSH_INTERVAL, self._flush_logs)
    
    def _flush_logs(self):
        log_manager = LogManager.instance()
        entries = log_manager.flush()
        
        if entries and self._is_expanded:
            self._append_entries(entries)
        
        self._start_flush_timer()
    
    def _append_entries(self, entries: List[LogEntry]):
        for entry in entries:
            line = entry.format()
            self._log_lines.append(line)
        
        while len(self._log_lines) > self.MAX_LINES:
            self._log_lines.pop(0)
        
        self._refresh_display()
    
    def _refresh_display(self):
        if not hasattr(self, '_text_area') or not self._text_area:
            return
        
        self._text_area.delete("1.0", "end")
        self._text_area.insert("1.0", "\n".join(self._log_lines))
        
        if self._auto_scroll_var.get():
            self._text_area.see("end")
    
    def append_log(self, entry: LogEntry):
        LogManager.instance().log(entry)
    
    def clear_logs(self):
        self._on_clear()
    
    def expand(self):
        if not self._is_expanded:
            self._on_toggle()
    
    def collapse(self):
        if self._is_expanded:
            self._on_toggle()
    
    def is_expanded(self) -> bool:
        return self._is_expanded
    
    def destroy(self):
        if self._flush_timer:
            self.after_cancel(self._flush_timer)
        super().destroy()
