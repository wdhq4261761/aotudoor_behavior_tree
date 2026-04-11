"""
测试报警节点默认值修复
"""
import os
import tempfile
from bt_nodes.actions.alarm import AlarmNode
from bt_core.config import NodeConfig
from config.settings_manager import SettingsManager
from bt_utils.resource_manager import ResourceManager

def test_alarm_node_default_values():
    """测试报警节点默认值是否正确保存到 config 中"""
    
    # 创建一个空的 NodeConfig
    config = NodeConfig()
    
    # 创建报警节点
    node = AlarmNode("test_alarm", config)
    
    # 获取默认值
    default_sound = ResourceManager().get_alarm_sound_path()
    default_volume = SettingsManager().get("alarm_volume", 70)
    
    # 验证实例变量
    assert node.sound_path == default_sound, f"sound_path 应该是 {default_sound}"
    assert node.volume == default_volume, f"volume 应该是 {default_volume}"
    
    # 验证 config.extra 中是否保存了默认值
    assert "sound_path" in config.extra, "sound_path 应该被保存到 config.extra 中"
    assert "volume" in config.extra, "volume 应该被保存到 config.extra 中"
    
    assert config.extra["sound_path"] == default_sound, f"config.extra['sound_path'] 应该是 {default_sound}"
    assert config.extra["volume"] == default_volume, f"config.extra['volume'] 应该是 {default_volume}"
    
    print("[OK] 测试通过: 报警节点默认值正确保存到 config 中")
    print(f"  - 默认音效路径: {default_sound}")
    print(f"  - 默认音量: {default_volume}")
    print(f"  - config.extra: {config.extra}")

def test_alarm_node_custom_values():
    """测试报警节点自定义值是否正确"""
    
    # 创建一个带有自定义值的 NodeConfig
    config = NodeConfig()
    config.set("sound_path", "custom_sound.mp3")
    config.set("volume", 50)
    
    # 创建报警节点
    node = AlarmNode("test_alarm", config)
    
    # 验证实例变量使用了自定义值
    assert node.sound_path == "custom_sound.mp3", "sound_path 应该是自定义值"
    assert node.volume == 50, "volume 应该是自定义值"
    
    # 验证 config.extra 中的值没有被覆盖
    assert config.extra["sound_path"] == "custom_sound.mp3", "config.extra['sound_path'] 不应该被覆盖"
    assert config.extra["volume"] == 50, "config.extra['volume'] 不应该被覆盖"
    
    print("[OK] 测试通过: 报警节点自定义值正确")
    print(f"  - 自定义音效路径: custom_sound.mp3")
    print(f"  - 自定义音量: 50")

def test_alarm_node_serialization():
    """测试报警节点序列化和反序列化"""
    
    # 创建一个空的 NodeConfig
    config = NodeConfig()
    
    # 创建报警节点
    node1 = AlarmNode("test_alarm", config)
    
    # 序列化
    node_dict = node1.to_dict()
    
    # 验证序列化后的数据包含默认值
    assert "config" in node_dict, "序列化数据应该包含 config"
    assert "extra" in node_dict["config"], "config 应该包含 extra"
    assert "sound_path" in node_dict["config"]["extra"], "extra 应该包含 sound_path"
    assert "volume" in node_dict["config"]["extra"], "extra 应该包含 volume"
    
    # 反序列化
    node2 = AlarmNode.from_dict(node_dict)
    
    # 验证反序列化后的节点有相同的值
    assert node2.sound_path == node1.sound_path, "反序列化后的 sound_path 应该相同"
    assert node2.volume == node1.volume, "反序列化后的 volume 应该相同"
    
    print("[OK] 测试通过: 报警节点序列化和反序列化正确")
    print(f"  - 序列化数据: {node_dict['config']['extra']}")

if __name__ == "__main__":
    print("\n=== 开始测试报警节点默认值修复 ===\n")
    
    test_alarm_node_default_values()
    print()
    
    test_alarm_node_custom_values()
    print()
    
    test_alarm_node_serialization()
    print()
    
    print("=== 所有测试通过! ===\n")
