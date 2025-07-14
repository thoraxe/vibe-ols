"""
Utility helper functions for the Vibe OLS application.
Common functionality shared across different modules.
"""

import hashlib
from typing import Any, Dict
from ..core.logging import get_logger

def generate_id(content: str, prefix: str = "id", length: int = 8) -> str:
    """
    Generate a unique ID based on content hash.
    
    Args:
        content: The content to hash
        prefix: Prefix for the ID
        length: Length of the hash portion
        
    Returns:
        Unique ID string
    """
    hash_value = hashlib.md5(content.encode()).hexdigest()[:length]
    return f"{prefix}_{hash_value}"

def format_context(context: Dict[str, Any]) -> str:
    """
    Format context dictionary into a readable string.
    
    Args:
        context: Dictionary of context information
        
    Returns:
        Formatted context string
    """
    if not context:
        return ""
    
    context_items = [f"{key}: {value}" for key, value in context.items()]
    return "\n".join(context_items)

def prepare_prompt_with_context(query: str, context: Dict[str, Any] | None = None) -> str:
    """
    Prepare a prompt by combining query with context information.
    
    Args:
        query: The main query text
        context: Optional context information
        
    Returns:
        Complete prompt string
    """
    if not context:
        return query
    
    context_str = format_context(context)
    return f"{query}\n\nAdditional Context:\n{context_str}"

def create_mcp_log_handler(server_name: str):
    """
    Create a custom logging handler for MCP server messages.
    
    Args:
        server_name: Name of the MCP server for context in log messages
        
    Returns:
        Async function that handles MCP log messages
    """
    logger = get_logger(f"mcp.{server_name}")
    
    async def mcp_log_handler(params):
        """Custom handler for MCP server log messages."""
        # Extract log information from the params object
        level = getattr(params, 'level', 'info')
        message = getattr(params, 'data', str(params))
        logger_name = getattr(params, 'logger', None)
        
        # Map MCP log levels to Python logging levels
        level_map = {
            "debug": logger.debug,
            "info": logger.info,
            "notice": logger.info,
            "warning": logger.warning,
            "error": logger.error,
            "critical": logger.critical,
            "alert": logger.critical,
            "emergency": logger.critical,
        }
        
        # Get the appropriate logging function
        log_func = level_map.get(level.lower(), logger.info)
        
        # Format the message with server context
        formatted_message = f"[MCP:{server_name}] {message}"
        if logger_name:
            formatted_message = f"[MCP:{server_name}:{logger_name}] {message}"
        
        # Log the message
        log_func(formatted_message)
    
    return mcp_log_handler 