import threading
from queue import Queue, Empty
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import time


class UpdateType(Enum):
    NODE_STATUS = "node_status"
    LOG_FLUSH = "log_flush"
    CANVAS_REDRAW = "canvas_redraw"
    ENGINE_STATUS = "engine_status"


@dataclass
class UpdateTask:
    update_type: UpdateType
    data: Any
    callback: Callable


class UIUpdateDispatcher:
    _instance: Optional["UIUpdateDispatcher"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._task_queue: Queue = Queue()
        self._widget = None
        self._last_event_time = 0
        self._event_debounce_ms = 16
        self._node_status_cache: Dict[str, tuple] = {}
        self._max_batch_size = 50
        self._polling_active = False
        self._polling_interval_ms = 30
    
    @classmethod
    def get_instance(cls) -> "UIUpdateDispatcher":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        with cls._lock:
            if cls._instance is not None:
                cls._instance = None
    
    def attach(self, widget):
        self._widget = widget
        widget.bind("<<UIUpdate>>", self._process_updates)
    
    def detach(self):
        if self._widget:
            self._widget.unbind("<<UIUpdate>>")
            self._widget = None
    
    def dispatch(self, update_type: UpdateType, data: Any = None, callback: Callable = None):
        if update_type == UpdateType.NODE_STATUS:
            node_id = data.get("node_id") if data else None
            if node_id:
                self._node_status_cache[node_id] = (data, callback)
        
        task = UpdateTask(update_type, data, callback)
        self._task_queue.put(task)
        
        self._schedule_process()
    
    def dispatch_node_status(self, node_id: str, status: str, callback: Callable = None):
        if node_id:
            self._node_status_cache[node_id] = ({"node_id": node_id, "status": status}, callback)
        
        task = UpdateTask(UpdateType.NODE_STATUS, {"node_id": node_id, "status": status}, callback)
        self._task_queue.put(task)
        
        self._schedule_process()
    
    def dispatch_log_flush(self):
        task = UpdateTask(UpdateType.LOG_FLUSH, None, None)
        self._task_queue.put(task)
        self._schedule_process()
    
    def dispatch_engine_status(self, status: str, node_status: Any = None, callback: Callable = None):
        task = UpdateTask(UpdateType.ENGINE_STATUS, {"status": status, "node_status": node_status}, callback)
        self._task_queue.put(task)
        
        self._schedule_process()
    
    def _schedule_process(self):
        if self._widget is None:
            return
        
        try:
            self._widget.after(0, self._process_updates_safe)
        except Exception:
            pass
    
    def _process_updates_safe(self):
        try:
            self._process_updates()
        except Exception as e:
            print(f"[WARN] UI更新处理失败: {e}")
    
    def _process_updates(self, event=None):
        processed = 0
        
        while processed < self._max_batch_size:
            try:
                task = self._task_queue.get_nowait()
                
                if task.update_type == UpdateType.NODE_STATUS:
                    node_id = task.data.get("node_id") if task.data else None
                    if node_id and node_id in self._node_status_cache:
                        cached_data, cached_callback = self._node_status_cache.pop(node_id, (None, None))
                        if cached_callback:
                            try:
                                cached_callback(cached_data.get("node_id"), cached_data.get("status"))
                            except Exception as e:
                                print(f"[WARN] UI更新回调执行失败: {e}")
                            processed += 1
                            continue
                
                if task.callback:
                    try:
                        if task.update_type == UpdateType.NODE_STATUS and task.data:
                            task.callback(task.data.get("node_id"), task.data.get("status"))
                        else:
                            task.callback(task.data)
                    except Exception as e:
                        print(f"[WARN] UI更新回调执行失败: {e}")
                
                processed += 1
                
            except Empty:
                break
        
        if not self._task_queue.empty():
            if self._widget:
                self._widget.after(10, self._process_updates_safe)
    
    def process_pending(self):
        self._process_updates()
    
    def get_pending_count(self) -> int:
        return self._task_queue.qsize()
    
    def clear_all(self):
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
            except Empty:
                break
        self._node_status_cache.clear()
    
    def start_polling(self):
        if self._polling_active:
            return
        
        self._polling_active = True
        self._poll()
    
    def stop_polling(self):
        self._polling_active = False
    
    def _poll(self):
        if not self._polling_active:
            return
        
        if self._widget is None:
            return
        
        try:
            pending = self._task_queue.qsize()
            if pending > 0:
                self._process_updates()
        except Exception:
            pass
        
        if self._polling_active:
            self._widget.after(self._polling_interval_ms, self._poll)


def get_dispatcher() -> UIUpdateDispatcher:
    return UIUpdateDispatcher.get_instance()
