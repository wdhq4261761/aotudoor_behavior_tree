"""
DD输入初始化钩子
在程序启动时设置环境变量
"""
import os

os.environ['AUTODOOR_USE_DD'] = '1'
