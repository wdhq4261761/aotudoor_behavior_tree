from typing import Any, Dict, List, Callable
import threading


class Blackboard:
    """黑板系统 - 节点间数据共享

    提供节点间的数据共享机制，支持订阅/通知模式。
    线程安全实现，使用可重入锁保护数据访问。

    Attributes:
        BUILTIN_VARS: 内置变量默认值
    """
    BUILTIN_VARS = {
        "last_detection_position": None,
        "last_number_value": None,
        "execution_count": 0,
    }

    def __init__(self):
        self._data: Dict[str, Any] = dict(self.BUILTIN_VARS)
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()

    def get(self, key: str, default: Any = None) -> Any:
        """获取变量值

        Args:
            key: 变量名
            default: 默认值

        Returns:
            变量值
        """
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置变量值

        Args:
            key: 变量名
            value: 变量值
        """
        with self._lock:
            old_value = self._data.get(key)
            self._data[key] = value
            self._notify_subscribers(key, old_value, value)

    def increment(self, key: str, amount: int = 1) -> None:
        """递增变量

        Args:
            key: 变量名
            amount: 递增量
        """
        with self._lock:
            current = self._data.get(key, 0)
            if isinstance(current, (int, float)):
                self._data[key] = current + amount

    def delete(self, key: str) -> None:
        """删除变量

        Args:
            key: 变量名
        """
        with self._lock:
            if key in self._data and key not in self.BUILTIN_VARS:
                del self._data[key]

    def exists(self, key: str) -> bool:
        """检查变量是否存在

        Args:
            key: 变量名

        Returns:
            是否存在
        """
        with self._lock:
            return key in self._data

    def clear(self) -> None:
        """清空黑板（保留内置变量）"""
        with self._lock:
            self._data = dict(self.BUILTIN_VARS)

    def subscribe(self, key: str, callback: Callable[[Any, Any], None]) -> None:
        """订阅变量变化

        Args:
            key: 变量名
            callback: 回调函数 (old_value, new_value)
        """
        with self._lock:
            if key not in self._subscribers:
                self._subscribers[key] = []
            self._subscribers[key].append(callback)

    def unsubscribe(self, key: str, callback: Callable = None) -> None:
        """取消订阅

        Args:
            key: 变量名
            callback: 回调函数，为None时取消所有订阅
        """
        with self._lock:
            if key not in self._subscribers:
                return

            if callback is None:
                del self._subscribers[key]
            elif callback in self._subscribers[key]:
                self._subscribers[key].remove(callback)

    def _notify_subscribers(self, key: str, old_value: Any, new_value: Any) -> None:
        """通知订阅者

        Args:
            key: 变量名
            old_value: 旧值
            new_value: 新值
        """
        if key in self._subscribers:
            subscribers = self._subscribers[key][:]
            for callback in subscribers:
                try:
                    callback(old_value, new_value)
                except Exception:
                    pass

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典

        Returns:
            字典表示
        """
        with self._lock:
            return dict(self._data)

    def from_dict(self, data: Dict[str, Any]) -> None:
        """从字典导入

        Args:
            data: 字典数据
        """
        with self._lock:
            self._data.update(data)

    def get_all_keys(self) -> List[str]:
        """获取所有变量名

        Returns:
            变量名列表
        """
        with self._lock:
            return list(self._data.keys())

    def get_snapshot(self) -> Dict[str, Any]:
        """获取黑板数据快照

        Returns:
            数据快照
        """
        with self._lock:
            return dict(self._data)
