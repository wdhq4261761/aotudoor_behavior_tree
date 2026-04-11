import os
import subprocess
import sys
import threading
from bt_core.nodes import ActionNode, NodeStatus
from bt_core.config import NodeConfig
from typing import Dict, Any, List, Optional


class CodeNode(ActionNode):
    NODE_TYPE = "CodeNode"

    CODE_TYPE_EXTENSIONS = {
        "python": [".py", ".pyw"],
        "batch": [".bat", ".cmd"],
        "powershell": [".ps1"],
    }

    def __init__(self, node_id: str = None, config: NodeConfig = None):
        super().__init__(node_id, config)
        self.code_path = self.config.get("code_path", "")
        self.code_type = self.config.get("code_type", "auto")
        self.args: List[str] = self.config.get("args", [])
        self.wait_complete = self.config.get_bool("wait_complete", True)
        self._process: Optional[subprocess.Popen] = None
        self._aborted = False
        self._lock = threading.Lock()

    def _detect_code_type(self) -> str:
        if self.code_type != "auto":
            return self.code_type

        _, ext = os.path.splitext(self.code_path.lower())
        
        for code_type, extensions in self.CODE_TYPE_EXTENSIONS.items():
            if ext in extensions:
                return code_type

        return "python"

    def _build_command(self, code_path: str = None) -> List[str]:
        if code_path is None:
            code_path = self.code_path
        
        code_type = self._detect_code_type()
        
        if code_type == "python":
            cmd = [sys.executable, code_path]
        elif code_type == "batch":
            cmd = ["cmd", "/c", code_path]
        elif code_type == "powershell":
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", code_path]
        else:
            cmd = [sys.executable, code_path]

        if self.args:
            cmd.extend([str(arg) for arg in self.args])

        return cmd

    def _execute_action(self, context) -> NodeStatus:
        from bt_utils.log_manager import LogManager, LogLevel
        
        with self._lock:
            self._aborted = False
        
        try:
            code_path = self.code_path
            
            if not code_path:
                LogManager.instance().log_failure(
                    node_type="代码节点",
                    node_name=self.name,
                    reason="代码路径为空"
                )
                return NodeStatus.FAILURE
            
            absolute_code_path = code_path
            
            if code_path.startswith("./"):
                if hasattr(context, 'resolve_path') and context.resolve_path:
                    absolute_code_path = context.resolve_path(code_path)
                elif hasattr(context, 'project_root'):
                    project_root = context.project_root
                    absolute_code_path = os.path.join(project_root, code_path[2:])
                else:
                    LogManager.instance().log_failure(
                        node_type="代码节点",
                        node_name=self.name,
                        reason="无法解析相对路径，缺少项目根目录"
                    )
                    return NodeStatus.FAILURE
            else:
                if not os.path.isabs(code_path):
                    absolute_code_path = os.path.abspath(code_path)
            
            if not os.path.exists(absolute_code_path):
                LogManager.instance().log_failure(
                    node_type="代码节点",
                    node_name=self.name,
                    reason=f"代码文件不存在: {absolute_code_path}"
                )
                return NodeStatus.FAILURE

            cmd = self._build_command(absolute_code_path)
            
            import locale
            preferred_encoding = locale.getpreferredencoding(False)
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding=preferred_encoding,
                errors='replace'
            )
            
            if self.wait_complete:
                try:
                    stdout, stderr = self._process.communicate()
                    
                    with self._lock:
                        if self._aborted:
                            LogManager.instance().log_info(
                                node_type="代码节点",
                                node_name=self.name,
                                message="执行已被中止"
                            )
                            return NodeStatus.FAILURE
                    
                    if self._process.returncode != 0:
                        error_msg = f"返回码: {self._process.returncode}"
                        if stderr:
                            error_msg += f", 错误: {stderr[:200]}"
                        
                        LogManager.instance().log_failure(
                            node_type="代码节点",
                            node_name=self.name,
                            reason=error_msg
                        )
                        return NodeStatus.FAILURE
                    
                    if stdout and stdout.strip():
                        output_lines = stdout.strip().split('\n')
                        for line in output_lines:
                            LogManager.instance().log_info(
                                node_type="代码节点",
                                node_name=self.name,
                                message=line
                            )
                    else:
                        LogManager.instance().log_success(
                            node_type="代码节点",
                            node_name=self.name
                        )
                    return NodeStatus.SUCCESS
                    
                except Exception as e:
                    with self._lock:
                        if self._aborted:
                            return NodeStatus.FAILURE
                    raise
            else:
                LogManager.instance().log_success(
                    node_type="代码节点",
                    node_name=self.name
                )
                return NodeStatus.SUCCESS

        except Exception as e:
            LogManager.instance().log_failure(
                node_type="代码节点",
                node_name=self.name,
                reason=f"执行异常: {str(e)}"
            )
            return NodeStatus.FAILURE
        finally:
            self._process = None

    def abort(self, context) -> None:
        with self._lock:
            self._aborted = True
        
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=1)
            except Exception:
                pass
        self._process = None
        super().abort(context)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["code_path"] = self.code_path
        data["config"]["code_type"] = self.code_type
        data["config"]["args"] = self.args
        data["config"]["wait_complete"] = self.wait_complete
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeNode":
        config = NodeConfig.from_dict(data.get("config", {}))
        node = cls(node_id=data.get("id"), config=config)
        node.code_path = config.get("code_path", "")
        node.code_type = config.get("code_type", "auto")
        node.args = config.get("args", [])
        node.wait_complete = config.get_bool("wait_complete", True)
        return node
