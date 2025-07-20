#!/usr/bin/env python3
"""
AI Assistant Memory Example.

This example demonstrates how an AI assistant can use the memory system
to maintain context across conversations and provide personalized responses.
"""

import asyncio
from datetime import datetime
from src.memory_manager import MemoryManager
from src.models import MemoryType

class AIAssistant:
    """Simple AI Assistant with memory capabilities."""
    
    def __init__(self, db_path=":memory:"):
        self.memory = None
        self.db_path = db_path
        self.user_name = None
        
    async def initialize(self):
        """Initialize the assistant's memory system."""
        self.memory = MemoryManager(self.db_path)
        await self.memory.initialize()
        
        # Try to recall user's name
        name_memories = await self.memory.get_memories_by_tags(["user-name"])
        if name_memories:
            # Extract name from the first memory
            content = name_memories[0].content
            if "name is" in content.lower():
                self.user_name = content.split("name is")[-1].strip()
        
    async def close(self):
        """Close the memory system."""
        if self.memory:
            await self.memory.close()
    
    async def remember_user_info(self, info_type, content, tags=None):
        """Store user information."""
        if tags is None:
            tags = []
        
        await self.memory.store_memory(
            content=content,
            memory_type=MemoryType.FACT,
            tags=["user-info"] + tags,
            context="User information"
        )
        print(f"🧠 Remembered: {content}")
    
    async def remember_preference(self, preference, tags=None):
        """Store user preference."""
        if tags is None:
            tags = []
            
        await self.memory.store_memory(
            content=preference,
            memory_type=MemoryType.PREFERENCE,
            tags=["user-preference"] + tags,
            context="User preferences"
        )
        print(f"⚙️  Noted preference: {preference}")
    
    async def remember_conversation(self, topic, details, tags=None):
        """Store conversation details."""
        if tags is None:
            tags = []
            
        await self.memory.store_memory(
            content=f"Discussed {topic}: {details}",
            memory_type=MemoryType.CONVERSATION,
            tags=["conversation", topic.lower()] + tags,
            context="Conversation history"
        )
        print(f"💬 Recorded conversation about: {topic}")
    
    async def add_note(self, note, tags=None):
        """Add a note or reminder."""
        if tags is None:
            tags = []
            
        await self.memory.store_memory(
            content=note,
            memory_type=MemoryType.NOTE,
            tags=["note"] + tags,
            context="Assistant notes"
        )
        print(f"📝 Added note: {note}")
    
    async def recall_about(self, topic):
        """Recall information about a topic."""
        memories = await self.memory.retrieve_memories(topic)
        return memories
    
    async def get_user_preferences(self):
        """Get all user preferences."""
        return await self.memory.list_memories(memory_type=MemoryType.PREFERENCE)
    
    async def get_conversation_history(self, topic=None):
        """Get conversation history, optionally filtered by topic."""
        if topic:
            return await self.memory.get_memories_by_tags([topic.lower()])
        else:
            return await self.memory.list_memories(memory_type=MemoryType.CONVERSATION)
    
    async def get_pending_notes(self):
        """Get pending notes and reminders."""
        return await self.memory.get_memories_by_tags(["note"])
    
    def greet_user(self):
        """Greet the user, using their name if known."""
        if self.user_name:
            return f"Hello {self.user_name}! How can I help you today?"
        else:
            return "Hello! How can I help you today?"

async def simulate_ai_assistant_conversation():
    """Simulate a conversation with an AI assistant that has memory."""
    print("🤖 AI Assistant with Memory - Conversation Simulation")
    print("=" * 60)
    
    assistant = AIAssistant()
    await assistant.initialize()
    
    try:
        # Initial greeting
        print(f"\nAssistant: {assistant.greet_user()}")
        
        # Simulate user introducing themselves
        print("\nUser: Hi, my name is Alice and I'm a Python developer.")
        await assistant.remember_user_info(
            "User's name is Alice", 
            tags=["user-name", "personal"]
        )
        await assistant.remember_user_info(
            "User is a Python developer", 
            tags=["profession", "python"]
        )
        
        print("Assistant: Nice to meet you, Alice! I'll remember that you're a Python developer.")
        
        # User shares preferences
        print("\nUser: I prefer using VS Code and I like minimal, clean code.")
        await assistant.remember_preference(
            "Prefers VS Code as editor", 
            tags=["editor", "tools"]
        )
        await assistant.remember_preference(
            "Likes minimal, clean code style", 
            tags=["coding-style", "preferences"]
        )
        
        print("Assistant: Got it! I've noted your preferences for VS Code and clean coding style.")
        
        # Discuss a project
        print("\nUser: I'm working on a web API project using FastAPI.")
        await assistant.remember_conversation(
            "Web API Project",
            "User is building a web API using FastAPI framework",
            tags=["project", "fastapi", "web-api"]
        )
        
        print("Assistant: Interesting! FastAPI is a great choice for web APIs. I'll remember this project.")
        
        # Add some notes
        await assistant.add_note(
            "Alice might need help with FastAPI authentication later",
            tags=["todo", "fastapi", "authentication"]
        )
        
        # Simulate a later conversation
        print("\n" + "-" * 40)
        print("--- Later conversation ---")
        print("-" * 40)
        
        # Assistant recalls user info
        print(f"\nAssistant: {assistant.greet_user()}")
        
        print("\nUser: Can you remind me what we discussed about my project?")
        
        # Recall project information
        project_memories = await assistant.recall_about("FastAPI")
        if project_memories:
            print("Assistant: I remember we discussed your web API project:")
            for memory in project_memories:
                print(f"  - {memory.content}")
        
        # Show user preferences when giving advice
        print("\nUser: What editor should I use for this project?")
        
        preferences = await assistant.get_user_preferences()
        editor_prefs = [p for p in preferences if "editor" in p.tags]
        
        if editor_prefs:
            print(f"Assistant: Based on your preferences, I'd recommend {editor_prefs[0].content.lower()}.")
        
        # Check pending notes
        print("\nAssistant: By the way, I have a note that you might need help with FastAPI authentication. Is that still relevant?")
        
        print("\nUser: Yes, actually I do need help with that!")
        
        # Update the note
        notes = await assistant.get_pending_notes()
        auth_notes = [n for n in notes if "authentication" in n.tags]
        if auth_notes:
            await assistant.memory.update_memory(
                auth_notes[0].id,
                content="Alice needs help with FastAPI authentication - ACTIVE",
                tags=["active", "fastapi", "authentication", "help-needed"]
            )
        
        print("Assistant: Perfect! I've updated my notes. Let's work on FastAPI authentication together.")
        
        # Show memory statistics
        print("\n" + "=" * 40)
        print("Memory Statistics")
        print("=" * 40)
        
        stats = await assistant.memory.get_memory_statistics()
        print(f"📊 Total memories stored: {stats['total_count']}")
        print(f"   User facts: {stats['fact_count']}")
        print(f"   Preferences: {stats['preference_count']}")
        print(f"   Conversations: {stats['conversation_count']}")
        print(f"   Notes: {stats['note_count']}")
        
        # Show all tags
        tags = await assistant.memory.get_all_tags()
        print(f"🏷️  Memory tags: {', '.join(sorted(tags))}")
        
        print("\n✨ AI Assistant conversation simulation completed!")
        
    finally:
        await assistant.close()

async def demonstrate_context_awareness():
    """Demonstrate how the assistant maintains context awareness."""
    print("\n" + "=" * 60)
    print("🎯 Context Awareness Demonstration")
    print("=" * 60)
    
    assistant = AIAssistant()
    await assistant.initialize()
    
    try:
        # Build up context over multiple interactions
        contexts = [
            ("User is learning machine learning", ["learning", "ml", "education"]),
            ("User prefers hands-on examples over theory", ["learning-style", "practical"]),
            ("User has experience with Python but new to ML", ["experience", "python", "ml"]),
            ("User is interested in computer vision applications", ["ml", "computer-vision", "interest"]),
        ]
        
        print("\n1. Building Context...")
        for content, tags in contexts:
            await assistant.memory.store_memory(
                content=content,
                memory_type=MemoryType.FACT,
                tags=tags,
                context="User context"
            )
            print(f"   📝 {content}")
        
        # Demonstrate context-aware responses
        print("\n2. Context-Aware Responses...")
        
        # When user asks about ML resources
        print("\nUser: Can you recommend some machine learning resources?")
        
        # Assistant recalls learning style and experience
        learning_style = await assistant.memory.get_memories_by_tags(["learning-style"])
        experience = await assistant.memory.get_memories_by_tags(["experience"])
        interests = await assistant.memory.get_memories_by_tags(["interest"])
        
        print("Assistant: Based on what I know about you:")
        if learning_style:
            print(f"  - You prefer {learning_style[0].content.lower()}")
        if experience:
            print(f"  - You have {experience[0].content.lower()}")
        if interests:
            print(f"  - You're interested in {interests[0].content.lower()}")
        
        print("  I'd recommend practical, hands-on computer vision tutorials using Python!")
        
        # Record this recommendation
        await assistant.remember_conversation(
            "ML Resources",
            "Recommended practical computer vision tutorials based on user's learning style and interests",
            tags=["recommendation", "ml", "computer-vision"]
        )
        
        print("\n3. Context Evolution...")
        
        # User provides feedback
        print("\nUser: That's perfect! I tried the tutorials and really enjoyed them.")
        
        # Update context based on feedback
        await assistant.memory.store_memory(
            content="User enjoyed the recommended computer vision tutorials",
            memory_type=MemoryType.FACT,
            tags=["feedback", "positive", "computer-vision", "tutorials"],
            context="User feedback"
        )
        
        # Assistant can now make even better recommendations
        print("Assistant: Great! Since you enjoyed those, I can recommend more advanced computer vision projects next time.")
        
        print("\n✨ Context awareness demonstration completed!")
        
    finally:
        await assistant.close()

if __name__ == "__main__":
    asyncio.run(simulate_ai_assistant_conversation())
    asyncio.run(demonstrate_context_awareness())