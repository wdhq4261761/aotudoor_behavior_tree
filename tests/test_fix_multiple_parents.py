"""
修复方案示例代码

这个文件展示了如何修复子节点被多个父节点连接的问题
"""

# 方案1：强制树结构（推荐）


class Node_Fixed:
    """修复后的 Node 类（方案1：强制树结构）"""
    
    def __init__(self, node_id: str = None, name: str = ""):
        self.node_id = node_id or "node"
        self.name = name
        self.children = []
        self.parent = None
    
    def add_child(self, child: "Node_Fixed") -> None:
        """添加子节点（带检查）"""
        if child.parent is not None and child.parent != self:
            raise ValueError(
                f"节点 '{child.name}' 已经有父节点 '{child.parent.name}'，"
                f"不能添加到 '{self.name}'"
            )
        
        if child in self.children:
            print(f"[WARNING] 节点 '{child.name}' 已经是 '{self.name}' 的子节点")
            return
        
        child.parent = self
        self.children.append(child)
        print(f"[OK] 成功添加子节点: {self.name} -> {child.name}")
    
    def remove_child(self, child: "Node_Fixed") -> None:
        """移除子节点（带检查）"""
        if child not in self.children:
            print(f"[WARNING] 节点 '{child.name}' 不是 '{self.name}' 的子节点")
            return
        
        if child.parent == self:
            child.parent = None
        
        self.children.remove(child)
        print(f"[OK] 成功移除子节点: {self.name} -> {child.name}")


# 方案2：支持有向无环图（DAG）


class Node_DAG:
    """支持 DAG 的 Node 类（方案2）"""
    
    def __init__(self, node_id: str = None, name: str = ""):
        self.node_id = node_id or "node"
        self.name = name
        self.children = []
        self.parents = []  # 改为列表，支持多个父节点
    
    def add_child(self, child: "Node_DAG") -> None:
        """添加子节点（支持多父节点）"""
        if self not in child.parents:
            child.parents.append(self)
            print(f"[OK] 添加父节点引用: {child.name}.parents += {self.name}")
        
        if child not in self.children:
            self.children.append(child)
            print(f"[OK] 添加子节点引用: {self.name}.children += {child.name}")
    
    def remove_child(self, child: "Node_DAG") -> None:
        """移除子节点（支持多父节点）"""
        if child in self.children:
            self.children.remove(child)
            print(f"[OK] 移除子节点引用: {self.name}.children -= {child.name}")
        
        if self in child.parents:
            child.parents.remove(self)
            print(f"[OK] 移除父节点引用: {child.name}.parents -= {self.name}")
    
    def get_parent_count(self) -> int:
        """获取父节点数量"""
        return len(self.parents)


# GUI 层面的修复


class Canvas_Fixed:
    """修复后的 Canvas 类（GUI 层面）"""
    
    def __init__(self):
        self.nodes = {}
        self.connections = []
    
    def add_connection(self, parent_id: str, child_id: str) -> bool:
        """添加连接（带完整检查）"""
        
        # 检查节点是否存在
        if parent_id not in self.nodes:
            print(f"[ERROR] 父节点 '{parent_id}' 不存在")
            return False
        
        if child_id not in self.nodes:
            print(f"[ERROR] 子节点 '{child_id}' 不存在")
            return False
        
        # 检查是否已经存在相同的连接
        if any(c[0] == parent_id and c[1] == child_id for c in self.connections):
            print(f"[WARNING] 连接已存在: {parent_id} -> {child_id}")
            return False
        
        # 检查子节点是否已经有父节点
        existing_parents = [c[0] for c in self.connections if c[1] == child_id]
        if existing_parents:
            print(f"[ERROR] 子节点 '{child_id}' 已经有父节点: {existing_parents}")
            print(f"[ERROR] 不能重复连接")
            return False
        
        # 检查是否会形成循环
        if self._would_create_cycle(parent_id, child_id):
            print(f"[ERROR] 添加连接会形成循环: {parent_id} -> {child_id}")
            return False
        
        # 添加连接
        self.connections.append((parent_id, child_id))
        print(f"[OK] 成功添加连接: {parent_id} -> {child_id}")
        return True
    
    def _would_create_cycle(self, parent_id: str, child_id: str) -> bool:
        """检查添加连接是否会形成循环"""
        visited = set()
        stack = [child_id]
        
        while stack:
            current = stack.pop()
            if current == parent_id:
                return True
            if current in visited:
                continue
            visited.add(current)
            
            # 添加当前节点的所有子节点
            for p, c in self.connections:
                if p == current:
                    stack.append(c)
        
        return False


# 测试代码


def test_fixed_node():
    """测试修复后的 Node 类（方案1）"""
    print("\n" + "="*60)
    print("测试修复后的 Node 类（方案1：强制树结构）")
    print("="*60)
    
    # 创建节点
    action = Node_Fixed("action_1", "动作节点")
    seq1 = Node_Fixed("seq_1", "顺序节点1")
    seq2 = Node_Fixed("seq_2", "顺序节点2")
    
    # 第一次连接
    print("\n1. 第一次连接: seq1 -> action")
    try:
        seq1.add_child(action)
    except ValueError as e:
        print(f"[ERROR] {e}")
    
    # 第二次连接（应该失败）
    print("\n2. 第二次连接: seq2 -> action (应该失败)")
    try:
        seq2.add_child(action)
    except ValueError as e:
        print(f"[ERROR] {e}")
    
    # 检查状态
    print("\n3. 状态检查:")
    print(f"   action.parent = {action.parent.name if action.parent else 'None'}")
    print(f"   seq1.children = {[c.name for c in seq1.children]}")
    print(f"   seq2.children = {[c.name for c in seq2.children]}")
    
    print("\n[OK] 方案1成功防止了多父节点连接！")
    print("="*60 + "\n")


def test_dag_node():
    """测试支持 DAG 的 Node 类（方案2）"""
    print("\n" + "="*60)
    print("测试支持 DAG 的 Node 类（方案2）")
    print("="*60)
    
    # 创建节点
    action = Node_DAG("action_1", "动作节点")
    seq1 = Node_DAG("seq_1", "顺序节点1")
    seq2 = Node_DAG("seq_2", "顺序节点2")
    
    # 第一次连接
    print("\n1. 第一次连接: seq1 -> action")
    seq1.add_child(action)
    
    # 第二次连接（应该成功）
    print("\n2. 第二次连接: seq2 -> action")
    seq2.add_child(action)
    
    # 检查状态
    print("\n3. 状态检查:")
    print(f"   action.parents = {[p.name for p in action.parents]}")
    print(f"   seq1.children = {[c.name for c in seq1.children]}")
    print(f"   seq2.children = {[c.name for c in seq2.children]}")
    print(f"   action 父节点数量 = {action.get_parent_count()}")
    
    print("\n[OK] 方案2支持多父节点连接！")
    print("="*60 + "\n")


def test_fixed_canvas():
    """测试修复后的 Canvas 类（GUI 层面）"""
    print("\n" + "="*60)
    print("测试修复后的 Canvas 类（GUI 层面）")
    print("="*60)
    
    canvas = Canvas_Fixed()
    
    # 添加节点
    canvas.nodes = {
        "seq_1": {"name": "顺序节点1"},
        "seq_2": {"name": "顺序节点2"},
        "action_1": {"name": "动作节点"}
    }
    
    # 第一次连接
    print("\n1. 第一次连接: seq_1 -> action_1")
    canvas.add_connection("seq_1", "action_1")
    
    # 第二次连接（应该失败）
    print("\n2. 第二次连接: seq_2 -> action_1 (应该失败)")
    result = canvas.add_connection("seq_2", "action_1")
    print(f"   连接结果: {'成功' if result else '失败'}")
    
    # 检查状态
    print("\n3. 状态检查:")
    print(f"   connections = {canvas.connections}")
    
    # 测试循环检测
    print("\n4. 测试循环检测:")
    canvas.nodes["action_2"] = {"name": "动作节点2"}
    canvas.add_connection("action_1", "action_2")
    print(f"   添加连接: action_1 -> action_2")
    
    result = canvas.add_connection("action_2", "seq_1")
    print(f"   尝试添加连接: action_2 -> seq_1 (会形成循环)")
    print(f"   连接结果: {'成功' if result else '失败'}")
    
    print("\n[OK] GUI 层面成功防止了多父节点连接和循环！")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_fixed_node()
    test_dag_node()
    test_fixed_canvas()
