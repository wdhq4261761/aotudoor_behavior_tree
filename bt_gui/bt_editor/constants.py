NODE_CATEGORY_MAP = {
    "SequenceNode": "composite",
    "SelectorNode": "composite",
    "ParallelNode": "composite",
    "OCRConditionNode": "condition",
    "ImageConditionNode": "condition",
    "ColorConditionNode": "condition",
    "NumberConditionNode": "condition",
    "VariableConditionNode": "condition",
    "KeyPressNode": "action",
    "MouseClickNode": "action",
    "MouseMoveNode": "action",
    "MouseScrollNode": "action",
    "DelayNode": "action",
    "SetVariableNode": "action",
    "AlarmNode": "action",
    "ScriptNode": "action",
    "CodeNode": "action",
}

NODE_DISPLAY_NAMES = {
    "SequenceNode": "顺序",
    "SelectorNode": "选择",
    "ParallelNode": "并行",
    "OCRConditionNode": "OCR检测",
    "ImageConditionNode": "图像匹配",
    "ColorConditionNode": "颜色检测",
    "NumberConditionNode": "数字比较",
    "VariableConditionNode": "变量判断",
    "KeyPressNode": "按键",
    "MouseClickNode": "点击",
    "MouseMoveNode": "移动",
    "MouseScrollNode": "滚轮",
    "DelayNode": "延时",
    "SetVariableNode": "设变量",
    "AlarmNode": "报警",
    "ScriptNode": "脚本",
    "CodeNode": "代码",
}

NODE_DESCRIPTIONS = {
    "SequenceNode": "按顺序执行子节点",
    "SelectorNode": "选择第一个成功的子节点",
    "ParallelNode": "同时执行所有子节点",
    "OCRConditionNode": "检测文字内容",
    "ImageConditionNode": "匹配图像模板",
    "ColorConditionNode": "检测颜色值",
    "NumberConditionNode": "比较数值大小",
    "VariableConditionNode": "判断变量值",
    "KeyPressNode": "模拟键盘按键",
    "MouseClickNode": "模拟鼠标点击",
    "MouseMoveNode": "移动鼠标位置",
    "MouseScrollNode": "鼠标滚轮滚动",
    "DelayNode": "等待指定时间",
    "SetVariableNode": "设置变量值",
    "AlarmNode": "播放报警音效",
    "CodeNode": "执行外部代码文件",
    "ScriptNode": "执行Txt脚本文件",
}

COMPOSITE_NODES = ["SequenceNode", "SelectorNode", "ParallelNode"]
CONDITION_NODES = ["OCRConditionNode", "ImageConditionNode", "ColorConditionNode", "NumberConditionNode", "VariableConditionNode"]
ACTION_NODES = ["KeyPressNode", "MouseClickNode", "MouseMoveNode", "MouseScrollNode", "DelayNode", "SetVariableNode", "ScriptNode", "CodeNode", "AlarmNode"]

ALL_NODE_TYPES = COMPOSITE_NODES + CONDITION_NODES + ACTION_NODES


def get_node_category(node_type: str) -> str:
    return NODE_CATEGORY_MAP.get(node_type, "unknown")


def get_node_display_name(node_type: str) -> str:
    return NODE_DISPLAY_NAMES.get(node_type, node_type)


def get_node_description(node_type: str) -> str:
    return NODE_DESCRIPTIONS.get(node_type, "")


def build_node_categories(theme_colors: dict) -> dict:
    return {
        "组合节点": {
            "icon": "◇",
            "color": theme_colors.get('composite', '#6366F1'),
            "nodes": [
                ("SequenceNode", "顺序", "按顺序执行子节点"),
                ("SelectorNode", "选择", "选择第一个成功的子节点"),
                ("ParallelNode", "并行", "同时执行所有子节点"),
            ]
        },
        "条件节点": {
            "icon": "◇",
            "color": theme_colors.get('condition', '#10B981'),
            "nodes": [
                ("OCRConditionNode", "OCR检测", "检测文字内容"),
                ("ImageConditionNode", "图像匹配", "匹配图像模板"),
                ("ColorConditionNode", "颜色检测", "检测颜色值"),
                ("NumberConditionNode", "数字比较", "比较数值大小"),
                ("VariableConditionNode", "变量判断", "判断变量值"),
            ]
        },
        "动作节点": {
            "icon": "◆",
            "color": theme_colors.get('action', '#F59E0B'),
            "nodes": [
                ("KeyPressNode", "按键", "模拟键盘按键"),
                ("MouseClickNode", "点击", "模拟鼠标点击"),
                ("MouseMoveNode", "移动", "移动鼠标位置"),
                ("MouseScrollNode", "滚轮", "鼠标滚轮滚动"),
                ("DelayNode", "延时", "等待指定时间"),
                ("SetVariableNode", "设变量", "设置变量值"),
                ("AlarmNode", "报警", "播放报警音效"),
                ("CodeNode", "代码", "执行外部代码文件"),
                ("ScriptNode", "脚本", "执行Txt脚本文件"),
            ]
        },
    }
