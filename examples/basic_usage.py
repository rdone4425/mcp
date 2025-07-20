#!/usr/bin/env python3
"""
Basic usage examples for AI Context Memory.

This script demonstrates the core functionality of the AI Context Memory system
including storing, retrieving, and managing memories.
"""

import asyncio
from datetime import datetime
from src.memory_manager import MemoryManager
from src.models import MemoryType

async def basic_memory_operations():
    """Demonstrate basic memory operations."""
    print("🧠 AI Context Memory - Basic Usage Examples")
    print("=" * 50)
    
    # Initialize memory manager
    manager = MemoryManager(":memory:")  # Use in-memory database for demo
    await manager.initialize()
    
    try:
        # 1. Store different types of memories
        print("\n1. Storing Memories")
        print("-" * 20)
        
        # Store a fact
        fact_id = await manager.store_memory(
            content="Python is a high-level programming language created by Guido van Rossum",
            memory_type=MemoryType.FACT,
            tags=["python", "programming", "history"],
            context="Programming language facts"
        )
        print(f"✅ Stored fact with ID: {fact_id}")
        
        # Store a preference
        pref_id = await manager.store_memory(
            content="I prefer using VS Code for Python development",
            memory_type=MemoryType.PREFERENCE,
            tags=["editor", "python", "tools"],
            context="Development preferences"
        )
        print(f"✅ Stored preference with ID: {pref_id}")
        
        # Store a conversation
        conv_id = await manager.store_memory(
            content="Discussed implementing a REST API using FastAPI framework",
            memory_type=MemoryType.CONVERSATION,
            tags=["api", "fastapi", "discussion"],
            context="Team meeting notes"
        )
        print(f"✅ Stored conversation with ID: {conv_id}")
        
        # Store a note
        note_id = await manager.store_memory(
            content="Remember to update the documentation after the API changes",
            memory_type=MemoryType.NOTE,
            tags=["todo", "documentation", "api"],
            context="Action items"
        )
        print(f"✅ Stored note with ID: {note_id}")
        
        # 2. Retrieve memories
        print("\n2. Retrieving Memories")
        print("-" * 20)
        
        # Get a specific memory
        memory = await manager.get_memory_by_id(fact_id)
        print(f"📖 Retrieved memory: {memory.content[:50]}...")
        print(f"   Type: {memory.memory_type.value}")
        print(f"   Tags: {', '.join(memory.tags)}")
        print(f"   Access count: {memory.access_count}")
        
        # 3. Search memories
        print("\n3. Searching Memories")
        print("-" * 20)
        
        # Search by content
        python_memories = await manager.retrieve_memories("Python")
        print(f"🔍 Found {len(python_memories)} memories about Python:")
        for mem in python_memories:
            print(f"   - {mem.content[:60]}...")
        
        # Search by keywords
        api_memories = await manager.search_memories_by_keywords(["API", "FastAPI"])
        print(f"🔍 Found {len(api_memories)} memories about APIs:")
        for mem in api_memories:
            print(f"   - {mem.content[:60]}...")
        
        # Search by tags
        todo_memories = await manager.get_memories_by_tags(["todo"])
        print(f"🔍 Found {len(todo_memories)} todo memories:")
        for mem in todo_memories:
            print(f"   - {mem.content[:60]}...")
        
        # 4. List memories by type
        print("\n4. Listing Memories by Type")
        print("-" * 30)
        
        facts = await manager.list_memories(memory_type=MemoryType.FACT)
        preferences = await manager.list_memories(memory_type=MemoryType.PREFERENCE)
        conversations = await manager.list_memories(memory_type=MemoryType.CONVERSATION)
        notes = await manager.list_memories(memory_type=MemoryType.NOTE)
        
        print(f"📚 Facts: {len(facts)}")
        print(f"⚙️  Preferences: {len(preferences)}")
        print(f"💬 Conversations: {len(conversations)}")
        print(f"📝 Notes: {len(notes)}")
        
        # 5. Update a memory
        print("\n5. Updating Memory")
        print("-" * 18)
        
        success = await manager.update_memory(
            fact_id,
            content="Python is a high-level, interpreted programming language created by Guido van Rossum in 1991",
            tags=["python", "programming", "history", "interpreted"]
        )
        print(f"✏️  Updated memory: {success}")
        
        updated_memory = await manager.get_memory_by_id(fact_id)
        print(f"   New content: {updated_memory.content[:80]}...")
        print(f"   New tags: {', '.join(updated_memory.tags)}")
        
        # 6. Get statistics
        print("\n6. Memory Statistics")
        print("-" * 20)
        
        stats = await manager.get_memory_statistics()
        print(f"📊 Total memories: {stats['total_count']}")
        print(f"   Facts: {stats['fact_count']}")
        print(f"   Preferences: {stats['preference_count']}")
        print(f"   Conversations: {stats['conversation_count']}")
        print(f"   Notes: {stats['note_count']}")
        print(f"   Total tags: {stats['total_tags']}")
        print(f"   Average access count: {stats['avg_access_count']:.1f}")
        
        # 7. Get all tags
        print("\n7. Available Tags")
        print("-" * 16)
        
        all_tags = await manager.get_all_tags()
        print(f"🏷️  Available tags ({len(all_tags)}): {', '.join(sorted(all_tags))}")
        
        # 8. Advanced search
        print("\n8. Advanced Search")
        print("-" * 18)
        
        # Search with multiple criteria
        recent_python = await manager.search_memories(
            keywords=["Python"],
            memory_type=MemoryType.FACT,
            tags=["programming"]
        )
        print(f"🔍 Advanced search results: {len(recent_python)} memories")
        
        # Get recent memories
        recent = await manager.get_recent_memories(days=1)
        print(f"📅 Recent memories (last 24h): {len(recent)}")
        
        print("\n✨ Demo completed successfully!")
        
    finally:
        await manager.close()

async def demonstrate_memory_lifecycle():
    """Demonstrate complete memory lifecycle."""
    print("\n" + "=" * 50)
    print("🔄 Memory Lifecycle Demonstration")
    print("=" * 50)
    
    manager = MemoryManager(":memory:")
    await manager.initialize()
    
    try:
        # Create a memory
        print("\n1. Creating memory...")
        memory_id = await manager.store_memory(
            content="Learning about async programming in Python",
            memory_type=MemoryType.NOTE,
            tags=["learning", "python", "async"],
            context="Study notes"
        )
        print(f"✅ Created memory with ID: {memory_id}")
        
        # Access it multiple times to increase access count
        print("\n2. Accessing memory multiple times...")
        for i in range(3):
            memory = await manager.get_memory_by_id(memory_id)
            print(f"   Access {i+1}: Access count = {memory.access_count}")
        
        # Update the memory
        print("\n3. Updating memory...")
        await manager.update_memory(
            memory_id,
            content="Mastered async programming in Python - understanding coroutines and event loops",
            tags=["mastered", "python", "async", "coroutines"]
        )
        
        updated = await manager.get_memory_by_id(memory_id)
        print(f"✅ Updated content: {updated.content}")
        print(f"   Updated tags: {', '.join(updated.tags)}")
        
        # Show memory details
        print("\n4. Memory details:")
        print(f"   ID: {updated.id}")
        print(f"   Type: {updated.memory_type.value}")
        print(f"   Created: {updated.created_at}")
        print(f"   Updated: {updated.updated_at}")
        print(f"   Access count: {updated.access_count}")
        print(f"   Last accessed: {updated.last_accessed}")
        
        # Delete the memory
        print("\n5. Deleting memory...")
        success = await manager.delete_memory(memory_id)
        print(f"✅ Deleted: {success}")
        
        # Verify deletion
        deleted_memory = await manager.get_memory_by_id(memory_id)
        print(f"   Memory exists after deletion: {deleted_memory is not None}")
        
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(basic_memory_operations())
    asyncio.run(demonstrate_memory_lifecycle())