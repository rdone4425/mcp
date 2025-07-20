"""
End-to-end integration tests for AI Context Memory.
"""

import pytest
import pytest_asyncio
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch

from src.memory_manager import MemoryManager
from src.models import MemoryType
from src.security import EncryptionManager, PrivacyManager, SecureMemoryManager

class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    @pytest_asyncio.fixture
    async def memory_manager(self):
        """Create a memory manager for testing."""
        manager = MemoryManager(":memory:")
        await manager.initialize()
        yield manager
        await manager.close()
    
    @pytest_asyncio.fixture
    async def secure_memory_manager(self):
        """Create a secure memory manager for testing."""
        base_manager = MemoryManager(":memory:")
        await base_manager.initialize()
        
        encryption = EncryptionManager("test_password_123")
        privacy = PrivacyManager()
        
        secure_manager = SecureMemoryManager(base_manager, encryption, privacy)
        
        yield secure_manager
        await base_manager.close()
    
    @pytest.mark.asyncio
    async def test_complete_memory_lifecycle(self, memory_manager):
        """Test complete memory lifecycle from creation to deletion."""
        # 1. Store multiple memories
        memory_ids = []
        
        # Store different types of memories
        memory_ids.append(await memory_manager.store_memory(
            content="Python is a programming language",
            memory_type=MemoryType.FACT,
            tags=["python", "programming", "language"],
            context="Learning materials"
        ))
        
        memory_ids.append(await memory_manager.store_memory(
            content="I prefer dark mode in IDEs",
            memory_type=MemoryType.PREFERENCE,
            tags=["ui", "preference", "ide"],
            context="User preferences"
        ))
        
        memory_ids.append(await memory_manager.store_memory(
            content="Discussed project architecture with team",
            memory_type=MemoryType.CONVERSATION,
            tags=["meeting", "architecture", "team"],
            context="Daily standup"
        ))
        
        memory_ids.append(await memory_manager.store_memory(
            content="Remember to update documentation",
            memory_type=MemoryType.NOTE,
            tags=["todo", "documentation"],
            context="Project tasks"
        ))
        
        assert len(memory_ids) == 4
        assert all(mid > 0 for mid in memory_ids)
        
        # 2. Retrieve and verify memories
        for memory_id in memory_ids:
            memory = await memory_manager.get_memory_by_id(memory_id)
            assert memory is not None
            assert memory.id == memory_id
            assert memory.access_count >= 1  # Should be incremented
            assert memory.last_accessed is not None
        
        # 3. Search memories by content
        python_memories = await memory_manager.retrieve_memories("Python")
        assert len(python_memories) == 1
        assert python_memories[0].content == "Python is a programming language"
        
        # 4. Search by keywords with AND logic
        programming_memories = await memory_manager.search_memories_by_keywords(
            ["python", "programming"], 
            match_all=True
        )
        assert len(programming_memories) == 1
        
        # 5. Search by tags
        tag_memories = await memory_manager.get_memories_by_tags(["programming"])
        assert len(tag_memories) == 1
        
        # 6. List memories by type
        facts = await memory_manager.list_memories(memory_type=MemoryType.FACT)
        preferences = await memory_manager.list_memories(memory_type=MemoryType.PREFERENCE)
        conversations = await memory_manager.list_memories(memory_type=MemoryType.CONVERSATION)
        notes = await memory_manager.list_memories(memory_type=MemoryType.NOTE)
        
        assert len(facts) == 1
        assert len(preferences) == 1
        assert len(conversations) == 1
        assert len(notes) == 1
        
        # 7. Update a memory
        success = await memory_manager.update_memory(
            memory_ids[0],
            content="Python is a high-level programming language",
            tags=["python", "programming", "language", "high-level"]
        )
        assert success is True
        
        updated_memory = await memory_manager.get_memory_by_id(memory_ids[0])
        assert "high-level" in updated_memory.content
        assert "high-level" in updated_memory.tags
        
        # 8. Get statistics
        stats = await memory_manager.get_memory_statistics()
        assert stats['total_count'] == 4
        assert stats['fact_count'] == 1
        assert stats['preference_count'] == 1
        assert stats['conversation_count'] == 1
        assert stats['note_count'] == 1
        assert stats['total_tags'] > 0
        
        # 9. Get all tags
        all_tags = await memory_manager.get_all_tags()
        expected_tags = {
            "python", "programming", "language", "high-level",
            "ui", "preference", "ide",
            "meeting", "architecture", "team",
            "todo", "documentation"
        }
        assert set(all_tags) == expected_tags
        
        # 10. Delete memories one by one
        for memory_id in memory_ids:
            success = await memory_manager.delete_memory(memory_id)
            assert success is True
            
            # Verify deletion
            deleted_memory = await memory_manager.get_memory_by_id(memory_id)
            assert deleted_memory is None
        
        # 11. Verify all memories are gone
        final_stats = await memory_manager.get_memory_statistics()
        assert final_stats['total_count'] == 0
        
        # 12. Clean up unused tags
        deleted_tags = await memory_manager.cleanup_unused_tags()
        assert deleted_tags > 0
    
    @pytest.mark.asyncio
    async def test_advanced_search_scenarios(self, memory_manager):
        """Test advanced search scenarios."""
        # Store test data
        await memory_manager.store_memory(
            "Python web development with Django",
            MemoryType.FACT,
            tags=["python", "web", "django", "framework"]
        )
        
        await memory_manager.store_memory(
            "JavaScript frontend development",
            MemoryType.FACT,
            tags=["javascript", "frontend", "web"]
        )
        
        await memory_manager.store_memory(
            "Python data science with pandas",
            MemoryType.FACT,
            tags=["python", "data", "pandas", "science"]
        )
        
        await memory_manager.store_memory(
            "I prefer Python over JavaScript",
            MemoryType.PREFERENCE,
            tags=["python", "javascript", "preference"]
        )
        
        # Test keyword search with OR logic
        python_or_js = await memory_manager.search_memories_by_keywords(
            ["Python", "JavaScript"],
            match_all=False
        )
        assert len(python_or_js) == 4  # All memories contain either Python or JavaScript
        
        # Test keyword search with AND logic
        python_and_web = await memory_manager.search_memories_by_keywords(
            ["Python", "web"],
            match_all=True
        )
        assert len(python_and_web) == 1  # Only Django memory has both
        
        # Test tag search with OR logic
        web_memories = await memory_manager.get_memories_by_tags(
            ["web"],
            match_all=False
        )
        assert len(web_memories) == 2  # Django and JavaScript memories
        
        # Test tag search with AND logic
        python_web_memories = await memory_manager.get_memories_by_tags(
            ["python", "web"],
            match_all=True
        )
        assert len(python_web_memories) == 1  # Only Django memory
        
        # Test advanced search with multiple filters
        recent_memories = await memory_manager.get_recent_memories(days=1)
        assert len(recent_memories) == 4  # All memories are recent
        
        # Test memory type filtering
        facts_only = await memory_manager.search_memories(
            keywords=["Python"],
            memory_type=MemoryType.FACT
        )
        assert len(facts_only) == 2  # Django and pandas memories
        assert all(m.memory_type == MemoryType.FACT for m in facts_only)
    
    @pytest.mark.asyncio
    async def test_secure_memory_workflow(self, secure_memory_manager):
        """Test secure memory management workflow."""
        manager = secure_memory_manager
        
        # 1. Configure privacy settings
        manager.privacy.set_blocked_keywords(['password', 'secret', 'confidential'])
        manager.privacy.set_retention_period(30)
        
        # 2. Store secure memories
        memory_id = await manager.store_memory(
            content="User login credentials are stored securely",
            memory_type=MemoryType.FACT,
            tags=["security", "authentication"],
            context="Security documentation"
        )
        
        assert memory_id is not None
        
        # 3. Try to store blocked content (should fail)
        with pytest.raises(ValueError, match="Privacy validation failed"):
            await manager.store_memory(
                content="The password is 123456",
                memory_type=MemoryType.FACT
            )
        
        # 4. Retrieve and verify decryption
        memory = await manager.get_memory_by_id(memory_id)
        assert memory is not None
        assert memory.content == "User login credentials are stored securely"
        assert memory.context == "Security documentation"
        assert "security" in memory.tags
        
        # 5. Test content sanitization
        sanitized_content = manager.privacy.sanitize_content(
            "Contact john.doe@example.com or call 555-123-4567"
        )
        assert "[EMAIL]" in sanitized_content
        assert "[PHONE]" in sanitized_content
        assert "john.doe@example.com" not in sanitized_content
        assert "555-123-4567" not in sanitized_content
        
        # 6. Get security status
        status = manager.get_security_status()
        assert status['encryption_enabled'] is True
        assert 'privacy_settings' in status
        assert status['privacy_settings']['blocked_keywords_count'] == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, memory_manager):
        """Test concurrent memory operations."""
        import asyncio
        
        # Define concurrent operations
        async def store_memories():
            # Store memories sequentially to avoid tag conflicts
            memory_ids = []
            for i in range(10):
                memory_id = await memory_manager.store_memory(
                    content=f"Concurrent memory {i}",
                    memory_type=MemoryType.NOTE,
                    tags=[f"tag{i}", "concurrent"]
                )
                memory_ids.append(memory_id)
            return memory_ids
        
        async def search_memories():
            await asyncio.sleep(0.1)  # Let some memories be stored first
            return await memory_manager.retrieve_memories("Concurrent")
        
        async def get_statistics():
            await asyncio.sleep(0.2)  # Let more operations complete
            return await memory_manager.get_memory_statistics()
        
        # Run operations concurrently
        memory_ids, search_results, stats = await asyncio.gather(
            store_memories(),
            search_memories(),
            get_statistics()
        )
        
        # Verify results
        assert len(memory_ids) == 10
        assert all(mid > 0 for mid in memory_ids)
        assert len(search_results) <= 10  # May not find all if search ran early
        assert stats['total_count'] >= len(search_results)
    
    @pytest.mark.asyncio
    async def test_data_persistence(self):
        """Test data persistence across manager instances."""
        # Use a temporary file for this test
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            # First manager instance - store data
            manager1 = MemoryManager(db_path)
            await manager1.initialize()
            
            memory_id = await manager1.store_memory(
                content="Persistent memory test",
                memory_type=MemoryType.FACT,
                tags=["persistence", "test"]
            )
            
            await manager1.close()
            
            # Second manager instance - retrieve data
            manager2 = MemoryManager(db_path)
            await manager2.initialize()
            
            memory = await manager2.get_memory_by_id(memory_id)
            assert memory is not None
            assert memory.content == "Persistent memory test"
            assert "persistence" in memory.tags
            
            # Verify statistics
            stats = await manager2.get_memory_statistics()
            assert stats['total_count'] == 1
            assert stats['fact_count'] == 1
            
            await manager2.close()
            
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, memory_manager):
        """Test error handling and recovery scenarios."""
        # Test invalid memory type
        with pytest.raises(ValueError):
            await memory_manager.store_memory(
                content="Test content",
                memory_type="invalid_type"  # This should cause an error
            )
        
        # Test empty content
        with pytest.raises(ValueError):
            await memory_manager.store_memory(
                content="",
                memory_type=MemoryType.FACT
            )
        
        # Test invalid memory ID
        memory = await memory_manager.get_memory_by_id(99999)
        assert memory is None
        
        # Test invalid update
        success = await memory_manager.update_memory(99999, content="New content")
        assert success is False
        
        # Test invalid deletion
        success = await memory_manager.delete_memory(99999)
        assert success is False
        
        # Test invalid search parameters
        with pytest.raises(ValueError):
            await memory_manager.retrieve_memories("")  # Empty query
        
        with pytest.raises(ValueError):
            await memory_manager.search_memories_by_keywords([])  # Empty keywords
        
        with pytest.raises(ValueError):
            await memory_manager.get_memories_by_tags([])  # Empty tags
    
    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, memory_manager):
        """Test performance with a larger dataset."""
        import time
        
        # Store a moderate number of memories
        num_memories = 100
        start_time = time.time()
        
        memory_ids = []
        for i in range(num_memories):
            memory_id = await memory_manager.store_memory(
                content=f"Performance test memory {i} with some additional content to make it realistic",
                memory_type=MemoryType.FACT if i % 2 == 0 else MemoryType.NOTE,
                tags=[f"tag{i % 10}", "performance", "test"],
                context=f"Performance test context {i}"
            )
            memory_ids.append(memory_id)
        
        store_time = time.time() - start_time
        
        # Test search performance
        start_time = time.time()
        search_results = await memory_manager.retrieve_memories("Performance")
        search_time = time.time() - start_time
        
        # Test statistics performance
        start_time = time.time()
        stats = await memory_manager.get_memory_statistics()
        stats_time = time.time() - start_time
        
        # Verify results
        assert len(memory_ids) == num_memories
        assert len(search_results) == num_memories  # All contain "Performance"
        assert stats['total_count'] == num_memories
        
        # Performance assertions (reasonable thresholds)
        assert store_time < 10.0  # Should store 100 memories in under 10 seconds
        assert search_time < 1.0   # Should search in under 1 second
        assert stats_time < 1.0    # Should get stats in under 1 second
        
        print(f"Performance metrics:")
        print(f"  Store {num_memories} memories: {store_time:.2f}s")
        print(f"  Search {num_memories} memories: {search_time:.2f}s")
        print(f"  Get statistics: {stats_time:.2f}s")

class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    @pytest_asyncio.fixture
    async def ai_assistant_memory(self):
        """Create a memory manager simulating an AI assistant's memory."""
        manager = MemoryManager(":memory:")
        await manager.initialize()
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_ai_assistant_conversation_memory(self, ai_assistant_memory):
        """Test AI assistant conversation memory scenario."""
        manager = ai_assistant_memory
        
        # Simulate a conversation about a user's project
        await manager.store_memory(
            content="User is working on a Python web application using Flask",
            memory_type=MemoryType.FACT,
            tags=["user-project", "python", "flask", "web"],
            context="Project discussion"
        )
        
        await manager.store_memory(
            content="User prefers minimal dependencies and lightweight frameworks",
            memory_type=MemoryType.PREFERENCE,
            tags=["user-preference", "minimal", "lightweight"],
            context="Architecture preferences"
        )
        
        await manager.store_memory(
            content="Discussed database options: SQLite for development, PostgreSQL for production",
            memory_type=MemoryType.CONVERSATION,
            tags=["database", "sqlite", "postgresql", "discussion"],
            context="Technical consultation"
        )
        
        await manager.store_memory(
            content="User needs help with authentication implementation",
            memory_type=MemoryType.NOTE,
            tags=["todo", "authentication", "help-needed"],
            context="Follow-up tasks"
        )
        
        # AI assistant retrieves relevant context for new question about databases
        db_memories = await manager.retrieve_memories("database")
        assert len(db_memories) >= 1
        
        # AI assistant looks up user preferences
        preferences = await manager.list_memories(memory_type=MemoryType.PREFERENCE)
        assert len(preferences) >= 1
        assert "minimal" in preferences[0].tags
        
        # AI assistant checks conversation history
        conversations = await manager.list_memories(memory_type=MemoryType.CONVERSATION)
        assert len(conversations) >= 1
        
        # AI assistant reviews pending tasks
        todos = await manager.get_memories_by_tags(["todo"])
        assert len(todos) >= 1
        
        # Get the specific memory to check tags
        todo_memory = await manager.get_memory_by_id(todos[0].id)
        assert "authentication" in todo_memory.tags
    
    @pytest.mark.asyncio
    async def test_learning_assistant_scenario(self, ai_assistant_memory):
        """Test learning assistant scenario."""
        manager = ai_assistant_memory
        
        # Student learning Python
        await manager.store_memory(
            content="Python uses indentation to define code blocks",
            memory_type=MemoryType.FACT,
            tags=["python", "syntax", "indentation", "basics"],
            context="Python fundamentals"
        )
        
        await manager.store_memory(
            content="Student struggles with understanding list comprehensions",
            memory_type=MemoryType.NOTE,
            tags=["student-difficulty", "list-comprehensions", "python"],
            context="Learning challenges"
        )
        
        await manager.store_memory(
            content="Student prefers visual examples over text explanations",
            memory_type=MemoryType.PREFERENCE,
            tags=["learning-style", "visual", "examples"],
            context="Teaching approach"
        )
        
        # Later, when student asks about loops
        # AI can recall that student prefers visual examples
        learning_prefs = await manager.get_memories_by_tags(["learning-style"])
        assert len(learning_prefs) >= 1
        
        # Get the specific memory to check tags
        pref_memory = await manager.get_memory_by_id(learning_prefs[0].id)
        assert "visual" in pref_memory.tags
        
        # AI can also recall previous difficulties
        difficulties = await manager.get_memories_by_tags(["student-difficulty"])
        assert len(difficulties) >= 1
        
        # AI can build on previous knowledge
        python_facts = await manager.get_memories_by_tags(["python", "basics"])
        assert len(python_facts) >= 1
    
    @pytest.mark.asyncio
    async def test_personal_assistant_scenario(self, ai_assistant_memory):
        """Test personal assistant scenario."""
        manager = ai_assistant_memory
        
        # Store personal information and preferences
        await manager.store_memory(
            content="User has a meeting with the development team every Tuesday at 10 AM",
            memory_type=MemoryType.FACT,
            tags=["schedule", "meeting", "recurring", "tuesday"],
            context="Calendar information"
        )
        
        await manager.store_memory(
            content="User prefers coffee shops for informal meetings",
            memory_type=MemoryType.PREFERENCE,
            tags=["meeting-preference", "coffee-shop", "informal"],
            context="Meeting preferences"
        )
        
        await manager.store_memory(
            content="Remind user to prepare quarterly report by end of month",
            memory_type=MemoryType.NOTE,
            tags=["reminder", "quarterly-report", "deadline"],
            context="Important tasks"
        )
        
        # Assistant can recall schedule information
        schedule_info = await manager.get_memories_by_tags(["schedule"])
        assert len(schedule_info) >= 1
        
        # Assistant can suggest meeting locations based on preferences
        meeting_prefs = await manager.get_memories_by_tags(["meeting-preference"])
        assert len(meeting_prefs) >= 1
        
        # Assistant can track reminders and deadlines
        reminders = await manager.get_memories_by_tags(["reminder"])
        assert len(reminders) >= 1
        
        # Get comprehensive view of user's information
        stats = await manager.get_memory_statistics()
        assert stats['total_count'] >= 3