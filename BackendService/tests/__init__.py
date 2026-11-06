"""测试包：将 BackendService 目录加入 sys.path，使 `from core.xxx import ...` 可解析。"""
import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)
