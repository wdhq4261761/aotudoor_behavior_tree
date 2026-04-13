import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

from .theme import Theme
from .widgets import CardFrame, AnimatedButton


def create_settings_dialog(app) -> None:
    """创建设置对话框

    Args:
        app: 主应用实例
    """
    dialog = ctk.CTkToplevel(app)
    dialog.title("⚙️ 设置")
    dialog.geometry("580x560")
    dialog.transient(app)
    dialog.grab_set()
    dialog.attributes('-topmost', True)

    scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color='transparent')
    scroll_frame.pack(fill='both', expand=True, padx=10, pady=10)

    _create_tesseract_section(scroll_frame, app, dialog)
    _create_alarm_section(scroll_frame, app, dialog)
    _create_shortcuts_section(scroll_frame, app, dialog)
    _create_behavior_tree_section(scroll_frame, app, dialog)
    _create_ui_section(scroll_frame, app, dialog)

    btn_frame = ctk.CTkFrame(dialog, fg_color='transparent')
    btn_frame.pack(fill='x', padx=10, pady=10)

    AnimatedButton(btn_frame, text="💾 保存", width=80,
                   fg_color=Theme.COLORS['success'],
                   hover_color=Theme.COLORS['primary'],
                   command=lambda: _save_settings(app, dialog)).pack(side='right', padx=4)
    AnimatedButton(btn_frame, text="❌ 取消", width=80,
                   command=dialog.destroy).pack(side='right', padx=4)
    AnimatedButton(btn_frame, text="🔄 重置默认", width=90,
                   fg_color=Theme.COLORS['warning'],
                   hover_color=Theme.COLORS['primary'],
                   command=lambda: _reset_settings(app, dialog)).pack(side='left', padx=4)


def _create_tesseract_section(parent, app, dialog) -> None:
    card = CardFrame(parent, title="🔍 Tesseract OCR 设置")
    card.pack(fill='x', pady=(0, 6))

    row = ctk.CTkFrame(card.content, fg_color='transparent')
    row.pack(fill='x', pady=2)

    ctk.CTkLabel(row, text="路径:", font=Theme.get_font('sm'),
                 text_color=Theme.COLORS['text_secondary']).pack(side='left')
    app._settings_tesseract_path = tk.StringVar(
        value=app.settings_manager.get("tesseract_path", "")
    )
    ctk.CTkEntry(row, textvariable=app._settings_tesseract_path, width=300,
                 font=Theme.get_font('sm'), height=Theme.SIZES['input_height']).pack(
        side='left', padx=4, fill='x', expand=True)

    def browse_tesseract():
        path = filedialog.askdirectory(title="选择 Tesseract OCR 目录")
        if path:
            app._settings_tesseract_path.set(path)

    AnimatedButton(row, text="浏览", width=50, command=browse_tesseract).pack(side='left')


def _create_alarm_section(parent, app, dialog) -> None:
    card = CardFrame(parent, title="🔔 报警设置")
    card.pack(fill='x', pady=(0, 6))

    row1 = ctk.CTkFrame(card.content, fg_color='transparent')
    row1.pack(fill='x', pady=2)

    ctk.CTkLabel(row1, text="声音:", font=Theme.get_font('sm'),
                 text_color=Theme.COLORS['text_secondary']).pack(side='left')
    app._settings_alarm_sound = tk.StringVar(
        value=app.settings_manager.get("alarm_sound_path", "")
    )
    ctk.CTkEntry(row1, textvariable=app._settings_alarm_sound, width=300,
                 font=Theme.get_font('sm'), height=Theme.SIZES['input_height']).pack(
        side='left', padx=4, fill='x', expand=True)

    def browse_alarm():
        path = filedialog.askopenfilename(
            title="选择报警音效",
            filetypes=[("音频文件", "*.mp3 *.wav *.ogg"), ("所有文件", "*.*")]
        )
        if path:
            app._settings_alarm_sound.set(path)

    AnimatedButton(row1, text="浏览", width=50, command=browse_alarm).pack(side='left')

    row2 = ctk.CTkFrame(card.content, fg_color='transparent')
    row2.pack(fill='x', pady=2)

    ctk.CTkLabel(row2, text="音量:", font=Theme.get_font('sm'),
                 text_color=Theme.COLORS['text_secondary']).pack(side='left')
    app._settings_alarm_volume = tk.IntVar(
        value=app.settings_manager.get("alarm_volume", 70)
    )
    volume_slider = ctk.CTkSlider(row2, from_=0, to=100, width=200,
                                   variable=app._settings_alarm_volume,
                                   command=lambda v: volume_label.configure(text=f"{int(v)}%"))
    volume_slider.pack(side='left', padx=4)
    volume_label = ctk.CTkLabel(row2, text=f"{app._settings_alarm_volume.get()}%",
                                 font=Theme.get_font('sm'), width=40)
    volume_label.pack(side='left')


def _create_shortcuts_section(parent, app, dialog) -> None:
    card = CardFrame(parent, title="⌨️ 快捷键设置")
    card.pack(fill='x', pady=(0, 6))

    shortcuts = [
        ("开始运行:", "start", "start_shortcut"),
        ("停止运行:", "stop", "stop_shortcut"),
        ("录制按钮:", "record", "record_shortcut"),
    ]

    app._shortcut_vars = {}

    for label_text, key, var_name in shortcuts:
        row = ctk.CTkFrame(card.content, fg_color='transparent')
        row.pack(fill='x', pady=2)

        ctk.CTkLabel(row, text=label_text, font=Theme.get_font('sm'),
                     text_color=Theme.COLORS['text_secondary'], width=80).pack(side='left')

        var = tk.StringVar(value=app.settings_manager.get(f"shortcuts.{key}", "F10"))
        app._shortcut_vars[var_name] = var

        entry = ctk.CTkEntry(row, textvariable=var, width=80,
                              font=Theme.get_font('mono'), height=Theme.SIZES['input_height'],
                              state='disabled')
        entry.pack(side='left', padx=4)

        def start_listening(e=entry, v=var):
            e.configure(state='normal')
            e.delete(0, 'end')
            e.insert(0, "按下按键...")

            from pynput import keyboard
            def on_press(key):
                try:
                    if hasattr(key, 'char') and key.char:
                        key_name = key.char.upper()
                    elif hasattr(key, 'name'):
                        key_name = key.name.upper()
                    else:
                        key_name = str(key).upper()
                    e.after(0, lambda: _update_shortcut(e, v, key_name))
                    return False
                except:
                    return True

            listener = keyboard.Listener(on_press=on_press)
            listener.start()

        AnimatedButton(row, text="修改", width=50, command=start_listening).pack(side='left')


def _update_shortcut(entry, var, key_name):
    entry.configure(state='normal')
    entry.delete(0, 'end')
    entry.insert(0, key_name)
    var.set(key_name)
    entry.configure(state='disabled')


def _create_behavior_tree_section(parent, app, dialog) -> None:
    card = CardFrame(parent, title="🌲 行为树设置")
    card.pack(fill='x', pady=(0, 6))

    row1 = ctk.CTkFrame(card.content, fg_color='transparent')
    row1.pack(fill='x', pady=2)

    ctk.CTkLabel(row1, text="Tick间隔(ms):", font=Theme.get_font('sm'),
                 text_color=Theme.COLORS['text_secondary']).pack(side='left')
    app._settings_tick_interval = tk.StringVar(
        value=str(app.settings_manager.get("behavior_tree.tick_interval", 50))
    )
    ctk.CTkEntry(row1, textvariable=app._settings_tick_interval, width=60,
                 font=Theme.get_font('mono'), height=Theme.SIZES['input_height']).pack(side='left', padx=4)

    ctk.CTkLabel(row1, text="自动保存间隔(秒):", font=Theme.get_font('sm'),
                 text_color=Theme.COLORS['text_secondary']).pack(side='left', padx=(10, 0))
    app._settings_auto_save = tk.StringVar(
        value=str(app.settings_manager.get("behavior_tree.auto_save_interval", 30))
    )
    ctk.CTkEntry(row1, textvariable=app._settings_auto_save, width=60,
                 font=Theme.get_font('mono'), height=Theme.SIZES['input_height']).pack(side='left', padx=4)

    row2 = ctk.CTkFrame(card.content, fg_color='transparent')
    row2.pack(fill='x', pady=2)

    ctk.CTkLabel(row2, text="默认保存格式:", font=Theme.get_font('sm'),
                 text_color=Theme.COLORS['text_secondary']).pack(side='left')
    app._settings_default_format = tk.StringVar(
        value=app.settings_manager.get("behavior_tree.default_format", "json")
    )
    ctk.CTkComboBox(row2, variable=app._settings_default_format,
                     values=["json", "yaml", "txt"], width=100,
                     height=Theme.SIZES['input_height']).pack(side='left', padx=4)


def _create_ui_section(parent, app, dialog) -> None:
    card = CardFrame(parent, title="🎨 界面设置")
    card.pack(fill='x', pady=(0, 6))

    row1 = ctk.CTkFrame(card.content, fg_color='transparent')
    row1.pack(fill='x', pady=2)

    ctk.CTkLabel(row1, text="主题:", font=Theme.get_font('sm'),
                 text_color=Theme.COLORS['text_secondary']).pack(side='left')
    app._settings_theme = tk.StringVar(
        value=app.settings_manager.get("ui.theme", "dark")
    )
    ctk.CTkComboBox(row1, variable=app._settings_theme,
                     values=["深色", "浅色", "系统"], width=100,
                     height=Theme.SIZES['input_height']).pack(side='left', padx=4)

    ctk.CTkLabel(row1, text="语言:", font=Theme.get_font('sm'),
                 text_color=Theme.COLORS['text_secondary']).pack(side='left', padx=(10, 0))
    app._settings_language = tk.StringVar(
        value=app.settings_manager.get("ui.language", "zh_CN")
    )
    ctk.CTkComboBox(row1, variable=app._settings_language,
                     values=["简体中文", "English"], width=100,
                     height=Theme.SIZES['input_height']).pack(side='left', padx=4)


def _save_settings(app, dialog) -> None:
    try:
        app.settings_manager.set("tesseract_path", app._settings_tesseract_path.get())
        app.settings_manager.set("alarm_sound_path", app._settings_alarm_sound.get())
        app.settings_manager.set("alarm_volume", app._settings_alarm_volume.get())

        shortcuts = {}
        for var_name, var in app._shortcut_vars.items():
            key = var_name.replace("_shortcut", "")
            shortcuts[key] = var.get()
        app.settings_manager.set("shortcuts", shortcuts)

        app.settings_manager.set("behavior_tree", {
            "tick_interval": int(app._settings_tick_interval.get()),
            "auto_save_interval": int(app._settings_auto_save.get()),
            "default_format": app._settings_default_format.get(),
        })

        theme_value = app._settings_theme.get()
        theme_map = {"深色": "dark", "浅色": "light", "系统": "system"}
        app.settings_manager.set("ui", {
            "theme": theme_map.get(theme_value, theme_value),
            "language": app._settings_language.get(),
        })

        app.settings_manager.save_settings()

        from bt_utils.ocr_manager import OCRManager
        OCRManager.set_tesseract_path(app._settings_tesseract_path.get())

        messagebox.showinfo("成功", "✅ 设置已保存")
        dialog.destroy()
    except Exception as e:
        messagebox.showerror("错误", f"❌ 保存设置失败: {str(e)}")


def _reset_settings(app, dialog) -> None:
    if messagebox.askyesno("确认", "确定要重置所有设置为默认值吗？"):
        app.settings_manager.reset()
        dialog.destroy()
        create_settings_dialog(app)
