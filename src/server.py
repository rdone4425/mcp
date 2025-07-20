"""
MCP Server main entry point for AI Context Memory.
"""

import asyncio
import logging
import os
import sys
import argparse
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from .memory_manager import MemoryManager
from .tools import register_tools

# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)

class AIContextMemoryServer:
    """Main MCP server class for AI context memory."""
    
    def __init__(self, 
                 db_path: str = "memories.db",
                 server_name: str = "ai-context-memory",
                 server_version: str = "0.1.0"):
        """Initialize the MCP server.
        
        Args:
            db_path: Path to the SQLite database file
            server_name: Name of the MCP server
            server_version: Version of the MCP server
        """
        self.db_path = db_path
        self.server_name = server_name
        self.server_version = server_version
        
        # Initialize MCP server
        self.server = Server(server_name)
        self.memory_manager = None
        self._initialized = False
        
        logger.info(f"Initializing {server_name} v{server_version}")
        logger.info(f"Database path: {db_path}")
        
    async def initialize(self):
        """Initialize the server and register tools."""
        if self._initialized:
            logger.warning("Server already initialized")
            return
            
        try:
            logger.info("Initializing memory manager...")
            self.memory_manager = MemoryManager(self.db_path)
            await self.memory_manager.initialize()
            
            logger.info("Registering MCP tools...")
            register_tools(self.server, self.memory_manager)
            
            self._initialized = True
            logger.info("Server initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise
            
    async def cleanup(self):
        """Cleanup server resources."""
        try:
            if self.memory_manager:
                logger.info("Closing memory manager...")
                await self.memory_manager.close()
                
            logger.info("Server cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information."""
        info = {
            "name": self.server_name,
            "version": self.server_version,
            "database_path": self.db_path,
            "initialized": self._initialized
        }
        
        if self.memory_manager and self._initialized:
            try:
                stats = await self.memory_manager.get_memory_statistics()
                info["memory_statistics"] = stats
            except Exception as e:
                logger.warning(f"Could not get memory statistics: {e}")
                info["memory_statistics"] = {"error": str(e)}
        
        return info
        
    async def run(self):
        """Run the MCP server."""
        try:
            # Initialize server
            await self.initialize()
            
            # Get server capabilities
            capabilities = self.server.get_capabilities(
                notification_options=None,
                experimental_capabilities=None,
            )
            
            logger.info("Starting MCP server...")
            logger.info(f"Server capabilities: {capabilities}")
            
            # Run server with stdio transport
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                initialization_options = InitializationOptions(
                    server_name=self.server_name,
                    server_version=self.server_version,
                    capabilities=capabilities,
                )
                
                logger.info("MCP server is running and ready to accept connections")
                
                try:
                    await self.server.run(
                        read_stream,
                        write_stream,
                        initialization_options,
                    )
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, shutting down...")
                except Exception as e:
                    logger.error(f"Server error: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Failed to run server: {e}")
            raise
        finally:
            # Cleanup
            await self.cleanup()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Context Memory MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run with default settings
  %(prog)s --db-path ./my_memories.db  # Use custom database path
  %(prog)s --log-level DEBUG        # Enable debug logging
  %(prog)s --log-file server.log    # Log to file
        """
    )
    
    parser.add_argument(
        "--db-path",
        default="memories.db",
        help="Path to SQLite database file (default: memories.db)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        help="Log file path (optional, logs to stderr by default)"
    )
    
    parser.add_argument(
        "--server-name",
        default="ai-context-memory",
        help="MCP server name (default: ai-context-memory)"
    )
    
    parser.add_argument(
        "--server-version",
        default="0.1.0",
        help="MCP server version (default: 0.1.0)"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show server information and exit"
    )
    
    return parser.parse_args()

async def show_server_info(args):
    """Show server information."""
    server = AIContextMemoryServer(
        db_path=args.db_path,
        server_name=args.server_name,
        server_version=args.server_version
    )
    
    try:
        await server.initialize()
        info = await server.get_server_info()
        
        print(f"Server Name: {info['name']}")
        print(f"Server Version: {info['version']}")
        print(f"Database Path: {info['database_path']}")
        print(f"Initialized: {info['initialized']}")
        
        if 'memory_statistics' in info and 'error' not in info['memory_statistics']:
            stats = info['memory_statistics']
            print(f"\nMemory Statistics:")
            print(f"  Total Memories: {stats.get('total_count', 0)}")
            print(f"  Facts: {stats.get('fact_count', 0)}")
            print(f"  Notes: {stats.get('note_count', 0)}")
            print(f"  Preferences: {stats.get('preference_count', 0)}")
            print(f"  Conversations: {stats.get('conversation_count', 0)}")
            print(f"  Total Tags: {stats.get('total_tags', 0)}")
            
    except Exception as e:
        print(f"Error getting server info: {e}")
        sys.exit(1)
    finally:
        await server.cleanup()

async def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Show info and exit if requested
    if args.info:
        await show_server_info(args)
        return
    
    # Validate database path
    db_path = Path(args.db_path)
    if db_path.exists() and not db_path.is_file():
        logger.error(f"Database path exists but is not a file: {db_path}")
        sys.exit(1)
    
    # Create database directory if it doesn't exist
    db_dir = db_path.parent
    if not db_dir.exists():
        logger.info(f"Creating database directory: {db_dir}")
        db_dir.mkdir(parents=True, exist_ok=True)
    
    # Create and run server
    server = AIContextMemoryServer(
        db_path=str(db_path),
        server_name=args.server_name,
        server_version=args.server_version
    )
    
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())