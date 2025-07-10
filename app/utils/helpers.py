"""
Utility helper functions for the Vibe OLS application.
Common functionality shared across different modules.
"""

import hashlib
from typing import Any, Dict

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