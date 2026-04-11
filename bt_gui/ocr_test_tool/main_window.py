import customtkinter as ctk
from typing import Optional
from PIL import Image as PILImage
from bt_gui.ocr_test_tool.test_runner import TestRunner
from bt_utils.parameter_manager import ParameterManager


class OCRTestMainWindow(ctk.CTk):
    """OCR测试工具主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.title("OCR参数测试工具")
        self.geometry("1400x800")
        
        self.test_runner = TestRunner()
        self.param_manager = ParameterManager()
        
        self.current_image: Optional[PILImage.Image] = None
        self.test_history = []
        
        self._create_ui()
        self._setup_layout()
        
    def _create_ui(self):
        """创建UI组件"""
        self._create_toolbar()
        self._create_main_panels()
        self._create_status_bar()
        
    def _create_toolbar(self):
        """创建工具栏"""
        self.toolbar = ctk.CTkFrame(self, height=50)
        self.toolbar.pack(fill="x", padx=10, pady=5)
        
        self.btn_screenshot = ctk.CTkButton(
            self.toolbar,
            text="全屏截图",
            command=self._on_screenshot_full
        )
        self.btn_screenshot.pack(side="left", padx=5)
        
        self.btn_region_screenshot = ctk.CTkButton(
            self.toolbar,
            text="区域截图",
            command=self._on_screenshot_region
        )
        self.btn_region_screenshot.pack(side="left", padx=5)
        
        self.btn_load_image = ctk.CTkButton(
            self.toolbar,
            text="加载图片",
            command=self._on_load_image
        )
        self.btn_load_image.pack(side="left", padx=5)
        
        self.btn_save_config = ctk.CTkButton(
            self.toolbar,
            text="保存配置",
            command=self._on_save_config
        )
        self.btn_save_config.pack(side="left", padx=5)
        
        self.btn_load_config = ctk.CTkButton(
            self.toolbar,
            text="加载配置",
            command=self._on_load_config
        )
        self.btn_load_config.pack(side="left", padx=5)
        
    def _create_main_panels(self):
        """创建主面板"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.main_frame.grid_columnconfigure(0, weight=4)
        self.main_frame.grid_columnconfigure(1, weight=3)
        self.main_frame.grid_columnconfigure(2, weight=3)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        self.screenshot_panel = ctk.CTkFrame(self.main_frame)
        self.screenshot_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.param_panel = ctk.CTkFrame(self.main_frame)
        self.param_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.result_panel = ctk.CTkFrame(self.main_frame)
        self.result_panel.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        
        self._setup_screenshot_panel()
        self._setup_param_panel()
        self._setup_result_panel()
        
    def _setup_screenshot_panel(self):
        """设置截图面板"""
        label = ctk.CTkLabel(
            self.screenshot_panel,
            text="图像预览区",
            font=("Arial", 16, "bold")
        )
        label.pack(pady=10)
        
        self.original_image_label = ctk.CTkLabel(
            self.screenshot_panel,
            text="原始图像",
            font=("Arial", 12)
        )
        self.original_image_label.pack(pady=5)
        
        self.original_image_frame = ctk.CTkFrame(
            self.screenshot_panel,
            width=400,
            height=250
        )
        self.original_image_frame.pack(pady=5, padx=10, fill="x")
        self.original_image_frame.pack_propagate(False)
        
        self.preprocessed_image_label = ctk.CTkLabel(
            self.screenshot_panel,
            text="预处理图像",
            font=("Arial", 12)
        )
        self.preprocessed_image_label.pack(pady=5)
        
        self.preprocessed_image_frame = ctk.CTkFrame(
            self.screenshot_panel,
            width=400,
            height=250
        )
        self.preprocessed_image_frame.pack(pady=5, padx=10, fill="x")
        self.preprocessed_image_frame.pack_propagate(False)
        
        self.btn_start_test = ctk.CTkButton(
            self.screenshot_panel,
            text="开始测试",
            command=self._on_start_test,
            height=40,
            font=("Arial", 14, "bold")
        )
        self.btn_start_test.pack(pady=20)
        
    def _setup_param_panel(self):
        """设置参数面板"""
        label = ctk.CTkLabel(
            self.param_panel,
            text="参数调节区",
            font=("Arial", 16, "bold")
        )
        label.pack(pady=10)
        
        prep_label = ctk.CTkLabel(
            self.param_panel,
            text="预处理参数",
            font=("Arial", 12, "bold")
        )
        prep_label.pack(pady=5)
        
        self.scale_slider = self._create_slider(
            self.param_panel, "放大倍数", 1.0, 5.0, 2.5
        )
        self.contrast_slider = self._create_slider(
            self.param_panel, "对比度增强", 0.5, 5.0, 2.5
        )
        self.sharpness_slider = self._create_slider(
            self.param_panel, "锐化强度", 0.5, 5.0, 2.0
        )
        self.threshold_slider = self._create_slider(
            self.param_panel, "二值化阈值", 50, 200, 130
        )
        
        ocr_label = ctk.CTkLabel(
            self.param_panel,
            text="OCR参数",
            font=("Arial", 12, "bold")
        )
        ocr_label.pack(pady=10)
        
        self.language_var = ctk.StringVar(value="chi_sim")
        language_menu = ctk.CTkOptionMenu(
            self.param_panel,
            variable=self.language_var,
            values=["eng", "chi_sim", "chi_tra"],
            width=200
        )
        language_menu.pack(pady=5)
        
        test_label = ctk.CTkLabel(
            self.param_panel,
            text="测试参数",
            font=("Arial", 12, "bold")
        )
        test_label.pack(pady=10)
        
        self.keywords_entry = ctk.CTkEntry(
            self.param_panel,
            placeholder_text="关键词(逗号分隔)",
            width=200
        )
        self.keywords_entry.pack(pady=5)
        
        self.expected_entry = ctk.CTkEntry(
            self.param_panel,
            placeholder_text="预期结果",
            width=200
        )
        self.expected_entry.pack(pady=5)
        
    def _setup_result_panel(self):
        """设置结果面板"""
        label = ctk.CTkLabel(
            self.result_panel,
            text="结果展示区",
            font=("Arial", 16, "bold")
        )
        label.pack(pady=10)
        
        result_label = ctk.CTkLabel(
            self.result_panel,
            text="识别结果",
            font=("Arial", 12, "bold")
        )
        result_label.pack(pady=5)
        
        self.result_textbox = ctk.CTkTextbox(
            self.result_panel,
            width=300,
            height=150
        )
        self.result_textbox.pack(pady=5, padx=10, fill="x")
        
        stats_label = ctk.CTkLabel(
            self.result_panel,
            text="性能统计",
            font=("Arial", 12, "bold")
        )
        stats_label.pack(pady=10)
        
        self.stats_textbox = ctk.CTkTextbox(
            self.result_panel,
            width=300,
            height=150
        )
        self.stats_textbox.pack(pady=5, padx=10, fill="x")
        
    def _create_slider(self, parent, label: str, min_val: float, max_val: float, default: float):
        """创建滑块控件"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=2)
        
        label_widget = ctk.CTkLabel(frame, text=label, width=100)
        label_widget.pack(side="left")
        
        slider = ctk.CTkSlider(
            frame,
            from_=min_val,
            to=max_val,
            number_of_steps=100
        )
        slider.set(default)
        slider.pack(side="left", fill="x", expand=True, padx=5)
        
        value_label = ctk.CTkLabel(frame, text=f"{default:.1f}", width=50)
        value_label.pack(side="left")
        
        def update_label(value):
            value_label.configure(text=f"{value:.1f}")
        
        slider.configure(command=update_label)
        
        return slider
        
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ctk.CTkFrame(self, height=30)
        self.status_bar.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="就绪",
            font=("Arial", 10)
        )
        self.status_label.pack(side="left", padx=10)
        
    def _setup_layout(self):
        """设置布局"""
        pass
        
    def _on_screenshot_full(self):
        """全屏截图"""
        self.status_label.configure(text="正在截图...")
        self.update()
        
        from PIL import ImageGrab
        self.current_image = ImageGrab.grab()
        
        self.status_label.configure(text="截图完成")
        self._update_image_display()
        
    def _on_screenshot_region(self):
        """区域截图"""
        self.status_label.configure(text="请选择截图区域...")
        
    def _on_load_image(self):
        """加载图片"""
        from tkinter import filedialog
        
        filepath = filedialog.askopenfilename(
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp"),
                ("所有文件", "*.*")
            ]
        )
        
        if filepath:
            self.current_image = PILImage.open(filepath)
            self.status_label.configure(text=f"已加载: {filepath}")
            self._update_image_display()
        
    def _on_save_config(self):
        """保存配置"""
        from tkinter import filedialog
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")]
        )
        
        if filepath:
            params = self._get_current_params()
            self.param_manager.save_config(params, filepath)
            self.status_label.configure(text=f"配置已保存: {filepath}")
        
    def _on_load_config(self):
        """加载配置"""
        from tkinter import filedialog
        
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON文件", "*.json")]
        )
        
        if filepath:
            params = self.param_manager.load_config(filepath)
            self._set_current_params(params)
            self.status_label.configure(text=f"配置已加载: {filepath}")
        
    def _on_start_test(self):
        """开始测试"""
        if not self.current_image:
            self.status_label.configure(text="请先截图或加载图片")
            return
        
        self.status_label.configure(text="正在测试...")
        self.update()
        
        params = self._get_current_params()
        result = self.test_runner.run_single_test(self.current_image, params)
        
        self.test_history.append(result)
        self._display_result(result)
        
        self.status_label.configure(text="测试完成")
        
    def _get_current_params(self) -> dict:
        """获取当前参数"""
        return {
            "preprocessing": {
                "scale_factor": self.scale_slider.get(),
                "contrast_enhance": self.contrast_slider.get(),
                "sharpness_enhance": self.sharpness_slider.get(),
                "binary_threshold": int(self.threshold_slider.get())
            },
            "ocr": {
                "language": self.language_var.get()
            },
            "test": {
                "keywords": self.keywords_entry.get(),
                "expected_text": self.expected_entry.get()
            }
        }
        
    def _set_current_params(self, params: dict):
        """设置当前参数"""
        prep = params.get('preprocessing', {})
        self.scale_slider.set(prep.get('scale_factor', 2.5))
        self.contrast_slider.set(prep.get('contrast_enhance', 2.5))
        self.sharpness_slider.set(prep.get('sharpness_enhance', 2.0))
        self.threshold_slider.set(prep.get('binary_threshold', 130))
        
        ocr = params.get('ocr', {})
        self.language_var.set(ocr.get('language', 'chi_sim'))
        
        test = params.get('test', {})
        self.keywords_entry.delete(0, 'end')
        self.keywords_entry.insert(0, test.get('keywords', ''))
        self.expected_entry.delete(0, 'end')
        self.expected_entry.insert(0, test.get('expected_text', ''))
        
    def _update_image_display(self):
        """更新图像显示"""
        pass
        
    def _display_result(self, result):
        """显示测试结果"""
        self.result_textbox.delete("1.0", "end")
        self.result_textbox.insert("1.0", f"识别结果:\n{result.recognized_text}\n\n")
        self.result_textbox.insert("end", f"成功: {'是' if result.success else '否'}\n")
        self.result_textbox.insert("end", f"置信度: {result.confidence:.2f}\n")
        
        if result.position:
            self.result_textbox.insert("end", f"位置: {result.position}\n")
        
        self.stats_textbox.delete("1.0", "end")
        self.stats_textbox.insert("1.0", f"处理时间: {result.processing_time:.2f} ms\n")
        
        if self.test_history:
            stats = self.test_runner.get_statistics(self.test_history)
            self.stats_textbox.insert("end", f"\n统计信息:\n")
            self.stats_textbox.insert("end", f"总测试次数: {stats.total_tests}\n")
            self.stats_textbox.insert("end", f"成功次数: {stats.success_count}\n")
            self.stats_textbox.insert("end", f"成功率: {stats.success_rate:.2%}\n")
            self.stats_textbox.insert("end", f"平均耗时: {stats.avg_time:.2f} ms\n")


def main():
    """主函数"""
    app = OCRTestMainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
