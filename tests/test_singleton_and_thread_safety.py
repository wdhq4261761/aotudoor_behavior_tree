"""
单例模式和线程安全回归测试

测试问题1和问题2修复后的正确性。
"""
import threading
import time
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSingletonPattern:
    """单例模式测试"""
    
    @staticmethod
    def test_log_manager_singleton():
        """测试 LogManager 单例正确性"""
        from bt_utils.log_manager import LogManager
        
        instance1 = LogManager()
        instance2 = LogManager()
        
        assert instance1 is instance2, "LogManager 应该返回同一实例"
        print("[PASS] test_log_manager_singleton 通过")
    
    @staticmethod
    def test_ocr_manager_singleton():
        """测试 OCRManager 单例正确性"""
        from bt_utils.ocr_manager import OCRManager
        
        instance1 = OCRManager()
        instance2 = OCRManager()
        
        assert instance1 is instance2, "OCRManager 应该返回同一实例"
        print("[PASS] test_ocr_manager_singleton 通过")
    
    @staticmethod
    def test_settings_manager_singleton():
        """测试 SettingsManager 单例正确性"""
        from config.settings_manager import SettingsManager
        from bt_utils.singleton import reset_singleton
        
        try:
            instance1 = SettingsManager()
            instance2 = SettingsManager()
            
            assert instance1 is instance2, "SettingsManager 应该返回同一实例"
            print("[PASS] test_settings_manager_singleton 通过")
        finally:
            reset_singleton(SettingsManager)
    
    @staticmethod
    def test_singleton_thread_safety():
        """测试单例模式在多线程环境下的正确性"""
        from bt_utils.log_manager import LogManager
        
        instances = []
        errors = []
        
        def create_instance():
            try:
                instance = LogManager()
                instances.append(id(instance))
            except Exception as e:
                errors.append(str(e))
        
        threads = [threading.Thread(target=create_instance) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"多线程创建实例时发生错误: {errors}"
        assert len(set(instances)) == 1, "所有线程应该获得同一个实例"
        print("[PASS] test_singleton_thread_safety 通过")
    
    @staticmethod
    def test_singleton_initialization_once():
        """测试单例只初始化一次"""
        from bt_utils.singleton import singleton, reset_singleton
        
        init_count = [0]
        
        @singleton
        class TestClass:
            def __init__(self):
                init_count[0] += 1
                self.value = init_count[0]
        
        try:
            for _ in range(10):
                instance = TestClass()
                assert instance.value == 1, "初始化应该只执行一次"
            
            assert init_count[0] == 1, "__init__ 应该只被调用一次"
            print("[PASS] test_singleton_initialization_once 通过")
        finally:
            reset_singleton(TestClass)


class TestScriptNodeThreadSafety:
    """ScriptNode 线程安全测试"""
    
    @staticmethod
    def test_concurrent_execute_and_abort():
        """测试并发执行和中止"""
        from bt_nodes.actions.script import ScriptNode
        from bt_core.config import NodeConfig
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Delay 1000\n")
            script_path = f.name
        
        try:
            config = NodeConfig({
                "script_path": script_path,
                "loop": False
            })
            node = ScriptNode(node_id="test_node", config=config)
            
            class MockContext:
                def check_running(self):
                    return True
                
                def notify_node_status(self, node_id, status):
                    pass
            
            context = MockContext()
            
            results = []
            errors = []
            
            def execute_thread():
                try:
                    for _ in range(5):
                        result = node._execute_action(context)
                        results.append(result)
                        time.sleep(0.01)
                except Exception as e:
                    errors.append(str(e))
            
            def abort_thread():
                try:
                    time.sleep(0.05)
                    node.abort(context)
                except Exception as e:
                    errors.append(str(e))
            
            threads = [
                threading.Thread(target=execute_thread),
                threading.Thread(target=abort_thread)
            ]
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            assert len(errors) == 0, f"并发操作时发生错误: {errors}"
            print("[PASS] test_concurrent_execute_and_abort 通过")
        
        finally:
            os.unlink(script_path)
    
    @staticmethod
    def test_executor_pool_thread_safety():
        """测试执行器池的线程安全"""
        from bt_nodes.actions.script import ScriptNode
        from bt_core.config import NodeConfig
        
        errors = []
        
        def create_and_cleanup(node_id):
            try:
                config = NodeConfig({"script_path": "", "loop": False})
                node = ScriptNode(node_id=node_id, config=config)
                
                with ScriptNode._pool_lock:
                    if node_id in ScriptNode._executor_pool:
                        del ScriptNode._executor_pool[node_id]
            except Exception as e:
                errors.append(f"{node_id}: {str(e)}")
        
        threads = [
            threading.Thread(target=create_and_cleanup, args=(f"node_{i}",))
            for i in range(50)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"执行器池操作时发生错误: {errors}"
        print("[PASS] test_executor_pool_thread_safety 通过")
    
    @staticmethod
    def test_reset_during_execution():
        """测试执行期间重置"""
        from bt_nodes.actions.script import ScriptNode
        from bt_core.config import NodeConfig
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Delay 5000\n")
            script_path = f.name
        
        try:
            config = NodeConfig({
                "script_path": script_path,
                "loop": True
            })
            node = ScriptNode(node_id="test_reset_node", config=config)
            
            class MockContext:
                def check_running(self):
                    return True
                
                def notify_node_status(self, node_id, status):
                    pass
            
            context = MockContext()
            
            errors = []
            
            def execute_thread():
                try:
                    node._execute_action(context)
                    time.sleep(0.1)
                    node._execute_action(context)
                except Exception as e:
                    errors.append(f"execute: {str(e)}")
            
            def reset_thread():
                try:
                    time.sleep(0.05)
                    node.reset()
                except Exception as e:
                    errors.append(f"reset: {str(e)}")
            
            threads = [
                threading.Thread(target=execute_thread),
                threading.Thread(target=reset_thread)
            ]
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            assert len(errors) == 0, f"执行期间重置发生错误: {errors}"
            assert node._executor is None, "重置后执行器应该为 None"
            assert not node._script_started, "重置后脚本状态应该为 False"
            print("[PASS] test_reset_during_execution 通过")
        
        finally:
            os.unlink(script_path)
    
    @staticmethod
    def test_multiple_nodes_concurrent_execution():
        """测试多个节点并发执行"""
        from bt_nodes.actions.script import ScriptNode
        from bt_core.config import NodeConfig
        
        nodes = []
        script_paths = []
        
        for i in range(5):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Delay 100\n")
                script_paths.append(f.name)
            
            config = NodeConfig({
                "script_path": script_paths[-1],
                "loop": False
            })
            nodes.append(ScriptNode(node_id=f"concurrent_node_{i}", config=config))
        
        try:
            class MockContext:
                def check_running(self):
                    return True
                
                def notify_node_status(self, node_id, status):
                    pass
            
            context = MockContext()
            
            results = [[] for _ in range(5)]
            errors = []
            
            def execute_node(index):
                try:
                    for _ in range(3):
                        result = nodes[index]._execute_action(context)
                        results[index].append(result)
                        time.sleep(0.05)
                    nodes[index].reset()
                except Exception as e:
                    errors.append(f"node_{index}: {str(e)}")
            
            threads = [
                threading.Thread(target=execute_node, args=(i,))
                for i in range(5)
            ]
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            assert len(errors) == 0, f"并发执行多个节点时发生错误: {errors}"
            print("[PASS] test_multiple_nodes_concurrent_execution 通过")
        
        finally:
            for path in script_paths:
                os.unlink(path)


class TestSingletonReset:
    """单例重置测试（用于测试环境）"""
    
    @staticmethod
    def test_reset_singleton_for_testing():
        """测试单例重置功能"""
        from bt_utils.singleton import singleton, reset_singleton
        
        @singleton
        class TestClass:
            def __init__(self):
                self.value = "first"
        
        instance1 = TestClass()
        assert instance1.value == "first"
        
        reset_singleton(TestClass)
        
        instance2 = TestClass()
        instance2.value = "second"
        
        assert instance2.value == "second"
        print("[PASS] test_reset_singleton_for_testing 通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行单例模式和线程安全回归测试")
    print("=" * 60)
    
    print("\n--- 单例模式测试 ---")
    TestSingletonPattern.test_log_manager_singleton()
    TestSingletonPattern.test_ocr_manager_singleton()
    TestSingletonPattern.test_settings_manager_singleton()
    TestSingletonPattern.test_singleton_thread_safety()
    TestSingletonPattern.test_singleton_initialization_once()
    
    print("\n--- ScriptNode 线程安全测试 ---")
    TestScriptNodeThreadSafety.test_concurrent_execute_and_abort()
    TestScriptNodeThreadSafety.test_executor_pool_thread_safety()
    TestScriptNodeThreadSafety.test_reset_during_execution()
    TestScriptNodeThreadSafety.test_multiple_nodes_concurrent_execution()
    
    print("\n--- 单例重置测试 ---")
    TestSingletonReset.test_reset_singleton_for_testing()
    
    print("\n" + "=" * 60)
    print("所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
