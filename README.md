# AI Context Memory MCP Server

A powerful Model Context Protocol server for AI context memory management with SQLite storage, encryption, and privacy features.

## 🚀 Overview

AI Context Memory enables AI assistants to store, retrieve, and manage contextual information across conversations. It provides persistent memory capabilities with enterprise-grade security and privacy features.

### Key Features

- **🧠 Intelligent Memory Management**: Store facts, preferences, conversations, and notes
- **🔍 Advanced Search**: Keyword search, tag filtering, date ranges, and complex queries
- **🔐 Security & Privacy**: Optional encryption, PII sanitization, and data retention policies
- **🏷️ Tag Organization**: Flexible tagging system for memory categorization
- **📊 Analytics**: Comprehensive memory statistics and usage insights
- **🔄 MCP Protocol**: Full Model Context Protocol compliance
- **💾 Local Storage**: SQLite database for privacy and offline operation

## 📦 Installation

### Using uvx (Recommended)

```bash
# Install and run with uvx
uvx ai-context-memory

# Or install specific version
uvx ai-context-memory@0.1.0
```

### From Source

```bash
# Clone the repository
git clone https://github.com/your-org/ai-context-memory.git
cd ai-context-memory

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Using pip

```bash
# Install from PyPI (when published)
pip install ai-context-memory
```

## 🚀 Quick Start

### Basic Usage

```bash
# Start the MCP server with default settings
python -m src.server

# Use custom database path
python -m src.server --db-path ./my_memories.db

# Enable debug logging
python -m src.server --log-level DEBUG

# Show server information
python -m src.server --info
```

### MCP Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "ai-context-memory": {
      "command": "uvx",
      "args": ["ai-context-memory"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## 🛠️ Available Tools

### Core Memory Operations

#### `store_memory`
Store a new memory with content, type, tags, and context.

```json
{
  "content": "Python is a high-level programming language",
  "memory_type": "fact",
  "tags": ["python", "programming", "language"],
  "context": "Learning materials"
}
```

#### `retrieve_memories`
Search memories by content query.

```json
{
  "query": "Python programming",
  "memory_type": "fact",
  "limit": 10
}
```

#### `get_memory`
Get a specific memory by ID.

```json
{
  "memory_id": 123
}
```

### Advanced Search

#### `search_memories`
Advanced search with multiple filters.

```json
{
  "keywords": ["python", "web"],
  "memory_type": "fact",
  "tags": ["programming"],
  "days_back": 30,
  "limit": 20
}
```

### Memory Management

#### `list_memories`
List memories with pagination and filtering.

```json
{
  "memory_type": "preference",
  "limit": 50,
  "offset": 0
}
```

#### `update_memory`
Update existing memory content, context, or tags.

```json
{
  "memory_id": 123,
  "content": "Updated content",
  "tags": ["new", "tags"]
}
```

#### `delete_memory`
Delete a specific memory.

```json
{
  "memory_id": 123
}
```

#### `clear_memories`
Clear memories (requires confirmation).

```json
{
  "memory_type": "note",
  "confirm": true
}
```

### Analytics & Management

#### `get_memory_statistics`
Get comprehensive memory statistics.

```json
{}
```

#### `get_tags`
Get all available tags.

```json
{}
```

## 🔐 Security & Privacy

### Encryption

Enable encryption for sensitive data:

```bash
# Set encryption password via environment variable
export MEMORY_ENCRYPTION_PASSWORD="your-secure-password"
python -m src.server
```

### Privacy Features

- **PII Sanitization**: Automatically masks emails, phone numbers, credit cards, SSNs
- **Blocked Keywords**: Configure keywords that should not be stored
- **Data Retention**: Set automatic cleanup of old memories
- **Content Limits**: Configurable length limits for content and context

### Configuration Example

```python
from src.security import PrivacyManager

privacy = PrivacyManager()
privacy.set_blocked_keywords(['password', 'secret', 'confidential'])
privacy.set_retention_period(90)  # 90 days
```

## 📊 Memory Types

| Type | Description | Use Case |
|------|-------------|----------|
| `fact` | Factual information | Knowledge, definitions, facts |
| `preference` | User preferences | Settings, choices, likes/dislikes |
| `conversation` | Conversation history | Important discussions, decisions |
| `note` | General notes | Reminders, todos, observations |

## 🏷️ Tagging System

Organize memories with flexible tags:

```bash
# Store memory with tags
{
  "content": "User prefers dark mode",
  "memory_type": "preference",
  "tags": ["ui", "theme", "user-preference"]
}

# Search by tags
{
  "tags": ["ui", "theme"],
  "match_all_tags": true
}
```

## 📈 Usage Examples

### AI Assistant Memory

```python
# Store user project information
await store_memory(
    content="User is building a Flask web application",
    memory_type="fact",
    tags=["project", "flask", "web"],
    context="Current project"
)

# Store user preferences
await store_memory(
    content="User prefers minimal dependencies",
    memory_type="preference",
    tags=["architecture", "dependencies"],
    context="Development preferences"
)

# Later, retrieve relevant context
memories = await retrieve_memories("Flask project")
```

### Learning Assistant

```python
# Track learning progress
await store_memory(
    content="Student struggles with list comprehensions",
    memory_type="note",
    tags=["python", "difficulty", "comprehensions"],
    context="Learning challenges"
)

# Store learning preferences
await store_memory(
    content="Student learns better with visual examples",
    memory_type="preference",
    tags=["learning-style", "visual"],
    context="Teaching approach"
)
```

### Personal Assistant

```python
# Store schedule information
await store_memory(
    content="Team meeting every Tuesday at 10 AM",
    memory_type="fact",
    tags=["schedule", "meeting", "recurring"],
    context="Calendar"
)

# Store reminders
await store_memory(
    content="Prepare quarterly report by month end",
    memory_type="note",
    tags=["reminder", "deadline", "report"],
    context="Important tasks"
)
```

## 🔧 Configuration Options

### Command Line Arguments

```bash
python -m src.server \
  --db-path ./memories.db \
  --log-level DEBUG \
  --log-file server.log \
  --server-name my-memory-server \
  --server-version 1.0.0
```

### Environment Variables

```bash
# Database configuration
export MEMORY_DB_PATH="./data/memories.db"
export MEMORY_LOG_LEVEL="INFO"

# Security configuration
export MEMORY_ENCRYPTION_PASSWORD="secure-password"
export MEMORY_BLOCKED_KEYWORDS="password,secret,confidential"
export MEMORY_RETENTION_DAYS="90"
```

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_memory_manager.py
pytest tests/test_security.py
pytest tests/test_end_to_end.py

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Performance Testing

```bash
# Run performance tests
pytest tests/test_end_to_end.py::TestEndToEndWorkflows::test_performance_with_large_dataset -v -s
```

## 📚 API Documentation

### Memory Object Structure

```json
{
  "id": 123,
  "content": "Memory content",
  "memory_type": "fact",
  "context": "Additional context",
  "tags": ["tag1", "tag2"],
  "created_at": "2023-01-01T12:00:00",
  "updated_at": "2023-01-02T12:00:00",
  "access_count": 5,
  "last_accessed": "2023-01-03T12:00:00"
}
```

### Error Handling

The server provides detailed error messages for common issues:

- Invalid memory types
- Empty content
- Blocked keywords (when privacy is enabled)
- Content too long
- Memory not found
- Database errors

## 🔍 Troubleshooting

### Common Issues

**Database locked error**
```bash
# Stop any running instances and restart
pkill -f "ai-context-memory"
python -m src.server
```

**Permission denied**
```bash
# Check database file permissions
ls -la memories.db
chmod 644 memories.db
```

**Memory not found**
- Verify memory ID exists
- Check if memory was deleted
- Ensure database is properly initialized

### Debug Mode

```bash
# Enable debug logging
python -m src.server --log-level DEBUG --log-file debug.log

# Check logs
tail -f debug.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

### Development Setup

```bash
git clone https://github.com/your-org/ai-context-memory.git
cd ai-context-memory
pip install -e .[dev]
pre-commit install
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses [SQLite](https://sqlite.org/) for local storage
- Encryption powered by [cryptography](https://cryptography.io/)

## 📞 Support

- 📖 [Documentation](https://github.com/your-org/ai-context-memory/wiki)
- 🐛 [Issue Tracker](https://github.com/your-org/ai-context-memory/issues)
- 💬 [Discussions](https://github.com/your-org/ai-context-memory/discussions)