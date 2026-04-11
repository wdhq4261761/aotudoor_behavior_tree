"""
验证三个修复的测试
"""
import os
import tempfile
from bt_utils.project_manager import ProjectManager
from bt_utils.resource_importer import ResourceImporter
from bt_utils.package_exporter import PackageExporter
from bt_nodes.actions.alarm import AlarmNode
from bt_core.config import NodeConfig
from config.settings_manager import SettingsManager
from bt_utils.resource_manager import ResourceManager

def test_script_file_filter():
    """测试1: 脚本文件过滤器修复"""
    from bt_gui.bt_editor.property import NODE_CONFIG_SCHEMAS
    
    script_props = NODE_CONFIG_SCHEMAS.get("ScriptNode", [])
    script_path_prop = None
    for prop in script_props:
        if prop.get("key") == "script_path":
            script_path_prop = prop
            break
    
    assert script_path_prop is not None, "ScriptNode 应该有 script_path 属性"
    
    filetypes = script_path_prop.get("filetypes", [])
    assert len(filetypes) > 0, "script_path 应该有 filetypes"
    
    has_all_files = any("*.*" in ft for ft in filetypes)
    assert has_all_files, "filetypes 应该包含所有文件选项 (*.*)."
    
    print("[OK] 测试1通过: 脚本文件过滤器已修复,默认显示所有文件")

def test_alarm_node_defaults():
    """测试2: 报警节点默认值修复"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = os.path.join(tmp_dir, "TestProject")
        
        manager = ProjectManager(project_root)
        manager.create_project("TestProject", "测试项目")
        
        config = NodeConfig()
        node = AlarmNode("test_alarm", config)
        
        default_sound = ResourceManager().get_alarm_sound_path()
        default_volume = SettingsManager().get("alarm_volume", 70)
        
        assert node.sound_path == default_sound, f"报警节点应该使用默认音效路径: {default_sound}"
        assert node.volume == default_volume, f"报警节点应该使用默认音量: {default_volume}"
        
        print(f"[OK] 测试2通过: 报警节点使用默认值")
        print(f"  - 默认音效路径: {default_sound}")
        print(f"  - 默认音量: {default_volume}")

def test_export_button_exists():
    """测试3: 导出按钮存在性检查"""
    from bt_gui.bt_editor.toolbar import EditorToolbar
    
    import inspect
    sig = inspect.signature(EditorToolbar.__init__)
    params = list(sig.parameters.keys())
    
    assert "on_export" in params, "EditorToolbar 应该有 on_export 参数"
    
    assert hasattr(EditorToolbar, '_on_export_click'), "EditorToolbar 应该有 _on_export_click 方法"
    
    print("[OK] 测试3通过: 导出按钮已添加到工具栏")

if __name__ == "__main__":
    print("\n=== 开始验证三个修复 ===\n")
    
    test_script_file_filter()
    print()
    
    test_alarm_node_defaults()
    print()
    
    test_export_button_exists()
    print()
    
    print("=== 所有验证测试通过! ===\n")
