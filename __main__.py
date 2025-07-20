#!/usr/bin/env python3
"""
AI Context Memory 包主入口
支持 python -m ai_context_memory 运行
"""

import sys
from pathlib import Path

# 添加src目录到路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from ai_context_memory.cli import main

if __name__ == "__main__":
    main()