import pyautogui
import time
import math
import threading
from typing import Tuple


class InputController:
    """输入控制器

    封装键盘和鼠标操作，提供统一的输入控制接口。
    """

    _simulate_lock = threading.Lock()
    _simulating = False
    
    @classmethod
    def is_simulating(cls) -> bool:
        """检查当前是否正在执行模拟操作
        
        Returns:
            是否正在执行模拟操作
        """
        with cls._simulate_lock:
            return cls._simulating
    
    @classmethod
    def _set_simulating(cls, value: bool):
        """设置模拟状态
        
        Args:
            value: 是否正在执行模拟操作
        """
        with cls._simulate_lock:
            cls._simulating = value
    
    @classmethod
    def release_all(cls):
        """释放所有按下的按键和鼠标按钮
        
        使用 pynput 的 Controller 来释放所有按键，无需跟踪按键状态。
        """
        print(f"[DEBUG] InputController.release_all() 被调用")
        
        cls._set_simulating(True)
        try:
            from pynput import keyboard, mouse
            
            keyboard_controller = keyboard.Controller()
            mouse_controller = mouse.Controller()
            
            for key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
                       keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
                       keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
                       keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r,
                       keyboard.Key.caps_lock, keyboard.Key.num_lock,
                       keyboard.Key.scroll_lock]:
                try:
                    keyboard_controller.release(key)
                except:
                    pass
            
            for char in 'abcdefghijklmnopqrstuvwxyz0123456789':
                try:
                    keyboard_controller.release(char)
                except:
                    pass
            
            for key_name in ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
                            'space', 'enter', 'tab', 'escape', 'backspace', 'delete', 'insert',
                            'home', 'end', 'page_up', 'page_down', 'up', 'down', 'left', 'right']:
                try:
                    keyboard_controller.release(getattr(keyboard.Key, key_name, None))
                except:
                    pass
            
            mouse_controller.release(mouse.Button.left)
            mouse_controller.release(mouse.Button.right)
            mouse_controller.release(mouse.Button.middle)
            
            print(f"[DEBUG] 所有按键和鼠标按钮已释放")
        except Exception as e:
            print(f"[WARN] 释放按键时出错: {e}")
        finally:
            cls._set_simulating(False)

    def __init__(self):
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01

    def key_press(self, key: str, action: str = "press", duration: int = 0) -> None:
        """按键操作

        Args:
            key: 按键名称
            action: 动作类型 (press/down/up)
            duration: 按住时长（毫秒）
        """
        self._set_simulating(True)
        try:
            if action == "press":
                if duration > 0:
                    pyautogui.keyDown(key)
                    pyautogui.sleep(duration / 1000)
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
        """按下按键

        Args:
            key: 按键名称
        """
        self._set_simulating(True)
        try:
            pyautogui.keyDown(key)
        finally:
            self._set_simulating(False)

    def key_up(self, key: str) -> None:
        """释放按键

        Args:
            key: 按键名称
        """
        self._set_simulating(True)
        try:
            pyautogui.keyUp(key)
        finally:
            self._set_simulating(False)

    def mouse_click(self, button: str = "left", position: Tuple[int, int] = None,
                   action: str = "press", duration: int = 0) -> None:
        """鼠标点击

        Args:
            button: 鼠标按钮 (left/right/middle)
            position: 点击位置 (x, y)
            action: 动作类型 (press/down/up)
            duration: 按住时长（毫秒）
        """
        self._set_simulating(True)
        try:
            if position:
                pyautogui.moveTo(position[0], position[1])

            if action == "press":
                if duration > 0:
                    pyautogui.mouseDown(button=button)
                    pyautogui.sleep(duration / 1000)
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
        """按下鼠标

        Args:
            button: 鼠标按钮
        """
        self._set_simulating(True)
        try:
            pyautogui.mouseDown(button=button)
        finally:
            self._set_simulating(False)

    def mouse_up(self, button: str = "left") -> None:
        """释放鼠标

        Args:
            button: 鼠标按钮
        """
        self._set_simulating(True)
        try:
            pyautogui.mouseUp(button=button)
        finally:
            self._set_simulating(False)

    def mouse_move(self, position: Tuple[int, int], relative: bool = False,
                   smooth: bool = False, duration: float = 0.3) -> None:
        """移动鼠标

        Args:
            position: 目标位置 (x, y)
            relative: 是否相对移动
            smooth: 是否平滑移动
            duration: 平滑移动时长（秒）
        """
        if smooth:
            self._smooth_move(position, relative, duration)
        elif relative:
            pyautogui.move(position[0], position[1])
        else:
            pyautogui.moveTo(position[0], position[1])

    def _smooth_move(self, target: Tuple[int, int], relative: bool, duration: float) -> None:
        """平滑移动鼠标

        Args:
            target: 目标位置
            relative: 是否相对移动
            duration: 移动时长
        """
        start_x, start_y = pyautogui.position()

        if relative:
            target_x = start_x + target[0]
            target_y = start_y + target[1]
        else:
            target_x, target_y = target

        distance = math.sqrt((target_x - start_x) ** 2 + (target_y - start_y) ** 2)
        
        if distance < 1:
            return

        steps = max(int(duration * 60), 10)
        
        for i in range(steps + 1):
            t = i / steps
            t = t * t * (3 - 2 * t)
            
            current_x = int(start_x + (target_x - start_x) * t)
            current_y = int(start_y + (target_y - start_y) * t)
            
            pyautogui.moveTo(current_x, current_y, _pause=False)
            time.sleep(duration / steps)

    def move_to(self, x: int, y: int, smooth: bool = False, duration: float = 0.3) -> None:
        """移动鼠标到指定位置

        Args:
            x: X坐标
            y: Y坐标
            smooth: 是否平滑移动
            duration: 平滑移动时长
        """
        self.mouse_move((x, y), relative=False, smooth=smooth, duration=duration)

    def mouse_scroll(self, amount: int, position: Tuple[int, int] = None) -> None:
        """鼠标滚轮

        Args:
            amount: 滚动量
            position: 滚动位置
        """
        if position:
            pyautogui.moveTo(position[0], position[1])
        pyautogui.scroll(amount)

    def get_position(self) -> Tuple[int, int]:
        """获取当前鼠标位置

        Returns:
            当前鼠标位置 (x, y)
        """
        return pyautogui.position()
