"""OCR测试工具启动脚本"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bt_gui.ocr_test_tool.main_window import main

if __name__ == "__main__":
    main()
