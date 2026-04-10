import os
import subprocess
import sys
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

    def _detect_code_type(self) -> str:
        if self.code_type != "auto":
            return self.code_type

        _, ext = os.path.splitext(self.code_path.lower())
        
        for code_type, extensions in self.CODE_TYPE_EXTENSIONS.items():
            if ext in extensions:
                return code_type

        return "python"

    def _build_command(self) -> List[str]:
        code_type = self._detect_code_type()
        
        if code_type == "python":
            cmd = [sys.executable, self.code_path]
        elif code_type == "batch":
            cmd = ["cmd", "/c", self.code_path]
        elif code_type == "powershell":
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", self.code_path]
        else:
            cmd = [sys.executable, self.code_path]

        if self.args:
            cmd.extend([str(arg) for arg in self.args])

        return cmd

    def _execute_action(self, context) -> NodeStatus:
        try:
            if not os.path.exists(self.code_path):
                print(f"[WARN] CodeNode: 代码文件不存在: {self.code_path}")
                return NodeStatus.FAILURE

            cmd = self._build_command()
            
            if self.wait_complete:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                if result.returncode != 0:
                    print(f"[WARN] CodeNode执行失败 (返回码: {result.returncode})")
                    if result.stderr:
                        print(f"   错误输出: {result.stderr[:500]}")
                    return NodeStatus.FAILURE
                
                return NodeStatus.SUCCESS
            else:
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return NodeStatus.SUCCESS

        except Exception as e:
            print(f"[WARN] CodeNode错误: {e}")
            return NodeStatus.FAILURE

    def abort(self, context) -> None:
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=2)
            except Exception:
                try:
                    self._process.kill()
                except Exception:
                    pass
        self._process = None
        super().abort(context)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"]["extra"]["code_path"] = self.code_path
        data["config"]["extra"]["code_type"] = self.code_type
        data["config"]["extra"]["args"] = self.args
        data["config"]["extra"]["wait_complete"] = self.wait_complete
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
