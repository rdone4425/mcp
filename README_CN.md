# AI上下文记忆 MCP服务器

一个强大的模型上下文协议服务器，用于AI上下文记忆管理，具备SQLite存储、加密和隐私保护功能。

## 🚀 概述

AI上下文记忆使AI助手能够跨对话存储、检索和管理上下文信息。它提供持久化记忆能力，具备企业级安全和隐私保护功能。

### 核心特性

- **🧠 智能记忆管理**：存储事实、偏好、对话和笔记
- **🔍 高级搜索**：关键词搜索、标签过滤、日期范围和复杂查询
- **🔐 安全与隐私**：可选加密、PII脱敏和数据保留策略
- **🏷️ 标签组织**：灵活的标签系统用于记忆分类
- **📊 分析统计**：全面的记忆统计和使用洞察
- **🔄 MCP协议**：完全符合模型上下文协议
- **💾 本地存储**：SQLite数据库保护隐私和离线操作

## 📦 安装

### 使用uvx（推荐）

```bash
# 使用uvx安装并运行
uvx ai-context-memory

# 或安装特定版本
uvx ai-context-memory@0.1.0
```

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/your-org/ai-context-memory.git
cd ai-context-memory

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

### 使用pip

```bash
# 从PyPI安装（发布后）
pip install ai-context-memory
```

## 🚀 快速开始

### 基本使用

```bash
# 使用默认设置启动MCP服务器
python -m src.server

# 使用自定义数据库路径
python -m src.server --db-path ./my_memories.db

# 启用调试日志
python -m src.server --log-level DEBUG

# 显示服务器信息
python -m src.server --info
```

### MCP配置

添加到你的MCP客户端配置：

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

## 🛠️ 可用工具

### 核心记忆操作

#### `store_memory`
存储新记忆，包含内容、类型、标签和上下文。

```json
{
  "content": "Python是一种高级编程语言",
  "memory_type": "fact",
  "tags": ["python", "编程", "语言"],
  "context": "学习资料"
}
```

#### `retrieve_memories`
通过内容查询搜索记忆。

```json
{
  "query": "Python编程",
  "memory_type": "fact",
  "limit": 10
}
```

#### `get_memory`
通过ID获取特定记忆。

```json
{
  "memory_id": 123
}
```

### 高级搜索

#### `search_memories`
使用多个过滤器进行高级搜索。

```json
{
  "keywords": ["python", "web"],
  "memory_type": "fact",
  "tags": ["编程"],
  "days_back": 30,
  "limit": 20
}
```

### 记忆管理

#### `list_memories`
列出记忆，支持分页和过滤。

```json
{
  "memory_type": "preference",
  "limit": 50,
  "offset": 0
}
```

#### `update_memory`
更新现有记忆的内容、上下文或标签。

```json
{
  "memory_id": 123,
  "content": "更新的内容",
  "tags": ["新", "标签"]
}
```

#### `delete_memory`
删除特定记忆。

```json
{
  "memory_id": 123
}
```

#### `clear_memories`
清除记忆（需要确认）。

```json
{
  "memory_type": "note",
  "confirm": true
}
```

### 分析与管理

#### `get_memory_statistics`
获取全面的记忆统计信息。

```json
{}
```

#### `get_tags`
获取所有可用标签。

```json
{}
```

## 🔐 安全与隐私

### 加密

为敏感数据启用加密：

```bash
# 通过环境变量设置加密密码
export MEMORY_ENCRYPTION_PASSWORD="your-secure-password"
python -m src.server
```

### 隐私功能

- **PII脱敏**：自动屏蔽邮箱、电话号码、信用卡、社会保险号
- **阻止关键词**：配置不应存储的关键词
- **数据保留**：设置旧记忆的自动清理
- **内容限制**：可配置的内容和上下文长度限制

### 配置示例

```python
from src.security import PrivacyManager

privacy = PrivacyManager()
privacy.set_blocked_keywords(['密码', '秘密', '机密'])
privacy.set_retention_period(90)  # 90天
```

## 📊 记忆类型

| 类型 | 描述 | 使用场景 |
|------|-------------|----------|
| `fact` | 事实信息 | 知识、定义、事实 |
| `preference` | 用户偏好 | 设置、选择、喜好 |
| `conversation` | 对话历史 | 重要讨论、决定 |
| `note` | 一般笔记 | 提醒、待办、观察 |

## 🏷️ 标签系统

使用灵活标签组织记忆：

```bash
# 存储带标签的记忆
{
  "content": "用户偏好深色模式",
  "memory_type": "preference",
  "tags": ["界面", "主题", "用户偏好"]
}

# 按标签搜索
{
  "tags": ["界面", "主题"],
  "match_all_tags": true
}
```

## 📈 使用示例

### AI助手记忆

```python
# 存储用户项目信息
await store_memory(
    content="用户正在构建Flask网络应用",
    memory_type="fact",
    tags=["项目", "flask", "web"],
    context="当前项目"
)

# 存储用户偏好
await store_memory(
    content="用户偏好最少依赖",
    memory_type="preference",
    tags=["架构", "依赖"],
    context="开发偏好"
)

# 稍后检索相关上下文
memories = await retrieve_memories("Flask项目")
```

### 学习助手

```python
# 跟踪学习进度
await store_memory(
    content="学生在列表推导式方面有困难",
    memory_type="note",
    tags=["python", "困难", "推导式"],
    context="学习挑战"
)

# 存储学习偏好
await store_memory(
    content="学生通过视觉示例学习更好",
    memory_type="preference",
    tags=["学习风格", "视觉"],
    context="教学方法"
)
```

### 个人助理

```python
# 存储日程信息
await store_memory(
    content="每周二上午10点团队会议",
    memory_type="fact",
    tags=["日程", "会议", "定期"],
    context="日历"
)

# 存储提醒
await store_memory(
    content="月底前准备季度报告",
    memory_type="note",
    tags=["提醒", "截止日期", "报告"],
    context="重要任务"
)
```

## 🔧 配置选项

### 命令行参数

```bash
python -m src.server \
  --db-path ./memories.db \
  --log-level DEBUG \
  --log-file server.log \
  --server-name my-memory-server \
  --server-version 1.0.0
```

### 环境变量

```bash
# 数据库配置
export MEMORY_DB_PATH="./data/memories.db"
export MEMORY_LOG_LEVEL="INFO"

# 安全配置
export MEMORY_ENCRYPTION_PASSWORD="secure-password"
export MEMORY_BLOCKED_KEYWORDS="密码,秘密,机密"
export MEMORY_RETENTION_DAYS="90"
```

## 🧪 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试类别
pytest tests/test_memory_manager.py
pytest tests/test_security.py
pytest tests/test_end_to_end.py

# 运行覆盖率测试
pytest --cov=src --cov-report=html
```

### 代码质量

```bash
# 格式化代码
black src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/
```

### 性能测试

```bash
# 运行性能测试
pytest tests/test_end_to_end.py::TestEndToEndWorkflows::test_performance_with_large_dataset -v -s
```

## 📚 API文档

### 记忆对象结构

```json
{
  "id": 123,
  "content": "记忆内容",
  "memory_type": "fact",
  "context": "附加上下文",
  "tags": ["标签1", "标签2"],
  "created_at": "2023-01-01T12:00:00",
  "updated_at": "2023-01-02T12:00:00",
  "access_count": 5,
  "last_accessed": "2023-01-03T12:00:00"
}
```

### 错误处理

服务器为常见问题提供详细的错误消息：

- 无效的记忆类型
- 空内容
- 阻止的关键词（启用隐私时）
- 内容过长
- 记忆未找到
- 数据库错误

## 🔍 故障排除

### 常见问题

**数据库锁定错误**
```bash
# 停止任何运行的实例并重启
pkill -f "ai-context-memory"
python -m src.server
```

**权限被拒绝**
```bash
# 检查数据库文件权限
ls -la memories.db
chmod 644 memories.db
```

**记忆未找到**
- 验证记忆ID是否存在
- 检查记忆是否已被删除
- 确保数据库正确初始化

### 调试模式

```bash
# 启用调试日志
python -m src.server --log-level DEBUG --log-file debug.log

# 查看日志
tail -f debug.log
```

## 🤝 贡献

1. Fork仓库
2. 创建功能分支
3. 进行更改
4. 添加测试
5. 运行测试套件
6. 提交拉取请求

### 开发设置

```bash
git clone https://github.com/your-org/ai-context-memory.git
cd ai-context-memory
pip install -e .[dev]
pre-commit install
```

## 📄 许可证

MIT许可证 - 详见[LICENSE](LICENSE)文件。

## 🙏 致谢

- 基于[模型上下文协议](https://modelcontextprotocol.io/)构建
- 使用[SQLite](https://sqlite.org/)进行本地存储
- 加密由[cryptography](https://cryptography.io/)提供支持

## 📞 支持

- 📖 [文档](https://github.com/your-org/ai-context-memory/wiki)
- 🐛 [问题跟踪](https://github.com/your-org/ai-context-memory/issues)
- 💬 [讨论](https://github.com/your-org/ai-context-memory/discussions)