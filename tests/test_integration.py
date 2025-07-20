"""
Integration tests for AI Context Memory MCP Server.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch

from src.server import AIContextMemoryServer, setup_logging, parse_arguments

class TestAIContextMemoryServer:
    """Test cases for AIContextMemoryServer."""
    
    @pytest_asyncio.fixture
    async def server(self):
        """Create a test server."""
        server = AIContextMemoryServer(":memory:")
        yield server
        await server.cleanup()
    
    @pytest_asyncio.fixture
    async def file_server(self):
        """Create a test server with file database."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        server = AIContextMemoryServer(db_path)
        yield server
        await server.cleanup()
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, server):
        """Test server initialization."""
        assert not server._initialized
        assert server.memory_manager is None
        
        await server.initialize()
        
        assert server._initialized
        assert server.memory_manager is not None
        assert server.server_name == "ai-context-memory"
        assert server.server_version == "0.1.0"
    
    @pytest.mark.asyncio
    async def test_server_double_initialization(self, server):
        """Test that double initialization is handled gracefully."""
        await server.initialize()
        assert server._initialized
        
        # Second initialization should not fail
        await server.initialize()
        assert server._initialized
    
    @pytest.mark.asyncio
    async def test_server_custom_parameters(self):
        """Test server with custom parameters."""
        server = AIContextMemoryServer(
            db_path=":memory:",
            server_name="custom-server",
            server_version="1.0.0"
        )
        
        assert server.server_name == "custom-server"
        assert server.server_version == "1.0.0"
        assert server.db_path == ":memory:"
        
        await server.cleanup()
    
    @pytest.mark.asyncio
    async def test_get_server_info_uninitialized(self, server):
        """Test getting server info before initialization."""
        info = await server.get_server_info()
        
        assert info["name"] == "ai-context-memory"
        assert info["version"] == "0.1.0"
        assert info["database_path"] == ":memory:"
        assert info["initialized"] is False
        assert "memory_statistics" not in info
    
    @pytest.mark.asyncio
    async def test_get_server_info_initialized(self, server):
        """Test getting server info after initialization."""
        await server.initialize()
        info = await server.get_server_info()
        
        assert info["name"] == "ai-context-memory"
        assert info["version"] == "0.1.0"
        assert info["database_path"] == ":memory:"
        assert info["initialized"] is True
        assert "memory_statistics" in info
        
        # Check that statistics are included
        stats = info["memory_statistics"]
        assert "total_count" in stats
        assert "fact_count" in stats
    
    @pytest.mark.asyncio
    async def test_cleanup(self, server):
        """Test server cleanup."""
        await server.initialize()
        assert server.memory_manager is not None
        
        await server.cleanup()
        # Memory manager should still exist but be closed
        assert server.memory_manager is not None
    
    @pytest.mark.asyncio
    async def test_file_database_server(self, file_server):
        """Test server with file database."""
        await file_server.initialize()
        
        # Test that we can store and retrieve a memory
        memory_id = await file_server.memory_manager.store_memory(
            "Test memory",
            file_server.memory_manager._validate_memory_type("fact")
        )
        
        assert memory_id is not None
        
        memory = await file_server.memory_manager.get_memory_by_id(memory_id)
        assert memory is not None
        assert memory.content == "Test memory"

class TestServerUtilities:
    """Test server utility functions."""
    
    def test_setup_logging_default(self):
        """Test default logging setup."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging()
            mock_config.assert_called_once()
    
    def test_setup_logging_with_file(self):
        """Test logging setup with file."""
        with patch('logging.basicConfig') as mock_config, \
             patch('logging.FileHandler') as mock_file_handler:
            
            setup_logging(log_level="DEBUG", log_file="test.log")
            mock_config.assert_called_once()
            mock_file_handler.assert_called_once_with("test.log")
    
    def test_parse_arguments_default(self):
        """Test argument parsing with defaults."""
        with patch('sys.argv', ['server.py']):
            args = parse_arguments()
            
            assert args.db_path == "memories.db"
            assert args.log_level == "INFO"
            assert args.log_file is None
            assert args.server_name == "ai-context-memory"
            assert args.server_version == "0.1.0"
            assert args.info is False
    
    def test_parse_arguments_custom(self):
        """Test argument parsing with custom values."""
        test_args = [
            'server.py',
            '--db-path', 'custom.db',
            '--log-level', 'DEBUG',
            '--log-file', 'server.log',
            '--server-name', 'custom-server',
            '--server-version', '2.0.0',
            '--info'
        ]
        
        with patch('sys.argv', test_args):
            args = parse_arguments()
            
            assert args.db_path == "custom.db"
            assert args.log_level == "DEBUG"
            assert args.log_file == "server.log"
            assert args.server_name == "custom-server"
            assert args.server_version == "2.0.0"
            assert args.info is True

class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    @pytest_asyncio.fixture
    async def initialized_server(self):
        """Create and initialize a test server."""
        server = AIContextMemoryServer(":memory:")
        await server.initialize()
        yield server
        await server.cleanup()
    
    @pytest.mark.asyncio
    async def test_full_memory_workflow(self, initialized_server):
        """Test a complete memory management workflow."""
        server = initialized_server
        manager = server.memory_manager
        
        # Store a memory
        memory_id = await manager.store_memory(
            content="Python is a programming language",
            memory_type=manager._validate_memory_type("fact"),
            tags=["python", "programming"],
            context="Learning materials"
        )
        
        assert memory_id is not None
        
        # Retrieve the memory
        memory = await manager.get_memory_by_id(memory_id)
        assert memory is not None
        assert memory.content == "Python is a programming language"
        assert "python" in memory.tags
        assert "programming" in memory.tags
        assert memory.context == "Learning materials"
        
        # Search for memories
        results = await manager.retrieve_memories("Python")
        assert len(results) == 1
        assert results[0].id == memory_id
        
        # Update the memory
        success = await manager.update_memory(
            memory_id,
            content="Python is a high-level programming language"
        )
        assert success is True
        
        # Verify update
        updated_memory = await manager.get_memory_by_id(memory_id)
        assert updated_memory.content == "Python is a high-level programming language"
        
        # Get statistics
        stats = await manager.get_memory_statistics()
        assert stats['total_count'] == 1
        assert stats['fact_count'] == 1
        
        # Delete the memory
        success = await manager.delete_memory(memory_id)
        assert success is True
        
        # Verify deletion
        deleted_memory = await manager.get_memory_by_id(memory_id)
        assert deleted_memory is None
    
    @pytest.mark.asyncio
    async def test_server_info_with_data(self, initialized_server):
        """Test server info with actual data."""
        server = initialized_server
        manager = server.memory_manager
        
        # Add some test data
        await manager.store_memory("Fact 1", manager._validate_memory_type("fact"))
        await manager.store_memory("Note 1", manager._validate_memory_type("note"), tags=["test"])
        await manager.store_memory("Preference 1", manager._validate_memory_type("preference"))
        
        # Get server info
        info = await server.get_server_info()
        
        assert info["initialized"] is True
        stats = info["memory_statistics"]
        assert stats["total_count"] == 3
        assert stats["fact_count"] == 1
        assert stats["note_count"] == 1
        assert stats["preference_count"] == 1
        assert stats["total_tags"] == 1  # "test" tag
    
    @pytest.mark.asyncio
    async def test_error_handling_in_server_info(self):
        """Test error handling when getting server info."""
        server = AIContextMemoryServer(":memory:")
        await server.initialize()
        
        # Mock the memory manager to raise an exception
        with patch.object(server.memory_manager, 'get_memory_statistics', 
                         side_effect=Exception("Test error")):
            info = await server.get_server_info()
            
            assert info["initialized"] is True
            assert "memory_statistics" in info
            assert "error" in info["memory_statistics"]
            assert info["memory_statistics"]["error"] == "Test error"
        
        await server.cleanup()