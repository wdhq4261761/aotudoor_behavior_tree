"""
黑板系统线程安全测试

测试多线程环境下黑板系统的安全性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time
import random
from bt_core.blackboard import Blackboard


def test_concurrent_writes():
    """测试并发写入"""
    blackboard = Blackboard()
    errors = []
    
    def writer_thread(thread_id):
        try:
            for i in range(100):
                blackboard.set(f"key_{thread_id}", i)
                time.sleep(random.random() * 0.001)
        except Exception as e:
            errors.append(f"Thread {thread_id}: {e}")
    
    threads = []
    for i in range(10):
        t = threading.Thread(target=writer_thread, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert len(errors) == 0, f"发现错误: {errors}"
    print("[PASS] 并发写入测试通过")


def test_concurrent_reads():
    """测试并发读取"""
    blackboard = Blackboard()
    blackboard.set("test_key", "test_value")
    errors = []
    
    def reader_thread(thread_id):
        try:
            for i in range(100):
                value = blackboard.get("test_key")
                assert value == "test_value", f"读取值不正确: {value}"
                time.sleep(random.random() * 0.001)
        except Exception as e:
            errors.append(f"Thread {thread_id}: {e}")
    
    threads = []
    for i in range(10):
        t = threading.Thread(target=reader_thread, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert len(errors) == 0, f"发现错误: {errors}"
    print("[PASS] 并发读取测试通过")


def test_concurrent_increment():
    """测试并发递增"""
    blackboard = Blackboard()
    blackboard.set("counter", 0)
    
    def increment_thread():
        for _ in range(100):
            blackboard.increment("counter")
    
    threads = []
    for i in range(10):
        t = threading.Thread(target=increment_thread)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    final_value = blackboard.get("counter")
    assert final_value == 1000, f"期望值: 1000, 实际值: {final_value}"
    print("[PASS] 并发递增测试通过")


def test_subscribe_thread_safety():
    """测试订阅机制的线程安全"""
    blackboard = Blackboard()
    call_count = [0]
    
    def callback(old_value, new_value):
        call_count[0] += 1
    
    blackboard.subscribe("test_key", callback)
    
    def writer_thread(thread_id):
        for i in range(10):
            blackboard.set("test_key", f"value_{thread_id}_{i}")
    
    threads = []
    for i in range(10):
        t = threading.Thread(target=writer_thread, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert call_count[0] == 100, f"期望调用100次, 实际调用{call_count[0]}次"
    print("[PASS] 订阅机制线程安全测试通过")


def test_mixed_operations():
    """测试混合操作"""
    blackboard = Blackboard()
    errors = []
    
    def mixed_thread(thread_id):
        try:
            for i in range(50):
                op = random.choice(['get', 'set', 'increment', 'exists'])
                if op == 'get':
                    blackboard.get(f"key_{thread_id}")
                elif op == 'set':
                    blackboard.set(f"key_{thread_id}", i)
                elif op == 'increment':
                    blackboard.increment(f"counter_{thread_id}")
                elif op == 'exists':
                    blackboard.exists(f"key_{thread_id}")
                time.sleep(random.random() * 0.001)
        except Exception as e:
            errors.append(f"Thread {thread_id}: {e}")
    
    threads = []
    for i in range(10):
        t = threading.Thread(target=mixed_thread, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert len(errors) == 0, f"发现错误: {errors}"
    print("[PASS] 混合操作测试通过")


def test_builtin_vars_protection():
    """测试内置变量保护"""
    blackboard = Blackboard()
    
    blackboard.set("last_detection_position", (100, 200))
    assert blackboard.get("last_detection_position") == (100, 200)
    
    blackboard.delete("last_detection_position")
    assert blackboard.get("last_detection_position") is not None
    
    blackboard.clear()
    assert blackboard.get("last_detection_position") is None
    
    print("[PASS] 内置变量保护测试通过")


if __name__ == "__main__":
    print("=" * 60)
    print("黑板系统线程安全测试")
    print("=" * 60)
    
    test_concurrent_writes()
    test_concurrent_reads()
    test_concurrent_increment()
    test_subscribe_thread_safety()
    test_mixed_operations()
    test_builtin_vars_protection()
    
    print("=" * 60)
    print("所有测试通过!")
    print("=" * 60)
