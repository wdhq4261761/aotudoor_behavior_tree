from abc import ABC, abstractmethod
from typing import Tuple, Optional


class BaseInputController(ABC):
    """输入控制器基类

    定义输入控制器的标准接口。
    """

    @abstractmethod
    def key_press(self, key: str, action: str = "press", duration: int = 0) -> None:
        """按键操作

        Args:
            key: 按键名称
            action: 动作类型 (press/down/up)
            duration: 按住时长（毫秒）
        """
        pass

    @abstractmethod
    def key_down(self, key: str) -> None:
        """按下按键

        Args:
            key: 按键名称
        """
        pass

    @abstractmethod
    def key_up(self, key: str) -> None:
        """释放按键

        Args:
            key: 按键名称
        """
        pass

    @abstractmethod
    def mouse_click(self, button: str = "left", position: Tuple[int, int] = None,
                   action: str = "press", duration: int = 0) -> None:
        """鼠标点击

        Args:
            button: 鼠标按钮 (left/right/middle)
            position: 点击位置 (x, y)
            action: 动作类型 (press/down/up)
            duration: 按住时长（毫秒）
        """
        pass

    @abstractmethod
    def mouse_down(self, button: str = "left") -> None:
        """按下鼠标

        Args:
            button: 鼠标按钮
        """
        pass

    @abstractmethod
    def mouse_up(self, button: str = "left") -> None:
        """释放鼠标

        Args:
            button: 鼠标按钮
        """
        pass

    @abstractmethod
    def mouse_move(self, position: Tuple[int, int], relative: bool = False) -> None:
        """移动鼠标

        Args:
            position: 目标位置 (x, y)
            relative: 是否相对移动
        """
        pass

    @abstractmethod
    def mouse_scroll(self, amount: int, position: Tuple[int, int] = None) -> None:
        """鼠标滚轮

        Args:
            amount: 滚动量
            position: 滚动位置
        """
        pass

    def get_name(self) -> str:
        """获取控制器名称

        Returns:
            控制器名称
        """
        return self.__class__.__name__
