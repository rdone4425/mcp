# AI Context Memory 一键安装指南

## 🚀 快速开始

### 使用 uvx 从Git直接运行（推荐）

```bash
# 直接从GitHub运行MCP服务器
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory mcp

# 启动HTTP API服务器
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory http

# 启动交互式界面
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory interactive

# 创建MCP配置文件
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory config
```

### 使用 uvx 从PyPI运行

```bash
# 启动MCP服务器
uvx ai-context-memory mcp

# 启动HTTP API服务器
uvx ai-context-memory http

# 启动交互式界面
uvx ai-context-memory interactive

# 创建MCP配置文件
uvx ai-context-memory config
```

### 使用 uv 从GitHub安装

```bash
# 从GitHub安装到全局环境
uv tool install git+https://github.com/rdone4425/mcp.git

# 运行
ai-context-memory mcp
```

### 使用 pip 从GitHub安装

```bash
# 从GitHub安装
pip install git+https://github.com/rdone4425/mcp.git

# 运行
ai-context-memory mcp
```

### 使用 pip 安装

```bash
# 安装
pip install ai-context-memory

# 运行
ai-context-memory mcp
```

## 📋 可用命令

### MCP服务器模式
```bash
# 基本启动
uvx ai-context-memory mcp

# 自定义数据库路径
uvx ai-context-memory mcp --db-path ./my_memories.db

# 启用调试日志
uvx ai-context-memory mcp --log-level DEBUG
```

### HTTP API服务器模式
```bash
# 默认启动 (http://127.0.0.1:8000)
uvx ai-context-memory http

# 自定义地址和端口
uvx ai-context-memory http --host 0.0.0.0 --port 9000

# API文档地址: http://127.0.0.1:8000/docs
```

### 交互式命令行模式
```bash
# 启动交互式界面
uvx ai-context-memory interactive
```

### 配置文件生成
```bash
# 生成MCP配置文件到 ~/.kiro/settings/mcp.json
uvx ai-context-memory config
```

## 🔧 VSCode集成

### 1. 生成MCP配置
```bash
uvx ai-context-memory config
```

### 2. 在VSCode中使用
配置文件会自动创建到 `~/.kiro/settings/mcp.json`，Kiro会自动识别并连接。

### 3. 手动配置MCP
如果需要手动配置，在你的MCP配置文件中添加：

#### 从Git仓库运行（推荐）
```json
{
  "mcpServers": {
    "ai-context-memory": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/your-org/ai-context-memory", "ai-context-memory-mcp"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### 从PyPI运行
```json
{
  "mcpServers": {
    "ai-context-memory": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/rdone4425/mcp.git", "ai-context-memory", "mcp"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## 🌐 HTTP API使用

启动HTTP服务器后，可以通过REST API访问：

```bash
# 存储记忆
curl -X POST "http://localhost:8000/memories" \
     -H "Content-Type: application/json" \
     -d '{"content": "Python是编程语言", "memory_type": "fact", "tags": ["python"]}'

# 搜索记忆
curl "http://localhost:8000/memories/search?q=Python"

# 获取统计
curl "http://localhost:8000/stats"
```

访问 http://localhost:8000 查看完整的Web界面和API文档。

## 🛠️ 开发模式

### 从源码运行
```bash
# 克隆仓库
git clone https://github.com/rdone4425/mcp.git
cd mcp

# 使用uv安装依赖
uv sync

# 开发模式安装
uv pip install -e .

# 运行
ai-context-memory mcp
```

### 构建和发布
```bash
# 构建包
uv build

# 发布到PyPI
uv publish
```

## 📚 更多信息

- 📖 [完整文档](README.md)
- 🐛 [问题反馈](https://github.com/rdone4425/mcp/issues)
- 💬 [讨论区](https://github.com/rdone4425/mcp/discussions)

## 📁 数据存储

### 默认数据库位置
- **默认路径**: `~/.ai-context-memory/memories.db`
- **HTTP API**: `~/.ai-context-memory/api_memories.db`
- **交互式**: `~/.ai-context-memory/local_memories.db`

### 自定义数据库路径
```bash
# 使用自定义路径
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory mcp --db-path /path/to/your/database.db

# 使用相对路径
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory mcp --db-path ./project_memories.db
```

## 🎯 常见问题

### Q: 数据存储在哪里？
A: 默认存储在用户主目录的 `~/.ai-context-memory/` 文件夹中

### Q: 如何更改数据库位置？
A: 使用 `--db-path` 参数指定自定义路径

### Q: 如何备份数据？
A: 直接复制 `~/.ai-context-memory/` 文件夹或指定的数据库文件

### Q: 多个项目如何使用不同的数据库？
A: 为每个项目指定不同的 `--db-path` 参数

### Q: 如何启用HTTPS？
A: HTTP服务器目前只支持HTTP，建议在反向代理后面使用HTTPS

### Q: 支持哪些Python版本？
A: 支持Python 3.8及以上版本