"""
坐标偏移测量工具

提供可视化界面帮助用户测量两点之间的偏移量。
支持在全屏模式下点击选择参考点和目标点。
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Tuple
import platform


class OffsetMeasurementTool:
    """偏移测量工具
    
    用于帮助用户可视化测量两个屏幕位置之间的偏移量。
    
    使用流程:
    1. 调用 start_measurement() 开始测量
    2. 用户点击参考点 (识别目标位置)
    3. 用户点击目标点 (实际操作位置)
    4. 自动计算偏移量并通过回调返回
    
    示例:
        def on_offset_measured(offset_x, offset_y):
            print(f"偏移量: X={offset_x}, Y={offset_y}")
        
        tool = OffsetMeasurementTool(on_offset_measured)
        tool.start_measurement()
    """
    
    def __init__(self, callback: Callable[[int, int], None]):
        """初始化偏移测量工具
        
        Args:
            callback: 测量完成回调函数，接收 (offset_x, offset_y) 参数
        """
        self.callback = callback
        self.reference_point: Optional[Tuple[int, int]] = None
        self.target_point: Optional[Tuple[int, int]] = None
        self.overlay: Optional[tk.Toplevel] = None
        self.canvas: Optional[tk.Canvas] = None
        self.hint_label: Optional[tk.Label] = None
        self._is_measuring = False
    
    def start_measurement(self, parent: Optional[tk.Tk] = None):
        """开始偏移测量
        
        创建全屏透明遮罩窗口，等待用户点击。
        
        Args:
            parent: 父窗口（可选）
        """
        if self._is_measuring:
            return
        
        self._is_measuring = True
        self.reference_point = None
        self.target_point = None
        
        self._create_overlay(parent)
    
    def _create_overlay(self, parent: Optional[tk.Tk]):
        """创建全屏遮罩窗口"""
        self.overlay = tk.Toplevel(parent)
        self.overlay.title("偏移测量工具")
        
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-topmost', True)
        
        if platform.system() == 'Windows':
            self.overlay.attributes('-alpha', 0.3)
            self.overlay.configure(bg='#000000')
        else:
            self.overlay.configure(bg='#000000')
        
        self.canvas = tk.Canvas(
            self.overlay,
            highlightthickness=0,
            bg='#000000'
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.hint_label = tk.Label(
            self.overlay,
            text="请点击【参考点】(识别目标位置)",
            font=('Microsoft YaHei', 16, 'bold'),
            fg='#FFFFFF',
            bg='#333333',
            padx=20,
            pady=10
        )
        self.hint_label.place(relx=0.5, rely=0.1, anchor='center')
        
        self._create_help_panel()
        
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<Button-3>', self._cancel)
        self.overlay.bind('<Escape>', self._cancel)
        self.overlay.bind('<Control-c>', self._cancel)
        
        self.overlay.focus_set()
        self.overlay.grab_set()
    
    def _create_help_panel(self):
        """创建帮助面板"""
        help_frame = tk.Frame(self.overlay, bg='#333333', padx=15, pady=10)
        help_frame.place(relx=0.5, rely=0.9, anchor='center')
        
        help_text = tk.Label(
            help_frame,
            text="左键点击: 选择点 | 右键/ESC: 取消",
            font=('Microsoft YaHei', 10),
            fg='#AAAAAA',
            bg='#333333'
        )
        help_text.pack()
    
    def _on_click(self, event):
        """处理点击事件"""
        x = event.x_root
        y = event.y_root
        
        if self.reference_point is None:
            self.reference_point = (x, y)
            self._draw_reference_point(x, y)
            self.hint_label.config(text="请点击【目标点】(实际操作位置)")
        else:
            self.target_point = (x, y)
            self._draw_target_point(x, y)
            self._finish_measurement()
    
    def _draw_reference_point(self, x: int, y: int):
        """绘制参考点"""
        self.canvas.create_oval(
            x - 10, y - 10, x + 10, y + 10,
            outline='#00FF00',
            width=3,
            tags='reference'
        )
        self.canvas.create_line(
            x - 20, y, x + 20, y,
            fill='#00FF00',
            width=2,
            tags='reference'
        )
        self.canvas.create_line(
            x, y - 20, x, y + 20,
            fill='#00FF00',
            width=2,
            tags='reference'
        )
        self.canvas.create_text(
            x, y - 25,
            text=f"参考点 ({x}, {y})",
            fill='#00FF00',
            font=('Microsoft YaHei', 10, 'bold'),
            tags='reference'
        )
    
    def _draw_target_point(self, x: int, y: int):
        """绘制目标点"""
        self.canvas.create_oval(
            x - 10, y - 10, x + 10, y + 10,
            outline='#FF0000',
            width=3,
            tags='target'
        )
        self.canvas.create_line(
            x - 20, y, x + 20, y,
            fill='#FF0000',
            width=2,
            tags='target'
        )
        self.canvas.create_line(
            x, y - 20, x, y + 20,
            fill='#FF0000',
            width=2,
            tags='target'
        )
        self.canvas.create_text(
            x, y - 25,
            text=f"目标点 ({x}, {y})",
            fill='#FF0000',
            font=('Microsoft YaHei', 10, 'bold'),
            tags='target'
        )
        
        if self.reference_point:
            self.canvas.create_line(
                self.reference_point[0], self.reference_point[1],
                x, y,
                fill='#FFFF00',
                width=2,
                dash=(5, 5),
                tags='connection'
            )
    
    def _finish_measurement(self):
        """完成测量"""
        if self.reference_point and self.target_point:
            offset_x = self.target_point[0] - self.reference_point[0]
            offset_y = self.target_point[1] - self.reference_point[1]
            
            self._show_result(offset_x, offset_y)
            
            self.overlay.after(500, lambda: self._close_and_callback(offset_x, offset_y))
    
    def _show_result(self, offset_x: int, offset_y: int):
        """显示测量结果"""
        result_frame = tk.Frame(self.overlay, bg='#0066CC', padx=20, pady=15)
        result_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        tk.Label(
            result_frame,
            text="偏移量测量完成",
            font=('Microsoft YaHei', 14, 'bold'),
            fg='#FFFFFF',
            bg='#0066CC'
        ).pack()
        
        tk.Label(
            result_frame,
            text=f"X偏移: {offset_x:+d}  |  Y偏移: {offset_y:+d}",
            font=('Microsoft YaHei', 12),
            fg='#FFFFFF',
            bg='#0066CC'
        ).pack(pady=5)
        
        tk.Label(
            result_frame,
            text="窗口即将关闭...",
            font=('Microsoft YaHei', 10),
            fg='#AAAAAA',
            bg='#0066CC'
        ).pack()
    
    def _close_and_callback(self, offset_x: int, offset_y: int):
        """关闭窗口并回调"""
        self._close_overlay()
        if self.callback:
            self.callback(offset_x, offset_y)
    
    def _cancel(self, event=None):
        """取消测量"""
        self._close_overlay()
    
    def _close_overlay(self):
        """关闭遮罩窗口"""
        if self.overlay:
            self.overlay.grab_release()
            self.overlay.destroy()
            self.overlay = None
        self._is_measuring = False
        self.reference_point = None
        self.target_point = None


class OffsetMeasurementDialog:
    """偏移测量对话框
    
    提供更友好的对话框界面，包含预览和确认功能。
    """
    
    def __init__(self, parent: tk.Tk, callback: Callable[[int, int], None]):
        """初始化对话框
        
        Args:
            parent: 父窗口
            callback: 测量完成回调
        """
        self.parent = parent
        self.callback = callback
        self.tool: Optional[OffsetMeasurementTool] = None
        self.dialog: Optional[tk.Toplevel] = None
        self.offset_x = 0
        self.offset_y = 0
    
    def show(self):
        """显示对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("偏移量测量工具")
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self._create_ui()
        
        self.dialog.geometry(f"+{self.parent.winfo_x() + 200}+{self.parent.winfo_y() + 200}")
        self.dialog.wait_window()
    
    def _create_ui(self):
        """创建界面"""
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(
            main_frame,
            text="坐标偏移测量",
            font=('Microsoft YaHei', 14, 'bold')
        )
        title_label.pack(pady=(0, 15))
        
        self.result_frame = tk.Frame(main_frame)
        self.result_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            self.result_frame,
            text="X偏移:",
            font=('Microsoft YaHei', 11)
        ).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        
        self.x_var = tk.StringVar(value="0")
        self.x_entry = tk.Entry(
            self.result_frame,
            textvariable=self.x_var,
            font=('Microsoft YaHei', 11),
            width=10
        )
        self.x_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(
            self.result_frame,
            text="Y偏移:",
            font=('Microsoft YaHei', 11)
        ).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        
        self.y_var = tk.StringVar(value="0")
        self.y_entry = tk.Entry(
            self.result_frame,
            textvariable=self.y_var,
            font=('Microsoft YaHei', 11),
            width=10
        )
        self.y_entry.grid(row=1, column=1, padx=5, pady=5)
        
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        measure_btn = tk.Button(
            btn_frame,
            text="📐 测量偏移",
            font=('Microsoft YaHei', 10),
            command=self._start_measurement,
            width=12
        )
        measure_btn.pack(side=tk.LEFT, padx=5)
        
        ok_btn = tk.Button(
            btn_frame,
            text="确定",
            font=('Microsoft YaHei', 10),
            command=self._on_ok,
            width=8
        )
        ok_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="取消",
            font=('Microsoft YaHei', 10),
            command=self._on_cancel,
            width=8
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def _start_measurement(self):
        """开始测量"""
        self.dialog.withdraw()
        
        def on_measured(offset_x, offset_y):
            self.offset_x = offset_x
            self.offset_y = offset_y
            self.x_var.set(str(offset_x))
            self.y_var.set(str(offset_y))
            self.dialog.deiconify()
        
        self.tool = OffsetMeasurementTool(on_measured)
        self.tool.start_measurement(self.parent)
    
    def _on_ok(self):
        """确认"""
        try:
            offset_x = int(self.x_var.get())
            offset_y = int(self.y_var.get())
        except ValueError:
            offset_x = 0
            offset_y = 0
        
        self.dialog.destroy()
        if self.callback:
            self.callback(offset_x, offset_y)
    
    def _on_cancel(self):
        """取消"""
        self.dialog.destroy()


def measure_offset(parent: Optional[tk.Tk] = None, callback: Callable[[int, int], None] = None) -> OffsetMeasurementTool:
    """便捷函数：启动偏移测量
    
    Args:
        parent: 父窗口
        callback: 测量完成回调
    
    Returns:
        OffsetMeasurementTool: 测量工具实例
    """
    tool = OffsetMeasurementTool(callback)
    tool.start_measurement(parent)
    return tool


def show_offset_dialog(parent: tk.Tk, callback: Callable[[int, int], None]):
    """便捷函数：显示偏移测量对话框
    
    Args:
        parent: 父窗口
        callback: 测量完成回调
    """
    dialog = OffsetMeasurementDialog(parent, callback)
    dialog.show()
