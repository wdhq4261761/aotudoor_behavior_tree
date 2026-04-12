import threading
import time
from typing import Callable, Dict, Optional, Set
from pynput import keyboard


class GlobalHotkeyManager:
    """全局热键管理器
    
    使用 pynput 库实现全局热键监听，支持在窗口失去焦点时也能响应快捷键。
    添加了优化来减少被 pyautogui 模拟按键干扰的可能性。
    """
    
    _instance: Optional["GlobalHotkeyManager"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._listener: Optional[keyboard.Listener] = None
        self._hotkeys: Dict[str, Callable] = {}
        self._pressed_keys: Set[keyboard.Key] = set()
        self._lock = threading.Lock()
        self._running = False
        self._last_trigger_time: Dict[str, float] = {}
        self._debounce_interval = 0.1
    
    @classmethod
    def get_instance(cls) -> "GlobalHotkeyManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        if cls._instance is not None:
            cls._instance.stop()
            cls._instance = None
    
    def start(self):
        """启动全局热键监听"""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
                suppress=False
            )
            self._listener.start()
    
    def stop(self):
        """停止全局热键监听"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            if self._listener:
                self._listener.stop()
                self._listener = None
            self._pressed_keys.clear()
            self._last_trigger_time.clear()
    
    def register(self, key_name: str, callback: Callable):
        """注册热键
        
        Args:
            key_name: 热键名称，如 "F10", "F12", "ctrl+s" 等
            callback: 回调函数
        """
        normalized = self._normalize_key(key_name)
        with self._lock:
            self._hotkeys[normalized] = callback
    
    def unregister(self, key_name: str):
        """取消注册热键
        
        Args:
            key_name: 热键名称
        """
        normalized = self._normalize_key(key_name)
        with self._lock:
            if normalized in self._hotkeys:
                del self._hotkeys[normalized]
    
    def update_hotkey(self, old_key: str, new_key: str, callback: Callable):
        """更新热键绑定
        
        Args:
            old_key: 旧热键
            new_key: 新热键
            callback: 回调函数
        """
        if old_key:
            self.unregister(old_key)
        if new_key:
            self.register(new_key, callback)
    
    def _normalize_key(self, key_name: str) -> str:
        """标准化热键名称
        
        Args:
            key_name: 原始热键名称
            
        Returns:
            标准化后的热键名称
        """
        if not key_name:
            return ""
        
        key_name = key_name.strip().lower()
        
        key_name = key_name.replace("<", "").replace(">", "")
        
        parts = key_name.split("+")
        parts = [p.strip() for p in parts]
        
        normalized_parts = []
        for part in parts:
            if part in ("ctrl", "control"):
                normalized_parts.append("ctrl")
            elif part in ("alt",):
                normalized_parts.append("alt")
            elif part in ("shift",):
                normalized_parts.append("shift")
            elif part in ("win", "super", "cmd", "command"):
                normalized_parts.append("cmd")
            elif part.startswith("f") and part[1:].isdigit():
                normalized_parts.append(part)
            elif len(part) == 1:
                normalized_parts.append(part)
            else:
                normalized_parts.append(part)
        
        return "+".join(sorted(normalized_parts))
    
    def _on_press(self, key):
        """按键按下事件处理"""
        try:
            from bt_utils.input_controller import InputController
            if InputController.is_simulating():
                return
            
            key_name = self._get_key_name(key)
            if key_name:
                self._pressed_keys.add(key_name)
                self._check_hotkeys()
        except Exception:
            pass
    
    def _on_release(self, key):
        """按键释放事件处理"""
        try:
            from bt_utils.input_controller import InputController
            if InputController.is_simulating():
                return
            
            key_name = self._get_key_name(key)
            if key_name and key_name in self._pressed_keys:
                self._pressed_keys.discard(key_name)
        except Exception:
            pass
    
    def _get_key_name(self, key) -> str:
        """获取按键名称
        
        Args:
            key: pynput 按键对象
            
        Returns:
            标准化的按键名称
        """
        if hasattr(key, 'char') and key.char:
            return key.char.lower()
        elif hasattr(key, 'name'):
            name = key.name.lower()
            if name.startswith('ctrl'):
                return 'ctrl'
            elif name.startswith('alt'):
                return 'alt'
            elif name.startswith('shift'):
                return 'shift'
            elif name.startswith('cmd') or name.startswith('super'):
                return 'cmd'
            elif name.startswith('f') and name[1:].isdigit():
                return name
            return name
        return str(key).lower()
    
    def _check_hotkeys(self):
        """检查是否触发了注册的热键"""
        current_combo = self._get_current_combo()
        
        with self._lock:
            if current_combo in self._hotkeys:
                current_time = time.time()
                last_time = self._last_trigger_time.get(current_combo, 0)
                
                if current_time - last_time < self._debounce_interval:
                    return
                
                self._last_trigger_time[current_combo] = current_time
                callback = self._hotkeys[current_combo]
                try:
                    callback()
                except Exception as e:
                    print(f"[WARN] 热键回调执行失败: {e}")
    
    def _get_current_combo(self) -> str:
        """获取当前按下的组合键
        
        Returns:
            组合键字符串
        """
        return "+".join(sorted(self._pressed_keys))


def get_hotkey_manager() -> GlobalHotkeyManager:
    """获取全局热键管理器单例"""
    return GlobalHotkeyManager.get_instance()
