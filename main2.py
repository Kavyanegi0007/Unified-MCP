# """
# Main Orchestrator: MCP Server (stdio) + Azure OpenAI Decision Making

# Fixed version with proper stdio_client context manager usage.

# Usage:
#     # Interactive mode
#     python main.py
    
#     # Single query
#     python main.py --query "Find similar images to cat.jpg"
# """

# import asyncio
# import logging
# import json
# import os
# import sys
# from typing import Dict, Any, List, Optional, Tuple
# from pathlib import Path
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # Try to import MCP client
# try:
#     from mcp import ClientSession, StdioServerParameters
#     from mcp.client.stdio import stdio_client
# except ImportError:
#     logger.error("❌ mcp package not installed. Run: pip install mcp")
#     sys.exit(1)

# # Try to import Azure OpenAI
# try:
#     from openai import AzureOpenAI
# except ImportError:
#     logger.error("❌ openai package not installed. Run: pip install openai")
#     sys.exit(1)

# # ============================================
# # Configuration
# # ============================================

# BASE_DIR = Path(__file__).parent

# # ============================================
# # MCP Client (talks to MCP server via stdio)
# # ============================================

# class MCPStdioClient:
#     """
#     Client that communicates with MCP server via stdio (standard input/output)
#     This is the same transport Claude Desktop uses!
#     """
    
#     def __init__(self, server_script_path: Path):
#         self.server_script_path = server_script_path
#         self.session: Optional[ClientSession] = None
#         self.read_stream = None
#         self.write_stream = None
#         self.tools_cache = []
#         self._context_manager = None
    
#     async def connect(self):
#         """Connect to MCP server via stdio"""
#         try:
#             # Create server parameters
#             server_params = StdioServerParameters(
#                 command=sys.executable,  # Python executable
#                 args=[str(self.server_script_path)],  # Just the script, server handles --transport stdio
#                 env=None
#             )

#             # Connect via stdio - USE AS CONTEXT MANAGER
#             logger.info(f"📡 Connecting to MCP server via stdio: {self.server_script_path}")

#             # Store context manager
#             self._context_manager = stdio_client(server_params)

#             # Enter the context manager - returns (read_stream, write_stream)
#             read_stream, write_stream = await self._context_manager.__aenter__()
#             self.read_stream = read_stream
#             self.write_stream = write_stream

#             # Create session
#             self.session = ClientSession(self.read_stream, self.write_stream)
#             await self.session.__aenter__()

#             # Initialize
#             await self.session.initialize()

#             logger.info("✅ Connected to MCP server via stdio")

#             # Get available tools
#             await self._refresh_tools()

#         except Exception as e:
#             logger.error(f"❌ Failed to connect to MCP server: {e}")
#             import traceback
#             logger.error(traceback.format_exc())
#             raise
    
#     async def _refresh_tools(self):
#         """Get list of available tools from server"""
#         try:
#             result = await self.session.list_tools()
#             self.tools_cache = result.tools
#             logger.info(f"📋 Found {len(self.tools_cache)} tool(s)")
#         except Exception as e:
#             logger.error(f"❌ Error listing tools: {e}")
#             self.tools_cache = []
    
#     def get_tools(self) -> List[Dict[str, Any]]:
#         """Get cached list of tools"""
#         return [
#             {
#                 "name": tool.name,
#                 "description": tool.description,
#                 "inputSchema": tool.inputSchema
#             }
#             for tool in self.tools_cache
#         ]
    
#     async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
#         """Call a tool on the MCP server"""
#         try:
#             logger.info(f"🔧 Calling tool: {tool_name}")
#             logger.debug(f"   Arguments: {arguments}")
            
#             # Call tool via MCP
#             result = await self.session.call_tool(tool_name, arguments)
            
#             # Extract content
#             if result.content:
#                 # MCP returns content as a list
#                 content_list = []
#                 for item in result.content:
#                     if hasattr(item, 'text'):
#                         content_list.append(item.text)
#                     elif hasattr(item, 'data'):
#                         content_list.append(item.data)
                
#                 return {
#                     "success": True,
#                     "content": content_list,
#                     "raw": str(result.content)
#                 }
#             else:
#                 return {
#                     "success": True,
#                     "content": [],
#                     "raw": str(result)
#                 }
        
#         except Exception as e:
#             logger.error(f"❌ Error calling tool: {e}")
#             return {
#                 "success": False,
#                 "error": str(e)
#             }
    
#     async def close(self):
#         """Close the MCP connection"""
#         try:
#             if self.session:
#                 await self.session.__aexit__(None, None, None)
            
#             if self._context_manager:
#                 await self._context_manager.__aexit__(None, None, None)
            
#             logger.info("✅ MCP connection closed")
#         except Exception as e:
#             logger.error(f"Error closing connection: {e}")


# # ============================================
# # Azure OpenAI Orchestrator
# # ============================================

# class AzureOpenAIOrchestrator:
#     """
#     Uses Azure OpenAI to decide which MCP tools to call
#     """
    
#     def __init__(self, available_tools: List[Dict[str, Any]]):
#         """
#         Initialize Azure OpenAI orchestrator
        
#         Args:
#             available_tools: List of available MCP tools
#         """
#         self.available_tools = available_tools
#         self._init_azure_openai()
    
#     def _init_azure_openai(self):
#         """Initialize Azure OpenAI client"""
#         try:
#             self.client = AzureOpenAI(
#                 api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#                 api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
#                 azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
#             )
#             self.model = os.getenv("AZURE_DEPLOYMENT", "gpt-4")
#             logger.info(f"✅ Initialized Azure OpenAI with model: {self.model}")
#         except Exception as e:
#             logger.error(f"❌ Failed to initialize Azure OpenAI: {e}")
#             raise
    
#     def _convert_tools_to_openai_format(self) -> List[Dict[str, Any]]:
#         """Convert MCP tool definitions to OpenAI function calling format"""
#         openai_tools = []
        
#         for tool in self.available_tools:
#             tool_name = tool.get("name")
#             description = tool.get("description", "")
#             input_schema = tool.get("inputSchema", {})
            
#             # Use the inputSchema from MCP if available
#             if input_schema:
#                 parameters = input_schema
#             else:
#                 # Fallback: create basic parameters
#                 parameters = {"type": "object", "properties": {}, "required": []}
                
#                 if tool_name == "search_similar":
#                     parameters["properties"] = {
#                         "query_image_path": {
#                             "type": "string",
#                             "description": "Path or URL to the query image"
#                         },
#                         "k": {
#                             "type": "integer",
#                             "description": "Number of similar images to return (default: 5)",
#                             "default": 5
#                         }
#                     }
#                     parameters["required"] = ["query_image_path"]
                
#                 elif tool_name == "process_user_query":
#                     parameters["properties"] = {
#                         "query": {
#                             "type": "string",
#                             "description": "SQL query or natural language question about the database"
#                         }
#                     }
#                     parameters["required"] = ["query"]
                
#                 elif tool_name == "image_search":
#                     parameters["properties"] = {
#                         "query": {
#                             "type": "string",
#                             "description": "Search query for images"
#                         }
#                     }
#                     parameters["required"] = ["query"]
            
#             openai_tools.append({
#                 "type": "function",
#                 "function": {
#                     "name": tool_name,
#                     "description": description,
#                     "parameters": parameters
#                 }
#             })
        
#         return openai_tools
    
#     async def decide_and_get_tool_call(self, user_query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
#         """
#         Ask Azure OpenAI which tool to call and with what arguments
        
#         Returns:
#             Tuple of (tool_name, arguments) or None if no tool needed
#         """
#         try:
#             tools = self._convert_tools_to_openai_format()
            
#             messages = [
#                 {
#                     "role": "system",
#                     "content": "You are a helpful assistant with access to various tools. "
#                                "Analyze the user's query and decide which tool to use. also read the tool descriptions carefully."
#                 },
#                 {
#                     "role": "user",
#                     "content": user_query
#                 }
#             ]
            
#             response = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=messages,
#                 tools=tools,
#                 tool_choice="auto"
#             )
            
#             message = response.choices[0].message
            
#             if message.tool_calls:
#                 tool_call = message.tool_calls[0]
#                 tool_name = tool_call.function.name
#                 arguments = json.loads(tool_call.function.arguments)
                
#                 logger.info(f"🤖 Azure OpenAI decided: {tool_name}")
#                 logger.debug(f"   Arguments: {arguments}")
#                 return (tool_name, arguments)
#             else:
#                 logger.info("🤖 Azure OpenAI says: No tool needed for this query")
#                 return None
        
#         except Exception as e:
#             logger.error(f"❌ Error in Azure OpenAI decision: {e}")
#             return None
    
#     async def synthesize_response(self, user_query: str, tool_name: str, tool_result: Dict[str, Any]) -> str:
#         """
#         Have Azure OpenAI synthesize a natural language response from tool results
#         """
#         try:
#             messages = [
#                 {
#                     "role": "system",
#                     "content": "You are a helpful assistant. Synthesize the tool results into a clear, natural response."
#                 },
#                 {
#                     "role": "user",
#                     "content": user_query
#                 },
#                 {
#                     "role": "assistant",
#                     "content": None,
#                     "tool_calls": [{
#                         "id": "call_1",
#                         "type": "function",
#                         "function": {
#                             "name": tool_name,
#                             "arguments": "{}"
#                         }
#                     }]
#                 },
#                 {
#                     "role": "tool",
#                     "tool_call_id": "call_1",
#                     "name": tool_name,
#                     "content": json.dumps(tool_result)
#                 }
#             ]
            
#             response = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=messages
#             )
            
#             return response.choices[0].message.content
        
#         except Exception as e:
#             logger.error(f"❌ Error synthesizing response: {e}")
#             # Fallback: just show the results
#             if "content" in tool_result and tool_result["content"]:
#                 return "\n".join(str(c) for c in tool_result["content"])
#             return f"Tool {tool_name} returned: {json.dumps(tool_result, indent=2)}"


# # ============================================
# # Main Orchestrator
# # ============================================

# class MCPOrchestrator:
#     """
#     Main orchestrator that:
#     1. Connects to MCP server via stdio
#     2. Uses Azure OpenAI to decide which tools to call
#     3. Executes tools via MCP
#     4. Returns synthesized responses
#     """
    
#     def __init__(
#         self,
#         mcp_client: MCPStdioClient,
#         llm_orchestrator: AzureOpenAIOrchestrator
#     ):
#         self.mcp_client = mcp_client
#         self.llm = llm_orchestrator
    
#     @classmethod
#     async def create(cls, server_script: str = "server.py") -> "MCPOrchestrator":
#         """
#         Factory method to create and initialize orchestrator
        
#         Args:
#             server_script: Path to server.py
        
#         Returns:
#             Initialized MCPOrchestrator instance
#         """
#         # Find server script
#         server_path = BASE_DIR / server_script
#         if not server_path.exists():
#             raise FileNotFoundError(f"Server script not found: {server_path}")
        
#         logger.info(f"🚀 Initializing MCP Orchestrator")
#         logger.info(f"   Server: {server_path}")
#         logger.info(f"   LLM: Azure OpenAI")
        
#         # Create and connect MCP client
#         mcp_client = MCPStdioClient(server_path)
#         await mcp_client.connect()
        
#         # Get available tools
#         tools = mcp_client.get_tools()
#         logger.info(f"📋 Available tools:")
#         for tool in tools:
#             logger.info(f"   - {tool.get('name')}: {tool.get('description')}")
        
#         # Create Azure OpenAI orchestrator
#         llm_orchestrator = AzureOpenAIOrchestrator(tools)
        
#         return cls(mcp_client, llm_orchestrator)
    
#     async def process_query(self, user_query: str) -> Tuple[str, Dict[str, Any]]:
#         """
#         Process a user query:
#         1. Azure OpenAI decides which tool to use
#         2. Call tool via MCP
#         3. Azure OpenAI synthesizes response
        
#         Args:
#             user_query: The user's question
        
#         Returns:
#             Tuple of (response_text, metadata)
#         """
#         logger.info(f"💬 Processing query: {user_query}")
        
#         # Step 1: Azure OpenAI decides which tool to call
#         decision = await self.llm.decide_and_get_tool_call(user_query)
        
#         if decision is None:
#             # No tool needed, Azure OpenAI can answer directly
#             response = "I can answer this directly without using any tools."
#             return (response, {"tool_used": None, "tool_result": None})
        
#         tool_name, arguments = decision
        
#         # Step 2: Call the tool via MCP (stdio)
#         logger.info(f"🔧 Calling MCP tool via stdio: {tool_name}")
#         tool_result = await self.mcp_client.call_tool(tool_name, arguments)
        
#         if not tool_result.get("success", False):
#             error_msg = f"Error calling tool {tool_name}: {tool_result.get('error', 'Unknown error')}"
#             logger.error(f"❌ {error_msg}")
#             return (error_msg, {"tool_used": tool_name, "tool_result": tool_result, "error": True})
        
#         logger.info(f"✅ Tool executed successfully")
        
#         # Step 3: Azure OpenAI synthesizes natural language response
#         logger.info("💬 Synthesizing response...")
#         response = await self.llm.synthesize_response(user_query, tool_name, tool_result)
        
#         metadata = {
#             "tool_used": tool_name,
#             "tool_arguments": arguments,
#             "tool_result": tool_result,
#             "error": False
#         }
        
#         return (response, metadata)
    
#     async def close(self):
#         """Clean up resources"""
#         logger.info("🧹 Cleaning up...")
#         await self.mcp_client.close()
#         logger.info("✅ Cleanup complete")


# # ============================================
# # Interactive Mode
# # ============================================

# async def interactive_mode():
#     """
#     Run in interactive mode - chat with the orchestrator
#     """
#     print("=" * 60)
#     print("🤖 MCP Orchestrator - Interactive Mode (stdio)")
#     print("=" * 60)
#     print()
#     print("Starting up...")
#     print()
    
#     # Create orchestrator
#     orchestrator = await MCPOrchestrator.create()
    
#     print("=" * 60)
#     print("✅ Ready! Type your queries (or 'quit' to exit)")
#     print("=" * 60)
#     print()
    
#     try:
#         while True:
#             # Get user input
#             try:
#                 user_query = input("💬 You: ").strip()
#             except (EOFError, KeyboardInterrupt):
#                 print()
#                 break
            
#             if not user_query:
#                 continue
            
#             if user_query.lower() in ['quit', 'exit', 'q']:
#                 break
            
#             # Process query
#             print("🤖 Assistant: Processing...")
#             print()
            
#             try:
#                 response, metadata = await orchestrator.process_query(user_query)
                
#                 # Display response
#                 print(f"🤖 Assistant: {response}")
#                 print()
                
#                 # Display metadata
#                 if metadata.get("tool_used"):
#                     print(f"   🛠️  Tool used: {metadata['tool_used']}")
#                     print()
            
#             except Exception as e:
#                 print(f"❌ Error: {e}")
#                 logger.exception("Full error:")
#                 print()
    
#     finally:
#         # Cleanup
#         await orchestrator.close()
#         print()
#         print("👋 Goodbye!")


# # ============================================
# # Single Query Mode
# # ============================================

# async def single_query_mode(query: str):
#     """
#     Process a single query and exit
#     """
#     print(f"Processing query: {query}")
#     print()
    
#     # Create orchestrator
#     orchestrator = await MCPOrchestrator.create()
    
#     try:
#         # Process query
#         response, metadata = await orchestrator.process_query(query)
        
#         # Display results
#         print("=" * 60)
#         print("RESPONSE:")
#         print("=" * 60)
#         print(response)
#         print()
        
#         if metadata.get("tool_used"):
#             print("=" * 60)
#             print("METADATA:")
#             print("=" * 60)
#             print(f"Tool used: {metadata['tool_used']}")
#             print(f"Arguments: {metadata.get('tool_arguments')}")
#             print()
    
#     finally:
#         await orchestrator.close()


# # ============================================
# # Main Entry Point
# # ============================================

# def main():
#     """Main entry point"""
    
#     # Check for required environment variables
#     required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
#     missing = [var for var in required_vars if not os.getenv(var)]
#     if missing:
#         print(f"❌ Missing environment variables: {', '.join(missing)}")
#         print("Please set them in your .env file")
#         print()
#         print("Required .env file format:")
#         print("AZURE_OPENAI_API_KEY=your_key_here")
#         print("AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com")
#         print("AZURE_OPENAI_MODEL=gpt-4")
#         sys.exit(1)
    
#     # Check for query argument
#     if len(sys.argv) > 2 and sys.argv[1] == "--query":
#         query = sys.argv[2]
#         asyncio.run(single_query_mode(query))
#     else:
#         asyncio.run(interactive_mode())


# if __name__ == "__main__":
#     main()
"""
Main Orchestrator: MCP Server (stdio) + Azure OpenAI Decision Making

VERSION WITH ERROR SUPPRESSION - Hides harmless cleanup errors from MCP SDK

Usage:
    # Interactive mode
    python main.py
    
    # Single query
    python main.py --query "Find similar images to cat.jpg"
"""

import asyncio
import logging
import json
import os
import sys
import warnings
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# Configure Logging with Error Suppression
# ============================================

# Custom filter to suppress MCP SDK cleanup errors
class MCPCleanupFilter(logging.Filter):
    """Filter out harmless MCP SDK cleanup warnings"""
    def filter(self, record):
        msg = str(record.msg)
        # Suppress the known asyncio cleanup errors from MCP SDK
        if "error occurred during closing of asynchronous generator" in msg:
            return False
        if "cancel scope" in msg and "RuntimeError" in msg:
            return False
        if "asyncgen" in msg:
            return False
        return True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Apply cleanup filter to asyncio logger
asyncio_logger = logging.getLogger('asyncio')
asyncio_logger.addFilter(MCPCleanupFilter())
asyncio_logger.setLevel(logging.ERROR)  # Only show actual errors

# Suppress anyio warnings about task groups
warnings.filterwarnings('ignore', category=RuntimeWarning, module='anyio')

logger.info("🔧 Error suppression enabled for MCP SDK cleanup warnings")

# ============================================
# MCP and Azure OpenAI Imports
# ============================================

# Try to import MCP client
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    logger.error("❌ mcp package not installed. Run: pip install mcp")
    sys.exit(1)

# Try to import Azure OpenAI
try:
    from openai import AzureOpenAI
except ImportError:
    logger.error("❌ openai package not installed. Run: pip install openai")
    sys.exit(1)

# ============================================
# Configuration
# ============================================

BASE_DIR = Path(__file__).parent

# ============================================
# MCP Client (talks to MCP server via stdio)
# ============================================

class MCPStdioClient:
    """
    Client that communicates with MCP server via stdio (standard input/output)
    This is the same transport Claude Desktop uses!
    
    Note: Harmless cleanup errors from MCP SDK are suppressed via logging filter
    """
    
    def __init__(self, server_script_path: Path):
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self.tools_cache = []
        self._connected = False
    
    async def connect(self):
        """Connect to MCP server via stdio"""
        if self._connected:
            logger.warning("Already connected to MCP server")
            return
        
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[str(self.server_script_path)],
                env=None
            )

            logger.info(f"📡 Connecting to MCP server via stdio: {self.server_script_path}")

            # Store context managers
            self._stdio_context = stdio_client(server_params)
            self._read_stream, self._write_stream = await self._stdio_context.__aenter__()

            # Create and enter session
            self._session_context = ClientSession(self._read_stream, self._write_stream)
            self.session = await self._session_context.__aenter__()

            # Initialize
            await self.session.initialize()

            self._connected = True
            logger.info("✅ Connected to MCP server via stdio")

            # Get available tools
            await self._refresh_tools()

        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP server: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await self._emergency_cleanup()
            raise
    
    async def _emergency_cleanup(self):
        """Emergency cleanup on connection failure"""
        try:
            if hasattr(self, '_session_context'):
                await self._session_context.__aexit__(None, None, None)
        except:
            pass
        
        try:
            if hasattr(self, '_stdio_context'):
                await self._stdio_context.__aexit__(None, None, None)
        except:
            pass
    
    async def _refresh_tools(self):
        """Get list of available tools from server"""
        try:
            result = await self.session.list_tools()
            self.tools_cache = result.tools
            logger.info(f"📋 Found {len(self.tools_cache)} tool(s)")
        except Exception as e:
            logger.error(f"❌ Error listing tools: {e}")
            self.tools_cache = []
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get cached list of tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            }
            for tool in self.tools_cache
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self._connected:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            logger.info(f"🔧 Calling tool: {tool_name}")
            logger.debug(f"   Arguments: {arguments}")
            
            # Call tool via MCP
            result = await self.session.call_tool(tool_name, arguments)
            
            # Extract content
            if result.content:
                content_list = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        content_list.append(item.text)
                    elif hasattr(item, 'data'):
                        content_list.append(item.data)
                
                return {
                    "success": True,
                    "content": content_list,
                    "raw": str(result.content)
                }
            else:
                return {
                    "success": True,
                    "content": [],
                    "raw": str(result)
                }
        
        except Exception as e:
            logger.error(f"❌ Error calling tool: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close(self):
        """
        Close the MCP connection
        
        Note: Any cleanup errors from MCP SDK are suppressed (they're harmless)
        """
        if not self._connected:
            return
        
        logger.info("🧹 Closing MCP connection...")
        
        # Close in LIFO order - session first, then stdio
        # Errors are logged at DEBUG level (suppressed by default)
        try:
            if hasattr(self, '_session_context') and self._session_context:
                await self._session_context.__aexit__(None, None, None)
                logger.debug("Session context exited")
        except Exception as e:
            logger.debug(f"Session cleanup exception (expected): {e}")
        
        try:
            if hasattr(self, '_stdio_context') and self._stdio_context:
                await self._stdio_context.__aexit__(None, None, None)
                logger.debug("Stdio context exited")
        except Exception as e:
            logger.debug(f"Stdio cleanup exception (expected): {e}")
        
        self._connected = False
        logger.info("✅ MCP connection closed cleanly")


# ============================================
# Azure OpenAI Orchestrator
# ============================================

class AzureOpenAIOrchestrator:
    """Uses Azure OpenAI to decide which MCP tools to call"""
    
    def __init__(self, available_tools: List[Dict[str, Any]]):
        self.available_tools = available_tools
        self._init_azure_openai()
    
    def _init_azure_openai(self):
        """Initialize Azure OpenAI client"""
        try:
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            self.model = os.getenv("AZURE_DEPLOYMENT", "gpt-4")
            logger.info(f"✅ Initialized Azure OpenAI with model: {self.model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure OpenAI: {e}")
            raise
    
    def _convert_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        """Convert MCP tool definitions to OpenAI function calling format"""
        openai_tools = []
        
        for tool in self.available_tools:
            tool_name = tool.get("name")
            description = tool.get("description", "")
            input_schema = tool.get("inputSchema", {})
            
            if input_schema:
                parameters = input_schema
            else:
                parameters = {"type": "object", "properties": {}, "required": []}
                
                if tool_name == "process_user_query":
                    parameters["properties"] = {
                        "user_query": {
                            "type": "string",
                            "description": "The SQL query or question to process"
                        }
                    }
                    parameters["required"] = ["user_query"]
            
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": description,
                    "parameters": parameters
                }
            }
            openai_tools.append(openai_tool)
        
        return openai_tools
    
    async def decide_and_get_tool_call(self, user_query: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Use Azure OpenAI to decide which tool to call"""
        try:
            openai_tools = self._convert_tools_to_openai_format()
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that decides which tool to use to answer user queries. "
                        "Analyze the user's question and determine if you need to call a tool. "
                        "If you need to call a tool, use function calling. "
                        "If you can answer without a tool, just respond normally."
                    )
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                logger.info(f"🎯 LLM decided to use tool: {tool_name}")
                return (tool_name, arguments)
            else:
                logger.info("🎯 LLM decided no tool is needed")
                return None
        
        except Exception as e:
            logger.error(f"❌ Error in Azure OpenAI decision: {e}")
            raise
    
    async def synthesize_response(
        self, 
        user_query: str, 
        tool_name: str, 
        tool_result: Dict[str, Any]
    ) -> str:
        """Synthesize a natural language response from tool results"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. The user asked a question, "
                        "and a tool was called to get information. "
                        "Synthesize the tool's result into a clear, natural language response. "
                        "Be concise but informative."
                    )
                },
                {
                    "role": "user",
                    "content": f"User query: {user_query}"
                },
                {
                    "role": "assistant",
                    "content": f"I used the '{tool_name}' tool and got this result:\n{json.dumps(tool_result, indent=2)}"
                },
                {
                    "role": "user",
                    "content": "Please provide a natural language response to the original query based on this tool result."
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            
            synthesized = response.choices[0].message.content
            logger.info("✅ Response synthesized")
            return synthesized
        
        except Exception as e:
            logger.error(f"❌ Error synthesizing response: {e}")
            return f"Tool '{tool_name}' returned: {json.dumps(tool_result, indent=2)}"


# ============================================
# Main Orchestrator
# ============================================

class MCPOrchestrator:
    """
    Main orchestrator that:
    1. Connects to MCP server via stdio
    2. Uses Azure OpenAI to decide which tools to call
    3. Executes tools via MCP
    4. Returns synthesized responses
    """
    
    def __init__(self, mcp_client: MCPStdioClient, llm_orchestrator: AzureOpenAIOrchestrator):
        self.mcp_client = mcp_client
        self.llm = llm_orchestrator
    
    @classmethod
    async def create(cls, server_script: str = "server.py") -> "MCPOrchestrator":
        """Factory method to create and initialize orchestrator"""
        server_path = BASE_DIR / server_script
        if not server_path.exists():
            raise FileNotFoundError(f"Server script not found: {server_path}")
        
        logger.info(f"🚀 Initializing MCP Orchestrator")
        logger.info(f"   Server: {server_path}")
        logger.info(f"   LLM: Azure OpenAI")
        
        mcp_client = MCPStdioClient(server_path)
        await mcp_client.connect()
        
        tools = mcp_client.get_tools()
        logger.info(f"📋 Available tools:")
        for tool in tools:
            logger.info(f"   - {tool.get('name')}: {tool.get('description')}")
        
        llm_orchestrator = AzureOpenAIOrchestrator(tools)
        
        return cls(mcp_client, llm_orchestrator)
    
    async def process_query(self, user_query: str) -> Tuple[str, Dict[str, Any]]:
        """Process a user query"""
        logger.info(f"💬 Processing query: {user_query}")
        
        decision = await self.llm.decide_and_get_tool_call(user_query)
        
        if decision is None:
            response = "I can answer this directly without using any tools."
            return (response, {"tool_used": None, "tool_result": None})
        
        tool_name, arguments = decision
        
        logger.info(f"🔧 Calling MCP tool via stdio: {tool_name}")
        tool_result = await self.mcp_client.call_tool(tool_name, arguments)
        
        if not tool_result.get("success", False):
            error_msg = f"Error calling tool {tool_name}: {tool_result.get('error', 'Unknown error')}"
            logger.error(f"❌ {error_msg}")
            return (error_msg, {"tool_used": tool_name, "tool_result": tool_result, "error": True})
        
        logger.info(f"✅ Tool executed successfully")
        
        logger.info("💬 Synthesizing response...")
        response = await self.llm.synthesize_response(user_query, tool_name, tool_result)
        
        metadata = {
            "tool_used": tool_name,
            "tool_arguments": arguments,
            "tool_result": tool_result,
            "error": False
        }
        
        return (response, metadata)
    
    async def close(self):
        """Clean up resources"""
        logger.info("🧹 Cleaning up orchestrator...")
        await self.mcp_client.close()
        logger.info("✅ Orchestrator cleanup complete")


# ============================================
# Interactive Mode
# ============================================

async def interactive_mode():
    """Run in interactive mode - chat with the orchestrator"""
    print("=" * 60)
    print("🤖 MCP Orchestrator - Interactive Mode")
    print("=" * 60)
    print()
    print("Starting up...")
    print()
    
    orchestrator = await MCPOrchestrator.create()
    
    print("=" * 60)
    print("✅ Ready! Type your queries (or 'quit' to exit)")
    print("=" * 60)
    print()
    
    try:
        while True:
            try:
                user_query = input("💬 You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            
            if not user_query:
                continue
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                break
            
            print("🤖 Assistant: Processing...")
            print()
            
            try:
                response, metadata = await orchestrator.process_query(user_query)
                
                print(f"🤖 Assistant: {response}")
                print()
                
                if metadata.get("tool_used"):
                    print(f"   🛠️  Tool used: {metadata['tool_used']}")
                    print()
            
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.exception("Full error:")
                print()
    
    finally:
        await orchestrator.close()
        print()
        print("👋 Goodbye!")


# ============================================
# Single Query Mode
# ============================================

async def single_query_mode(query: str):
    """Process a single query and exit"""
    print(f"Processing query: {query}")
    print()
    
    orchestrator = await MCPOrchestrator.create()
    
    try:
        response, metadata = await orchestrator.process_query(query)
        
        print("=" * 60)
        print("RESPONSE:")
        print("=" * 60)
        print(response)
        print()
        
        if metadata.get("tool_used"):
            print("=" * 60)
            print("METADATA:")
            print("=" * 60)
            print(f"Tool used: {metadata['tool_used']}")
            print(f"Arguments: {metadata.get('tool_arguments')}")
            print()
    
    finally:
        await orchestrator.close()


# ============================================
# Main Entry Point
# ============================================

def main():
    """Main entry point"""
    
    required_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Please set them in your .env file")
        print()
        print("Required .env file format:")
        print("AZURE_OPENAI_API_KEY=your_key_here")
        print("AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com")
        print("AZURE_OPENAI_MODEL=gpt-4")
        sys.exit(1)
    
    if len(sys.argv) > 2 and sys.argv[1] == "--query":
        query = sys.argv[2]
        asyncio.run(single_query_mode(query))
    else:
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()