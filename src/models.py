"""
Data models and types for AI Context Memory.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

class MemoryType(Enum):
    """Memory type enumeration."""
    FACT = "fact"
    PREFERENCE = "preference"
    CONVERSATION = "conversation"
    NOTE = "note"

@dataclass
class Memory:
    """Memory data model."""
    id: Optional[int] = None
    content: str = ""
    memory_type: MemoryType = MemoryType.NOTE
    context: Optional[str] = None
    tags: List[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class Tag:
    """Tag data model."""
    id: Optional[int] = None
    name: str = ""

@dataclass
class MemorySearchResult:
    """Search result wrapper."""
    memories: List[Memory]
    total_count: int
    has_more: bool