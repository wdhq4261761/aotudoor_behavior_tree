"""
输入控制器工厂
根据配置或编译参数选择具体实现
支持DD虚拟键盘和PyAutoGUI两种方式
"""
import os
import sys
import threading
import time
from typing import Optional, Tuple

from .base_input import BaseInputController


USE_DD_INPUT = os.environ.get('AUTODOOR_USE_DD', '0') == '1'

_dd_input_instance = None


def _safe_print(message: str):
    """安全打印，处理编码问题"""
    try:
        print(message)
    except UnicodeEncodeError:
        pass


def _get_dd_input(app=None):
    """延迟加载DD输入实例"""
    global _dd_input_instance
    if _dd_input_instance is None:
        try:
            from .dd_input import DDVirtualInput
            _dd_input_instance = DDVirtualInput(app=app)
        except Exception:
            pass
    return _dd_input_instance


class PyAutoGUIInput(BaseInputController):
    """PyAutoGUI输入控制器"""
    
    def __init__(self, app=None):
        self._available = True
        self.app = app
        self._simulate_lock = threading.Lock()
        self._simulating = False
        
        import pyautogui
        pyautogui.FAILSAFE = False
    
    def get_name(self) -> str:
        return "PyAutoGUI"
    
    def _log(self, message: str):
        """日志输出"""
        pass
    
    def _set_simulating(self, value: bool):
        with self._simulate_lock:
            self._simulating = value
    
    def key_press(self, key: str, action: str = "press", duration: int = 0) -> None:
        """按键操作"""
        import pyautogui
        self._set_simulating(True)
        try:
            if action == "press":
                if duration > 0:
                    pyautogui.keyDown(key)
                    time.sleep(duration / 1000.0)
                    pyautogui.keyUp(key)
                else:
                    pyautogui.press(key)
            elif action == "down":
                pyautogui.keyDown(key)
            elif action == "up":
                pyautogui.keyUp(key)
        finally:
            self._set_simulating(False)
    
    def key_down(self, key: str) -> None:
        """按下按键"""
        import pyautogui
        self._set_simulating(True)
        try:
            pyautogui.keyDown(key)
        finally:
            self._set_simulating(False)
    
    def key_up(self, key: str) -> None:
        """释放按键"""
        import pyautogui
        self._set_simulating(True)
        try:
            pyautogui.keyUp(key)
        finally:
            self._set_simulating(False)
    
    def mouse_click(self, button: str = "left", position: Tuple[int, int] = None,
                   action: str = "press", duration: int = 0) -> None:
        """鼠标点击"""
        import pyautogui
        self._set_simulating(True)
        try:
            if position:
                pyautogui.moveTo(position[0], position[1])
            
            if action == "press":
                if duration > 0:
                    pyautogui.mouseDown(button=button)
                    time.sleep(duration / 1000.0)
                    pyautogui.mouseUp(button=button)
                else:
                    pyautogui.click(button=button)
            elif action == "down":
                pyautogui.mouseDown(button=button)
            elif action == "up":
                pyautogui.mouseUp(button=button)
        finally:
            self._set_simulating(False)
    
    def mouse_down(self, button: str = "left") -> None:
        """按下鼠标"""
        import pyautogui
        self._set_simulating(True)
        try:
            pyautogui.mouseDown(button=button)
        finally:
            self._set_simulating(False)
    
    def mouse_up(self, button: str = "left") -> None:
        """释放鼠标"""
        import pyautogui
        self._set_simulating(True)
        try:
            pyautogui.mouseUp(button=button)
        finally:
            self._set_simulating(False)
    
    def mouse_move(self, position: Tuple[int, int], relative: bool = False) -> None:
        """移动鼠标"""
        import pyautogui
        if relative:
            pyautogui.move(position[0], position[1])
        else:
            pyautogui.moveTo(position[0], position[1])
    
    def mouse_scroll(self, amount: int, position: Tuple[int, int] = None) -> None:
        """鼠标滚轮"""
        import pyautogui
        if position:
            pyautogui.moveTo(position[0], position[1])
        pyautogui.scroll(amount)


class DDInputWrapper(BaseInputController):
    """DD输入控制器包装器"""
    
    def __init__(self, dd_instance, app=None):
        self._dd = dd_instance
        self.app = app
    
    def get_name(self) -> str:
        return "DD虚拟键盘"
    
    def _log(self, message: str):
        pass
    
    def key_press(self, key: str, action: str = "press", duration: int = 0) -> None:
        """按键操作"""
        if action == "press":
            self._dd.key_press(key, action, duration)
        elif action == "down":
            self._dd.key_down(key)
        elif action == "up":
            self._dd.key_up(key)
    
    def key_down(self, key: str) -> None:
        """按下按键"""
        self._dd.key_down(key)
    
    def key_up(self, key: str) -> None:
        """释放按键"""
        self._dd.key_up(key)
    
    def mouse_click(self, button: str = "left", position: Tuple[int, int] = None,
                   action: str = "press", duration: int = 0) -> None:
        """鼠标点击"""
        self._dd.mouse_click(button, position, action, duration)
    
    def mouse_down(self, button: str = "left") -> None:
        """按下鼠标"""
        self._dd.mouse_down(button)
    
    def mouse_up(self, button: str = "left") -> None:
        """释放鼠标"""
        self._dd.mouse_up(button)
    
    def mouse_move(self, position: Tuple[int, int], relative: bool = False) -> None:
        """移动鼠标"""
        self._dd.mouse_move(position, relative)
    
    def mouse_scroll(self, amount: int, position: Tuple[int, int] = None) -> None:
        """鼠标滚轮"""
        self._dd.mouse_scroll(amount, position)


class InputController:
    """
    输入控制器类（工厂模式）
    
    根据环境变量 AUTODOOR_USE_DD 自动选择DD虚拟键盘或PyAutoGUI
    """
    
    def __init__(self, app=None, method: str = None):
        self.app = app
        self._method = method
        self._impl = None
        
        self._init_implementation()
    
    def _init_implementation(self):
        """初始化具体实现"""
        method = self._method
        
        if method is None:
            if USE_DD_INPUT:
                method = 'dd'
            else:
                method = 'pyautogui'
        
        if method == 'dd':
            dd_instance = _get_dd_input(self.app)
            if dd_instance and dd_instance.is_available:
                self._impl = DDInputWrapper(dd_instance, self.app)
                self._method = 'dd'
                return
            else:
                # DD版本：如果DD不可用，不回退到PyAutoGUI，保持为None
                self._impl = None
                self._method = 'dd'
                return
        
        # 非DD版本：使用PyAutoGUI
        self._impl = PyAutoGUIInput(self.app)
        self._method = 'pyautogui'
    
    @property
    def method(self) -> str:
        return self._method
    
    @property
    def is_available(self) -> bool:
        return self._impl is not None
    
    def _log(self, message: str):
        pass
    
    def key_press(self, key: str, action: str = "press", duration: int = 0) -> None:
        if self._impl:
            self._impl.key_press(key, action, duration)
    
    def key_down(self, key: str) -> None:
        if self._impl:
            self._impl.key_down(key)
    
    def key_up(self, key: str) -> None:
        if self._impl:
            self._impl.key_up(key)
    
    def mouse_click(self, button: str = "left", position: tuple = None,
                   action: str = "press", duration: int = 0) -> None:
        if self._impl:
            self._impl.mouse_click(button, position, action, duration)
    
    def mouse_down(self, button: str = "left") -> None:
        if self._impl:
            self._impl.mouse_down(button)
    
    def mouse_up(self, button: str = "left") -> None:
        if self._impl:
            self._impl.mouse_up(button)
    
    def mouse_move(self, position: tuple, relative: bool = False, smooth: bool = False) -> None:
        if self._impl:
            self._impl.mouse_move(position, relative)
    
    def mouse_scroll(self, amount: int, position: tuple = None) -> None:
        if self._impl:
            self._impl.mouse_scroll(amount, position)
    
    def get_position(self) -> tuple:
        try:
            import pyautogui
            return pyautogui.position()
        except:
            return (0, 0)


def create_input_controller(app=None, method: str = None) -> InputController:
    return InputController(app=app, method=method)
