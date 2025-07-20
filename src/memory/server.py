#!/usr/bin/env python3
"""
AI Context Memory MCP Server 主入口
支持直接从uvx运行
"""

import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path

def setup_paths():
    """设置Python路径"""
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent
    
    # 添加src目录到路径
    src_dir = project_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    return project_root

async def run_mcp_server():
    """运行MCP服务器"""
    try:
        # 尝试导入MCP相关模块
        from mcp.server import Server
        from mcp.server.models import InitializationOptions
        import mcp.server.stdio
        import mcp.types as types
        
        from .memory_manager import MemoryManager
        from .tools import register_tools
        
        # 创建服务器
        server = Server("ai-context-memory")
        
        # 初始化记忆管理器
        memory_manager = MemoryManager(":memory:")  # 使用内存数据库作为默认
        await memory_manager.initialize()
        
        # 注册工具
        register_tools(server, memory_manager)
        
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
        print(f"❌ MCP依赖未安装: {e}")
        print("请安装MCP依赖: pip install mcp")
        return False
    except Exception as e:
        print(f"❌ MCP服务器启动失败: {e}")
        return False
    
    return True

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description="AI Context Memory MCP Server")
    parser.add_argument("--db-path", default=":memory:", help="数据库路径")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 设置路径
    setup_paths()
    
    print("🚀 AI Context Memory MCP Server")
    print("=" * 40)
    
    try:
        asyncio.run(run_mcp_server())
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()