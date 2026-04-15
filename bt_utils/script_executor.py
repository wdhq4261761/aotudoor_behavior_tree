import threading
import time
import re
import weakref
import atexit
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor


class ScriptExecutor:
    """脚本执行器

    解析和执行脚本文件，支持循环执行和暂停/恢复。
    使用线程池优化并发执行。
    
    支持上下文管理器协议，确保资源正确释放。
    
    使用方式:
        # 方式1：上下文管理器（推荐）
        with ScriptExecutor() as executor:
            executor.run_script(script)
        
        # 方式2：手动管理
        executor = ScriptExecutor()
        try:
            executor.run_script(script)
        finally:
            executor.shutdown()
    """
    
    _instances = weakref.WeakSet()
    
    _executor_pool: Optional[ThreadPoolExecutor] = None
    _futures: Dict[str, any] = {}
    
    def __init__(self, max_workers: int = 4):
        self.is_running = False
        self.is_paused = False
        self.execution_thread = None
        self._input_controller = None
        self._executor_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._futures = {}
        
        ScriptExecutor._instances.add(self)
    
    def __enter__(self) -> "ScriptExecutor":
        """进入上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """退出上下文管理器，确保资源释放"""
        self.shutdown()
        return False
    
    def __del__(self):
        """析构方法，作为资源清理的最后保障"""
        try:
            self.shutdown()
        except Exception:
            pass
    
    @classmethod
    def cleanup_all(cls) -> None:
        """清理所有实例（用于程序退出时）"""
        for instance in list(cls._instances):
            try:
                instance.shutdown()
            except Exception:
                pass
        
    @property
    def input_controller(self):
        if self._input_controller is None:
            from .input_controller_factory import InputController
            self._input_controller = InputController()
        return self._input_controller
    
    def run_script(self, script_content: str, loop: bool = False) -> None:
        """执行脚本

        Args:
            script_content: 脚本内容
            loop: 是否循环执行
        """
        commands = self._parse_script(script_content)
        if not commands:
            return

        self.is_running = True
        self.is_paused = False

        def execute():
            pressed_keys = set()

            while self.is_running:
                for command in commands:
                    if not self.is_running:
                        break

                    while self.is_paused:
                        time.sleep(0.1)

                    self._execute_command(command, pressed_keys)

                if not loop:
                    break

            self._release_all_keys(pressed_keys)
            self.is_running = False

        self.execution_thread = threading.Thread(target=execute, daemon=True)
        self.execution_thread.start()
    
    def submit_script(self, script_id: str, script_content: str, 
                      loop: bool = False, callback=None) -> None:
        """提交脚本到线程池执行

        Args:
            script_id: 脚本ID
            script_content: 脚本内容
            loop: 是否循环执行
            callback: 完成回调
        """
        commands = self._parse_script(script_content)
        if not commands:
            if callback:
                callback(False)
            return

        def execute():
            pressed_keys = set()
            success = True
            
            try:
                while self.is_running:
                    for command in commands:
                        if not self.is_running:
                            break

                        while self.is_paused:
                            time.sleep(0.1)

                        self._execute_command(command, pressed_keys)

                    if not loop:
                        break
            except Exception:
                success = False
            finally:
                self._release_all_keys(pressed_keys)
                
            if script_id in self._futures:
                del self._futures[script_id]
            
            if callback:
                callback(success)

        future = self._executor_pool.submit(execute)
        self._futures[script_id] = future
    
    def cancel_script(self, script_id: str) -> bool:
        """取消脚本执行

        Args:
            script_id: 脚本ID

        Returns:
            是否成功取消
        """
        if script_id in self._futures:
            future = self._futures[script_id]
            cancelled = future.cancel()
            del self._futures[script_id]
            return cancelled
        return False

    def _parse_script(self, content: str) -> List[dict]:
        """解析脚本内容

        Args:
            content: 脚本内容

        Returns:
            命令列表
        """
        commands = []

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            key_pattern = re.compile(r'^(KeyDown|KeyUp)\s+["\'](.*?)["\']\s*,\s*(\d+)$', re.IGNORECASE)
            match = key_pattern.match(line)
            if match:
                commands.append({
                    "type": match.group(1).lower(),
                    "key": match.group(2).lower(),
                    "count": int(match.group(3))
                })
                continue

            mouse_pattern = re.compile(r'^(Left|Right|Middle)(Down|Up)\s+(\d+)$', re.IGNORECASE)
            match = mouse_pattern.match(line)
            if match:
                commands.append({
                    "type": f"mouse_{match.group(2).lower()}",
                    "button": match.group(1).lower(),
                    "count": int(match.group(3))
                })
                continue

            move_pattern = re.compile(r'^MoveTo\s+(\d+)\s*,\s*(\d+)$', re.IGNORECASE)
            match = move_pattern.match(line)
            if match:
                commands.append({
                    "type": "moveto",
                    "x": int(match.group(1)),
                    "y": int(match.group(2))
                })
                continue

            delay_pattern = re.compile(r'^Delay\s+(\d+)$', re.IGNORECASE)
            match = delay_pattern.match(line)
            if match:
                commands.append({
                    "type": "delay",
                    "time": int(match.group(1))
                })
                continue

        return commands

    def _execute_command(self, command: dict, pressed_keys: set) -> None:
        """执行单个命令

        Args:
            command: 命令字典
            pressed_keys: 已按下按键集合
        """
        if command["type"] == "keydown":
            key = command["key"]
            for _ in range(command["count"]):
                if key not in pressed_keys:
                    self.input_controller.key_down(key)
                    pressed_keys.add(key)

        elif command["type"] == "keyup":
            key = command["key"]
            for _ in range(command["count"]):
                if key in pressed_keys:
                    self.input_controller.key_up(key)
                    pressed_keys.remove(key)

        elif command["type"] == "mouse_down":
            for _ in range(command["count"]):
                self.input_controller.mouse_down(command["button"])

        elif command["type"] == "mouse_up":
            for _ in range(command["count"]):
                self.input_controller.mouse_up(command["button"])

        elif command["type"] == "moveto":
            self.input_controller.move_to(command["x"], command["y"])

        elif command["type"] == "delay":
            delay_time = command["time"] / 1000
            elapsed = 0
            while elapsed < delay_time and self.is_running:
                sleep_time = min(0.1, delay_time - elapsed)
                time.sleep(sleep_time)
                elapsed += sleep_time

    def _release_all_keys(self, pressed_keys: set) -> None:
        """释放所有按键

        Args:
            pressed_keys: 已按下按键集合
        """
        for key in pressed_keys:
            try:
                self.input_controller.key_up(key)
            except Exception:
                pass

    def stop_script(self) -> None:
        """停止脚本执行"""
        self.is_running = False
        self.is_paused = False
        
        for future in self._futures.values():
            future.cancel()
        self._futures.clear()

    def pause_script(self) -> None:
        """暂停脚本执行"""
        self.is_paused = True

    def resume_script(self) -> None:
        """恢复脚本执行"""
        self.is_paused = False
        
    def shutdown(self) -> None:
        """关闭线程池"""
        self.stop_script()
        if self._executor_pool:
            self._executor_pool.shutdown(wait=False)
            self._executor_pool = None


atexit.register(ScriptExecutor.cleanup_all)
