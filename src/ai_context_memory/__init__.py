"""
AI Context Memory - AI上下文记忆管理系统
"""

__version__ = "1.0.0"
__author__ = "AI Context Memory Team"
__description__ = "AI Context Memory MCP Server - AI上下文记忆管理服务"

from .memory_manager import MemoryManager
from .models import Memory, MemoryType
from .database import DatabaseManager

__all__ = [
    "MemoryManager",
    "Memory", 
    "MemoryType",
    "DatabaseManager",
    "__version__",
]