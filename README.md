# Memory

AI记忆管理服务 - 让AI记住重要信息

## 🚀 一键使用

```bash
# MCP服务器（用于VSCode/Kiro）
uvx --from git+https://github.com/rdone4425/mcp.git memory mcp

# HTTP API服务器
uvx --from git+https://github.com/rdone4425/mcp.git memory http

# 交互式命令行
uvx --from git+https://github.com/rdone4425/mcp.git memory interactive
```

## 🔧 VSCode集成

```bash
# 自动配置
uvx --from git+https://github.com/rdone4425/mcp.git memory config
```

## 📚 功能

- 存储和检索AI对话记忆
- 支持标签分类
- 全文搜索
- 数据加密
- HTTP API接口

## 💾 数据存储

默认存储在 `~/.ai-context-memory/memories.db`

## 🛠️ 自定义

```bash
# 自定义数据库路径
uvx --from git+https://github.com/rdone4425/mcp.git memory mcp --db-path ./my_db.db

# 自定义端口
uvx --from git+https://github.com/rdone4425/mcp.git memory http --port 9000
```

就这么简单！