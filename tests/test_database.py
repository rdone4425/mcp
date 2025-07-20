"""
Unit tests for DatabaseManager.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock

from src.database import DatabaseManager

class TestDatabaseManager:
    """Test cases for DatabaseManager."""
    
    @pytest_asyncio.fixture
    async def db_manager(self):
        """Create a test database manager."""
        manager = DatabaseManager(":memory:")  # Use in-memory database for tests
        await manager.initialize()
        yield manager
        await manager.close()
    
    @pytest_asyncio.fixture
    async def file_db_manager(self):
        """Create a test database manager with file storage."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        manager = DatabaseManager(db_path)
        await manager.initialize()
        yield manager
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, db_manager):
        """Test database initialization creates all required tables."""
        # Check if tables exist
        tables = await db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = [table['name'] for table in tables]
        
        assert 'memories' in table_names
        assert 'tags' in table_names
        assert 'memory_tags' in table_names
    
    @pytest.mark.asyncio
    async def test_database_indexes(self, db_manager):
        """Test that required indexes are created."""
        indexes = await db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        index_names = [index['name'] for index in indexes]
        
        assert 'idx_memories_type' in index_names
        assert 'idx_memories_created' in index_names
        assert 'idx_memories_content' in index_names
        assert 'idx_tags_name' in index_names
    
    @pytest.mark.asyncio
    async def test_execute_query(self, db_manager):
        """Test query execution."""
        # Insert test data
        await db_manager.execute_update(
            "INSERT INTO memories (content, memory_type) VALUES (?, ?)",
            ("Test memory", "fact")
        )
        
        # Query the data
        results = await db_manager.execute_query(
            "SELECT content, memory_type FROM memories WHERE memory_type = ?",
            ("fact",)
        )
        
        assert len(results) == 1
        assert results[0]['content'] == "Test memory"
        assert results[0]['memory_type'] == "fact"
    
    @pytest.mark.asyncio
    async def test_execute_update(self, db_manager):
        """Test update execution."""
        # Insert test data
        await db_manager.execute_update(
            "INSERT INTO memories (content, memory_type) VALUES (?, ?)",
            ("Test memory", "fact")
        )
        
        # Update the data
        affected_rows = await db_manager.execute_update(
            "UPDATE memories SET content = ? WHERE memory_type = ?",
            ("Updated memory", "fact")
        )
        
        assert affected_rows == 1
        
        # Verify the update
        results = await db_manager.execute_query(
            "SELECT content FROM memories WHERE memory_type = ?",
            ("fact",)
        )
        assert results[0]['content'] == "Updated memory"
    
    @pytest.mark.asyncio
    async def test_execute_insert(self, db_manager):
        """Test insert execution with return of last row ID."""
        memory_id = await db_manager.execute_insert(
            "INSERT INTO memories (content, memory_type) VALUES (?, ?)",
            ("Test memory", "fact")
        )
        
        assert memory_id is not None
        assert memory_id > 0
        
        # Verify the insert
        results = await db_manager.execute_query(
            "SELECT id, content FROM memories WHERE id = ?",
            (memory_id,)
        )
        assert len(results) == 1
        assert results[0]['id'] == memory_id
        assert results[0]['content'] == "Test memory"
    
    @pytest.mark.asyncio
    async def test_execute_transaction(self, db_manager):
        """Test transaction execution."""
        queries = [
            ("INSERT INTO memories (content, memory_type) VALUES (?, ?)", ("Memory 1", "fact")),
            ("INSERT INTO memories (content, memory_type) VALUES (?, ?)", ("Memory 2", "preference")),
            ("INSERT INTO tags (name) VALUES (?)", ("test-tag",))
        ]
        
        success = await db_manager.execute_transaction(queries)
        assert success is True
        
        # Verify all inserts were successful
        memories = await db_manager.execute_query("SELECT COUNT(*) as count FROM memories")
        tags = await db_manager.execute_query("SELECT COUNT(*) as count FROM tags")
        
        assert memories[0]['count'] == 2
        assert tags[0]['count'] == 1
    
    @pytest.mark.asyncio
    async def test_get_or_create_tag_new(self, db_manager):
        """Test creating a new tag."""
        tag_id = await db_manager.get_or_create_tag("new-tag")
        
        assert tag_id is not None
        assert tag_id > 0
        
        # Verify the tag was created
        results = await db_manager.execute_query(
            "SELECT name FROM tags WHERE id = ?",
            (tag_id,)
        )
        assert len(results) == 1
        assert results[0]['name'] == "new-tag"
    
    @pytest.mark.asyncio
    async def test_get_or_create_tag_existing(self, db_manager):
        """Test getting an existing tag."""
        # Create a tag first
        first_id = await db_manager.get_or_create_tag("existing-tag")
        
        # Try to get the same tag again
        second_id = await db_manager.get_or_create_tag("existing-tag")
        
        assert first_id == second_id
        
        # Verify only one tag exists
        results = await db_manager.execute_query(
            "SELECT COUNT(*) as count FROM tags WHERE name = ?",
            ("existing-tag",)
        )
        assert results[0]['count'] == 1
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, db_manager):
        """Test that foreign key constraints are enforced."""
        # Insert a memory
        memory_id = await db_manager.execute_insert(
            "INSERT INTO memories (content, memory_type) VALUES (?, ?)",
            ("Test memory", "fact")
        )
        
        # Insert a tag
        tag_id = await db_manager.execute_insert(
            "INSERT INTO tags (name) VALUES (?)",
            ("test-tag",)
        )
        
        # Create association
        await db_manager.execute_update(
            "INSERT INTO memory_tags (memory_id, tag_id) VALUES (?, ?)",
            (memory_id, tag_id)
        )
        
        # Delete the memory - should cascade delete the association
        await db_manager.execute_update(
            "DELETE FROM memories WHERE id = ?",
            (memory_id,)
        )
        
        # Verify association was deleted
        associations = await db_manager.execute_query(
            "SELECT COUNT(*) as count FROM memory_tags WHERE memory_id = ?",
            (memory_id,)
        )
        assert associations[0]['count'] == 0
    
    @pytest.mark.asyncio
    async def test_file_database_creation(self, file_db_manager):
        """Test that file-based database is created properly."""
        # Test basic functionality with file database
        memory_id = await file_db_manager.execute_insert(
            "INSERT INTO memories (content, memory_type) VALUES (?, ?)",
            ("File test memory", "note")
        )
        
        assert memory_id is not None
        
        # Verify data persistence
        results = await file_db_manager.execute_query(
            "SELECT content FROM memories WHERE id = ?",
            (memory_id,)
        )
        assert len(results) == 1
        assert results[0]['content'] == "File test memory"
    
    # CRUD Operations Tests
    @pytest.mark.asyncio
    async def test_create_memory_without_tags(self, db_manager):
        """Test creating a memory without tags."""
        memory_id = await db_manager.create_memory(
            content="Test memory content",
            memory_type="fact",
            context="Test context"
        )
        
        assert memory_id is not None
        assert memory_id > 0
        
        # Verify the memory was created
        memory = await db_manager.get_memory(memory_id)
        assert memory is not None
        assert memory['content'] == "Test memory content"
        assert memory['memory_type'] == "fact"
        assert memory['context'] == "Test context"
        assert memory['tags'] == []
    
    @pytest.mark.asyncio
    async def test_create_memory_with_tags(self, db_manager):
        """Test creating a memory with tags."""
        memory_id = await db_manager.create_memory(
            content="Tagged memory",
            memory_type="note",
            tags=["important", "work", "project"]
        )
        
        assert memory_id is not None
        
        # Verify the memory and tags
        memory = await db_manager.get_memory(memory_id)
        assert memory is not None
        assert memory['content'] == "Tagged memory"
        assert set(memory['tags']) == {"important", "work", "project"}
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_memory(self, db_manager):
        """Test getting a memory that doesn't exist."""
        memory = await db_manager.get_memory(99999)
        assert memory is None
    
    @pytest.mark.asyncio
    async def test_update_memory_content(self, db_manager):
        """Test updating memory content."""
        # Create a memory
        memory_id = await db_manager.create_memory(
            content="Original content",
            memory_type="fact"
        )
        
        # Update the content
        success = await db_manager.update_memory(
            memory_id,
            content="Updated content"
        )
        assert success is True
        
        # Verify the update
        memory = await db_manager.get_memory(memory_id)
        assert memory['content'] == "Updated content"
    
    @pytest.mark.asyncio
    async def test_update_memory_tags(self, db_manager):
        """Test updating memory tags."""
        # Create a memory with tags
        memory_id = await db_manager.create_memory(
            content="Test memory",
            memory_type="note",
            tags=["old-tag"]
        )
        
        # Update the tags
        success = await db_manager.update_memory(
            memory_id,
            tags=["new-tag", "another-tag"]
        )
        assert success is True
        
        # Verify the update
        memory = await db_manager.get_memory(memory_id)
        assert set(memory['tags']) == {"new-tag", "another-tag"}
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_memory(self, db_manager):
        """Test updating a memory that doesn't exist."""
        success = await db_manager.update_memory(
            99999,
            content="New content"
        )
        assert success is False
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, db_manager):
        """Test deleting a memory."""
        # Create a memory
        memory_id = await db_manager.create_memory(
            content="To be deleted",
            memory_type="note"
        )
        
        # Delete the memory
        success = await db_manager.delete_memory(memory_id)
        assert success is True
        
        # Verify it's gone
        memory = await db_manager.get_memory(memory_id)
        assert memory is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_memory(self, db_manager):
        """Test deleting a memory that doesn't exist."""
        success = await db_manager.delete_memory(99999)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_search_memories_by_content(self, db_manager):
        """Test searching memories by content."""
        # Create test memories
        await db_manager.create_memory("Python programming", "fact")
        await db_manager.create_memory("Java development", "fact")
        await db_manager.create_memory("Python is great", "preference")
        
        # Search for Python
        results = await db_manager.search_memories(query="Python")
        assert len(results) == 2
        
        # Verify all results contain "Python"
        for memory in results:
            assert "Python" in memory['content']
    
    @pytest.mark.asyncio
    async def test_search_memories_by_type(self, db_manager):
        """Test searching memories by type."""
        # Create test memories
        await db_manager.create_memory("Fact 1", "fact")
        await db_manager.create_memory("Fact 2", "fact")
        await db_manager.create_memory("Note 1", "note")
        
        # Search for facts
        results = await db_manager.search_memories(memory_type="fact")
        assert len(results) == 2
        
        # Verify all results are facts
        for memory in results:
            assert memory['memory_type'] == "fact"
    
    @pytest.mark.asyncio
    async def test_search_memories_by_tags(self, db_manager):
        """Test searching memories by tags."""
        # Create test memories with tags
        await db_manager.create_memory("Memory 1", "fact", tags=["work", "important"])
        await db_manager.create_memory("Memory 2", "note", tags=["personal"])
        await db_manager.create_memory("Memory 3", "fact", tags=["work", "project"])
        
        # Search for work-related memories
        results = await db_manager.search_memories(tags=["work"])
        assert len(results) == 2
        
        # Verify all results have the work tag
        for memory in results:
            assert "work" in memory['tags']
    
    @pytest.mark.asyncio
    async def test_list_memories_with_pagination(self, db_manager):
        """Test listing memories with pagination."""
        # Create test memories
        for i in range(5):
            await db_manager.create_memory(f"Memory {i}", "fact")
        
        # Test pagination
        page1 = await db_manager.list_memories(limit=2, offset=0)
        page2 = await db_manager.list_memories(limit=2, offset=2)
        
        assert len(page1) == 2
        assert len(page2) == 2
        
        # Verify no overlap
        page1_ids = {m['id'] for m in page1}
        page2_ids = {m['id'] for m in page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    @pytest.mark.asyncio
    async def test_clear_memories_by_type(self, db_manager):
        """Test clearing memories by type."""
        # Create test memories
        await db_manager.create_memory("Fact 1", "fact")
        await db_manager.create_memory("Fact 2", "fact")
        await db_manager.create_memory("Note 1", "note")
        
        # Clear only facts
        cleared_count = await db_manager.clear_memories(memory_type="fact")
        assert cleared_count == 2
        
        # Verify only notes remain
        remaining = await db_manager.list_memories()
        assert len(remaining) == 1
        assert remaining[0]['memory_type'] == "note"
    
    @pytest.mark.asyncio
    async def test_clear_all_memories(self, db_manager):
        """Test clearing all memories."""
        # Create test memories
        await db_manager.create_memory("Memory 1", "fact")
        await db_manager.create_memory("Memory 2", "note")
        
        # Clear all memories
        cleared_count = await db_manager.clear_memories()
        assert cleared_count == 2
        
        # Verify no memories remain
        remaining = await db_manager.list_memories()
        assert len(remaining) == 0
    
    @pytest.mark.asyncio
    async def test_get_memory_count(self, db_manager):
        """Test getting memory count."""
        # Initially no memories
        count = await db_manager.get_memory_count()
        assert count == 0
        
        # Create test memories
        await db_manager.create_memory("Fact 1", "fact")
        await db_manager.create_memory("Fact 2", "fact")
        await db_manager.create_memory("Note 1", "note")
        
        # Test total count
        total_count = await db_manager.get_memory_count()
        assert total_count == 3
        
        # Test count by type
        fact_count = await db_manager.get_memory_count(memory_type="fact")
        assert fact_count == 2
        
        note_count = await db_manager.get_memory_count(memory_type="note")
        assert note_count == 1
    
    @pytest.mark.asyncio
    async def test_get_all_tags(self, db_manager):
        """Test getting all tags."""
        # Create memories with tags
        await db_manager.create_memory("Memory 1", "fact", tags=["python", "programming"])
        await db_manager.create_memory("Memory 2", "note", tags=["work", "important"])
        
        # Get all tags
        tags = await db_manager.get_all_tags()
        tag_names = {tag['name'] for tag in tags}
        
        assert len(tags) == 4
        assert tag_names == {"python", "programming", "work", "important"}
    
    @pytest.mark.asyncio
    async def test_delete_unused_tags(self, db_manager):
        """Test deleting unused tags."""
        # Create a memory with tags
        memory_id = await db_manager.create_memory("Test", "fact", tags=["used", "unused"])
        
        # Remove one tag by updating the memory
        await db_manager.update_memory(memory_id, tags=["used"])
        
        # Delete unused tags
        deleted_count = await db_manager.delete_unused_tags()
        assert deleted_count == 1
        
        # Verify only used tag remains
        tags = await db_manager.get_all_tags()
        assert len(tags) == 1
        assert tags[0]['name'] == "used"
    
    @pytest.mark.asyncio
    async def test_access_count_tracking(self, db_manager):
        """Test that access count is tracked when getting memories."""
        # Create a memory
        memory_id = await db_manager.create_memory("Test memory", "fact")
        
        # Get the memory multiple times
        memory1 = await db_manager.get_memory(memory_id)
        memory2 = await db_manager.get_memory(memory_id)
        
        # Access count should increase
        assert memory1['access_count'] == 1
        assert memory2['access_count'] == 2
    
    # Memory CRUD operation tests
    @pytest.mark.asyncio
    async def test_insert_memory(self, db_manager):
        """Test inserting a new memory."""
        memory_id = await db_manager.insert_memory(
            "Test memory content", 
            "fact", 
            "Test context"
        )
        
        assert memory_id is not None
        assert memory_id > 0
        
        # Verify the memory was inserted
        memory = await db_manager.get_memory_by_id(memory_id)
        assert memory is not None
        assert memory['content'] == "Test memory content"
        assert memory['memory_type'] == "fact"
        assert memory['context'] == "Test context"
        assert memory['access_count'] == 0
    
    @pytest.mark.asyncio
    async def test_get_memory_by_id(self, db_manager):
        """Test retrieving memory by ID."""
        # Insert test memory
        memory_id = await db_manager.insert_memory("Test content", "note")
        
        # Retrieve memory
        memory = await db_manager.get_memory_by_id(memory_id)
        assert memory is not None
        assert memory['id'] == memory_id
        assert memory['content'] == "Test content"
        assert memory['memory_type'] == "note"
        
        # Test non-existent memory
        non_existent = await db_manager.get_memory_by_id(99999)
        assert non_existent is None
    
    @pytest.mark.asyncio
    async def test_update_memory_content(self, db_manager):
        """Test updating memory content."""
        # Insert test memory
        memory_id = await db_manager.insert_memory("Original content", "fact")
        
        # Update content
        success = await db_manager.update_memory_content(memory_id, "Updated content")
        assert success is True
        
        # Verify update
        memory = await db_manager.get_memory_by_id(memory_id)
        assert memory['content'] == "Updated content"
        
        # Test updating non-existent memory
        success = await db_manager.update_memory_content(99999, "New content")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_update_memory_access(self, db_manager):
        """Test updating memory access count."""
        # Insert test memory
        memory_id = await db_manager.insert_memory("Test content", "fact")
        
        # Update access count
        success = await db_manager.update_memory_access(memory_id)
        assert success is True
        
        # Verify access count increased
        memory = await db_manager.get_memory_by_id(memory_id)
        assert memory['access_count'] == 1
        assert memory['last_accessed'] is not None
        
        # Update again
        await db_manager.update_memory_access(memory_id)
        memory = await db_manager.get_memory_by_id(memory_id)
        assert memory['access_count'] == 2
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, db_manager):
        """Test deleting a memory."""
        # Insert test memory
        memory_id = await db_manager.insert_memory("Test content", "fact")
        
        # Verify memory exists
        memory = await db_manager.get_memory_by_id(memory_id)
        assert memory is not None
        
        # Delete memory
        success = await db_manager.delete_memory(memory_id)
        assert success is True
        
        # Verify memory is deleted
        memory = await db_manager.get_memory_by_id(memory_id)
        assert memory is None
        
        # Test deleting non-existent memory
        success = await db_manager.delete_memory(99999)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_search_memories_by_content(self, db_manager):
        """Test searching memories by content."""
        # Insert test memories
        await db_manager.insert_memory("Python programming", "fact")
        await db_manager.insert_memory("JavaScript coding", "fact")
        await db_manager.insert_memory("Python is great", "preference")
        
        # Search for "Python"
        results = await db_manager.search_memories_by_content("Python")
        assert len(results) == 2
        
        # Search with type filter
        results = await db_manager.search_memories_by_content("Python", "fact")
        assert len(results) == 1
        assert results[0]['content'] == "Python programming"
        
        # Search with limit
        results = await db_manager.search_memories_by_content("Python", limit=1)
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_get_memories_by_type(self, db_manager):
        """Test getting memories by type."""
        # Insert test memories
        await db_manager.insert_memory("Fact 1", "fact")
        await db_manager.insert_memory("Fact 2", "fact")
        await db_manager.insert_memory("Note 1", "note")
        
        # Get facts
        facts = await db_manager.get_memories_by_type("fact")
        assert len(facts) == 2
        
        # Get notes
        notes = await db_manager.get_memories_by_type("note")
        assert len(notes) == 1
        
        # Test with limit
        facts_limited = await db_manager.get_memories_by_type("fact", limit=1)
        assert len(facts_limited) == 1
    
    @pytest.mark.asyncio
    async def test_clear_memories(self, db_manager):
        """Test clearing memories."""
        # Insert test memories
        await db_manager.insert_memory("Fact 1", "fact")
        await db_manager.insert_memory("Fact 2", "fact")
        await db_manager.insert_memory("Note 1", "note")
        
        # Clear facts only
        cleared_count = await db_manager.clear_memories_by_type("fact")
        assert cleared_count == 2
        
        # Verify facts are cleared but notes remain
        facts = await db_manager.get_memories_by_type("fact")
        notes = await db_manager.get_memories_by_type("note")
        assert len(facts) == 0
        assert len(notes) == 1
        
        # Clear all memories
        cleared_count = await db_manager.clear_all_memories()
        assert cleared_count == 1
        
        # Verify all memories are cleared
        all_memories = await db_manager.get_all_memories()
        assert len(all_memories) == 0
    
    # Tag CRUD operation tests
    @pytest.mark.asyncio
    async def test_tag_operations(self, db_manager):
        """Test tag CRUD operations."""
        # Insert tag
        tag_id = await db_manager.insert_tag("python")
        assert tag_id is not None
        
        # Get tag by ID
        tag = await db_manager.get_tag_by_id(tag_id)
        assert tag is not None
        assert tag['name'] == "python"
        
        # Get tag by name
        tag = await db_manager.get_tag_by_name("python")
        assert tag is not None
        assert tag['id'] == tag_id
        
        # Insert another tag
        await db_manager.insert_tag("javascript")
        
        # Get all tags
        all_tags = await db_manager.get_all_tags()
        assert len(all_tags) == 2
        
        # Delete tag
        success = await db_manager.delete_tag(tag_id)
        assert success is True
        
        # Verify tag is deleted
        tag = await db_manager.get_tag_by_id(tag_id)
        assert tag is None
    
    @pytest.mark.asyncio
    async def test_memory_tag_associations(self, db_manager):
        """Test memory-tag associations."""
        # Insert memory and tags
        memory_id = await db_manager.insert_memory("Python tutorial", "note")
        tag1_id = await db_manager.insert_tag("python")
        tag2_id = await db_manager.insert_tag("tutorial")
        
        # Add associations
        success1 = await db_manager.add_memory_tag(memory_id, tag1_id)
        success2 = await db_manager.add_memory_tag(memory_id, tag2_id)
        assert success1 is True
        assert success2 is True
        
        # Get memory tags
        memory_tags = await db_manager.get_memory_tags(memory_id)
        assert len(memory_tags) == 2
        tag_names = [tag['name'] for tag in memory_tags]
        assert "python" in tag_names
        assert "tutorial" in tag_names
        
        # Get memories by tag
        memories_with_python = await db_manager.get_memories_by_tag(tag1_id)
        assert len(memories_with_python) == 1
        assert memories_with_python[0]['id'] == memory_id
        
        # Remove association
        success = await db_manager.remove_memory_tag(memory_id, tag1_id)
        assert success is True
        
        # Verify association removed
        memory_tags = await db_manager.get_memory_tags(memory_id)
        assert len(memory_tags) == 1
        assert memory_tags[0]['name'] == "tutorial"
    
    @pytest.mark.asyncio
    async def test_get_memories_by_tag_names(self, db_manager):
        """Test getting memories by tag names."""
        # Insert memories and tags
        memory1_id = await db_manager.insert_memory("Python basics", "note")
        memory2_id = await db_manager.insert_memory("JavaScript basics", "note")
        memory3_id = await db_manager.insert_memory("Advanced Python", "note")
        
        python_tag_id = await db_manager.insert_tag("python")
        js_tag_id = await db_manager.insert_tag("javascript")
        basics_tag_id = await db_manager.insert_tag("basics")
        
        # Create associations
        await db_manager.add_memory_tag(memory1_id, python_tag_id)
        await db_manager.add_memory_tag(memory1_id, basics_tag_id)
        await db_manager.add_memory_tag(memory2_id, js_tag_id)
        await db_manager.add_memory_tag(memory2_id, basics_tag_id)
        await db_manager.add_memory_tag(memory3_id, python_tag_id)
        
        # Search by single tag
        python_memories = await db_manager.get_memories_by_tag_names(["python"])
        assert len(python_memories) == 2
        
        # Search by multiple tags
        basics_memories = await db_manager.get_memories_by_tag_names(["basics"])
        assert len(basics_memories) == 2
        
        # Search by multiple tag names (OR operation)
        multi_tag_memories = await db_manager.get_memories_by_tag_names(["python", "javascript"])
        assert len(multi_tag_memories) == 3  # All memories have either python or javascript tag
    
    @pytest.mark.asyncio
    async def test_advanced_search(self, db_manager):
        """Test advanced search with multiple filters."""
        # Insert test data
        memory1_id = await db_manager.insert_memory("Python programming tutorial", "fact")
        memory2_id = await db_manager.insert_memory("JavaScript web development", "note")
        memory3_id = await db_manager.insert_memory("Python data science", "fact")
        
        python_tag_id = await db_manager.insert_tag("python")
        tutorial_tag_id = await db_manager.insert_tag("tutorial")
        
        await db_manager.add_memory_tag(memory1_id, python_tag_id)
        await db_manager.add_memory_tag(memory1_id, tutorial_tag_id)
        await db_manager.add_memory_tag(memory3_id, python_tag_id)
        
        # Search by content only
        results = await db_manager.search_memories_with_filters(content_search="Python")
        assert len(results) == 2
        
        # Search by content and type
        results = await db_manager.search_memories_with_filters(
            content_search="Python", 
            memory_type="fact"
        )
        assert len(results) == 2
        
        # Search by tags
        results = await db_manager.search_memories_with_filters(tag_names=["python"])
        assert len(results) == 2
        
        # Search by content, type, and tags
        results = await db_manager.search_memories_with_filters(
            content_search="tutorial",
            memory_type="fact",
            tag_names=["python"]
        )
        assert len(results) == 1
        assert results[0]['id'] == memory1_id
        
        # Test with limit
        results = await db_manager.search_memories_with_filters(
            content_search="Python",
            limit=1
        )
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_get_memory_count(self, db_manager):
        """Test getting memory count."""
        # Insert test memories
        await db_manager.insert_memory("Fact 1", "fact")
        await db_manager.insert_memory("Fact 2", "fact")
        await db_manager.insert_memory("Note 1", "note")
        
        # Get total count
        total_count = await db_manager.get_memory_count()
        assert total_count == 3
        
        # Get count by type
        fact_count = await db_manager.get_memory_count("fact")
        assert fact_count == 2
        
        note_count = await db_manager.get_memory_count("note")
        assert note_count == 1