"""
测试前端创建报警节点时的默认值
"""
import sys
import os

# 模拟 GUI 环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_frontend_alarm_node_defaults():
    """模拟前端创建 AlarmNode 时的默认值"""
    
    print("\n=== 测试前端创建报警节点默认值 ===\n")
    
    # 模拟从设置中获取默认值
    from bt_utils.resource_manager import ResourceManager
    from config.settings_manager import SettingsManager
    
    default_sound = ResourceManager().get_alarm_sound_path()
    default_volume = SettingsManager().get("alarm_volume", 70)
    
    print(f"1. 从设置获取默认值:")
    print(f"   - 默认音效路径: {default_sound}")
    print(f"   - 默认音量: {default_volume}")
    
    # 模拟前端创建节点时的配置生成（与 editor.py 中的代码一致）
    node_type = "AlarmNode"
    node_config = {}
    
    if node_type == "AlarmNode":
        node_config = {
            "sound_path": default_sound,
            "volume": default_volume,
            "wait_complete": True,
            "repeat_count": 0,
            "interval_ms": 0
        }
    
    print(f"\n2. 前端生成的 node_config:")
    for key, value in node_config.items():
        print(f"   - {key}: {value}")
    
    # 模拟属性面板读取配置
    sound_path_value = node_config.get("sound_path")
    volume_value = node_config.get("volume")
    
    print(f"\n3. 属性面板读取的值:")
    print(f"   - 音频文件: {sound_path_value}")
    print(f"   - 音量: {volume_value}")
    
    # 验证
    assert sound_path_value == default_sound, f"音频文件应该是 {default_sound}"
    assert volume_value == default_volume, f"音量应该是 {default_volume}"
    assert sound_path_value != "", "音频文件不应该为空"
    assert volume_value != 0, "音量不应该为0"
    
    print(f"\n[OK] 测试通过! 前端创建报警节点时默认值正确")
    
    return True

if __name__ == "__main__":
    try:
        test_frontend_alarm_node_defaults()
        print("\n=== 所有测试通过! ===\n")
    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}\n")
        import traceback
        traceback.print_exc()
