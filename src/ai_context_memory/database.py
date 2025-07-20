"""
Database Manager for SQLite operations.
"""

import sqlite3
import aiosqlite
from typing import List, Dict, Any, Optional, Tuple
import logging
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLite database manager for memory storage."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 使用用户主目录下的.ai-context-memory文件夹
            from pathlib import Path
            data_dir = Path.home() / ".ai-context-memory"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "memories.db")
        self.db_path = db_path
        self._initialized = False
        self._connection = None  # For in-memory databases
        
    async def initialize(self):
        """Initialize database and create tables."""
        try:
            # Create directory if it doesn't exist
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # For in-memory databases, keep a persistent connection
            if self.db_path == ":memory:":
                self._connection = await aiosqlite.connect(self.db_path)
                await self._setup_database(self._connection)
            else:
                async with aiosqlite.connect(self.db_path) as db:
                    await self._setup_database(db)
                
            self._initialized = True
            logger.info(f"Database initialized successfully at {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
            
    async def _setup_database(self, db):
        """Setup database tables and indexes."""
        # Enable foreign key constraints
        await db.execute("PRAGMA foreign_keys = ON")
        
        # Create memories table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        """)
        
        # Create tags table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        
        # Create memory_tags association table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS memory_tags (
                memory_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (memory_id, tag_id),
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_type 
            ON memories(memory_type)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_created 
            ON memories(created_at)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_content 
            ON memories(content)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags_name 
            ON tags(name)
        """)
        
        await db.commit()
        
    async def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
        try:
            # Use persistent connection for in-memory databases
            if self._connection:
                db = self._connection
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(query, params or ())
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                async with aiosqlite.connect(self.db_path) as db:
                    # Ensure initialization for file databases
                    if not self._initialized:
                        await self._setup_database(db)
                        self._initialized = True
                        
                    db.row_factory = aiosqlite.Row
                    cursor = await db.execute(query, params or ())
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
        
    async def execute_update(
        self, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
        try:
            # Use persistent connection for in-memory databases
            if self._connection:
                db = self._connection
                cursor = await db.execute(query, params or ())
                await db.commit()
                return cursor.rowcount
            else:
                async with aiosqlite.connect(self.db_path) as db:
                    # Ensure initialization for file databases
                    if not self._initialized:
                        await self._setup_database(db)
                        self._initialized = True
                        
                    cursor = await db.execute(query, params or ())
                    await db.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Update execution failed: {e}")
            raise
            
    async def execute_insert(
        self, 
        query: str, 
        params: Optional[Tuple] = None
    ) -> int:
        """Execute an INSERT query and return the last row ID."""
        try:
            # Use persistent connection for in-memory databases
            if self._connection:
                db = self._connection
                cursor = await db.execute(query, params or ())
                await db.commit()
                return cursor.lastrowid
            else:
                async with aiosqlite.connect(self.db_path) as db:
                    # Ensure initialization for file databases
                    if not self._initialized:
                        await self._setup_database(db)
                        self._initialized = True
                        
                    cursor = await db.execute(query, params or ())
                    await db.commit()
                    return cursor.lastrowid
        except Exception as e:
            logger.error(f"Insert execution failed: {e}")
            raise
        
    async def execute_transaction(self, queries: List[Tuple[str, Tuple]]) -> bool:
        """Execute multiple queries in a transaction."""
        try:
            # Use persistent connection for in-memory databases
            if self._connection:
                db = self._connection
                async with db.execute("BEGIN"):
                    for query, params in queries:
                        await db.execute(query, params)
                    await db.commit()
                return True
            else:
                async with aiosqlite.connect(self.db_path) as db:
                    # Ensure initialization for file databases
                    if not self._initialized:
                        await self._setup_database(db)
                        self._initialized = True
                        
                    async with db.execute("BEGIN"):
                        for query, params in queries:
                            await db.execute(query, params)
                        await db.commit()
                    return True
        except Exception as e:
            logger.error(f"Transaction execution failed: {e}")
            raise
            
    async def get_or_create_tag(self, tag_name: str) -> int:
        """Get existing tag ID or create new tag and return its ID."""
        try:
            # Try to get existing tag
            result = await self.execute_query(
                "SELECT id FROM tags WHERE name = ?", 
                (tag_name,)
            )
            
            if result:
                return result[0]['id']
            
            # Create new tag if it doesn't exist
            tag_id = await self.execute_insert(
                "INSERT INTO tags (name) VALUES (?)", 
                (tag_name,)
            )
            return tag_id
            
        except Exception as e:
            logger.error(f"Failed to get or create tag '{tag_name}': {e}")
            raise
            
    async def close(self):
        """Close database connection (for cleanup)."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            
    # Memory CRUD Operations
    async def create_memory(
        self, 
        content: str, 
        memory_type: str, 
        context: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """Create a new memory and return its ID."""
        try:
            # Insert the memory
            memory_id = await self.execute_insert(
                """INSERT INTO memories (content, memory_type, context) 
                   VALUES (?, ?, ?)""",
                (content, memory_type, context)
            )
            
            # Add tags if provided
            if tags:
                tag_queries = []
                for tag_name in tags:
                    tag_id = await self.get_or_create_tag(tag_name)
                    tag_queries.append((
                        "INSERT OR IGNORE INTO memory_tags (memory_id, tag_id) VALUES (?, ?)",
                        (memory_id, tag_id)
                    ))
                
                if tag_queries:
                    await self.execute_transaction(tag_queries)
            
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to create memory: {e}")
            raise
            
    async def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """Get a memory by ID with its tags."""
        try:
            # Update access count and last accessed time first
            updated_rows = await self.execute_update(
                """UPDATE memories 
                   SET access_count = access_count + 1, 
                       last_accessed = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (memory_id,)
            )
            
            if updated_rows == 0:
                return None  # Memory doesn't exist
            
            # Get memory details (now with updated access count)
            memories = await self.execute_query(
                """SELECT id, content, memory_type, context, created_at, 
                          updated_at, access_count, last_accessed 
                   FROM memories WHERE id = ?""",
                (memory_id,)
            )
            
            if not memories:
                return None
                
            memory = memories[0]
            
            # Get associated tags
            tags = await self.execute_query(
                """SELECT t.name FROM tags t 
                   JOIN memory_tags mt ON t.id = mt.tag_id 
                   WHERE mt.memory_id = ?""",
                (memory_id,)
            )
            
            memory['tags'] = [tag['name'] for tag in tags]
            
            return memory
            
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
        """Update a memory's content, context, or tags."""
        try:
            # Check if memory exists
            existing = await self.execute_query(
                "SELECT id FROM memories WHERE id = ?", 
                (memory_id,)
            )
            if not existing:
                return False
            
            # Update content and/or context if provided
            if content is not None or context is not None:
                if content is not None and context is not None:
                    await self.execute_update(
                        """UPDATE memories 
                           SET content = ?, context = ?, updated_at = CURRENT_TIMESTAMP 
                           WHERE id = ?""",
                        (content, context, memory_id)
                    )
                elif content is not None:
                    await self.execute_update(
                        """UPDATE memories 
                           SET content = ?, updated_at = CURRENT_TIMESTAMP 
                           WHERE id = ?""",
                        (content, memory_id)
                    )
                else:  # context is not None
                    await self.execute_update(
                        """UPDATE memories 
                           SET context = ?, updated_at = CURRENT_TIMESTAMP 
                           WHERE id = ?""",
                        (context, memory_id)
                    )
            
            # Update tags if provided
            if tags is not None:
                # Remove existing tags
                await self.execute_update(
                    "DELETE FROM memory_tags WHERE memory_id = ?",
                    (memory_id,)
                )
                
                # Add new tags
                if tags:
                    tag_queries = []
                    for tag_name in tags:
                        tag_id = await self.get_or_create_tag(tag_name)
                        tag_queries.append((
                            "INSERT INTO memory_tags (memory_id, tag_id) VALUES (?, ?)",
                            (memory_id, tag_id)
                        ))
                    
                    await self.execute_transaction(tag_queries)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            raise
            
    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory by ID."""
        try:
            affected_rows = await self.execute_update(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,)
            )
            return affected_rows > 0
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            raise
            
    async def search_memories(
        self,
        query: Optional[str] = None,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search memories with various filters."""
        try:
            # Build the SQL query dynamically
            sql_parts = [
                """SELECT DISTINCT m.id, m.content, m.memory_type, m.context, 
                          m.created_at, m.updated_at, m.access_count, m.last_accessed
                   FROM memories m"""
            ]
            params = []
            conditions = []
            
            # Join with tags if needed
            if tags:
                sql_parts.append(
                    """LEFT JOIN memory_tags mt ON m.id = mt.memory_id
                       LEFT JOIN tags t ON mt.tag_id = t.id"""
                )
            
            # Add WHERE conditions
            if query:
                conditions.append("m.content LIKE ?")
                params.append(f"%{query}%")
                
            if memory_type:
                conditions.append("m.memory_type = ?")
                params.append(memory_type)
                
            if tags:
                tag_placeholders = ",".join("?" * len(tags))
                conditions.append(f"t.name IN ({tag_placeholders})")
                params.extend(tags)
            
            if conditions:
                sql_parts.append("WHERE " + " AND ".join(conditions))
            
            # Add ordering
            sql_parts.append("ORDER BY m.created_at DESC")
            
            # Add pagination
            if limit:
                sql_parts.append("LIMIT ?")
                params.append(limit)
                
            if offset:
                sql_parts.append("OFFSET ?")
                params.append(offset)
            
            sql = " ".join(sql_parts)
            memories = await self.execute_query(sql, tuple(params))
            
            # Get tags for each memory
            for memory in memories:
                memory_tags = await self.execute_query(
                    """SELECT t.name FROM tags t 
                       JOIN memory_tags mt ON t.id = mt.tag_id 
                       WHERE mt.memory_id = ?""",
                    (memory['id'],)
                )
                memory['tags'] = [tag['name'] for tag in memory_tags]
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            raise
            
    async def list_memories(
        self,
        memory_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List memories with optional filtering and pagination."""
        try:
            sql = """SELECT id, content, memory_type, context, created_at, 
                            updated_at, access_count, last_accessed 
                     FROM memories"""
            params = []
            
            if memory_type:
                sql += " WHERE memory_type = ?"
                params.append(memory_type)
            
            sql += " ORDER BY created_at DESC"
            
            if limit:
                sql += " LIMIT ?"
                params.append(limit)
                
            if offset:
                sql += " OFFSET ?"
                params.append(offset)
            
            memories = await self.execute_query(sql, tuple(params))
            
            # Get tags for each memory
            for memory in memories:
                memory_tags = await self.execute_query(
                    """SELECT t.name FROM tags t 
                       JOIN memory_tags mt ON t.id = mt.tag_id 
                       WHERE mt.memory_id = ?""",
                    (memory['id'],)
                )
                memory['tags'] = [tag['name'] for tag in memory_tags]
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to list memories: {e}")
            raise
            
    async def clear_memories(self, memory_type: Optional[str] = None) -> int:
        """Clear memories, optionally filtered by type."""
        try:
            if memory_type:
                affected_rows = await self.execute_update(
                    "DELETE FROM memories WHERE memory_type = ?",
                    (memory_type,)
                )
            else:
                affected_rows = await self.execute_update("DELETE FROM memories")
            
            return affected_rows
            
        except Exception as e:
            logger.error(f"Failed to clear memories: {e}")
            raise
            
    # Tag CRUD Operations
    async def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all tags."""
        try:
            return await self.execute_query("SELECT id, name FROM tags ORDER BY name")
        except Exception as e:
            logger.error(f"Failed to get all tags: {e}")
            raise
            
    async def delete_unused_tags(self) -> int:
        """Delete tags that are not associated with any memories."""
        try:
            affected_rows = await self.execute_update(
                """DELETE FROM tags WHERE id NOT IN (
                       SELECT DISTINCT tag_id FROM memory_tags
                   )"""
            )
            return affected_rows
        except Exception as e:
            logger.error(f"Failed to delete unused tags: {e}")
            raise
            
    async def get_memory_count(self, memory_type: Optional[str] = None) -> int:
        """Get count of memories, optionally filtered by type."""
        try:
            if memory_type:
                result = await self.execute_query(
                    "SELECT COUNT(*) as count FROM memories WHERE memory_type = ?",
                    (memory_type,)
                )
            else:
                result = await self.execute_query("SELECT COUNT(*) as count FROM memories")
            
            return result[0]['count'] if result else 0
            
        except Exception as e:
            logger.error(f"Failed to get memory count: {e}")
            raise
            
    # Memory CRUD operations
    async def insert_memory(
        self, 
        content: str, 
        memory_type: str, 
        context: Optional[str] = None
    ) -> int:
        """Insert a new memory and return its ID."""
        query = """
            INSERT INTO memories (content, memory_type, context, created_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        return await self.execute_insert(query, (content, memory_type, context))
        
    async def get_memory_by_id(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """Get a memory by its ID."""
        query = "SELECT * FROM memories WHERE id = ?"
        results = await self.execute_query(query, (memory_id,))
        return results[0] if results else None
        
    async def update_memory_content(self, memory_id: int, content: str) -> bool:
        """Update memory content and set updated_at timestamp."""
        query = """
            UPDATE memories 
            SET content = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """
        affected_rows = await self.execute_update(query, (content, memory_id))
        return affected_rows > 0
        
    async def update_memory_access(self, memory_id: int) -> bool:
        """Update memory access count and last_accessed timestamp."""
        query = """
            UPDATE memories 
            SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP 
            WHERE id = ?
        """
        affected_rows = await self.execute_update(query, (memory_id,))
        return affected_rows > 0
        
    async def delete_memory(self, memory_id: int) -> bool:
        """Delete a memory by ID."""
        query = "DELETE FROM memories WHERE id = ?"
        affected_rows = await self.execute_update(query, (memory_id,))
        return affected_rows > 0
        
    async def search_memories_by_content(
        self, 
        search_term: str, 
        memory_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search memories by content with optional type filter."""
        if memory_type:
            query = """
                SELECT * FROM memories 
                WHERE content LIKE ? AND memory_type = ?
                ORDER BY created_at DESC
            """
            params = (f"%{search_term}%", memory_type)
        else:
            query = """
                SELECT * FROM memories 
                WHERE content LIKE ?
                ORDER BY created_at DESC
            """
            params = (f"%{search_term}%",)
            
        if limit:
            query += " LIMIT ?"
            params = params + (limit,)
            
        return await self.execute_query(query, params)
        
    async def get_memories_by_type(
        self, 
        memory_type: str, 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get memories by type with pagination."""
        query = """
            SELECT * FROM memories 
            WHERE memory_type = ?
            ORDER BY created_at DESC
        """
        params = [memory_type]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
        if offset:
            query += " OFFSET ?"
            params.append(offset)
            
        return await self.execute_query(query, tuple(params))
        
    async def get_all_memories(
        self, 
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all memories with pagination."""
        query = "SELECT * FROM memories ORDER BY created_at DESC"
        params = []
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
        if offset:
            query += " OFFSET ?"
            params.append(offset)
            
        return await self.execute_query(query, tuple(params))
        
    async def clear_memories_by_type(self, memory_type: str) -> int:
        """Clear all memories of a specific type."""
        query = "DELETE FROM memories WHERE memory_type = ?"
        return await self.execute_update(query, (memory_type,))
        
    async def clear_all_memories(self) -> int:
        """Clear all memories."""
        query = "DELETE FROM memories"
        return await self.execute_update(query)
        
    # Tag CRUD operations
    async def insert_tag(self, name: str) -> int:
        """Insert a new tag and return its ID."""
        query = "INSERT INTO tags (name) VALUES (?)"
        return await self.execute_insert(query, (name,))
        
    async def get_tag_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a tag by its name."""
        query = "SELECT * FROM tags WHERE name = ?"
        results = await self.execute_query(query, (name,))
        return results[0] if results else None
        
    async def get_tag_by_id(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """Get a tag by its ID."""
        query = "SELECT * FROM tags WHERE id = ?"
        results = await self.execute_query(query, (tag_id,))
        return results[0] if results else None
        
    async def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all tags."""
        query = "SELECT * FROM tags ORDER BY name"
        return await self.execute_query(query)
        
    async def delete_tag(self, tag_id: int) -> bool:
        """Delete a tag by ID."""
        query = "DELETE FROM tags WHERE id = ?"
        affected_rows = await self.execute_update(query, (tag_id,))
        return affected_rows > 0
        
    # Memory-Tag association operations
    async def add_memory_tag(self, memory_id: int, tag_id: int) -> bool:
        """Associate a memory with a tag."""
        query = "INSERT OR IGNORE INTO memory_tags (memory_id, tag_id) VALUES (?, ?)"
        affected_rows = await self.execute_update(query, (memory_id, tag_id))
        return affected_rows > 0
        
    async def remove_memory_tag(self, memory_id: int, tag_id: int) -> bool:
        """Remove association between memory and tag."""
        query = "DELETE FROM memory_tags WHERE memory_id = ? AND tag_id = ?"
        affected_rows = await self.execute_update(query, (memory_id, tag_id))
        return affected_rows > 0
        
    async def get_memory_tags(self, memory_id: int) -> List[Dict[str, Any]]:
        """Get all tags for a specific memory."""
        query = """
            SELECT t.* FROM tags t
            JOIN memory_tags mt ON t.id = mt.tag_id
            WHERE mt.memory_id = ?
            ORDER BY t.name
        """
        return await self.execute_query(query, (memory_id,))
        
    async def get_memories_by_tag(self, tag_id: int) -> List[Dict[str, Any]]:
        """Get all memories associated with a specific tag."""
        query = """
            SELECT m.* FROM memories m
            JOIN memory_tags mt ON m.id = mt.memory_id
            WHERE mt.tag_id = ?
            ORDER BY m.created_at DESC
        """
        return await self.execute_query(query, (tag_id,))
        
    async def get_memories_by_tag_names(self, tag_names: List[str]) -> List[Dict[str, Any]]:
        """Get memories that have any of the specified tags."""
        if not tag_names:
            return []
            
        placeholders = ",".join("?" * len(tag_names))
        query = f"""
            SELECT DISTINCT m.* FROM memories m
            JOIN memory_tags mt ON m.id = mt.memory_id
            JOIN tags t ON mt.tag_id = t.id
            WHERE t.name IN ({placeholders})
            ORDER BY m.created_at DESC
        """
        return await self.execute_query(query, tuple(tag_names))
        
    async def clear_memory_tags(self, memory_id: int) -> int:
        """Remove all tag associations for a memory."""
        query = "DELETE FROM memory_tags WHERE memory_id = ?"
        return await self.execute_update(query, (memory_id,))
        
    # Advanced search operations
    async def search_memories_with_filters(
        self,
        content_search: Optional[str] = None,
        memory_type: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Advanced search with multiple filters."""
        conditions = []
        params = []
        
        base_query = "SELECT DISTINCT m.* FROM memories m"
        
        # Join with tags if needed
        if tag_names:
            base_query += """
                JOIN memory_tags mt ON m.id = mt.memory_id
                JOIN tags t ON mt.tag_id = t.id
            """
            placeholders = ",".join("?" * len(tag_names))
            conditions.append(f"t.name IN ({placeholders})")
            params.extend(tag_names)
        
        # Add content search
        if content_search:
            conditions.append("m.content LIKE ?")
            params.append(f"%{content_search}%")
            
        # Add memory type filter
        if memory_type:
            conditions.append("m.memory_type = ?")
            params.append(memory_type)
            
        # Add date filters
        if date_from:
            conditions.append("m.created_at >= ?")
            params.append(date_from)
            
        if date_to:
            conditions.append("m.created_at <= ?")
            params.append(date_to)
        
        # Build final query
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
            
        base_query += " ORDER BY m.created_at DESC"
        
        # Add pagination
        if limit:
            base_query += " LIMIT ?"
            params.append(limit)
            
        if offset:
            base_query += " OFFSET ?"
            params.append(offset)
            
        return await self.execute_query(base_query, tuple(params))
        
    async def get_memory_count(self, memory_type: Optional[str] = None) -> int:
        """Get total count of memories, optionally filtered by type."""
        if memory_type:
            query = "SELECT COUNT(*) as count FROM memories WHERE memory_type = ?"
            params = (memory_type,)
        else:
            query = "SELECT COUNT(*) as count FROM memories"
            params = ()
            
        result = await self.execute_query(query, params)
        return result[0]['count'] if result else 0