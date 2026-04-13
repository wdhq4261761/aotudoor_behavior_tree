from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List
import threading
from bt_utils.singleton import singleton


class LogLevel(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    ABORTED = "aborted"
    INFO = "info"


@dataclass
class LogEntry:
    timestamp: datetime = field(default_factory=datetime.now)
    level: LogLevel = LogLevel.INFO
    node_type: str = ""
    node_name: str = ""
    message: str = ""
    
    def format(self) -> str:
        time_str = self.timestamp.strftime("%H:%M:%S")
        
        if self.level == LogLevel.SUCCESS:
            if self.message:
                return f"[{time_str}] ✅ {self.node_type} \"{self.node_name}\" - 成功: {self.message}"
            return f"[{time_str}] ✅ {self.node_type} \"{self.node_name}\" - 成功"
        elif self.level == LogLevel.FAILURE:
            return f"[{time_str}] ❌ {self.node_type} \"{self.node_name}\" - 失败: {self.message}"
        elif self.level == LogLevel.ABORTED:
            return f"[{time_str}] ⏸️ {self.node_type} \"{self.node_name}\" - 中止"
        else:
            return f"[{time_str}] ℹ️ {self.node_type} \"{self.node_name}\" - {self.message}"


@singleton
class LogManager:
    """日志管理器
    
    使用单例模式，线程安全。
    """
    
    def __init__(self):
        self._buffer: List[LogEntry] = []
        self._buffer_lock = threading.Lock()
    
    @classmethod
    def instance(cls) -> "LogManager":
        return cls()
    
    def log(self, entry: LogEntry) -> None:
        with self._buffer_lock:
            self._buffer.append(entry)
        
        try:
            from bt_utils.ui_dispatcher import UIUpdateDispatcher
            dispatcher = UIUpdateDispatcher.get_instance()
            dispatcher.dispatch_log_flush()
        except ImportError:
            pass
    
    def log_success(self, node_type: str, node_name: str, message: str = "") -> None:
        self.log(LogEntry(
            level=LogLevel.SUCCESS,
            node_type=node_type,
            node_name=node_name,
            message=message
        ))
    
    def log_failure(self, node_type: str, node_name: str, reason: str) -> None:
        self.log(LogEntry(
            level=LogLevel.FAILURE,
            node_type=node_type,
            node_name=node_name,
            message=reason
        ))
    
    def log_aborted(self, node_type: str, node_name: str) -> None:
        self.log(LogEntry(
            level=LogLevel.ABORTED,
            node_type=node_type,
            node_name=node_name
        ))
    
    def log_info(self, node_type: str, node_name: str, message: str = "") -> None:
        self.log(LogEntry(
            level=LogLevel.INFO,
            node_type=node_type,
            node_name=node_name,
            message=message
        ))
    
    def flush(self) -> List[LogEntry]:
        with self._buffer_lock:
            entries = self._buffer.copy()
            self._buffer.clear()
            return entries
    
    def clear(self) -> None:
        with self._buffer_lock:
            self._buffer.clear()
    
    def get_buffer_size(self) -> int:
        with self._buffer_lock:
            return len(self._buffer)
