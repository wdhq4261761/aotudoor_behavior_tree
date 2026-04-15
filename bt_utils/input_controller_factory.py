"""
输入控制器工厂
根据配置或编译参数选择具体实现
支持DD虚拟键盘和PyAutoGUI两种方式
"""
import os
import threading
import time
from typing import Optional

from .base_input import BaseInputController


USE_DD_INPUT = os.environ.get('AUTODOOR_USE_DD', '0') == '1'

_dd_input_instance = None
_pyautogui_input_instance = None


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
    
    @property
    def method_name(self) -> str:
        return "PyAutoGUI"
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def _log(self, message: str):
        """日志输出"""
        if self.app:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(message)
            else:
                print(message)
    
    def _set_simulating(self, value: bool):
        with self._simulate_lock:
            self._simulating = value
    
    def key_down(self, key: str, priority: int = 0) -> bool:
        import pyautogui
        self._set_simulating(True)
        try:
            pyautogui.keyDown(key)
            return True
        except Exception as e:
            self._log(f"❌ 按键按下错误: {str(e)}")
            return False
        finally:
            self._set_simulating(False)
    
    def key_up(self, key: str, priority: int = 0) -> bool:
        import pyautogui
        self._set_simulating(True)
        try:
            pyautogui.keyUp(key)
            return True
        except Exception as e:
            self._log(f"❌ 按键抬起错误: {str(e)}")
            return False
        finally:
            self._set_simulating(False)
    
    def press_key(self, key: str, delay: float = 0, priority: int = 0) -> bool:
        import pyautogui
        self._set_simulating(True)
        try:
            if delay > 0:
                pyautogui.keyDown(key)
                time.sleep(delay)
                pyautogui.keyUp(key)
            else:
                pyautogui.press(key)
            return True
        except Exception as e:
            self._log(f"❌ 按键执行错误: {str(e)}")
            return False
        finally:
            self._set_simulating(False)
    
    def mouse_move(self, x: int, y: int) -> bool:
        import pyautogui
        try:
            pyautogui.moveTo(x, y)
            return True
        except Exception as e:
            self._log(f"❌ 鼠标移动错误: {str(e)}")
            return False
    
    def mouse_move_relative(self, dx: int, dy: int) -> bool:
        import pyautogui
        try:
            pyautogui.moveRel(dx, dy)
            return True
        except Exception as e:
            self._log(f"❌ 鼠标相对移动错误: {str(e)}")
            return False
    
    def mouse_click(self, button: str = 'left') -> bool:
        import pyautogui
        try:
            pyautogui.click(button=button)
            return True
        except Exception as e:
            self._log(f"❌ 鼠标点击错误: {str(e)}")
            return False
    
    def mouse_down(self, button: str = 'left') -> bool:
        import pyautogui
        try:
            pyautogui.mouseDown(button=button)
            return True
        except Exception as e:
            self._log(f"❌ 鼠标按下错误: {str(e)}")
            return False
    
    def mouse_up(self, button: str = 'left') -> bool:
        import pyautogui
        try:
            pyautogui.mouseUp(button=button)
            return True
        except Exception as e:
            self._log(f"❌ 鼠标抬起错误: {str(e)}")
            return False
    
    def mouse_scroll(self, clicks: int) -> bool:
        import pyautogui
        try:
            pyautogui.scroll(clicks)
            return True
        except Exception as e:
            self._log(f"❌ 鼠标滚轮错误: {str(e)}")
            return False


class InputController:
    """
    输入控制器类（工厂模式）
    
    根据环境变量 AUTODOOR_USE_DD 自动选择DD虚拟键盘或PyAutoGUI
    保持与现有代码的完全兼容
    """
    
    def __init__(self, app=None, method: str = None):
        """
        初始化输入控制器
        
        Args:
            app: 应用实例
            method: 输入方式，可选 'pyautogui' 或 'dd'
                   如果为None，则根据环境变量自动选择
        """
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
            impl = _get_dd_input(self.app)
            if impl and impl.is_available:
                self._impl = impl
                self._method = 'dd'
                self._log(f"✅ InputController初始化完成，使用DD虚拟键盘")
                return
        
        impl = PyAutoGUIInput(self.app)
        if impl and impl.is_available:
            self._impl = impl
            self._method = 'pyautogui'
            self._log(f"✅ InputController初始化完成，使用PyAutoGUI")
        else:
            self._log("❌ InputController初始化失败：无可用的输入方式")
    
    @property
    def method(self) -> str:
        """返回当前使用的输入方式"""
        return self._method
    
    @property
    def method_name(self) -> str:
        """返回当前输入方式的名称"""
        if self._impl:
            return self._impl.method_name
        return "Unknown"
    
    @property
    def is_available(self) -> bool:
        """返回当前输入方式是否可用"""
        if self._impl:
            return self._impl.is_available
        return False
    
    def _log(self, message: str):
        """日志输出"""
        if self.app:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(message)
            else:
                print(message)
        else:
            print(message)
    
    def key_press(self, key: str, action: str = "press", duration: int = 0) -> None:
        """按键操作（兼容旧接口）"""
        if action == "press":
            self.press_key(key, delay=duration / 1000.0 if duration > 0 else 0)
        elif action == "down":
            self.key_down(key)
        elif action == "up":
            self.key_up(key)
    
    def key_down(self, key: str, priority: int = 0) -> bool:
        if self._impl:
            return self._impl.key_down(key, priority)
        return False
    
    def key_up(self, key: str, priority: int = 0) -> bool:
        if self._impl:
            return self._impl.key_up(key, priority)
        return False
    
    def press_key(self, key: str, delay: float = 0, priority: int = 0) -> bool:
        if self._impl:
            return self._impl.press_key(key, delay, priority)
        return False
    
    def mouse_move(self, position: tuple, relative: bool = False, smooth: bool = False) -> None:
        """鼠标移动（兼容旧接口）"""
        if self._impl:
            if relative:
                self._impl.mouse_move_relative(position[0], position[1])
            else:
                self._impl.mouse_move(position[0], position[1])
    
    def mouse_click(self, button: str = "left", position: tuple = None,
                   action: str = "press", duration: int = 0) -> None:
        """鼠标点击（兼容旧接口）"""
        if self._impl:
            if position:
                self._impl.mouse_move(position[0], position[1])
            
            if action == "press":
                self._impl.mouse_down(button)
                if duration > 0:
                    time.sleep(duration / 1000.0)
                self._impl.mouse_up(button)
            elif action == "down":
                self._impl.mouse_down(button)
            elif action == "up":
                self._impl.mouse_up(button)
    
    def mouse_down(self, button: str = "left") -> None:
        if self._impl:
            self._impl.mouse_down(button)
    
    def mouse_up(self, button: str = "left") -> None:
        if self._impl:
            self._impl.mouse_up(button)
    
    def mouse_scroll(self, amount: int, position: tuple = None) -> None:
        """鼠标滚轮（兼容旧接口）"""
        if self._impl:
            if position:
                self._impl.mouse_move(position[0], position[1])
            self._impl.mouse_scroll(amount)
    
    def get_position(self) -> tuple:
        """获取当前鼠标位置"""
        try:
            import pyautogui
            return pyautogui.position()
        except:
            return (0, 0)


def create_input_controller(app=None, method: str = None) -> InputController:
    """
    创建输入控制器的工厂函数
    
    Args:
        app: 应用实例
        method: 输入方式，可选 'pyautogui' 或 'dd'
    
    Returns:
        InputController实例
    """
    return InputController(app=app, method=method)
