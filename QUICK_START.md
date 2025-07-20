# 🚀 AI Context Memory 快速开始

## 一键运行命令

### 方式1：使用完整CLI（推荐）
```bash
# MCP服务器
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory mcp

# HTTP API服务器
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory http

# 交互式界面
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory interactive
```

### 方式2：直接运行MCP服务器
```bash
# 仅MCP服务器（最简单）
uvx --from git+https://github.com/rdone4425/mcp.git mcp_server
```

## VSCode/Kiro集成

### 自动配置
```bash
# 生成MCP配置文件
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory config
```

### 手动配置
在 `~/.kiro/settings/mcp.json` 中添加：

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

## 测试命令

```bash
# 测试MCP服务器是否正常
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory mcp --help

# 测试HTTP API
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory http --port 8080
# 然后访问 http://localhost:8080
```

## 常用参数

```bash
# 自定义数据库路径
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory mcp --db-path ./my_memories.db

# 启用调试日志
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory mcp --log-level DEBUG

# HTTP服务器自定义端口
uvx --from git+https://github.com/rdone4425/mcp.git ai-context-memory http --port 9000
```

## 数据存储

- **默认位置**: `~/.ai-context-memory/memories.db`
- **备份方法**: 复制整个 `~/.ai-context-memory/` 文件夹

## 故障排除

如果遇到问题，请检查：

1. **Python版本**: 需要Python 3.8+
2. **网络连接**: 确保能访问GitHub
3. **权限问题**: 确保有写入主目录的权限

```bash
# 检查Python版本
python --version

# 检查uvx是否安装
uvx --version

# 如果uvx未安装
pip install uv
```