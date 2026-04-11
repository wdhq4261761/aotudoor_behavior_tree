from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class NodeConfig:
    """节点配置数据类
    
    Args:
        name: 节点名称
        description: 节点描述
        enabled: 是否启用
        retry_count: 重试次数（-1表示无限）
        repeat_count: 重复次数（-1表示无限）
        repeat_interval_ms: 重复间隔（毫秒）
        timeout_ms: 超时时间（毫秒）
        extra: 额外配置字段
    """
    name: str = ""
    description: str = ""
    enabled: bool = True
    retry_count: int = 0
    repeat_count: int = 0
    repeat_interval_ms: int = 100
    timeout_ms: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        if hasattr(self, key):
            return getattr(self, key, default)
        return self.extra.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        if hasattr(self, key) and key != "extra":
            setattr(self, key, value)
        else:
            self.extra[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（扁平化格式，与原项目兼容）
        
        Returns:
            字典表示
        """
        result = {}
        
        if self.name:
            result["name"] = self.name
        if self.description:
            result["description"] = self.description
        result["enabled"] = self.enabled
        if self.retry_count != 0:
            result["retry_count"] = self.retry_count
        if self.repeat_count != 0:
            result["repeat_count"] = self.repeat_count
        if self.repeat_interval_ms != 100:
            result["repeat_interval_ms"] = self.repeat_interval_ms
        if self.timeout_ms != 0:
            result["timeout_ms"] = self.timeout_ms
        
        if self.extra:
            for key, value in self.extra.items():
                result[key] = value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeConfig":
        """从字典反序列化
        
        Args:
            data: 字典数据
            
        Returns:
            NodeConfig 实例
        """
        def to_int(value, default=0):
            if value is None:
                return default
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                try:
                    return int(value)
                except ValueError:
                    return default
            return default
        
        def to_bool(value, default=True):
            if value is None:
                return default
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        
        known_keys = {
            "name", "description", "enabled", "retry_count", 
            "repeat_count", "repeat_interval_ms", "timeout_ms", "extra"
        }
        
        extra = data.get("extra", {})
        
        for key, value in data.items():
            if key not in known_keys:
                extra[key] = value
        
        return cls(
            name=str(data.get("name", "")),
            description=str(data.get("description", "")),
            enabled=to_bool(data.get("enabled", True)),
            retry_count=to_int(data.get("retry_count", 0)),
            repeat_count=to_int(data.get("repeat_count", 0)),
            repeat_interval_ms=to_int(data.get("repeat_interval_ms", 100)),
            timeout_ms=to_int(data.get("timeout_ms", 0)),
            extra=extra,
        )
    
    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数类型的配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            整数配置值
        """
        value = self.get(key, default)
        if value is None:
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return default
        return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔类型的配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            布尔配置值
        """
        value = self.get(key, default)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点类型的配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            浮点配置值
        """
        value = self.get(key, default)
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return default
        return default
