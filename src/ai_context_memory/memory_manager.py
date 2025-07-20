"""
Memory Manager for handling AI context memory operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

try:
    from .database import DatabaseManager
    from .models import Memory, MemoryType
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    from database import DatabaseManager
    from models import Memory, MemoryType

logger = logging.getLogger(__name__)

class MemoryManager:
    """Core memory management class."""
    
    def __init__(self, db_path: str = "memories.db"):
        self.db_manager = DatabaseManager(db_path)
        
    async def initialize(self):
        """Initialize the memory manager and database."""
        await self.db_manager.initialize()
        
    async def close(self):
        """Close the memory manager and database connections."""
        await self.db_manager.close()
        
    def _validate_memory_type(self, memory_type: MemoryType) -> str:
        """Validate and convert MemoryType enum to string."""
        if isinstance(memory_type, MemoryType):
            return memory_type.value
        elif isinstance(memory_type, str):
            # Validate that the string is a valid memory type
            try:
                MemoryType(memory_type)
                return memory_type
            except ValueError:
                raise ValueError(f"Invalid memory type: {memory_type}")
        else:
            raise ValueError(f"Memory type must be MemoryType enum or string, got {type(memory_type)}")
    
    def _validate_content(self, content: str) -> str:
        """Validate memory content."""
        if not content or not content.strip():
            raise ValueError("Memory content cannot be empty")
        
        # Trim whitespace and limit length
        content = content.strip()
        if len(content) > 10000:  # 10KB limit
            raise ValueError("Memory content too long (max 10000 characters)")
            
        return content
    
    def _validate_tags(self, tags: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean tags."""
        if not tags:
            return None
            
        cleaned_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                raise ValueError(f"Tag must be string, got {type(tag)}")
            
            tag = tag.strip().lower()
            if not tag:
                continue  # Skip empty tags
                
            if len(tag) > 50:
                raise ValueError(f"Tag too long (max 50 characters): {tag}")
                
            if tag not in cleaned_tags:  # Remove duplicates
                cleaned_tags.append(tag)
        
        return cleaned_tags if cleaned_tags else None
    
    def _dict_to_memory(self, memory_dict: Dict[str, Any]) -> Memory:
        """Convert database dictionary to Memory object."""
        def parse_datetime(dt_str):
            """Parse datetime string from database."""
            if not dt_str:
                return None
            try:
                # Handle SQLite datetime format
                if isinstance(dt_str, str):
                    # SQLite CURRENT_TIMESTAMP format: YYYY-MM-DD HH:MM:SS
                    if ' ' in dt_str and len(dt_str) == 19:
                        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                    else:
                        return datetime.fromisoformat(dt_str)
                return dt_str
            except (ValueError, TypeError):
                return None
        
        return Memory(
            id=memory_dict['id'],
            content=memory_dict['content'],
            memory_type=MemoryType(memory_dict['memory_type']),
            context=memory_dict.get('context'),
            tags=memory_dict.get('tags', []),
            created_at=parse_datetime(memory_dict.get('created_at')),
            updated_at=parse_datetime(memory_dict.get('updated_at')),
            access_count=memory_dict.get('access_count', 0),
            last_accessed=parse_datetime(memory_dict.get('last_accessed'))
        )
        
    async def store_memory(
        self, 
        content: str, 
        memory_type: MemoryType, 
        tags: Optional[List[str]] = None,
        context: Optional[str] = None
    ) -> int:
        """Store a new memory."""
        try:
            # Validate inputs
            content = self._validate_content(content)
            memory_type_str = self._validate_memory_type(memory_type)
            tags = self._validate_tags(tags)
            
            # Validate context
            if context is not None:
                context = context.strip()
                if len(context) > 1000:  # 1KB limit for context
                    raise ValueError("Context too long (max 1000 characters)")
                if not context:
                    context = None
            
            # Store in database
            memory_id = await self.db_manager.create_memory(
                content=content,
                memory_type=memory_type_str,
                context=context,
                tags=tags
            )
            
            logger.info(f"Stored memory {memory_id} of type {memory_type_str}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
            
    async def retrieve_memories(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """Retrieve memories based on query."""
        try:
            # Validate inputs
            if not query or not query.strip():
                raise ValueError("Query cannot be empty")
            
            query = query.strip()
            memory_type_str = None
            if memory_type:
                memory_type_str = self._validate_memory_type(memory_type)
            
            if limit is not None and limit <= 0:
                raise ValueError("Limit must be positive")
            
            # Search in database
            memory_dicts = await self.db_manager.search_memories(
                query=query,
                memory_type=memory_type_str,
                limit=limit
            )
            
            # Convert to Memory objects
            memories = [self._dict_to_memory(mem_dict) for mem_dict in memory_dicts]
            
            logger.info(f"Retrieved {len(memories)} memories for query: {query}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            raise
            
    async def get_memory_by_id(self, memory_id: int) -> Optional[Memory]:
        """Get a specific memory by ID."""
        try:
            if memory_id <= 0:
                raise ValueError("Memory ID must be positive")
            
            memory_dict = await self.db_manager.get_memory(memory_id)
            if not memory_dict:
                return None
                
            return self._dict_to_memory(memory_dict)
            
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {e}")
            raise
            
    async def update_memory(
        self, 
        memory_id: int, 
        content: Optional[str] = None,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Update an existing memory."""
        try:
            if memory_id <= 0:
                raise ValueError("Memory ID must be positive")
            
            # Validate inputs if provided
            if content is not None:
                content = self._validate_content(content)
            
            if context is not None:
                context = context.strip()
                if len(context) > 1000:
                    raise ValueError("Context too long (max 1000 characters)")
                if not context:
                    context = None
            
            if tags is not None:
                tags = self._validate_tags(tags)
            
            # Update in database
            success = await self.db_manager.update_memory(
                memory_id=memory_id,
                content=content,
                context=context,
                tags=tags
            )
            
            if success:
                logger.info(f"Updated memory {memory_id}")
            else:
                logger.warning(f"Memory {memory_id} not found for update")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            raise
            
    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory."""
        try:
            if memory_id <= 0:
                raise ValueError("Memory ID must be positive")
            
            success = await self.db_manager.delete_memory(memory_id)
            
            if success:
                logger.info(f"Deleted memory {memory_id}")
            else:
                logger.warning(f"Memory {memory_id} not found for deletion")
                
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            raise
            
    async def list_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Memory]:
        """List memories with pagination."""
        try:
            # Validate inputs
            memory_type_str = None
            if memory_type:
                memory_type_str = self._validate_memory_type(memory_type)
            
            if limit is not None and limit <= 0:
                raise ValueError("Limit must be positive")
                
            if offset is not None and offset < 0:
                raise ValueError("Offset must be non-negative")
            
            # Get from database
            memory_dicts = await self.db_manager.list_memories(
                memory_type=memory_type_str,
                limit=limit,
                offset=offset
            )
            
            # Convert to Memory objects
            memories = [self._dict_to_memory(mem_dict) for mem_dict in memory_dicts]
            
            logger.info(f"Listed {len(memories)} memories")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to list memories: {e}")
            raise
            
    async def clear_memories(self, memory_type: Optional[MemoryType] = None) -> int:
        """Clear memories, optionally filtered by type."""
        try:
            memory_type_str = None
            if memory_type:
                memory_type_str = self._validate_memory_type(memory_type)
            
            cleared_count = await self.db_manager.clear_memories(memory_type_str)
            
            if memory_type_str:
                logger.info(f"Cleared {cleared_count} memories of type {memory_type_str}")
            else:
                logger.info(f"Cleared all {cleared_count} memories")
                
            return cleared_count
            
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            raise
            
    async def get_memory_count(self, memory_type: Optional[MemoryType] = None) -> int:
        """Get count of memories, optionally filtered by type."""
        try:
            memory_type_str = None
            if memory_type:
                memory_type_str = self._validate_memory_type(memory_type)
            
            count = await self.db_manager.get_memory_count(memory_type_str)
            return count
            
        except Exception as e:
            logger.error(f"Failed to get memory count: {e}")
            raise
            
    async def get_all_tags(self) -> List[str]:
        """Get all available tags."""
        try:
            tag_dicts = await self.db_manager.get_all_tags()
            tags = [tag_dict['name'] for tag_dict in tag_dicts]
            return tags
            
        except Exception as e:
            logger.error(f"Failed to get all tags: {e}")
            raise
            
    async def cleanup_unused_tags(self) -> int:
        """Remove tags that are not associated with any memories."""
        try:
            deleted_count = await self.db_manager.delete_unused_tags()
            logger.info(f"Cleaned up {deleted_count} unused tags")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup unused tags: {e}")
            raise
            
    # Advanced search and management functions
    async def search_memories(
        self,
        keywords: Optional[List[str]] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Memory]:
        """Search memories with advanced filters."""
        try:
            # Validate inputs
            if keywords:
                keywords = [kw.strip() for kw in keywords if kw.strip()]
                if not keywords:
                    keywords = None
            
            memory_type_str = None
            if memory_type:
                memory_type_str = self._validate_memory_type(memory_type)
            
            if tags:
                tags = self._validate_tags(tags)
            
            if limit is not None and limit <= 0:
                raise ValueError("Limit must be positive")
                
            if offset is not None and offset < 0:
                raise ValueError("Offset must be non-negative")
            
            # Convert datetime to string for database query
            date_from_str = date_from.isoformat() if date_from else None
            date_to_str = date_to.isoformat() if date_to else None
            
            # Build search query
            content_search = None
            if keywords:
                # Combine keywords with OR logic for content search
                content_search = " ".join(keywords)
            
            # Use database advanced search
            memory_dicts = await self.db_manager.search_memories_with_filters(
                content_search=content_search,
                memory_type=memory_type_str,
                tag_names=tags,
                date_from=date_from_str,
                date_to=date_to_str,
                limit=limit,
                offset=offset
            )
            
            # Convert to Memory objects
            memories = [self._dict_to_memory(mem_dict) for mem_dict in memory_dicts]
            
            logger.info(f"Advanced search returned {len(memories)} memories")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            raise
            
    async def search_memories_by_keywords(
        self,
        keywords: List[str],
        match_all: bool = False,
        memory_type: Optional[MemoryType] = None,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """Search memories by keywords with AND/OR logic."""
        try:
            if not keywords:
                raise ValueError("Keywords list cannot be empty")
            
            # Clean keywords
            keywords = [kw.strip().lower() for kw in keywords if kw.strip()]
            if not keywords:
                raise ValueError("No valid keywords provided")
            
            memory_type_str = None
            if memory_type:
                memory_type_str = self._validate_memory_type(memory_type)
            
            if limit is not None and limit <= 0:
                raise ValueError("Limit must be positive")
            
            if match_all:
                # AND logic: search for memories containing all keywords
                memories = []
                for keyword in keywords:
                    keyword_memories = await self.db_manager.search_memories(
                        query=keyword,
                        memory_type=memory_type_str
                    )
                    
                    if not memories:
                        # First keyword - initialize with all matches
                        memories = [self._dict_to_memory(mem) for mem in keyword_memories]
                    else:
                        # Subsequent keywords - keep only memories that match
                        keyword_ids = {mem['id'] for mem in keyword_memories}
                        memories = [mem for mem in memories if mem.id in keyword_ids]
                
                # Apply limit if specified
                if limit:
                    memories = memories[:limit]
                    
            else:
                # OR logic: search for memories containing any keyword
                all_memory_dicts = []
                seen_ids = set()
                
                for keyword in keywords:
                    keyword_memories = await self.db_manager.search_memories(
                        query=keyword,
                        memory_type=memory_type_str
                    )
                    
                    for mem_dict in keyword_memories:
                        if mem_dict['id'] not in seen_ids:
                            all_memory_dicts.append(mem_dict)
                            seen_ids.add(mem_dict['id'])
                
                # Sort by creation date (newest first)
                all_memory_dicts.sort(key=lambda x: x['created_at'], reverse=True)
                
                # Apply limit if specified
                if limit:
                    all_memory_dicts = all_memory_dicts[:limit]
                
                memories = [self._dict_to_memory(mem_dict) for mem_dict in all_memory_dicts]
            
            logger.info(f"Keyword search ({'AND' if match_all else 'OR'}) returned {len(memories)} memories")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search by keywords: {e}")
            raise
            
    async def get_memories_by_tags(
        self,
        tags: List[str],
        match_all: bool = False,
        memory_type: Optional[MemoryType] = None,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """Get memories that have specific tags."""
        try:
            if not tags:
                raise ValueError("Tags list cannot be empty")
            
            # Validate and clean tags
            tags = self._validate_tags(tags)
            if not tags:
                raise ValueError("No valid tags provided")
            
            memory_type_str = None
            if memory_type:
                memory_type_str = self._validate_memory_type(memory_type)
            
            if limit is not None and limit <= 0:
                raise ValueError("Limit must be positive")
            
            if match_all:
                # AND logic: memories must have all specified tags
                # Get all memories first, then filter
                all_memories = await self.db_manager.list_memories(
                    memory_type=memory_type_str
                )
                
                # Filter to ensure ALL tags are present
                filtered_memories = []
                for mem_dict in all_memories:
                    mem_tags = set(mem_dict.get('tags', []))
                    if set(tags).issubset(mem_tags):
                        filtered_memories.append(mem_dict)
                
                # Apply limit if specified
                if limit:
                    filtered_memories = filtered_memories[:limit]
                
                memory_dicts = filtered_memories
                
            else:
                # OR logic: memories with any of the specified tags
                memory_dicts = await self.db_manager.get_memories_by_tag_names(tags)
                
                # Apply type filter if specified
                if memory_type_str:
                    memory_dicts = [
                        mem for mem in memory_dicts 
                        if mem['memory_type'] == memory_type_str
                    ]
                
                # Apply limit if specified
                if limit:
                    memory_dicts = memory_dicts[:limit]
            
            memories = [self._dict_to_memory(mem_dict) for mem_dict in memory_dicts]
            
            logger.info(f"Tag search ({'AND' if match_all else 'OR'}) returned {len(memories)} memories")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get memories by tags: {e}")
            raise
            
    async def get_recent_memories(
        self,
        days: int = 7,
        memory_type: Optional[MemoryType] = None,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """Get memories created in the last N days."""
        try:
            if days <= 0:
                raise ValueError("Days must be positive")
            
            # Calculate date threshold
            date_from = datetime.now() - timedelta(days=days)
            
            return await self.search_memories(
                memory_type=memory_type,
                date_from=date_from,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Failed to get recent memories: {e}")
            raise
            
    async def get_frequently_accessed_memories(
        self,
        min_access_count: int = 2,
        memory_type: Optional[MemoryType] = None,
        limit: Optional[int] = None
    ) -> List[Memory]:
        """Get memories that have been accessed frequently."""
        try:
            if min_access_count <= 0:
                raise ValueError("Minimum access count must be positive")
            
            memory_type_str = None
            if memory_type:
                memory_type_str = self._validate_memory_type(memory_type)
            
            if limit is not None and limit <= 0:
                raise ValueError("Limit must be positive")
            
            # Get all memories and filter by access count
            all_memories = await self.list_memories(
                memory_type=memory_type,
                limit=None  # Get all first, then filter
            )
            
            # Filter by access count
            frequent_memories = [
                mem for mem in all_memories 
                if mem.access_count >= min_access_count
            ]
            
            # Sort by access count (descending)
            frequent_memories.sort(key=lambda x: x.access_count, reverse=True)
            
            # Apply limit if specified
            if limit:
                frequent_memories = frequent_memories[:limit]
            
            logger.info(f"Found {len(frequent_memories)} frequently accessed memories")
            return frequent_memories
            
        except Exception as e:
            logger.error(f"Failed to get frequently accessed memories: {e}")
            raise
            
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about stored memories."""
        try:
            stats = {}
            
            # Total counts by type
            for memory_type in MemoryType:
                count = await self.get_memory_count(memory_type)
                stats[f"{memory_type.value}_count"] = count
            
            # Total count
            stats['total_count'] = await self.get_memory_count()
            
            # Tag statistics
            all_tags = await self.get_all_tags()
            stats['total_tags'] = len(all_tags)
            
            # Get all memories for additional statistics
            all_memories = await self.list_memories()
            
            if all_memories:
                # Access count statistics
                access_counts = [mem.access_count for mem in all_memories]
                stats['avg_access_count'] = sum(access_counts) / len(access_counts)
                stats['max_access_count'] = max(access_counts)
                stats['min_access_count'] = min(access_counts)
                
                # Date statistics
                created_dates = [mem.created_at for mem in all_memories if mem.created_at]
                if created_dates:
                    stats['oldest_memory'] = min(created_dates).isoformat()
                    stats['newest_memory'] = max(created_dates).isoformat()
                
                # Content length statistics
                content_lengths = [len(mem.content) for mem in all_memories]
                stats['avg_content_length'] = sum(content_lengths) / len(content_lengths)
                stats['max_content_length'] = max(content_lengths)
                stats['min_content_length'] = min(content_lengths)
                
                # Memories with tags vs without tags
                with_tags = sum(1 for mem in all_memories if mem.tags)
                stats['memories_with_tags'] = with_tags
                stats['memories_without_tags'] = len(all_memories) - with_tags
                
            else:
                # No memories exist
                stats.update({
                    'avg_access_count': 0,
                    'max_access_count': 0,
                    'min_access_count': 0,
                    'avg_content_length': 0,
                    'max_content_length': 0,
                    'min_content_length': 0,
                    'memories_with_tags': 0,
                    'memories_without_tags': 0
                })
            
            logger.info("Generated memory statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory statistics: {e}")
            raise
            
    async def update_memory_access_count(self, memory_id: int) -> bool:
        """Manually update memory access count (without retrieving content)."""
        try:
            if memory_id <= 0:
                raise ValueError("Memory ID must be positive")
            
            # Use database manager's update method
            success = await self.db_manager.execute_update(
                """UPDATE memories 
                   SET access_count = access_count + 1, 
                       last_accessed = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (memory_id,)
            )
            
            return success > 0
            
        except Exception as e:
            logger.error(f"Failed to update access count for memory {memory_id}: {e}")
            raise