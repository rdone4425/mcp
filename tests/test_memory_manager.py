"""
Unit tests for MemoryManager.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.memory_manager import MemoryManager
from src.models import Memory, MemoryType

class TestMemoryManager:
    """Test cases for MemoryManager."""
    
    @pytest_asyncio.fixture
    async def memory_manager(self):
        """Create a test memory manager."""
        manager = MemoryManager(":memory:")  # Use in-memory database for tests
        await manager.initialize()
        yield manager
        await manager.close()
    
    # Input validation tests
    @pytest.mark.asyncio
    async def test_validate_memory_type(self, memory_manager):
        """Test memory type validation."""
        # Valid enum
        result = memory_manager._validate_memory_type(MemoryType.FACT)
        assert result == "fact"
        
        # Valid string
        result = memory_manager._validate_memory_type("preference")
        assert result == "preference"
        
        # Invalid string
        with pytest.raises(ValueError, match="Invalid memory type"):
            memory_manager._validate_memory_type("invalid_type")
        
        # Invalid type
        with pytest.raises(ValueError, match="Memory type must be"):
            memory_manager._validate_memory_type(123)
    
    @pytest.mark.asyncio
    async def test_validate_content(self, memory_manager):
        """Test content validation."""
        # Valid content
        result = memory_manager._validate_content("  Valid content  ")
        assert result == "Valid content"
        
        # Empty content
        with pytest.raises(ValueError, match="Memory content cannot be empty"):
            memory_manager._validate_content("")
        
        with pytest.raises(ValueError, match="Memory content cannot be empty"):
            memory_manager._validate_content("   ")
        
        # Too long content
        long_content = "x" * 10001
        with pytest.raises(ValueError, match="Memory content too long"):
            memory_manager._validate_content(long_content)
    
    @pytest.mark.asyncio
    async def test_validate_tags(self, memory_manager):
        """Test tag validation."""
        # Valid tags
        result = memory_manager._validate_tags(["Python", "  programming  ", "AI"])
        assert result == ["python", "programming", "ai"]
        
        # Empty tags
        result = memory_manager._validate_tags([])
        assert result is None
        
        result = memory_manager._validate_tags(None)
        assert result is None
        
        # Remove duplicates and empty tags
        result = memory_manager._validate_tags(["python", "Python", "", "  ", "ai"])
        assert result == ["python", "ai"]
        
        # Invalid tag type
        with pytest.raises(ValueError, match="Tag must be string"):
            memory_manager._validate_tags([123])
        
        # Too long tag
        long_tag = "x" * 51
        with pytest.raises(ValueError, match="Tag too long"):
            memory_manager._validate_tags([long_tag])
    
    # Core functionality tests
    @pytest.mark.asyncio
    async def test_store_memory_basic(self, memory_manager):
        """Test storing a basic memory."""
        memory_id = await memory_manager.store_memory(
            content="Test memory content",
            memory_type=MemoryType.FACT
        )
        
        assert memory_id is not None
        assert memory_id > 0
        
        # Verify the memory was stored
        memory = await memory_manager.get_memory_by_id(memory_id)
        assert memory is not None
        assert memory.content == "Test memory content"
        assert memory.memory_type == MemoryType.FACT
        assert memory.tags == []
        assert memory.context is None
    
    @pytest.mark.asyncio
    async def test_store_memory_with_tags_and_context(self, memory_manager):
        """Test storing a memory with tags and context."""
        memory_id = await memory_manager.store_memory(
            content="Python programming tutorial",
            memory_type=MemoryType.NOTE,
            tags=["python", "programming", "tutorial"],
            context="Learning materials"
        )
        
        memory = await memory_manager.get_memory_by_id(memory_id)
        assert memory is not None
        assert memory.content == "Python programming tutorial"
        assert memory.memory_type == MemoryType.NOTE
        assert set(memory.tags) == {"python", "programming", "tutorial"}
        assert memory.context == "Learning materials"
    
    @pytest.mark.asyncio
    async def test_store_memory_validation_errors(self, memory_manager):
        """Test store memory validation errors."""
        # Empty content
        with pytest.raises(ValueError, match="Memory content cannot be empty"):
            await memory_manager.store_memory("", MemoryType.FACT)
        
        # Invalid memory type
        with pytest.raises(ValueError, match="Invalid memory type"):
            await memory_manager.store_memory("Content", "invalid_type")
        
        # Too long context
        long_context = "x" * 1001
        with pytest.raises(ValueError, match="Context too long"):
            await memory_manager.store_memory(
                "Content", 
                MemoryType.FACT, 
                context=long_context
            )
    
    @pytest.mark.asyncio
    async def test_get_memory_by_id(self, memory_manager):
        """Test getting memory by ID."""
        # Store a memory
        memory_id = await memory_manager.store_memory(
            "Test content", 
            MemoryType.PREFERENCE
        )
        
        # Get the memory
        memory = await memory_manager.get_memory_by_id(memory_id)
        assert memory is not None
        assert memory.id == memory_id
        assert memory.content == "Test content"
        assert memory.memory_type == MemoryType.PREFERENCE
        
        # Test non-existent memory
        non_existent = await memory_manager.get_memory_by_id(99999)
        assert non_existent is None
        
        # Test invalid ID
        with pytest.raises(ValueError, match="Memory ID must be positive"):
            await memory_manager.get_memory_by_id(0)
    
    @pytest.mark.asyncio
    async def test_retrieve_memories(self, memory_manager):
        """Test retrieving memories by query."""
        # Store test memories
        await memory_manager.store_memory("Python programming", MemoryType.FACT)
        await memory_manager.store_memory("Java development", MemoryType.FACT)
        await memory_manager.store_memory("Python is great", MemoryType.PREFERENCE)
        
        # Search for Python
        memories = await memory_manager.retrieve_memories("Python")
        assert len(memories) == 2
        for memory in memories:
            assert "Python" in memory.content
        
        # Search with type filter
        fact_memories = await memory_manager.retrieve_memories(
            "Python", 
            memory_type=MemoryType.FACT
        )
        assert len(fact_memories) == 1
        assert fact_memories[0].memory_type == MemoryType.FACT
        
        # Search with limit
        limited_memories = await memory_manager.retrieve_memories("Python", limit=1)
        assert len(limited_memories) == 1
        
        # Test validation errors
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await memory_manager.retrieve_memories("")
        
        with pytest.raises(ValueError, match="Limit must be positive"):
            await memory_manager.retrieve_memories("test", limit=0)
    
    @pytest.mark.asyncio
    async def test_update_memory(self, memory_manager):
        """Test updating memory."""
        # Store a memory
        memory_id = await memory_manager.store_memory(
            "Original content", 
            MemoryType.FACT,
            tags=["old-tag"]
        )
        
        # Update content
        success = await memory_manager.update_memory(
            memory_id, 
            content="Updated content"
        )
        assert success is True
        
        # Verify update
        memory = await memory_manager.get_memory_by_id(memory_id)
        assert memory.content == "Updated content"
        
        # Update tags
        success = await memory_manager.update_memory(
            memory_id,
            tags=["new-tag", "another-tag"]
        )
        assert success is True
        
        memory = await memory_manager.get_memory_by_id(memory_id)
        assert set(memory.tags) == {"new-tag", "another-tag"}
        
        # Update context
        success = await memory_manager.update_memory(
            memory_id,
            context="New context"
        )
        assert success is True
        
        memory = await memory_manager.get_memory_by_id(memory_id)
        assert memory.context == "New context"
        
        # Test non-existent memory
        success = await memory_manager.update_memory(99999, content="New content")
        assert success is False
        
        # Test validation errors
        with pytest.raises(ValueError, match="Memory ID must be positive"):
            await memory_manager.update_memory(0, content="Content")
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_manager):
        """Test deleting memory."""
        # Store a memory
        memory_id = await memory_manager.store_memory("To be deleted", MemoryType.NOTE)
        
        # Verify it exists
        memory = await memory_manager.get_memory_by_id(memory_id)
        assert memory is not None
        
        # Delete it
        success = await memory_manager.delete_memory(memory_id)
        assert success is True
        
        # Verify it's gone
        memory = await memory_manager.get_memory_by_id(memory_id)
        assert memory is None
        
        # Test deleting non-existent memory
        success = await memory_manager.delete_memory(99999)
        assert success is False
        
        # Test validation error
        with pytest.raises(ValueError, match="Memory ID must be positive"):
            await memory_manager.delete_memory(-1)
    
    @pytest.mark.asyncio
    async def test_list_memories(self, memory_manager):
        """Test listing memories."""
        # Store test memories
        await memory_manager.store_memory("Fact 1", MemoryType.FACT)
        await memory_manager.store_memory("Fact 2", MemoryType.FACT)
        await memory_manager.store_memory("Note 1", MemoryType.NOTE)
        
        # List all memories
        all_memories = await memory_manager.list_memories()
        assert len(all_memories) == 3
        
        # List by type
        facts = await memory_manager.list_memories(memory_type=MemoryType.FACT)
        assert len(facts) == 2
        for memory in facts:
            assert memory.memory_type == MemoryType.FACT
        
        # List with pagination
        page1 = await memory_manager.list_memories(limit=2, offset=0)
        page2 = await memory_manager.list_memories(limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 1
        
        # Test validation errors
        with pytest.raises(ValueError, match="Limit must be positive"):
            await memory_manager.list_memories(limit=0)
        
        with pytest.raises(ValueError, match="Offset must be non-negative"):
            await memory_manager.list_memories(offset=-1)
    
    @pytest.mark.asyncio
    async def test_clear_memories(self, memory_manager):
        """Test clearing memories."""
        # Store test memories
        await memory_manager.store_memory("Fact 1", MemoryType.FACT)
        await memory_manager.store_memory("Fact 2", MemoryType.FACT)
        await memory_manager.store_memory("Note 1", MemoryType.NOTE)
        
        # Clear facts only
        cleared_count = await memory_manager.clear_memories(MemoryType.FACT)
        assert cleared_count == 2
        
        # Verify only notes remain
        remaining = await memory_manager.list_memories()
        assert len(remaining) == 1
        assert remaining[0].memory_type == MemoryType.NOTE
        
        # Clear all remaining
        cleared_count = await memory_manager.clear_memories()
        assert cleared_count == 1
        
        # Verify all are gone
        remaining = await memory_manager.list_memories()
        assert len(remaining) == 0
    
    @pytest.mark.asyncio
    async def test_get_memory_count(self, memory_manager):
        """Test getting memory count."""
        # Initially no memories
        count = await memory_manager.get_memory_count()
        assert count == 0
        
        # Store test memories
        await memory_manager.store_memory("Fact 1", MemoryType.FACT)
        await memory_manager.store_memory("Fact 2", MemoryType.FACT)
        await memory_manager.store_memory("Note 1", MemoryType.NOTE)
        
        # Test total count
        total_count = await memory_manager.get_memory_count()
        assert total_count == 3
        
        # Test count by type
        fact_count = await memory_manager.get_memory_count(MemoryType.FACT)
        assert fact_count == 2
        
        note_count = await memory_manager.get_memory_count(MemoryType.NOTE)
        assert note_count == 1
    
    @pytest.mark.asyncio
    async def test_get_all_tags(self, memory_manager):
        """Test getting all tags."""
        # Store memories with tags
        await memory_manager.store_memory(
            "Memory 1", 
            MemoryType.FACT, 
            tags=["python", "programming"]
        )
        await memory_manager.store_memory(
            "Memory 2", 
            MemoryType.NOTE, 
            tags=["work", "important"]
        )
        
        # Get all tags
        tags = await memory_manager.get_all_tags()
        assert len(tags) == 4
        assert set(tags) == {"python", "programming", "work", "important"}
    
    @pytest.mark.asyncio
    async def test_cleanup_unused_tags(self, memory_manager):
        """Test cleaning up unused tags."""
        # Store a memory with tags
        memory_id = await memory_manager.store_memory(
            "Test memory", 
            MemoryType.FACT, 
            tags=["used", "unused"]
        )
        
        # Update memory to remove one tag
        await memory_manager.update_memory(memory_id, tags=["used"])
        
        # Cleanup unused tags
        deleted_count = await memory_manager.cleanup_unused_tags()
        assert deleted_count == 1
        
        # Verify only used tag remains
        tags = await memory_manager.get_all_tags()
        assert tags == ["used"]
    
    @pytest.mark.asyncio
    async def test_dict_to_memory_conversion(self, memory_manager):
        """Test conversion from database dict to Memory object."""
        # Store a memory
        memory_id = await memory_manager.store_memory(
            "Test content",
            MemoryType.PREFERENCE,
            tags=["test"],
            context="Test context"
        )
        
        # Get the memory to test conversion
        memory = await memory_manager.get_memory_by_id(memory_id)
        
        # Verify all fields are properly converted
        assert isinstance(memory, Memory)
        assert memory.id == memory_id
        assert memory.content == "Test content"
        assert memory.memory_type == MemoryType.PREFERENCE
        assert memory.tags == ["test"]
        assert memory.context == "Test context"
        assert isinstance(memory.created_at, datetime)
        assert isinstance(memory.updated_at, datetime)
        assert memory.access_count >= 1  # Should be incremented by get_memory_by_id
        assert memory.last_accessed is not None
    
    # Advanced search and management tests
    @pytest.mark.asyncio
    async def test_search_memories_advanced(self, memory_manager):
        """Test advanced search with multiple filters."""
        from datetime import datetime, timedelta
        
        # Store test memories
        await memory_manager.store_memory(
            "Python programming tutorial", 
            MemoryType.FACT, 
            tags=["python", "programming"]
        )
        await memory_manager.store_memory(
            "JavaScript web development", 
            MemoryType.NOTE, 
            tags=["javascript", "web"]
        )
        await memory_manager.store_memory(
            "Python data science", 
            MemoryType.FACT, 
            tags=["python", "data"]
        )
        
        # Search by keywords
        results = await memory_manager.search_memories(keywords=["Python"])
        assert len(results) == 2
        
        # Search by type
        results = await memory_manager.search_memories(memory_type=MemoryType.FACT)
        assert len(results) == 2
        
        # Search by tags
        results = await memory_manager.search_memories(tags=["python"])
        assert len(results) == 2
        
        # Combined search
        results = await memory_manager.search_memories(
            keywords=["Python"],
            memory_type=MemoryType.FACT,
            tags=["programming"]
        )
        assert len(results) == 1
        assert "tutorial" in results[0].content
        
        # Search with date range
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        results = await memory_manager.search_memories(
            date_from=yesterday,
            date_to=tomorrow
        )
        assert len(results) == 3  # All memories should be within this range
    
    @pytest.mark.asyncio
    async def test_search_memories_by_keywords(self, memory_manager):
        """Test keyword search with AND/OR logic."""
        # Store test memories
        await memory_manager.store_memory("Python programming tutorial", MemoryType.FACT)
        await memory_manager.store_memory("Python data science", MemoryType.FACT)
        await memory_manager.store_memory("JavaScript programming", MemoryType.NOTE)
        await memory_manager.store_memory("Web development tutorial", MemoryType.NOTE)
        
        # OR search (default)
        results = await memory_manager.search_memories_by_keywords(
            ["Python", "JavaScript"]
        )
        assert len(results) == 3  # Python programming, Python data, JavaScript programming
        
        # AND search
        results = await memory_manager.search_memories_by_keywords(
            ["Python", "programming"],
            match_all=True
        )
        assert len(results) == 1
        assert "Python programming tutorial" == results[0].content
        
        # Search with type filter
        results = await memory_manager.search_memories_by_keywords(
            ["programming"],
            memory_type=MemoryType.FACT
        )
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.FACT
        
        # Test validation errors
        with pytest.raises(ValueError, match="Keywords list cannot be empty"):
            await memory_manager.search_memories_by_keywords([])
        
        with pytest.raises(ValueError, match="No valid keywords provided"):
            await memory_manager.search_memories_by_keywords(["", "  "])
    
    @pytest.mark.asyncio
    async def test_get_memories_by_tags(self, memory_manager):
        """Test getting memories by tags with AND/OR logic."""
        # Store test memories
        await memory_manager.store_memory(
            "Memory 1", 
            MemoryType.FACT, 
            tags=["python", "programming", "tutorial"]
        )
        await memory_manager.store_memory(
            "Memory 2", 
            MemoryType.NOTE, 
            tags=["python", "data"]
        )
        await memory_manager.store_memory(
            "Memory 3", 
            MemoryType.FACT, 
            tags=["javascript", "programming"]
        )
        
        # OR search (default)
        results = await memory_manager.get_memories_by_tags(["python", "javascript"])
        assert len(results) == 3  # All memories have either python or javascript
        
        # AND search
        results = await memory_manager.get_memories_by_tags(
            ["python", "programming"],
            match_all=True
        )
        assert len(results) == 1
        assert "Memory 1" == results[0].content
        
        # Search with type filter
        results = await memory_manager.get_memories_by_tags(
            ["programming"],
            memory_type=MemoryType.FACT
        )
        assert len(results) == 2  # Memory 1 and Memory 3
        
        # Test validation errors
        with pytest.raises(ValueError, match="Tags list cannot be empty"):
            await memory_manager.get_memories_by_tags([])
    
    @pytest.mark.asyncio
    async def test_get_recent_memories(self, memory_manager):
        """Test getting recent memories."""
        # Store test memories
        await memory_manager.store_memory("Recent memory 1", MemoryType.FACT)
        await memory_manager.store_memory("Recent memory 2", MemoryType.NOTE)
        
        # Get memories from last 7 days (default)
        results = await memory_manager.get_recent_memories()
        assert len(results) == 2
        
        # Get memories from last 1 day
        results = await memory_manager.get_recent_memories(days=1)
        assert len(results) == 2  # Should still include today's memories
        
        # Get with type filter
        results = await memory_manager.get_recent_memories(
            days=7, 
            memory_type=MemoryType.FACT
        )
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.FACT
        
        # Test validation error
        with pytest.raises(ValueError, match="Days must be positive"):
            await memory_manager.get_recent_memories(days=0)
    
    @pytest.mark.asyncio
    async def test_get_frequently_accessed_memories(self, memory_manager):
        """Test getting frequently accessed memories."""
        # Store test memories
        memory1_id = await memory_manager.store_memory("Memory 1", MemoryType.FACT)
        memory2_id = await memory_manager.store_memory("Memory 2", MemoryType.NOTE)
        memory3_id = await memory_manager.store_memory("Memory 3", MemoryType.FACT)
        
        # Access some memories multiple times
        await memory_manager.get_memory_by_id(memory1_id)  # access_count = 1
        await memory_manager.get_memory_by_id(memory1_id)  # access_count = 2
        await memory_manager.get_memory_by_id(memory1_id)  # access_count = 3
        
        await memory_manager.get_memory_by_id(memory2_id)  # access_count = 1
        await memory_manager.get_memory_by_id(memory2_id)  # access_count = 2
        
        # memory3 has access_count = 0 (not accessed after creation)
        
        # Get frequently accessed (min 2 accesses)
        results = await memory_manager.get_frequently_accessed_memories(min_access_count=2)
        assert len(results) == 2  # Memory 1 and Memory 2
        
        # Results should be sorted by access count (descending)
        assert results[0].content == "Memory 1"  # access_count = 3
        assert results[1].content == "Memory 2"  # access_count = 2
        
        # Get with higher threshold
        results = await memory_manager.get_frequently_accessed_memories(min_access_count=3)
        assert len(results) == 1
        assert results[0].content == "Memory 1"
        
        # Get with type filter
        results = await memory_manager.get_frequently_accessed_memories(
            min_access_count=2,
            memory_type=MemoryType.FACT
        )
        assert len(results) == 1
        assert results[0].content == "Memory 1"
        
        # Test validation error
        with pytest.raises(ValueError, match="Minimum access count must be positive"):
            await memory_manager.get_frequently_accessed_memories(min_access_count=0)
    
    @pytest.mark.asyncio
    async def test_get_memory_statistics(self, memory_manager):
        """Test getting comprehensive memory statistics."""
        # Initially no memories
        stats = await memory_manager.get_memory_statistics()
        assert stats['total_count'] == 0
        assert stats['fact_count'] == 0
        assert stats['note_count'] == 0
        assert stats['preference_count'] == 0
        assert stats['conversation_count'] == 0
        assert stats['total_tags'] == 0
        
        # Store test memories
        memory1_id = await memory_manager.store_memory(
            "Short", 
            MemoryType.FACT, 
            tags=["tag1"]
        )
        await memory_manager.store_memory(
            "This is a longer memory content", 
            MemoryType.NOTE, 
            tags=["tag1", "tag2"]
        )
        await memory_manager.store_memory(
            "Medium length content", 
            MemoryType.PREFERENCE
        )
        
        # Access one memory to increase access count
        await memory_manager.get_memory_by_id(memory1_id)
        
        # Get updated statistics
        stats = await memory_manager.get_memory_statistics()
        
        # Verify counts
        assert stats['total_count'] == 3
        assert stats['fact_count'] == 1
        assert stats['note_count'] == 1
        assert stats['preference_count'] == 1
        assert stats['conversation_count'] == 0
        assert stats['total_tags'] == 2
        
        # Verify access statistics
        assert stats['max_access_count'] == 1
        assert stats['min_access_count'] == 0
        assert 0 < stats['avg_access_count'] < 1
        
        # Verify content length statistics
        assert stats['min_content_length'] == 5  # "Short"
        assert stats['max_content_length'] == 31  # "This is a longer memory content"
        assert 5 < stats['avg_content_length'] < 31
        
        # Verify tag statistics
        assert stats['memories_with_tags'] == 2
        assert stats['memories_without_tags'] == 1
        
        # Verify date statistics exist
        assert 'oldest_memory' in stats
        assert 'newest_memory' in stats
    
    @pytest.mark.asyncio
    async def test_update_memory_access_count(self, memory_manager):
        """Test manually updating memory access count."""
        # Store a memory
        memory_id = await memory_manager.store_memory("Test memory", MemoryType.FACT)
        
        # Get initial access count
        memory = await memory_manager.get_memory_by_id(memory_id)
        initial_count = memory.access_count
        
        # Manually update access count
        success = await memory_manager.update_memory_access_count(memory_id)
        assert success is True
        
        # Verify access count increased
        memory = await memory_manager.get_memory_by_id(memory_id)
        assert memory.access_count == initial_count + 2  # +1 from manual update, +1 from get_memory_by_id
        
        # Test with non-existent memory
        success = await memory_manager.update_memory_access_count(99999)
        assert success is False
        
        # Test validation error
        with pytest.raises(ValueError, match="Memory ID must be positive"):
            await memory_manager.update_memory_access_count(0)