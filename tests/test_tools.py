"""
Unit tests for MCP tools.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

import mcp.types as types
from mcp.server import Server

from src.tools import register_tools, validate_required_param, validate_optional_param, format_memory_for_output
from src.memory_manager import MemoryManager
from src.models import Memory, MemoryType

class TestToolValidation:
    """Test parameter validation functions."""
    
    def test_validate_required_param_success(self):
        """Test successful required parameter validation."""
        args = {"param1": "value1", "param2": 123}
        
        result = validate_required_param(args, "param1", str)
        assert result == "value1"
        
        result = validate_required_param(args, "param2", int)
        assert result == 123
    
    def test_validate_required_param_missing(self):
        """Test required parameter validation with missing parameter."""
        args = {"param1": "value1"}
        
        with pytest.raises(ValueError, match="Missing required parameter: param2"):
            validate_required_param(args, "param2", str)
    
    def test_validate_required_param_wrong_type(self):
        """Test required parameter validation with wrong type."""
        args = {"param1": 123}
        
        with pytest.raises(ValueError, match="Parameter 'param1' must be of type str"):
            validate_required_param(args, "param1", str)
    
    def test_validate_optional_param_success(self):
        """Test successful optional parameter validation."""
        args = {"param1": "value1", "param2": None}
        
        result = validate_optional_param(args, "param1", str, "default")
        assert result == "value1"
        
        result = validate_optional_param(args, "param2", str, "default")
        assert result == "default"
        
        result = validate_optional_param(args, "missing", str, "default")
        assert result == "default"
    
    def test_validate_optional_param_wrong_type(self):
        """Test optional parameter validation with wrong type."""
        args = {"param1": 123}
        
        with pytest.raises(ValueError, match="Parameter 'param1' must be of type str"):
            validate_optional_param(args, "param1", str, "default")
    
    def test_format_memory_for_output(self):
        """Test memory formatting for output."""
        memory = Memory(
            id=1,
            content="Test content",
            memory_type=MemoryType.FACT,
            context="Test context",
            tags=["tag1", "tag2"],
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            updated_at=datetime(2023, 1, 2, 12, 0, 0),
            access_count=5,
            last_accessed=datetime(2023, 1, 3, 12, 0, 0)
        )
        
        output = format_memory_for_output(memory)
        
        assert "ID: 1" in output
        assert "Content: Test content" in output
        assert "Type: fact" in output
        assert "Context: Test context" in output
        assert "Tags: tag1, tag2" in output
        assert "Created: 2023-01-01T12:00:00" in output
        assert "Updated: 2023-01-02T12:00:00" in output
        assert "Access Count: 5" in output
        assert "Last Accessed: 2023-01-03T12:00:00" in output

class TestMCPTools:
    """Test MCP tool implementations."""
    
    @pytest_asyncio.fixture
    async def mock_memory_manager(self):
        """Create a mock memory manager."""
        manager = AsyncMock(spec=MemoryManager)
        return manager
    
    @pytest_asyncio.fixture
    async def server_with_tools(self, mock_memory_manager):
        """Create a server with registered tools."""
        server = Server("test-server")
        register_tools(server, mock_memory_manager)
        return server, mock_memory_manager
    
    @pytest.mark.asyncio
    async def test_list_tools(self, server_with_tools):
        """Test that all tools are properly registered."""
        server, _ = server_with_tools
        
        # Get the list_tools handler
        list_tools_handler = None
        for handler in server._tool_list_handlers:
            list_tools_handler = handler
            break
        
        assert list_tools_handler is not None
        
        # Call the handler
        tools = await list_tools_handler()
        
        # Verify all expected tools are present
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "store_memory",
            "retrieve_memories", 
            "search_memories",
            "list_memories",
            "get_memory",
            "update_memory",
            "delete_memory",
            "clear_memories",
            "get_memory_statistics",
            "get_tags"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
        
        # Verify tool schemas have required properties
        store_tool = next(tool for tool in tools if tool.name == "store_memory")
        assert "content" in store_tool.inputSchema["properties"]
        assert "memory_type" in store_tool.inputSchema["properties"]
        assert store_tool.inputSchema["required"] == ["content", "memory_type"]
    
    @pytest.mark.asyncio
    async def test_store_memory_success(self, server_with_tools):
        """Test successful memory storage."""
        server, mock_manager = server_with_tools
        mock_manager.store_memory.return_value = 123
        
        # Get the store_memory handler
        store_handler = server._tool_call_handlers["store_memory"]
        
        # Call with valid arguments
        result = await store_handler({
            "content": "Test memory",
            "memory_type": "fact",
            "tags": ["test", "example"],
            "context": "Test context"
        })
        
        # Verify the call
        mock_manager.store_memory.assert_called_once_with(
            content="Test memory",
            memory_type=MemoryType.FACT,
            tags=["test", "example"],
            context="Test context"
        )
        
        # Verify the response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Memory stored successfully with ID: 123" in result[0].text
    
    @pytest.mark.asyncio
    async def test_store_memory_validation_error(self, server_with_tools):
        """Test store memory with validation error."""
        server, mock_manager = server_with_tools
        
        store_handler = server._tool_call_handlers["store_memory"]
        
        # Call with missing required parameter
        result = await store_handler({
            "content": "Test memory"
            # missing memory_type
        })
        
        # Verify error response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Error storing memory" in result[0].text
        assert "Missing required parameter: memory_type" in result[0].text
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_success(self, server_with_tools):
        """Test successful memory retrieval."""
        server, mock_manager = server_with_tools
        
        # Mock return value
        mock_memory = Memory(
            id=1,
            content="Test memory",
            memory_type=MemoryType.FACT,
            tags=["test"],
            created_at=datetime(2023, 1, 1),
            access_count=1
        )
        mock_manager.retrieve_memories.return_value = [mock_memory]
        
        retrieve_handler = server._tool_call_handlers["retrieve_memories"]
        
        # Call with valid arguments
        result = await retrieve_handler({
            "query": "test query",
            "memory_type": "fact",
            "limit": 10
        })
        
        # Verify the call
        mock_manager.retrieve_memories.assert_called_once_with(
            query="test query",
            memory_type=MemoryType.FACT,
            limit=10
        )
        
        # Verify the response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Found 1 memories" in result[0].text
        assert "Test memory" in result[0].text
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_no_results(self, server_with_tools):
        """Test memory retrieval with no results."""
        server, mock_manager = server_with_tools
        mock_manager.retrieve_memories.return_value = []
        
        retrieve_handler = server._tool_call_handlers["retrieve_memories"]
        
        result = await retrieve_handler({
            "query": "nonexistent"
        })
        
        # Verify the response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "No memories found matching the query" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_memory_success(self, server_with_tools):
        """Test successful get memory by ID."""
        server, mock_manager = server_with_tools
        
        mock_memory = Memory(
            id=123,
            content="Test memory",
            memory_type=MemoryType.NOTE,
            access_count=2
        )
        mock_manager.get_memory_by_id.return_value = mock_memory
        
        get_handler = server._tool_call_handlers["get_memory"]
        
        result = await get_handler({
            "memory_id": 123
        })
        
        # Verify the call
        mock_manager.get_memory_by_id.assert_called_once_with(123)
        
        # Verify the response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "ID: 123" in result[0].text
        assert "Test memory" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_memory_not_found(self, server_with_tools):
        """Test get memory with non-existent ID."""
        server, mock_manager = server_with_tools
        mock_manager.get_memory_by_id.return_value = None
        
        get_handler = server._tool_call_handlers["get_memory"]
        
        result = await get_handler({
            "memory_id": 999
        })
        
        # Verify the response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Memory with ID 999 not found" in result[0].text
    
    @pytest.mark.asyncio
    async def test_update_memory_success(self, server_with_tools):
        """Test successful memory update."""
        server, mock_manager = server_with_tools
        mock_manager.update_memory.return_value = True
        
        update_handler = server._tool_call_handlers["update_memory"]
        
        result = await update_handler({
            "memory_id": 123,
            "content": "Updated content",
            "tags": ["new", "tags"]
        })
        
        # Verify the call
        mock_manager.update_memory.assert_called_once_with(
            memory_id=123,
            content="Updated content",
            context=None,
            tags=["new", "tags"]
        )
        
        # Verify the response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Memory 123 updated successfully" in result[0].text
    
    @pytest.mark.asyncio
    async def test_delete_memory_success(self, server_with_tools):
        """Test successful memory deletion."""
        server, mock_manager = server_with_tools
        mock_manager.delete_memory.return_value = True
        
        delete_handler = server._tool_call_handlers["delete_memory"]
        
        result = await delete_handler({
            "memory_id": 123
        })
        
        # Verify the call
        mock_manager.delete_memory.assert_called_once_with(123)
        
        # Verify the response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Memory 123 deleted successfully" in result[0].text
    
    @pytest.mark.asyncio
    async def test_clear_memories_with_confirmation(self, server_with_tools):
        """Test clearing memories with confirmation."""
        server, mock_manager = server_with_tools
        mock_manager.clear_memories.return_value = 5
        
        clear_handler = server._tool_call_handlers["clear_memories"]
        
        result = await clear_handler({
            "confirm": True,
            "memory_type": "fact"
        })
        
        # Verify the call
        mock_manager.clear_memories.assert_called_once_with(MemoryType.FACT)
        
        # Verify the response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Cleared 5 memories of type 'fact'" in result[0].text
    
    @pytest.mark.asyncio
    async def test_clear_memories_without_confirmation(self, server_with_tools):
        """Test clearing memories without confirmation."""
        server, mock_manager = server_with_tools
        
        clear_handler = server._tool_call_handlers["clear_memories"]
        
        result = await clear_handler({
            "confirm": False
        })
        
        # Verify no call was made
        mock_manager.clear_memories.assert_not_called()
        
        # Verify the response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Operation cancelled" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_memory_statistics(self, server_with_tools):
        """Test getting memory statistics."""
        server, mock_manager = server_with_tools
        mock_manager.get_memory_statistics.return_value = {
            'total_count': 10,
            'fact_count': 5,
            'note_count': 3,
            'preference_count': 2,
            'conversation_count': 0,
            'total_tags': 8,
            'avg_access_count': 2.5,
            'max_access_count': 10,
            'min_access_count': 0
        }
        
        stats_handler = server._tool_call_handlers["get_memory_statistics"]
        
        result = await stats_handler({})
        
        # Verify the call
        mock_manager.get_memory_statistics.assert_called_once()
        
        # Verify the response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Memory Statistics" in result[0].text
        assert "Total: 10" in result[0].text
        assert "Facts: 5" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_tags(self, server_with_tools):
        """Test getting all tags."""
        server, mock_manager = server_with_tools
        mock_manager.get_all_tags.return_value = ["python", "javascript", "tutorial"]
        
        tags_handler = server._tool_call_handlers["get_tags"]
        
        result = await tags_handler({})
        
        # Verify the call
        mock_manager.get_all_tags.assert_called_once()
        
        # Verify the response
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Available tags (3)" in result[0].text
        assert "python" in result[0].text
        assert "javascript" in result[0].text
        assert "tutorial" in result[0].text