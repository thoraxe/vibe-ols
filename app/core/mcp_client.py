"""
MCP (Model Context Protocol) client for connecting to external tools and services.
Handles loading tools from MCP servers and providing them to AI agents.
"""

import asyncio
import inspect
from typing import Dict, List, Any, Optional, Callable
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from mcp.shared.metadata_utils import get_display_name

from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


class MCPClient:
    """
    Client for connecting to MCP (Model Context Protocol) servers.
    Loads tools from configured servers and provides them to AI agents.
    """
    
    def __init__(self):
        self.tools: List[Dict[str, Any]] = []
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.loaded = False
        self.connection_timeout = 10  # seconds
        
    async def load_tools(self) -> None:
        """
        Load tools from all configured MCP servers.
        """
        if not settings.is_mcp_configured:
            logger.info("🔧 MCP not configured or disabled, skipping tool loading")
            return
            
        logger.info("🔧 Loading tools from MCP servers...")
        
        server_configs = settings.mcp_servers_dict
        if not server_configs:
            logger.warning("⚠️ No MCP servers configured")
            return
            
        # Load tools from each configured server
        for server_name, endpoint in server_configs.items():
            try:
                # Use a timeout for each server connection
                await asyncio.wait_for(
                    self._load_tools_from_server(server_name, endpoint),
                    timeout=self.connection_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"❌ Timeout connecting to MCP server {server_name} ({endpoint}) after {self.connection_timeout}s")
            except Exception as e:
                logger.error(f"❌ Failed to load tools from {server_name} ({endpoint}): {e}")
                logger.exception(f"Error loading tools from {server_name}")
                
        self.loaded = True
        logger.info(f"✅ Successfully loaded {len(self.tools)} tools from MCP servers")
        
    async def _load_tools_from_server(self, server_name: str, endpoint: str) -> None:
        """
        Load tools from a specific MCP server.
        
        Args:
            server_name: Name of the MCP server
            endpoint: HTTP endpoint URL for the MCP server
        """
        logger.info(f"🔌 Connecting to MCP server: {server_name} ({endpoint})")
        
        client_context = None
        session = None
        
        try:
            # Use the streamable HTTP client pattern
            client_context = streamablehttp_client(endpoint)
            read_stream, write_stream, _ = await client_context.__aenter__()
            
            # Create a session using the client streams
            session = ClientSession(read_stream, write_stream)
            await session.__aenter__()
            
            # Initialize the connection
            await session.initialize()
            logger.debug(f"✅ Connected to MCP server: {server_name}")
            
            # Store the session and context for later cleanup
            self.sessions[server_name] = {
                'session': session,
                'client_context': client_context
            }
            
            # List available tools
            tools_response = await session.list_tools()
            
            # Process and store tools
            for tool in tools_response.tools:
                display_name = get_display_name(tool)
                function_name = tool.name
                logger.debug(f"📋 Found tool: {display_name} ({function_name})")
                
                # Create a tool wrapper function for the AI agent
                tool_function = self._create_tool_function(
                    server_name, 
                    function_name, 
                    display_name,
                    tool.description or "", 
                    tool.inputSchema,
                    session
                )
                
                # Store tool info
                self.tools.append({
                    "name": display_name,
                    "function_name": function_name,
                    "server": server_name,
                    "description": tool.description or "",
                    "schema": tool.inputSchema,
                    "function": tool_function
                })
                
            logger.info(f"✅ Loaded {len(tools_response.tools)} tools from {server_name}")
                    
        except Exception as e:
            logger.error(f"❌ Error connecting to MCP server {server_name}: {e}")
            
            # Clean up resources if initialization failed
            # Use a more robust cleanup approach
            await self._cleanup_failed_connection(server_name, session, client_context)
            raise
    
    async def _cleanup_failed_connection(self, server_name: str, session: Optional[ClientSession], client_context: Any) -> None:
        """
        Clean up resources from a failed connection attempt.
        
        Args:
            server_name: Name of the MCP server
            session: The session to clean up (if any)
            client_context: The client context to clean up (if any)
        """
        logger.debug(f"🧹 Cleaning up failed connection to {server_name}")
        
        # Clean up session
        if session:
            try:
                await asyncio.wait_for(session.__aexit__(None, None, None), timeout=5.0)
                logger.debug(f"✅ Cleaned up session for {server_name}")
            except Exception as cleanup_error:
                logger.debug(f"⚠️ Error cleaning up session for {server_name}: {cleanup_error}")
                
        # Clean up client context
        if client_context:
            try:
                await asyncio.wait_for(client_context.__aexit__(None, None, None), timeout=5.0)
                logger.debug(f"✅ Cleaned up client context for {server_name}")
            except Exception as cleanup_error:
                logger.debug(f"⚠️ Error cleaning up client context for {server_name}: {cleanup_error}")
                
        # Remove from sessions if it was added
        if server_name in self.sessions:
            del self.sessions[server_name]
            

    def _create_tool_function(
        self, 
        server_name: str, 
        function_name: str,
        display_name: str,
        description: str, 
        schema: Dict[str, Any],
        session: ClientSession  # This won't be used in the closure anymore
    ) -> Callable:
        """
        Create a wrapper function for an MCP tool that can be used by the AI agent.
        
        Args:
            server_name: Name of the MCP server
            function_name: Function name for the tool (same as tool name)
            display_name: Human-readable display name for the tool
            description: Tool description
            schema: Tool input schema
            session: MCP client session (for reference, not captured in closure)
            
        Returns:
            Callable function that can be used by the AI agent
        """
        
        async def tool_wrapper(*args, **kwargs) -> str:
            """
            Wrapper function that executes the MCP tool with the given parameters.
            """
            try:
                logger.debug(f"🔧 Executing tool {display_name} on server {server_name}")
                logger.debug(f"Parameters - args: {args}, kwargs: {kwargs}")
                
                # Get the current active session for this server
                # This ensures we use a fresh session if the old one was closed
                current_session = await self._get_or_create_session(server_name)
                if not current_session:
                    return f"Error: Unable to connect to MCP server {server_name}"
                
                # Pydantic AI might pass arguments in different ways
                # We need to map positional arguments to parameter names from the schema
                combined_kwargs = kwargs.copy()
                
                if args:
                    # If the first argument is a dict-like object, merge it with kwargs
                    if len(args) == 1 and hasattr(args[0], 'items'):
                        # It's likely a context or parameter dict
                        combined_kwargs.update(dict(args[0]))
                    else:
                        # Map positional arguments to parameter names from schema
                        if schema and "properties" in schema:
                            param_names = list(schema["properties"].keys())
                            logger.debug(f"📋 Available parameter names from schema: {param_names}")
                            
                            # Smart mapping based on tool semantics
                            # For namespace-specific tools, prioritize 'namespace' parameter
                            if 'namespace' in function_name and 'namespace' in param_names:
                                # For namespace tools, first arg is usually the namespace
                                if len(args) >= 1:
                                    combined_kwargs['namespace'] = args[0]
                                    logger.debug(f"🔗 Mapped args[0] = '{args[0]}' to parameter 'namespace' (namespace tool)")
                                # Map remaining args to other parameters
                                remaining_params = [p for p in param_names if p != 'namespace']
                                for i, arg_value in enumerate(args[1:], 1):
                                    if i-1 < len(remaining_params):
                                        param_name = remaining_params[i-1]
                                        combined_kwargs[param_name] = arg_value
                                        logger.debug(f"🔗 Mapped args[{i}] = '{arg_value}' to parameter '{param_name}'")
                            else:
                                # Default mapping: map each positional argument to its corresponding parameter name
                                for i, arg_value in enumerate(args):
                                    if i < len(param_names):
                                        param_name = param_names[i]
                                        combined_kwargs[param_name] = arg_value
                                        logger.debug(f"🔗 Mapped args[{i}] = '{arg_value}' to parameter '{param_name}'")
                                    else:
                                        logger.warning(f"⚠️ Too many positional arguments: args[{i}] = '{arg_value}' (no corresponding parameter)")
                        else:
                            logger.warning(f"⚠️ No schema available to map positional arguments: {args}")
                
                logger.debug(f"Combined parameters: {combined_kwargs}")
                
                # Call the tool through the MCP session using the function name
                logger.debug(f"🔧 Calling session.call_tool with tool_name='{function_name}', arguments={combined_kwargs}")
                
                try:
                    result = await current_session.call_tool(function_name, combined_kwargs)
                    logger.debug(f"✅ session.call_tool returned successfully")
                    logger.debug(f"📝 Raw result type: {type(result)}")
                    logger.debug(f"📝 Raw result: {result}")
                    
                    # Extract the result content
                    # Convert result to string representation
                    str_result = str(result)
                    logger.debug(f"📝 String result (length: {len(str_result)}): {str_result[:200]}...")
                    return str_result
                    
                except Exception as tool_error:
                    logger.error(f"❌ session.call_tool failed for tool '{function_name}': {tool_error}")
                    logger.error(f"❌ Tool error type: {type(tool_error)}")
                    logger.exception(f"❌ Full traceback for tool '{function_name}':")
                    
                    # If the session is closed, try to reconnect and retry once
                    if "ClosedResourceError" in str(type(tool_error)):
                        logger.info(f"🔄 Session closed, attempting to reconnect to {server_name}...")
                        await self._cleanup_session(server_name)
                        retry_session = await self._get_or_create_session(server_name)
                        if retry_session:
                            logger.info(f"🔄 Retrying tool call with new session...")
                            try:
                                result = await retry_session.call_tool(function_name, combined_kwargs)
                                logger.debug(f"✅ Retry successful")
                                str_result = str(result)
                                return str_result
                            except Exception as retry_error:
                                logger.error(f"❌ Retry failed: {retry_error}")
                                return f"Error executing tool {display_name} (retry failed): {str(retry_error)}"
                        else:
                            return f"Error executing tool {display_name}: Unable to reconnect to server"
                    
                    raise tool_error
                    
            except Exception as e:
                logger.error(f"❌ Error executing tool {display_name}: {e}")
                logger.error(f"❌ Error type: {type(e)}")
                logger.exception(f"❌ Full traceback for tool execution:")
                return f"Error executing tool {display_name}: {str(e)}"
        
        # Set function metadata for the AI agent
        tool_wrapper.__name__ = f"{server_name}_{function_name}"
        tool_wrapper.__doc__ = f"{display_name}: {description}"
        
        # Add type annotations in a simpler way that works with Pydantic AI
        # Instead of creating complex signatures, we'll use a simpler approach
        if schema and "properties" in schema:
            # Create a simple annotation dictionary
            annotations = {}
            for param_name, param_info in schema["properties"].items():
                param_type = param_info.get("type", "string")
                # Convert JSON Schema types to Python types
                if param_type == "string":
                    annotations[param_name] = str
                elif param_type == "integer":
                    annotations[param_name] = int
                elif param_type == "number":
                    annotations[param_name] = float
                elif param_type == "boolean":
                    annotations[param_name] = bool
                elif param_type == "array":
                    annotations[param_name] = list
                elif param_type == "object":
                    annotations[param_name] = dict
                else:
                    annotations[param_name] = str  # Default to string
            
            # Add return type annotation
            annotations["return"] = str
            
            # Set the annotations on the function
            tool_wrapper.__annotations__ = annotations
        
        return tool_wrapper
    
    async def _get_or_create_session(self, server_name: str) -> Optional[ClientSession]:
        """
        Get the current active session for a server, or create a new one if needed.
        
        Args:
            server_name: Name of the MCP server
            
        Returns:
            Active ClientSession for the server, or None if connection fails
        """
        try:
            # Check if we have an active session
            if server_name in self.sessions:
                session_info = self.sessions[server_name]
                session = session_info.get('session')
                
                # Test if the session is still active by trying a simple operation
                if session:
                    try:
                        # Try to list tools to check if session is alive
                        await session.list_tools()
                        logger.debug(f"✅ Existing session for {server_name} is active")
                        return session
                    except Exception as e:
                        logger.debug(f"🔄 Existing session for {server_name} is not active: {e}")
                        # Session is dead, clean it up
                        await self._cleanup_session(server_name)
            
            # No active session, create a new one
            logger.info(f"🔄 Creating new session for {server_name}")
            servers_dict = settings.mcp_servers_dict
            if server_name not in servers_dict:
                logger.error(f"❌ Server {server_name} not found in configuration")
                return None
                
            endpoint = servers_dict[server_name]
            
            # Create new connection
            client_context = streamablehttp_client(endpoint)
            read_stream, write_stream, _ = await client_context.__aenter__()
            
            # Create a session using the client streams
            session = ClientSession(read_stream, write_stream)
            await session.__aenter__()
            
            # Initialize the connection
            await session.initialize()
            logger.debug(f"✅ New session created for {server_name}")
            
            # Store the session and context
            self.sessions[server_name] = {
                'session': session,
                'client_context': client_context
            }
            
            return session
            
        except Exception as e:
            logger.error(f"❌ Failed to create session for {server_name}: {e}")
            return None
    
    async def _cleanup_session(self, server_name: str) -> None:
        """
        Clean up a specific server's session.
        
        Args:
            server_name: Name of the MCP server
        """
        if server_name not in self.sessions:
            return
            
        session_info = self.sessions[server_name]
        session = session_info.get('session')
        client_context = session_info.get('client_context')
        
        logger.debug(f"🧹 Cleaning up session for {server_name}")
        
        # Clean up session
        if session:
            try:
                await asyncio.wait_for(session.__aexit__(None, None, None), timeout=2.0)
                logger.debug(f"✅ Cleaned up session for {server_name}")
            except Exception as cleanup_error:
                logger.debug(f"⚠️ Error cleaning up session for {server_name}: {cleanup_error}")
                
        # Clean up client context
        if client_context:
            try:
                await asyncio.wait_for(client_context.__aexit__(None, None, None), timeout=2.0)
                logger.debug(f"✅ Cleaned up client context for {server_name}")
            except Exception as cleanup_error:
                logger.debug(f"⚠️ Error cleaning up client context for {server_name}: {cleanup_error}")
                
        # Remove from sessions
        del self.sessions[server_name]
        
    def get_tools_for_agent(self) -> List[Dict[str, Any]]:
        """
        Get all loaded tools formatted for use with AI agents.
        Returns a list of tool dictionaries with name, description, and function.
        """
        if not self.loaded:
            logger.warning("⚠️ Tools not loaded yet, returning empty list")
            return []
            
        formatted_tools = []
        for tool in self.tools:
            formatted_tools.append({
                "name": tool["function_name"],  # Use function name as the tool name
                "description": tool["description"],
                "function": tool["function"]
            })
        return formatted_tools
        
    def get_tool_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tool by its name.
        
        Args:
            name: The name of the tool to find
            
        Returns:
            Tool dictionary if found, None otherwise
        """
        for tool in self.tools:
            if tool["function_name"] == name or tool["name"] == name:
                return tool
        return None
        
    def list_available_tools(self) -> List[str]:
        """
        Get a list of all available tool names.
        
        Returns:
            List of tool names
        """
        return [tool["function_name"] for tool in self.tools]
        
    async def cleanup(self) -> None:
        """
        Clean up all MCP sessions and connections.
        """
        logger.info("🧹 Cleaning up MCP client resources...")
        
        for server_name, session_info in self.sessions.items():
            try:
                logger.debug(f"🧹 Cleaning up session for {server_name}")
                
                # Clean up session
                session = session_info.get('session')
                if session:
                    await session.__aexit__(None, None, None)
                    
                # Clean up client context
                client_context = session_info.get('client_context')
                if client_context:
                    await client_context.__aexit__(None, None, None)
                    
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning up session for {server_name}: {e}")
                
        self.sessions.clear()
        self.tools.clear()
        self.loaded = False
        
        logger.info("✅ MCP client cleanup completed")


# Global MCP client instance
mcp_client = MCPClient() 