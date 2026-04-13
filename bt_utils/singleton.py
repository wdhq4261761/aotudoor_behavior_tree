"""
单例模式装饰器

提供线程安全的单例模式实现。
"""
import threading
from typing import TypeVar, Callable, Any

T = TypeVar('T')


def singleton(cls: type) -> type:
    """线程安全的单例装饰器
    
    使用方式:
        @singleton
        class MyClass:
            pass
        
        instance = MyClass()  # 总是返回同一个实例
    
    特点:
        1. 线程安全：使用双重检查锁定
        2. 延迟初始化：首次调用时创建实例
        3. 透明使用：对调用者完全透明
        4. 保留类的静态方法和类方法
    """
    _instance = None
    _lock = threading.Lock()
    
    class SingletonWrapper(cls):
        """单例包装器，继承原始类以保留所有属性"""
        
        _original_class = cls
        _is_singleton = True
        _singleton_instance = None
        _singleton_lock = _lock
        
        def __new__(cls, *args, **kwargs):
            nonlocal _instance
            
            if _instance is None:
                with _lock:
                    if _instance is None:
                        _instance = super().__new__(cls)
                        _instance._singleton_initialized = False
            return _instance
        
        def __init__(self, *args, **kwargs):
            if not getattr(self, '_singleton_initialized', False):
                with _lock:
                    if not getattr(self, '_singleton_initialized', False):
                        super().__init__(*args, **kwargs)
                        self._singleton_initialized = True
    
    SingletonWrapper.__name__ = cls.__name__
    SingletonWrapper.__qualname__ = cls.__qualname__
    SingletonWrapper.__doc__ = cls.__doc__
    SingletonWrapper.__module__ = cls.__module__
    
    return SingletonWrapper


def is_singleton(cls: type) -> bool:
    """检查类是否为单例"""
    return getattr(cls, '_is_singleton', False)


def reset_singleton(cls: type) -> None:
    """重置单例实例（仅用于测试）
    
    警告：此函数仅应在测试代码中使用，
    在生产代码中调用可能导致不可预期行为。
    """
    if hasattr(cls, '_singleton_lock'):
        with cls._singleton_lock:
            if hasattr(cls, '_original_class'):
                original_cls = cls._original_class
                if hasattr(original_cls, '_instance'):
                    original_cls._instance = None
            cls._singleton_instance = None
