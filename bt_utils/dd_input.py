"""
DD虚拟键盘输入控制器实现
DD版专用方案
"""
import os
import sys
import ctypes
import time
from typing import Optional, Tuple

from .base_input import BaseInputController


VK_CODE_MAP = {
    'backspace': 0x08,
    'tab': 0x09,
    'enter': 0x0D,
    'return': 0x0D,
    'shift': 0x10,
    'control': 0x11,
    'ctrl': 0x11,
    'alt': 0x12,
    'pause': 0x13,
    'caps_lock': 0x14,
    'capslock': 0x14,
    'escape': 0x1B,
    'esc': 0x1B,
    'space': 0x20,
    'pageup': 0x21,
    'prior': 0x21,
    'pagedown': 0x22,
    'next': 0x22,
    'end': 0x23,
    'home': 0x24,
    'left': 0x25,
    'up': 0x26,
    'right': 0x27,
    'down': 0x28,
    'print_screen': 0x2C,
    'printscreen': 0x2C,
    'insert': 0x2D,
    'ins': 0x2D,
    'delete': 0x2E,
    'del': 0x2E,
    
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
    'z': 0x5A,
    
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74,
    'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
    'f11': 0x7A, 'f12': 0x7B,
    
    'shift_l': 0xA0, 'shiftleft': 0xA0,
    'shift_r': 0xA1, 'shiftright': 0xA1,
    'control_l': 0xA2, 'ctrlleft': 0xA2, 'ctrl_l': 0xA2,
    'control_r': 0xA3, 'ctrlright': 0xA3, 'ctrl_r': 0xA3,
    'alt_l': 0xA4, 'altleft': 0xA4,
    'alt_r': 0xA5, 'altright': 0xA5,
    
    'win_l': 0x5B, 'winleft': 0x5B,
    'win_r': 0x5C, 'winright': 0x5C,
    'win': 0x5B,
    
    'num_lock': 0x90, 'numlock': 0x90,
    'scroll_lock': 0x91, 'scrolllock': 0x91,
    
    'multiply': 0x6A,
    'add': 0x6B,
    'separator': 0x6C,
    'subtract': 0x6D,
    'decimal': 0x6E,
    'divide': 0x6F,
    
    'numpad0': 0x60, 'numpad1': 0x61, 'numpad2': 0x62,
    'numpad3': 0x63, 'numpad4': 0x64, 'numpad5': 0x65,
    'numpad6': 0x66, 'numpad7': 0x67, 'numpad8': 0x68,
    'numpad9': 0x69,
    
    'oem_1': 0xBA,
    'oem_plus': 0xBB,
    'oem_comma': 0xBC,
    'oem_minus': 0xBD,
    'oem_period': 0xBE,
    'oem_2': 0xBF,
    'oem_3': 0xC0,
    'oem_4': 0xDB,
    'oem_5': 0xDC,
    'oem_6': 0xDD,
    'oem_7': 0xDE,
    
    ';': 0xBA,
    '=': 0xBB,
    ',': 0xBC,
    '-': 0xBD,
    '.': 0xBE,
    '/': 0xBF,
    '`': 0xC0,
    '[': 0xDB,
    '\\': 0xDC,
    ']': 0xDD,
    "'": 0xDE,
}


class DDVirtualInput(BaseInputController):
    """DD虚拟键盘输入控制器"""
    
    def __init__(self, app=None, dll_path: str = None):
        self._dd_dll = None
        self._available = False
        self._dll_path = dll_path
        self.app = app
        self._vk_cache = {}
        
        self._load_dd_dll()
    
    def _load_dd_dll(self) -> bool:
        """加载DD虚拟键盘DLL"""
        possible_paths = []
        
        if self._dll_path:
            possible_paths.append(self._dll_path)
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        
        possible_paths.extend([
            os.path.join(base_path, "DD64.dll"),
            os.path.join(base_path, "drivers", "DD64.dll"),
            os.path.join(base_path, "..", "drivers", "DD64.dll"),
            os.path.join(os.path.dirname(base_path), "drivers", "DD64.dll"),
        ])
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    self._dd_dll = ctypes.windll.LoadLibrary(path)
                    result = self._dd_dll.DD_btn(0)
                    if result == 1:
                        self._available = True
                        self._dll_path = path
                        return True
                except Exception:
                    continue
        
        return False
    
    def get_name(self) -> str:
        return "DD虚拟键盘"
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    @property
    def dll_path(self) -> Optional[str]:
        return self._dll_path if self._available else None
    
    def _log(self, message: str):
        """日志输出"""
        pass
    
    def _get_dd_code(self, key: str) -> int:
        """
        获取DD键码
        通过DD_todc函数动态转换Windows VK码到DD码
        """
        key_lower = key.lower()
        
        if key_lower in self._vk_cache:
            return self._vk_cache[key_lower]
        
        vk_code = VK_CODE_MAP.get(key_lower)
        
        if vk_code is None:
            if len(key_lower) == 1 and key_lower.isalpha():
                vk_code = ord(key_lower.upper())
            else:
                return 0
        
        if self._available and self._dd_dll:
            try:
                dd_code = self._dd_dll.DD_todc(vk_code)
                if dd_code > 0:
                    self._vk_cache[key_lower] = dd_code
                    return dd_code
            except Exception:
                pass
        
        return 0
    
    def key_press(self, key: str, action: str = "press", duration: int = 0) -> None:
        """按键操作"""
        if action == "press":
            self.key_down(key)
            if duration > 0:
                time.sleep(duration / 1000.0)
            self.key_up(key)
        elif action == "down":
            self.key_down(key)
        elif action == "up":
            self.key_up(key)
    
    def key_down(self, key: str) -> None:
        """按下按键"""
        if not self._available or not self._dd_dll:
            return
        
        dd_code = self._get_dd_code(key)
        if dd_code == 0:
            return
        
        try:
            self._dd_dll.DD_key(dd_code, 1)
        except Exception:
            pass
    
    def key_up(self, key: str) -> None:
        """释放按键"""
        if not self._available or not self._dd_dll:
            return
        
        dd_code = self._get_dd_code(key)
        if dd_code == 0:
            return
        
        try:
            self._dd_dll.DD_key(dd_code, 2)
        except Exception:
            pass
    
    def mouse_click(self, button: str = "left", position: Tuple[int, int] = None,
                   action: str = "press", duration: int = 0) -> None:
        """鼠标点击"""
        if not self._available or not self._dd_dll:
            return
        
        if position:
            self.mouse_move(position, relative=False)
        
        if action == "press":
            self.mouse_down(button)
            if duration > 0:
                time.sleep(duration / 1000.0)
            self.mouse_up(button)
        elif action == "down":
            self.mouse_down(button)
        elif action == "up":
            self.mouse_up(button)
    
    def mouse_down(self, button: str = "left") -> None:
        """按下鼠标"""
        if not self._available or not self._dd_dll:
            return
        
        btn_map = {'left': 1, 'right': 4, 'middle': 16}
        btn_code = btn_map.get(button, 1)
        
        try:
            self._dd_dll.DD_btn(btn_code)
        except Exception:
            pass
    
    def mouse_up(self, button: str = "left") -> None:
        """释放鼠标"""
        if not self._available or not self._dd_dll:
            return
        
        btn_map = {'left': 2, 'right': 8, 'middle': 32}
        btn_code = btn_map.get(button, 2)
        
        try:
            self._dd_dll.DD_btn(btn_code)
        except Exception:
            pass
    
    def mouse_move(self, position: Tuple[int, int], relative: bool = False) -> None:
        """移动鼠标"""
        if not self._available or not self._dd_dll:
            return
        
        try:
            if relative:
                self._dd_dll.DD_movR(position[0], position[1])
            else:
                self._dd_dll.DD_mov(position[0], position[1])
        except Exception:
            pass
    
    def mouse_scroll(self, amount: int, position: Tuple[int, int] = None) -> None:
        """鼠标滚轮"""
        if not self._available or not self._dd_dll:
            return
        
        try:
            if position:
                self._dd_dll.DD_mov(position[0], position[1])
            self._dd_dll.DD_whl(amount)
        except Exception:
            pass
