"""
OpenShift AI Agent for troubleshooting and support.
Uses Pydantic AI to provide expert OpenShift guidance with MCP tools.
"""

from pydantic_ai import Agent
from typing import Dict, Any, Optional
from ..core.config import settings
from ..core.logging import get_logger
from ..core.mcp_client import mcp_client

logger = get_logger(__name__)

async def create_openshift_agent() -> Agent:
    """
    Create and configure the OpenShift troubleshooting AI agent with MCP tools.
    
    Returns:
        Configured Pydantic AI agent for OpenShift troubleshooting
    """
    logger.info("🤖 Initializing OpenShift AI Agent...")
    
    # Try to load available tools from MCP servers (graceful failure)
    mcp_tools = []
    try:
        logger.info("🔧 Attempting to load MCP tools...")
        await mcp_client.load_tools()
        mcp_tools = mcp_client.get_tools_for_agent()
        
        if mcp_tools:
            logger.info(f"✅ Loaded {len(mcp_tools)} MCP tools for the agent")
        else:
            logger.info("ℹ️ No MCP tools available (MCP servers may not be configured)")
            
    except Exception as e:
        logger.warning(f"⚠️ Failed to load MCP tools: {e}")
        logger.info("🔧 Agent will continue without MCP tools")
        mcp_tools = []
    
    # Create the base system prompt
    system_prompt = """You are an expert OpenShift troubleshooting assistant with deep knowledge of:

- OpenShift Container Platform (OCP) architecture and components
- Kubernetes fundamentals and OpenShift-specific extensions
- Pod lifecycle, deployment strategies, and workload management
- Networking (SDN, CNI, routes, services, ingress)
- Storage (persistent volumes, storage classes, CSI drivers)
- Security (RBAC, security contexts, network policies, admission controllers)
- Monitoring and logging (Prometheus, Grafana, EFK stack)
- Operators and Operator Lifecycle Manager (OLM)
- OpenShift CLI (oc) commands and troubleshooting techniques
- Common issues and their resolution patterns
- Performance optimization and resource management
- Cluster administration and maintenance

When responding to queries:
1. Provide clear, actionable troubleshooting steps
2. Include relevant oc commands with explanations
3. Reference OpenShift documentation when appropriate
4. Consider security implications in your recommendations
5. Explain the root cause when possible
6. Offer preventive measures to avoid similar issues

Be concise but comprehensive in your responses."""
    
    # Add MCP tool information to system prompt if available
    if mcp_tools:
        system_prompt += f"""

You have access to {len(mcp_tools)} external tools that can provide additional context and information:
- Consider using available tools to gather additional context before responding
- Tools can help you get real-time cluster information, logs, and configuration details
- Use tools to verify current state before providing recommendations"""
    
    agent = Agent(
        "openai:gpt-4o-mini",  # Default model
        system_prompt=system_prompt
    )
    
    # Add MCP tools to the agent if available
    if mcp_tools:
        try:
            for tool in mcp_tools:
                # Register each tool with the agent using the proper method
                agent.tool_plain(tool["function"])
            logger.info(f"✅ Registered {len(mcp_tools)} MCP tools with the agent")
        except Exception as e:
            logger.error(f"❌ Failed to register MCP tools with agent: {e}")
            logger.info("🔧 Agent will continue without MCP tools")
            if settings.DEBUG_MODE:
                logger.exception("Debug: Full exception during tool registration")
    
    logger.info("✅ OpenShift AI Agent initialized successfully")
    return agent

async def process_query_with_context(query: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Process a query using the OpenShift AI agent with MCP tools.
    
    Args:
        query: The user's query
        context: Additional context information (cluster info, logs, etc.)
        
    Returns:
        AI-generated response with MCP tool integration
    """
    logger.info(f"🔍 Processing query with MCP tools: {query[:100]}...")
    
    # Get the agent instance
    agent = await get_openshift_agent()
    
    # Process with the AI agent (it will use MCP tools as needed)
    try:
        logger.debug("🤖 Sending query to OpenShift AI Agent...")
        response = await agent.run(query)
        logger.info("✅ Query processed successfully")
        return response.data
    except Exception as e:
        logger.error(f"❌ Error processing query: {str(e)}")
        logger.exception("Full query error traceback:")
        return "I apologize, but I'm currently unable to process your query. Please try again later."

async def process_investigation_with_context(query: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Process an investigation query using the OpenShift AI agent with MCP tools.
    
    Args:
        query: The investigation query
        context: Additional context information (cluster info, logs, etc.)
        
    Returns:
        AI-generated investigation response with MCP tool integration
    """
    logger.info(f"🔍 Processing investigation with MCP tools: {query[:100]}...")
    
    # Get the agent instance
    agent = await get_openshift_agent()
    
    # Prepare the enhanced investigation prompt
    investigation_prompt = f"""Investigation Query: {query}

Please provide a thorough investigation and analysis. Consider multiple angles and potential root causes.
Use available tools to gather additional context if needed.

Please provide:
1. Initial assessment of the problem
2. Potential root causes
3. Detailed investigation steps
4. Recommended diagnostic commands
5. Potential solutions or mitigations
6. Prevention strategies

Context information: {context or 'No additional context provided.'}"""
    
    # Process with the AI agent
    try:
        logger.debug("🤖 Sending investigation to OpenShift AI Agent...")
        response = await agent.run(investigation_prompt)
        logger.info("✅ Investigation processed successfully")
        return response.data
    except Exception as e:
        logger.error(f"❌ Error processing investigation: {str(e)}")
        logger.exception("Full investigation error traceback:")
        return "I apologize, but I'm currently unable to process your investigation. Please try again later."

# Global agent instance
_openshift_agent = None

async def get_openshift_agent() -> Agent:
    """
    Get or create the OpenShift AI agent instance.
    
    Returns:
        The OpenShift AI agent instance
    """
    global _openshift_agent
    if _openshift_agent is None:
        _openshift_agent = await create_openshift_agent()
    return _openshift_agent 