from typing import Tuple, Optional
import ctypes
from ctypes import wintypes


user32 = ctypes.windll.user32


class CoordinateConverter:
    """坐标转换工具

    支持绝对坐标、相对坐标、窗口坐标之间的转换。
    """

    @staticmethod
    def get_screen_size() -> Tuple[int, int]:
        """获取屏幕尺寸

        Returns:
            (width, height) 元组
        """
        return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))

    @staticmethod
    def get_window_rect(hwnd: wintypes.HWND) -> Optional[Tuple[int, int, int, int]]:
        """获取窗口矩形区域

        Args:
            hwnd: 窗口句柄

        Returns:
            (left, top, right, bottom) 元组
        """
        rect = wintypes.RECT()
        if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return (rect.left, rect.top, rect.right, rect.bottom)
        return None

    @staticmethod
    def get_client_rect(hwnd: wintypes.HWND) -> Optional[Tuple[int, int, int, int]]:
        """获取客户区矩形区域

        Args:
            hwnd: 窗口句柄

        Returns:
            (left, top, right, bottom) 元组（相对于窗口）
        """
        rect = wintypes.RECT()
        if user32.GetClientRect(hwnd, ctypes.byref(rect)):
            return (rect.left, rect.top, rect.right, rect.bottom)
        return None

    @staticmethod
    def absolute_to_window(x: int, y: int, hwnd: wintypes.HWND) -> Optional[Tuple[int, int]]:
        """绝对坐标转窗口坐标

        Args:
            x: 绝对X坐标
            y: 绝对Y坐标
            hwnd: 窗口句柄

        Returns:
            (window_x, window_y) 元组
        """
        rect = CoordinateConverter.get_window_rect(hwnd)
        if not rect:
            return None

        return (x - rect[0], y - rect[1])

    @staticmethod
    def window_to_absolute(x: int, y: int, hwnd: wintypes.HWND) -> Optional[Tuple[int, int]]:
        """窗口坐标转绝对坐标

        Args:
            x: 窗口X坐标
            y: 窗口Y坐标
            hwnd: 窗口句柄

        Returns:
            (absolute_x, absolute_y) 元组
        """
        rect = CoordinateConverter.get_window_rect(hwnd)
        if not rect:
            return None

        return (x + rect[0], y + rect[1])

    @staticmethod
    def absolute_to_client(x: int, y: int, hwnd: wintypes.HWND) -> Optional[Tuple[int, int]]:
        """绝对坐标转客户区坐标

        Args:
            x: 绝对X坐标
            y: 绝对Y坐标
            hwnd: 窗口句柄

        Returns:
            (client_x, client_y) 元组
        """
        point = wintypes.POINT(x, y)
        if user32.ScreenToClient(hwnd, ctypes.byref(point)):
            return (point.x, point.y)
        return None

    @staticmethod
    def client_to_absolute(x: int, y: int, hwnd: wintypes.HWND) -> Optional[Tuple[int, int]]:
        """客户区坐标转绝对坐标

        Args:
            x: 客户区X坐标
            y: 客户区Y坐标
            hwnd: 窗口句柄

        Returns:
            (absolute_x, absolute_y) 元组
        """
        point = wintypes.POINT(x, y)
        if user32.ClientToScreen(hwnd, ctypes.byref(point)):
            return (point.x, point.y)
        return None

    @staticmethod
    def relative_to_absolute(rel_x: int, rel_y: int, base_x: int, base_y: int) -> Tuple[int, int]:
        """相对坐标转绝对坐标

        Args:
            rel_x: 相对X坐标
            rel_y: 相对Y坐标
            base_x: 基准X坐标
            base_y: 基准Y坐标

        Returns:
            (absolute_x, absolute_y) 元组
        """
        return (base_x + rel_x, base_y + rel_y)

    @staticmethod
    def absolute_to_relative(abs_x: int, abs_y: int, base_x: int, base_y: int) -> Tuple[int, int]:
        """绝对坐标转相对坐标

        Args:
            abs_x: 绝对X坐标
            abs_y: 绝对Y坐标
            base_x: 基准X坐标
            base_y: 基准Y坐标

        Returns:
            (relative_x, relative_y) 元组
        """
        return (abs_x - base_x, abs_y - base_y)

    @staticmethod
    def find_window(title: str = None, class_name: str = None) -> Optional[wintypes.HWND]:
        """查找窗口句柄

        Args:
            title: 窗口标题
            class_name: 窗口类名

        Returns:
            窗口句柄
        """
        return user32.FindWindowW(class_name, title)

    @staticmethod
    def get_foreground_window() -> Optional[wintypes.HWND]:
        """获取前台窗口句柄

        Returns:
            窗口句柄
        """
        return user32.GetForegroundWindow()
