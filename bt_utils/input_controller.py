import pyautogui
import time
import math
from typing import Tuple


class InputController:
    """输入控制器

    封装键盘和鼠标操作，提供统一的输入控制接口。
    """

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

    def key_down(self, key: str) -> None:
        """按下按键

        Args:
            key: 按键名称
        """
        pyautogui.keyDown(key)

    def key_up(self, key: str) -> None:
        """释放按键

        Args:
            key: 按键名称
        """
        pyautogui.keyUp(key)

    def mouse_click(self, button: str = "left", position: Tuple[int, int] = None,
                   action: str = "press", duration: int = 0) -> None:
        """鼠标点击

        Args:
            button: 鼠标按钮 (left/right/middle)
            position: 点击位置 (x, y)
            action: 动作类型 (press/down/up)
            duration: 按住时长（毫秒）
        """
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

    def mouse_down(self, button: str = "left") -> None:
        """按下鼠标

        Args:
            button: 鼠标按钮
        """
        pyautogui.mouseDown(button=button)

    def mouse_up(self, button: str = "left") -> None:
        """释放鼠标

        Args:
            button: 鼠标按钮
        """
        pyautogui.mouseUp(button=button)

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
