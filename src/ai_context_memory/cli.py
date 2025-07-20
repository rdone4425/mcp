#!/usr/bin/env python3
"""
AI Context Memory CLI - 命令行界面
支持一键启动MCP服务器和HTTP API服务器
"""

import sys
import os
import asyncio
import argparse
import subprocess
from pathlib import Path
from typing import Optional

def print_banner():
    """打印启动横幅"""
    print("""
🧠 AI Context Memory
===================
AI上下文记忆管理服务

支持模式:
  • MCP Server  - 模型上下文协议服务器
  • HTTP API    - REST API服务器  
  • Interactive - 交互式命令行
""")

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        sys.exit(1)

def get_project_root():
    """获取项目根目录"""
    # 尝试从包安装位置获取
    try:
        import ai_context_memory
        package_dir = Path(ai_context_memory.__file__).parent.parent.parent
        if (package_dir / "src").exists():
            return package_dir
    except ImportError:
        pass
    
    # 尝试从当前文件位置获取
    current_file = Path(__file__).resolve()
    for parent in current_file.parents:
        if (parent / "src" / "ai_context_memory").exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent
    
    # 使用当前工作目录
    return Path.cwd()

def get_default_db_path(db_name: str = "memories.db") -> str:
    """获取默认数据库路径"""
    # 使用用户主目录下的.ai-context-memory文件夹
    data_dir = Path.home() / ".ai-context-memory"
    data_dir.mkdir(exist_ok=True)
    return str(data_dir / db_name)

def setup_python_path():
    """设置Python路径"""
    project_root = get_project_root()
    src_dir = project_root / "src"
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    return project_root

async def start_mcp_server(args):
    """启动MCP服务器"""
    print("🚀 启动MCP服务器...")
    
    project_root = setup_python_path()
    server_script = project_root / "src" / "server.py"
    
    if not server_script.exists():
        # 尝试直接导入
        try:
            from ai_context_memory.server import main as server_main
            await server_main()
            return
        except ImportError:
            print(f"❌ 找不到服务器脚本: {server_script}")
            return
    
    # 构建命令参数
    cmd = [sys.executable, str(server_script)]
    
    if args.db_path:
        cmd.extend(["--db-path", args.db_path])
    if args.log_level:
        cmd.extend(["--log-level", args.log_level])
    if args.log_file:
        cmd.extend(["--log-file", args.log_file])
    
    db_path = args.db_path or get_default_db_path("memories.db")
    print(f"📍 数据库: {db_path}")
    print(f"📊 日志级别: {args.log_level or 'INFO'}")
    print("\n按 Ctrl+C 停止服务器\n")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 MCP服务器已停止")

async def start_http_server(args):
    """启动HTTP API服务器"""
    print("🌐 启动HTTP API服务器...")
    
    project_root = setup_python_path()
    
    try:
        # 尝试导入HTTP服务器模块
        sys.path.insert(0, str(project_root))
        
        # 动态导入并运行HTTP服务器
        import importlib.util
        
        http_server_file = project_root / "run_http_server.py"
        if http_server_file.exists():
            spec = importlib.util.spec_from_file_location("http_server", http_server_file)
            http_server = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(http_server)
            
            # 创建服务器实例
            server = http_server.MemoryHTTPServer(
                host=args.host,
                port=args.port,
                db_path=args.db_path or get_default_db_path("api_memories.db")
            )
            
            await server.start_server()
        else:
            print(f"❌ 找不到HTTP服务器脚本: {http_server_file}")
            
    except Exception as e:
        print(f"❌ 启动HTTP服务器失败: {e}")

async def start_interactive(args):
    """启动交互式界面"""
    print("💬 启动交互式界面...")
    
    project_root = setup_python_path()
    
    try:
        # 导入交互式服务
        sys.path.insert(0, str(project_root))
        
        import importlib.util
        service_file = project_root / "run_service.py"
        
        if service_file.exists():
            spec = importlib.util.spec_from_file_location("service", service_file)
            service = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(service)
            
            await service.main()
        else:
            print(f"❌ 找不到交互式服务脚本: {service_file}")
            
    except Exception as e:
        print(f"❌ 启动交互式界面失败: {e}")

def create_mcp_config(args):
    """创建MCP配置文件"""
    config = {
        "mcpServers": {
            "ai-context-memory": {
                "command": "uvx",
                "args": ["--from", "git+https://github.com/rdone4425/mcp.git", "ai-context-memory", "mcp"],
                "env": {
                    "LOG_LEVEL": args.log_level or "INFO"
                }
            }
        }
    }
    
    if args.db_path:
        config["mcpServers"]["ai-context-memory"]["env"]["MEMORY_DB_PATH"] = args.db_path
    
    import json
    config_path = Path.home() / ".kiro" / "settings" / "mcp.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 如果配置文件已存在，合并配置
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
            existing_config["mcpServers"].update(config["mcpServers"])
            config = existing_config
        except Exception as e:
            print(f"⚠️ 读取现有配置失败，将创建新配置: {e}")
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ MCP配置已创建: {config_path}")
    print("\n📋 配置内容:")
    print(json.dumps(config, indent=2, ensure_ascii=False))

def main():
    """主入口函数"""
    check_python_version()
    
    parser = argparse.ArgumentParser(
        description="AI Context Memory - AI上下文记忆管理服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动MCP服务器
  ai-context-memory mcp
  
  # 启动HTTP API服务器
  ai-context-memory http --port 8080
  
  # 启动交互式界面
  ai-context-memory interactive
  
  # 创建MCP配置文件
  ai-context-memory config
  
  # 使用uvx一键运行
  uvx ai-context-memory mcp
        """
    )
    
    # 添加全局参数
    parser.add_argument("--db-path", help="数据库文件路径")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="日志级别")
    parser.add_argument("--log-file", help="日志文件路径")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # MCP服务器命令
    mcp_parser = subparsers.add_parser("mcp", help="启动MCP服务器")
    mcp_parser.add_argument("--server-name", default="ai-context-memory", help="服务器名称")
    mcp_parser.add_argument("--server-version", default="1.0.0", help="服务器版本")
    
    # HTTP服务器命令
    http_parser = subparsers.add_parser("http", help="启动HTTP API服务器")
    http_parser.add_argument("--host", default="127.0.0.1", help="服务器地址")
    http_parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    
    # 交互式命令
    interactive_parser = subparsers.add_parser("interactive", help="启动交互式界面")
    
    # 配置命令
    config_parser = subparsers.add_parser("config", help="创建MCP配置文件")
    
    # 解析参数
    args = parser.parse_args()
    
    # 如果没有指定命令，显示帮助
    if not args.command:
        print_banner()
        parser.print_help()
        return
    
    # 执行对应命令
    try:
        if args.command == "mcp":
            asyncio.run(start_mcp_server(args))
        elif args.command == "http":
            asyncio.run(start_http_server(args))
        elif args.command == "interactive":
            asyncio.run(start_interactive(args))
        elif args.command == "config":
            create_mcp_config(args)
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()