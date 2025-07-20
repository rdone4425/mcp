# Memory - 一键安装

AI记忆管理服务，让AI记住重要信息。

## 🚀 安装使用

```bash
# MCP服务器（用于VSCode/Kiro）
uvx --from git+https://github.com/rdone4425/mcp.git memory mcp

# HTTP API服务器
uvx --from git+https://github.com/rdone4425/mcp.git memory http

# 交互式命令行
uvx --from git+https://github.com/rdone4425/mcp.git memory interactive

# 生成VSCode配置
uvx --from git+https://github.com/rdone4425/mcp.git memory config
```

## 🔧 常用参数

```bash
# 自定义数据库路径
uvx --from git+https://github.com/rdone4425/mcp.git memory mcp --db-path ./my_db.db

# 自定义HTTP端口
uvx --from git+https://github.com/rdone4425/mcp.git memory http --port 9000

# 启用调试日志
uvx --from git+https://github.com/rdone4425/mcp.git memory mcp --log-level DEBUG
```

## 💾 数据存储

- **默认位置**: `~/.ai-context-memory/memories.db`
- **备份方法**: 复制整个 `~/.ai-context-memory/` 文件夹

## 🎯 VSCode集成

1. 运行配置命令：
```bash
uvx --from git+https://github.com/rdone4425/mcp.git memory config
```

2. 重启VSCode，即可在Kiro中使用记忆功能

## ❓ 常见问题

**Q: 需要安装什么？**
A: 只需要Python 3.8+和uvx，其他依赖会自动安装

**Q: 数据存储在哪里？**
A: 默认在 `~/.ai-context-memory/` 文件夹

**Q: 如何备份数据？**
A: 复制 `~/.ai-context-memory/` 文件夹即可

**Q: 支持多项目？**
A: 使用 `--db-path` 参数为不同项目指定不同数据库

就这么简单！