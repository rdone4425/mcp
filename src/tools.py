"""
MCP tool definitions for AI Context Memory.
"""

from typing import Any, Dict, List, Optional
import json
import logging
from datetime import datetime

import mcp.types as types
from mcp.server import Server

from .memory_manager import MemoryManager
from .models import MemoryType

logger = logging.getLogger(__name__)

def validate_required_param(arguments: Dict[str, Any], param_name: str, param_type: type = str):
    """Validate that a required parameter exists and has the correct type."""
    if param_name not in arguments:
        raise ValueError(f"Missing required parameter: {param_name}")
    
    value = arguments[param_name]
    if not isinstance(value, param_type):
        raise ValueError(f"Parameter '{param_name}' must be of type {param_type.__name__}, got {type(value).__name__}")
    
    return value

def validate_optional_param(arguments: Dict[str, Any], param_name: str, param_type: type = str, default=None):
    """Validate an optional parameter if it exists."""
    if param_name not in arguments:
        return default
    
    value = arguments[param_name]
    if value is None:
        return default
    
    if not isinstance(value, param_type):
        raise ValueError(f"Parameter '{param_name}' must be of type {param_type.__name__}, got {type(value).__name__}")
    
    return value

def format_memory_for_output(memory) -> str:
    """Format a memory object for text output."""
    output = f"ID: {memory.id}\n"
    output += f"Content: {memory.content}\n"
    output += f"Type: {memory.memory_type.value}\n"
    
    if memory.context:
        output += f"Context: {memory.context}\n"
    
    if memory.tags:
        output += f"Tags: {', '.join(memory.tags)}\n"
    
    if memory.created_at:
        output += f"Created: {memory.created_at.isoformat()}\n"
    
    if memory.updated_at:
        output += f"Updated: {memory.updated_at.isoformat()}\n"
    
    output += f"Access Count: {memory.access_count}\n"
    
    if memory.last_accessed:
        output += f"Last Accessed: {memory.last_accessed.isoformat()}\n"
    
    return output

def register_tools(server: Server, memory_manager: MemoryManager):
    """Register all MCP tools with the server."""
    
    @server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        """List available tools."""
        return [
            types.Tool(
                name="store_memory",
                description="Store a new memory with content, type, optional tags and context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The memory content to store"
                        },
                        "memory_type": {
                            "type": "string",
                            "enum": ["fact", "preference", "conversation", "note"],
                            "description": "Type of memory"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional tags for the memory"
                        },
                        "context": {
                            "type": "string",
                            "description": "Optional context information"
                        }
                    },
                    "required": ["content", "memory_type"]
                }
            ),
            types.Tool(
                name="retrieve_memories",
                description="Retrieve memories based on a search query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find relevant memories"
                        },
                        "memory_type": {
                            "type": "string",
                            "enum": ["fact", "preference", "conversation", "note"],
                            "description": "Optional filter by memory type"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "Maximum number of memories to return"
                        }
                    },
                    "required": ["query"]
                }
            ),
            types.Tool(
                name="search_memories",
                description="Advanced search with multiple filters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keywords to search for"
                        },
                        "memory_type": {
                            "type": "string",
                            "enum": ["fact", "preference", "conversation", "note"],
                            "description": "Filter by memory type"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by tags"
                        },
                        "match_all_tags": {
                            "type": "boolean",
                            "description": "Whether to match all tags (AND) or any tag (OR)"
                        },
                        "days_back": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "Search within the last N days"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "Maximum number of memories to return"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="list_memories",
                description="List memories with optional filtering and pagination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_type": {
                            "type": "string",
                            "enum": ["fact", "preference", "conversation", "note"],
                            "description": "Filter by memory type"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "Maximum number of memories to return"
                        },
                        "offset": {
                            "type": "integer",
                            "minimum": 0,
                            "description": "Number of memories to skip"
                        }
                    },
                    "required": []
                }
            ),
            types.Tool(
                name="get_memory",
                description="Get a specific memory by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "ID of the memory to retrieve"
                        }
                    },
                    "required": ["memory_id"]
                }
            ),
            types.Tool(
                name="update_memory",
                description="Update an existing memory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "ID of the memory to update"
                        },
                        "content": {
                            "type": "string",
                            "description": "New content for the memory"
                        },
                        "context": {
                            "type": "string",
                            "description": "New context for the memory"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "New tags for the memory"
                        }
                    },
                    "required": ["memory_id"]
                }
            ),
            types.Tool(
                name="delete_memory",
                description="Delete a specific memory by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "ID of the memory to delete"
                        }
                    },
                    "required": ["memory_id"]
                }
            ),
            types.Tool(
                name="clear_memories",
                description="Clear all memories or memories of a specific type",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_type": {
                            "type": "string",
                            "enum": ["fact", "preference", "conversation", "note"],
                            "description": "Optional: only clear memories of this type"
                        },
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true to confirm the operation"
                        }
                    },
                    "required": ["confirm"]
                }
            ),
            types.Tool(
                name="get_memory_statistics",
                description="Get comprehensive statistics about stored memories",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            types.Tool(
                name="get_tags",
                description="Get all available tags",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    @server.call_tool()
    async def store_memory(arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Store a new memory."""
        try:
            # Validate required parameters
            content = validate_required_param(arguments, "content", str)
            memory_type_str = validate_required_param(arguments, "memory_type", str)
            
            # Validate optional parameters
            tags = validate_optional_param(arguments, "tags", list, [])
            context = validate_optional_param(arguments, "context", str)
            
            # Convert memory type string to enum
            try:
                memory_type = MemoryType(memory_type_str)
            except ValueError:
                raise ValueError(f"Invalid memory type: {memory_type_str}")
            
            # Store the memory
            memory_id = await memory_manager.store_memory(
                content=content,
                memory_type=memory_type,
                tags=tags,
                context=context
            )
            
            return [types.TextContent(
                type="text",
                text=f"Memory stored successfully with ID: {memory_id}"
            )]
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error storing memory: {str(e)}"
            )]
    
    @server.call_tool()
    async def retrieve_memories(arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Retrieve memories based on query."""
        try:
            # Validate required parameters
            query = validate_required_param(arguments, "query", str)
            
            # Validate optional parameters
            memory_type_str = validate_optional_param(arguments, "memory_type", str)
            limit = validate_optional_param(arguments, "limit", int)
            
            # Convert memory type if provided
            memory_type = None
            if memory_type_str:
                try:
                    memory_type = MemoryType(memory_type_str)
                except ValueError:
                    raise ValueError(f"Invalid memory type: {memory_type_str}")
            
            # Retrieve memories
            memories = await memory_manager.retrieve_memories(
                query=query,
                memory_type=memory_type,
                limit=limit
            )
            
            if not memories:
                return [types.TextContent(
                    type="text",
                    text="No memories found matching the query."
                )]
            
            # Format output
            output = f"Found {len(memories)} memories:\n\n"
            for i, memory in enumerate(memories, 1):
                output += f"--- Memory {i} ---\n"
                output += format_memory_for_output(memory)
                output += "\n"
            
            return [types.TextContent(
                type="text",
                text=output
            )]
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error retrieving memories: {str(e)}"
            )]
    
    @server.call_tool()
    async def search_memories(arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Search memories with advanced filters."""
        try:
            # Validate optional parameters
            keywords = validate_optional_param(arguments, "keywords", list)
            memory_type_str = validate_optional_param(arguments, "memory_type", str)
            tags = validate_optional_param(arguments, "tags", list)
            match_all_tags = validate_optional_param(arguments, "match_all_tags", bool, False)
            days_back = validate_optional_param(arguments, "days_back", int)
            limit = validate_optional_param(arguments, "limit", int)
            
            # Convert memory type if provided
            memory_type = None
            if memory_type_str:
                try:
                    memory_type = MemoryType(memory_type_str)
                except ValueError:
                    raise ValueError(f"Invalid memory type: {memory_type_str}")
            
            # Calculate date range if days_back is provided
            date_from = None
            if days_back:
                from datetime import timedelta
                date_from = datetime.now() - timedelta(days=days_back)
            
            # Perform search
            if tags and not keywords:
                # Tag-based search
                memories = await memory_manager.get_memories_by_tags(
                    tags=tags,
                    match_all=match_all_tags,
                    memory_type=memory_type,
                    limit=limit
                )
            elif keywords and not tags:
                # Keyword-based search
                memories = await memory_manager.search_memories_by_keywords(
                    keywords=keywords,
                    match_all=False,  # Use OR logic for keywords
                    memory_type=memory_type,
                    limit=limit
                )
            else:
                # Advanced search with multiple filters
                memories = await memory_manager.search_memories(
                    keywords=keywords,
                    memory_type=memory_type,
                    tags=tags,
                    date_from=date_from,
                    limit=limit
                )
            
            if not memories:
                return [types.TextContent(
                    type="text",
                    text="No memories found matching the search criteria."
                )]
            
            # Format output
            output = f"Found {len(memories)} memories:\n\n"
            for i, memory in enumerate(memories, 1):
                output += f"--- Memory {i} ---\n"
                output += format_memory_for_output(memory)
                output += "\n"
            
            return [types.TextContent(
                type="text",
                text=output
            )]
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error searching memories: {str(e)}"
            )]
    
    @server.call_tool()
    async def list_memories(arguments: Dict[str, Any]) -> List[types.TextContent]:
        """List all memories with optional filtering."""
        try:
            # Validate optional parameters
            memory_type_str = validate_optional_param(arguments, "memory_type", str)
            limit = validate_optional_param(arguments, "limit", int)
            offset = validate_optional_param(arguments, "offset", int)
            
            # Convert memory type if provided
            memory_type = None
            if memory_type_str:
                try:
                    memory_type = MemoryType(memory_type_str)
                except ValueError:
                    raise ValueError(f"Invalid memory type: {memory_type_str}")
            
            # List memories
            memories = await memory_manager.list_memories(
                memory_type=memory_type,
                limit=limit,
                offset=offset
            )
            
            if not memories:
                return [types.TextContent(
                    type="text",
                    text="No memories found."
                )]
            
            # Format output
            output = f"Found {len(memories)} memories:\n\n"
            for i, memory in enumerate(memories, 1):
                output += f"--- Memory {i} ---\n"
                output += format_memory_for_output(memory)
                output += "\n"
            
            return [types.TextContent(
                type="text",
                text=output
            )]
            
        except Exception as e:
            logger.error(f"Error listing memories: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error listing memories: {str(e)}"
            )]
    
    @server.call_tool()
    async def get_memory(arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get a specific memory by ID."""
        try:
            # Validate required parameters
            memory_id = validate_required_param(arguments, "memory_id", int)
            
            # Get the memory
            memory = await memory_manager.get_memory_by_id(memory_id)
            
            if not memory:
                return [types.TextContent(
                    type="text",
                    text=f"Memory with ID {memory_id} not found."
                )]
            
            # Format output
            output = format_memory_for_output(memory)
            
            return [types.TextContent(
                type="text",
                text=output
            )]
            
        except Exception as e:
            logger.error(f"Error getting memory: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error getting memory: {str(e)}"
            )]
    
    @server.call_tool()
    async def update_memory(arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Update an existing memory."""
        try:
            # Validate required parameters
            memory_id = validate_required_param(arguments, "memory_id", int)
            
            # Validate optional parameters
            content = validate_optional_param(arguments, "content", str)
            context = validate_optional_param(arguments, "context", str)
            tags = validate_optional_param(arguments, "tags", list)
            
            # At least one field must be provided for update
            if not any([content, context is not None, tags is not None]):
                raise ValueError("At least one field (content, context, or tags) must be provided for update")
            
            # Update the memory
            success = await memory_manager.update_memory(
                memory_id=memory_id,
                content=content,
                context=context,
                tags=tags
            )
            
            if success:
                return [types.TextContent(
                    type="text",
                    text=f"Memory {memory_id} updated successfully."
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Memory with ID {memory_id} not found."
                )]
            
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error updating memory: {str(e)}"
            )]
    
    @server.call_tool()
    async def delete_memory(arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Delete a specific memory."""
        try:
            # Validate required parameters
            memory_id = validate_required_param(arguments, "memory_id", int)
            
            # Delete the memory
            success = await memory_manager.delete_memory(memory_id)
            
            if success:
                return [types.TextContent(
                    type="text",
                    text=f"Memory {memory_id} deleted successfully."
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Memory with ID {memory_id} not found."
                )]
            
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error deleting memory: {str(e)}"
            )]
    
    @server.call_tool()
    async def clear_memories(arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Clear all memories or memories of a specific type."""
        try:
            # Validate required parameters
            confirm = validate_required_param(arguments, "confirm", bool)
            
            if not confirm:
                return [types.TextContent(
                    type="text",
                    text="Operation cancelled. Set 'confirm' to true to proceed with clearing memories."
                )]
            
            # Validate optional parameters
            memory_type_str = validate_optional_param(arguments, "memory_type", str)
            
            # Convert memory type if provided
            memory_type = None
            if memory_type_str:
                try:
                    memory_type = MemoryType(memory_type_str)
                except ValueError:
                    raise ValueError(f"Invalid memory type: {memory_type_str}")
            
            # Clear memories
            cleared_count = await memory_manager.clear_memories(memory_type)
            
            if memory_type:
                return [types.TextContent(
                    type="text",
                    text=f"Cleared {cleared_count} memories of type '{memory_type.value}'."
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"Cleared all {cleared_count} memories."
                )]
            
        except Exception as e:
            logger.error(f"Error clearing memories: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error clearing memories: {str(e)}"
            )]
    
    @server.call_tool()
    async def get_memory_statistics(arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get comprehensive statistics about stored memories."""
        try:
            # Get statistics
            stats = await memory_manager.get_memory_statistics()
            
            # Format output
            output = "Memory Statistics:\n\n"
            
            # Memory counts
            output += "Memory Counts:\n"
            output += f"  Total: {stats['total_count']}\n"
            output += f"  Facts: {stats['fact_count']}\n"
            output += f"  Notes: {stats['note_count']}\n"
            output += f"  Preferences: {stats['preference_count']}\n"
            output += f"  Conversations: {stats['conversation_count']}\n\n"
            
            # Tag statistics
            output += f"Tags: {stats['total_tags']} unique tags\n\n"
            
            if stats['total_count'] > 0:
                # Access statistics
                output += "Access Statistics:\n"
                output += f"  Average access count: {stats['avg_access_count']:.2f}\n"
                output += f"  Max access count: {stats['max_access_count']}\n"
                output += f"  Min access count: {stats['min_access_count']}\n\n"
                
                # Content statistics
                output += "Content Statistics:\n"
                output += f"  Average content length: {stats['avg_content_length']:.1f} characters\n"
                output += f"  Max content length: {stats['max_content_length']} characters\n"
                output += f"  Min content length: {stats['min_content_length']} characters\n\n"
                
                # Tag usage
                output += "Tag Usage:\n"
                output += f"  Memories with tags: {stats['memories_with_tags']}\n"
                output += f"  Memories without tags: {stats['memories_without_tags']}\n\n"
                
                # Date range
                if 'oldest_memory' in stats and 'newest_memory' in stats:
                    output += "Date Range:\n"
                    output += f"  Oldest memory: {stats['oldest_memory']}\n"
                    output += f"  Newest memory: {stats['newest_memory']}\n"
            
            return [types.TextContent(
                type="text",
                text=output
            )]
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error getting statistics: {str(e)}"
            )]
    
    @server.call_tool()
    async def get_tags(arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Get all available tags."""
        try:
            # Get all tags
            tags = await memory_manager.get_all_tags()
            
            if not tags:
                return [types.TextContent(
                    type="text",
                    text="No tags found."
                )]
            
            # Format output
            output = f"Available tags ({len(tags)}):\n\n"
            for tag in sorted(tags):
                output += f"  - {tag}\n"
            
            return [types.TextContent(
                type="text",
                text=output
            )]
            
        except Exception as e:
            logger.error(f"Error getting tags: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error getting tags: {str(e)}"
            )]