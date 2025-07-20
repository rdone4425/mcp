#!/usr/bin/env python3
"""
AI Context Memory MCP Server 独立入口
专门用于uvx直接运行MCP服务器
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

def setup_environment():
    """设置运行环境"""
    current_dir = Path(__file__).parent
    src_dir = current_dir / "src"
    
    # 添加路径
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

async def run_mcp_server():
    """运行MCP服务器"""
    print("🧠 AI Context Memory MCP Server")
    print("=" * 40)
    
    try:
        # 导入必要模块
        from mcp.server import Server
        from mcp.server.models import InitializationOptions
        import mcp.server.stdio
        import mcp.types as types
        
        # 导入项目模块
        import memory_manager
        import tools
        
        # 创建服务器
        server = Server("ai-context-memory")
        
        # 获取数据库路径
        db_path = os.environ.get("MEMORY_DB_PATH", "memories.db")
        
        # 初始化记忆管理器
        manager = memory_manager.MemoryManager(db_path)
        await manager.initialize()
        
        print(f"✅ 记忆管理器初始化完成，数据库: {db_path}")
        
        # 注册工具
        tools.register_tools(server, manager)
        
        print("✅ MCP工具注册完成")
        print("🚀 MCP服务器启动中...")
        print("\n按 Ctrl+C 停止服务器\n")
        
        # 运行服务器
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ai-context-memory",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={}
                    )
                )
            )
    
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        print("\n可能的解决方案:")
        print("1. 安装MCP依赖: pip install mcp")
        print("2. 检查项目文件是否完整")
        return False
    
    except Exception as e:
        print(f"❌ MCP服务器运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """主函数"""
    # 设置环境
    setup_environment()
    
    # 设置日志
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        asyncio.run(run_mcp_server())
    except KeyboardInterrupt:
        print("\n👋 MCP服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()