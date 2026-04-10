import ctypes
from ctypes import wintypes
import numpy as np
from PIL import Image
from typing import Optional, Tuple
import os

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

HWND = wintypes.HWND
HDC = wintypes.HDC
HBITMAP = wintypes.HANDLE
BOOL = wintypes.BOOL
RECT = wintypes.RECT

PW_CLIENTONLY = 0x1
PW_RENDERFULLCONTENT = 0x2

SRCCOPY = 0x00CC0020


class WindowCapture:
    """窗口捕获类

    使用Windows PrintWindow API进行后台截图。
    支持窗口最小化时截图。
    """

    @staticmethod
    def find_window(title: str = None, class_name: str = None) -> Optional[HWND]:
        """查找窗口句柄

        Args:
            title: 窗口标题（部分匹配）
            class_name: 窗口类名

        Returns:
            窗口句柄，未找到返回None
        """
        if title:
            hwnd = user32.FindWindowW(class_name, title)
            if hwnd:
                return hwnd

            hwnd = user32.GetForegroundWindow()
            if hwnd:
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buffer, length + 1)
                    if title.lower() in buffer.value.lower():
                        return hwnd

        return None

    @staticmethod
    def get_window_rect(hwnd: HWND) -> Optional[Tuple[int, int, int, int]]:
        """获取窗口矩形区域

        Args:
            hwnd: 窗口句柄

        Returns:
            (left, top, right, bottom) 元组
        """
        rect = RECT()
        if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return (rect.left, rect.top, rect.right, rect.bottom)
        return None

    @staticmethod
    def capture_window(hwnd: HWND, client_only: bool = False) -> Optional[Image.Image]:
        """捕获窗口图像

        Args:
            hwnd: 窗口句柄
            client_only: 是否仅捕获客户区

        Returns:
            PIL.Image 图像对象
        """
        rect = WindowCapture.get_window_rect(hwnd)
        if not rect:
            return None

        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        if width <= 0 or height <= 0:
            return None

        hwndDC = user32.GetWindowDC(hwnd)
        if not hwndDC:
            return None

        try:
            hdcMem = gdi32.CreateCompatibleDC(hwndDC)
            if not hdcMem:
                return None

            hBitmap = gdi32.CreateCompatibleBitmap(hwndDC, width, height)
            if not hBitmap:
                gdi32.DeleteDC(hdcMem)
                return None

            gdi32.SelectObject(hdcMem, hBitmap)

            flags = PW_CLIENTONLY if client_only else 0
            flags |= PW_RENDERFULLCONTENT

            result = user32.PrintWindow(hwnd, hdcMem, flags)

            if result:
                bitmap_info = BITMAPINFO()
                bitmap_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
                bitmap_info.bmiHeader.biWidth = width
                bitmap_info.bmiHeader.biHeight = -height
                bitmap_info.bmiHeader.biPlanes = 1
                bitmap_info.bmiHeader.biBitCount = 32
                bitmap_info.bmiHeader.biCompression = 0

                buffer_size = width * height * 4
                buffer = ctypes.create_string_buffer(buffer_size)

                gdi32.GetDIBits(
                    hdcMem, hBitmap, 0, height,
                    buffer, ctypes.byref(bitmap_info),
                    0
                )

                img_array = np.frombuffer(buffer.raw, dtype=np.uint8)
                img_array = img_array.reshape((height, width, 4))
                img_array = img_array[:, :, :3]
                img_array = img_array[:, :, ::-1]

                image = Image.fromarray(img_array, 'RGB')
                return image

        finally:
            gdi32.DeleteObject(hBitmap)
            gdi32.DeleteDC(hdcMem)
            user32.ReleaseDC(hwnd, hwndDC)

        return None

    @staticmethod
    def capture_by_title(title: str, client_only: bool = False) -> Optional[Image.Image]:
        """根据标题捕获窗口

        Args:
            title: 窗口标题
            client_only: 是否仅捕获客户区

        Returns:
            PIL.Image 图像对象
        """
        hwnd = WindowCapture.find_window(title=title)
        if not hwnd:
            return None

        return WindowCapture.capture_window(hwnd, client_only)


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3),
    ]
