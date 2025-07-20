# Memory 项目结构

## 📁 目录结构

```
memory/
├── src/ai_context_memory/    # 核心代码
├── README.md                 # 项目说明
├── INSTALL.md               # 安装指南
├── pyproject.toml           # 项目配置
└── mcp_server.py           # MCP服务器入口
```

## 🚀 一键命令

```bash
# 最简单的使用方式
uvx --from git+https://github.com/rdone4425/mcp.git memory mcp
```

## 🔧 开发

```bash
git clone https://github.com/rdone4425/mcp.git
cd mcp
uv sync
memory mcp
```

就这么简单！