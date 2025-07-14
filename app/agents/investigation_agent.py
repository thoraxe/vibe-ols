"""
OpenShift Investigation Agent for systematic troubleshooting.
Provides structured investigation with streaming execution and comprehensive reporting.
"""

from pydantic_ai import Agent, RunContext
from pydantic_ai.models import KnownModelName
from pydantic_ai.mcp import MCPServerStreamableHTTP
from typing import Dict, Any, Optional, List, Tuple, AsyncIterator
import asyncio
from ..core.config import settings
from ..core.logging import get_logger
from ..utils.helpers import create_mcp_log_handler

logger = get_logger(__name__)

class InvestigationContext:
    """Context object to track investigation state across streaming execution."""
    
    def __init__(self, initial_request: str):
        self.initial_request = initial_request
        self.tool_calls: List[Dict[str, Any]] = []
        self.llm_responses: List[str] = []
        self.completed = False
        self.summary_reason: Optional[str] = None
        self.full_output: List[str] = []
    
    def add_tool_call(self, tool_name: str, args: Dict[str, Any], result: Any = None):
        """Add a tool call record."""
        self.tool_calls.append({
            "tool_name": tool_name,
            "args": args,
            "result": result,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def add_llm_response(self, content: str):
        """Add LLM response content."""
        self.llm_responses.append(content)
        self.full_output.append(content)
    
    def mark_completed(self, reason: Optional[str] = None):
        """Mark investigation as completed."""
        self.completed = True
        self.summary_reason = reason
    
    def get_full_output(self) -> str:
        """Get the complete investigation output."""
        return "\n".join(self.full_output)

async def create_investigation_agent() -> Agent:
    """
    Create and configure the OpenShift Investigation AI agent with MCP tools.
    
    Returns:
        Configured Pydantic AI agent for OpenShift investigation
    """
    logger.info("🔍 Initializing OpenShift Investigation Agent...")
    
    # Create MCP server instances from configuration
    mcp_servers = []
    if settings.is_mcp_configured:
        logger.info("🔧 Setting up MCP servers for investigation agent...")
        
        server_configs = settings.mcp_servers_dict
        for server_name, endpoint in server_configs.items():
            try:
                # Create MCPServerStreamableHTTP instance with debug configuration
                server = MCPServerStreamableHTTP(
                    endpoint,
                    tool_prefix=server_name,  # Prefix tools with server name for identification
                    log_handler=create_mcp_log_handler(server_name),  # Custom log handler
                    timeout=10,  # Increased timeout for better debugging
                )
                mcp_servers.append(server)
                logger.info(f"✅ Added MCP server: {server_name} ({endpoint}) with debug logging")
            except Exception as e:
                logger.warning(f"⚠️ Failed to create MCP server {server_name} ({endpoint}): {e}")
                
        if mcp_servers:
            logger.info(f"✅ Configured {len(mcp_servers)} MCP servers for investigation agent")
        else:
            logger.info("ℹ️ No MCP servers successfully configured for investigation agent")
    else:
        logger.info("ℹ️ No MCP servers configured for investigation agent")
    
    # Create the investigation system prompt
    system_prompt = """You are an expert OpenShift troubleshooting agent. Your
primary function is to investigate OpenShift failures and produce
comprehensive diagnostic reports.

## Core Responsibilities

1. **Plan Development**: Always create a structured investigation plan before executing any tools
2. **Systematic Investigation**: Use available tools to gather relevant data from the OpenShift environment
3. **Comprehensive Reporting**: Generate detailed markdown reports with findings and recommendations

## Investigation Workflow

### Phase 1: Planning
- Analyze the investigation request to understand the scope and nature of the issue
- Identify what information you need to gather
- Create a step-by-step investigation plan listing:
  - Specific areas to investigate (namespaces, pods, services, etc.)
  - Tools you'll use and in what order
  - Expected outcomes from each step

### Phase 2: Execution
- Execute your plan systematically using available tools
- Gather data from OpenShift APIs through your tool set
- Adapt your approach based on findings (you may discover new areas to investigate)
- Document all tool outputs and observations

### Phase 3: Analysis & Reporting
- Synthesize findings into actionable insights
- Identify root causes where possible
- Provide specific remediation recommendations

## Available Tools
You have access to dynamically determined tools that interact with OpenShift APIs. These may include:
- Listing and describing pods, services, deployments, etc.
- Checking resource status and events
- Examining logs and configurations
- Querying cluster-level information

## Report Structure

Generate your final report in markdown format with these sections:

### Investigation Summary
- **Request**: Restate the original investigation request
- **Scope**: Define what was investigated
- **Key Findings**: High-level summary of discoveries

### Investigation Plan
- **Objective**: What you set out to investigate
- **Approach**: Step-by-step plan you developed
- **Tools Selected**: Which tools you planned to use and why

### Execution Details
- **Step-by-Step Findings**: Document each investigation step with:
  - Tool used
  - Command/query executed
  - Output received
  - Observations and insights
- **Unexpected Discoveries**: Any issues found beyond the original scope

### Analysis & Recommendations
- **Root Cause Analysis**: Your assessment of what caused the issue
- **Impact Assessment**: How this affects the OpenShift environment
- **Remediation Steps**: Specific, actionable recommendations ordered by priority
- **Prevention Measures**: Suggestions to avoid similar issues

### Supporting Data
- **Tool Outputs**: Relevant raw data from your investigation
- **Additional Context**: Any other pertinent information discovered

## Guidelines

- **Be Systematic**: Follow your plan but remain flexible to adapt based on findings
- **Be Thorough**: Don't stop at the first sign of an issue; investigate comprehensively
- **Be Precise**: Use exact resource names, namespaces, and technical details
- **Be Practical**: Focus on actionable insights that stakeholders can implement
- **Be Clear**: Write for knowledgeable OpenShift users who can act on your recommendations

## Error Handling
- If a tool fails, document the failure and try alternative approaches
- If you encounter access limitations, note them and work within available scope
- Always explain what you couldn't investigate and why

Remember: Your stakeholders are technically capable and expect detailed,
actionable intelligence to resolve OpenShift issues efficiently.
"""
    
    # Add MCP tool information to system prompt if available
    if mcp_servers:
        system_prompt += f"""

## Tools
Use available OpenShift tools strategically. Document tool calls and results. If a tool fails, try alternatives."""
    
    model_name: KnownModelName = "openai:gpt-4o-mini"
    if settings.OPENAI_MODEL:
        model_name = settings.OPENAI_MODEL  # type: ignore
    
    agent = Agent(
        model_name,
        system_prompt=system_prompt,
        mcp_servers=mcp_servers
    )
    
    logger.info("✅ OpenShift Investigation Agent initialized successfully")
    return agent

async def conduct_investigation(
    request: str, 
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Conduct a comprehensive investigation using the investigation agent with streaming output.
    
    Args:
        request: The investigation request
        context: Additional context information
        
    Returns:
        Comprehensive investigation report
    """
    logger.info(f"🔍 Starting investigation: {request[:100]}...")
    
    # Create investigation context
    investigation_context = InvestigationContext(request)
    
    # Get the investigation agent
    agent = await get_investigation_agent()
    
    # Prepare the investigation prompt
    investigation_prompt = f"""Investigation Request: {request}

Please conduct a systematic investigation of this issue. Follow these guidelines:

1. **Start with a clear plan**: Outline your investigation steps
2. **Execute step by step**: Work through your plan systematically
3. **Use tools actively**: Gather real data from the OpenShift environment
4. **Report as you go**: Provide updates after each major step
5. **Be thorough**: Don't stop at the first finding - investigate comprehensively

Additional context: {context if context else 'No additional context provided.'}

Begin your investigation now."""
    
    try:
        # Run the investigation with streaming using Agent.iter
        logger.info("🚀 Starting streaming investigation with Agent.iter...")
        async with agent.run_mcp_servers():
            result = await _run_streaming_investigation(agent, investigation_context, investigation_prompt)
        
        logger.info(f"✅ Investigation completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error during investigation: {str(e)}")
        logger.exception("Full investigation error traceback:")
        return f"Investigation failed due to an error: {str(e)}"

async def conduct_investigation_stream(
    request: str, 
    context: Optional[Dict[str, Any]] = None
) -> AsyncIterator[str]:
    """
    Conduct a comprehensive investigation with real-time streaming output.
    
    Args:
        request: The investigation request
        context: Additional context information
        
    Yields:
        Investigation content as it becomes available
    """
    logger.info(f"🌊 Starting streaming investigation: {request[:100]}...")
    
    # Create investigation context
    investigation_context = InvestigationContext(request)
    
    # Get the investigation agent
    agent = await get_investigation_agent()
    
    # Prepare the investigation prompt
    investigation_prompt = f"""Investigation Request: {request}

Please conduct a systematic investigation of this issue. Follow these guidelines:

1. **Start with a clear plan**: Outline your investigation steps
2. **Execute step by step**: Work through your plan systematically
3. **Use tools actively**: Gather real data from the OpenShift environment
4. **Report as you go**: Provide updates after each major step
5. **Be thorough**: Don't stop at the first finding - investigate comprehensively

Additional context: {context if context else 'No additional context provided.'}

Begin your investigation now."""
    
    try:
        # Run the investigation with real streaming using Agent.iter
        logger.info("🚀 Starting real-time streaming investigation with Agent.iter...")
        async with agent.run_mcp_servers():
            async for content_chunk in _run_real_streaming_investigation(agent, investigation_context, investigation_prompt):
                yield content_chunk
        
        logger.info(f"✅ Streaming investigation completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during streaming investigation: {str(e)}")
        logger.exception("Full streaming investigation error traceback:")
        error_message = f"Investigation failed due to an error: {str(e)}"
        yield error_message

async def _run_streaming_investigation(
    agent: Agent,
    context: InvestigationContext,
    prompt: str
) -> str:
    """
    Run the investigation with streaming output using Agent.iter.
    
    Args:
        agent: The investigation agent
        context: Investigation context
        prompt: Investigation prompt
        
    Returns:
        Complete investigation results
    """
    logger.info("🔄 Starting streaming investigation execution with Agent.iter...")
    
    try:
        # Use Agent.iter to get streaming output and accumulate results
        logger.info("📡 Starting agent iteration for streaming investigation...")
        
        # Accumulate streaming content
        streaming_content = []
        tool_call_count = 0
        llm_response_count = 0
        
        async with agent.iter(prompt) as agent_run:
            async for event in agent_run:
                # Log the event type for debugging
                event_type = type(event).__name__
                logger.info(f"📨 Received event: {event_type}")
                
                # Log the event content for debugging
                event_str = str(event)
                logger.debug(f"📋 Event details: {event_str[:300]}...")
                
                # Extract content from different event types
                if event_type == "UserPromptNode":
                    # Initial user prompt - skip for final output
                    continue
                    
                elif event_type == "ModelRequestNode":
                    # LLM request - may contain tool calls and results
                    llm_response_count += 1
                    logger.info(f"🧠 LLM Request #{llm_response_count}")
                    
                    # Extract tool calls from ModelRequestNode
                    try:
                        if hasattr(event, 'request'):
                            request = getattr(event, 'request', None)
                            if request and hasattr(request, 'parts'):
                                for part in request.parts:
                                    # Check for ToolReturnPart (tool results)
                                    if hasattr(part, 'tool_name'):
                                        tool_name = part.tool_name
                                        tool_call_count += 1
                                        logger.info(f"🔧 Tool Call #{tool_call_count}: {tool_name}")
                                        
                                        # Extract tool result content
                                        tool_result = getattr(part, 'content', '')
                                        logger.debug(f"📋 Tool Result: {tool_result[:200]}...")
                                        context.add_tool_call(tool_name, {}, tool_result)
                    except Exception as e:
                        logger.debug(f"⚠️ Error extracting tool calls from ModelRequestNode: {e}")
                    
                elif event_type == "CallToolsNode":
                    # Tool calls and LLM responses - extract content using safe attribute access
                    try:
                        # Extract model response content from CallToolsNode
                        if hasattr(event, 'model_response'):
                            model_response = getattr(event, 'model_response', None)
                            if model_response and hasattr(model_response, 'parts'):
                                for part in model_response.parts:
                                    # Check for TextPart content (LLM responses)
                                    if hasattr(part, 'content') and part.content:
                                        content = part.content
                                        logger.info(f"💬 LLM Response: {content[:100]}...")
                                        streaming_content.append(content)
                                        context.add_llm_response(content)
                                        
                                    # Check for ToolCallPart (tool calls)
                                    elif hasattr(part, 'tool_name'):
                                        tool_name = part.tool_name
                                        tool_call_count += 1
                                        logger.info(f"🔧 Tool Call #{tool_call_count}: {tool_name}")
                                        
                                        # Extract tool arguments if available
                                        tool_args = {}
                                        if hasattr(part, 'args'):
                                            tool_args = part.args
                                        elif hasattr(part, 'tool_call'):
                                            tool_call = part.tool_call
                                            if hasattr(tool_call, 'args'):
                                                tool_args = tool_call.args
                                        
                                        logger.debug(f"📋 Tool Args: {tool_args}")
                                        context.add_tool_call(tool_name, tool_args)
                                        
                                    # Check for ToolReturnPart (tool results)
                                    elif hasattr(part, 'tool_call_id'):
                                        tool_call_count += 1
                                        tool_name = getattr(part, 'tool_name', 'unknown_tool')
                                        logger.info(f"🔧 Tool Call #{tool_call_count}: {tool_name}")
                                        
                                        # Extract tool result content
                                        tool_result = getattr(part, 'content', '')
                                        logger.debug(f"📋 Tool Result: {tool_result}")
                                        context.add_tool_call(tool_name, {}, tool_result)
                        
                        # Fallback: extract content from string representation
                        if not streaming_content or "content" in event_str:
                            # Look for content in the string representation
                            if "TextPart(content=" in event_str:
                                logger.info(f"💬 LLM Response (from string): {event_str[:100]}...")
                                # Don't add to streaming_content to avoid duplicates
                                # streaming_content.append(event_str)
                                # context.add_llm_response(event_str)
                            
                    except Exception as e:
                        logger.debug(f"⚠️ Error extracting from CallToolsNode: {e}")
                        # Fallback: just log the event
                        logger.info(f"🔧 Tool/LLM Event: {event_str[:100]}...")
                                    
                elif event_type == "End":
                    # Final result - this should contain the complete output
                    logger.info("✅ Investigation completed - processing final result")
                    try:
                        # Try to extract data from End event
                        if hasattr(event, 'data'):
                            final_data = getattr(event, 'data', None)
                            if final_data:
                                if hasattr(final_data, 'output'):
                                    final_output = final_data.output
                                    logger.info(f"📄 Final output: {final_output[:200]}...")
                                    streaming_content.append(final_output)
                                    context.add_llm_response(final_output)
                                elif hasattr(final_data, 'value'):
                                    final_value = getattr(final_data, 'value', None)
                                    if final_value:
                                        logger.info(f"📄 Final value: {str(final_value)[:200]}...")
                                        streaming_content.append(str(final_value))
                                        context.add_llm_response(str(final_value))
                    except Exception as e:
                        logger.debug(f"⚠️ Error extracting from End event: {e}")
                        logger.info("✅ Investigation completed (no extractable output)")
                
                # Store the event for debugging
                context.full_output.append(f"[{event_type}] {event_str[:200]}...")
        
        # Build the complete report from streaming content
        complete_report = "\n".join(streaming_content) if streaming_content else ""
        
        # If we don't have streaming content, try to get the final result
        if not complete_report:
            logger.warning("⚠️ No streaming content captured, attempting to get final result...")
            try:
                # Try to get the result from the agent run
                if hasattr(agent_run, 'result'):
                    final_result = agent_run.result
                    if final_result and hasattr(final_result, 'output'):
                        complete_report = final_result.output
                        logger.info(f"📄 Retrieved final result: {complete_report[:200]}...")
                    elif final_result:
                        complete_report = str(final_result)
                        logger.info(f"📄 Retrieved final result (str): {complete_report[:200]}...")
                    else:
                        logger.warning("⚠️ Final result is None")
                        complete_report = "Investigation completed but no output captured."
                else:
                    logger.warning("⚠️ No result property found on agent_run")
                    complete_report = "Investigation completed but no output captured."
            except Exception as e:
                logger.error(f"❌ Failed to get final result: {e}")
                complete_report = "Investigation completed but no output captured."
        
        # Mark investigation as completed
        context.mark_completed("Investigation completed successfully")
        
        # Log final statistics
        logger.info(f"📊 Investigation completed:")
        logger.info(f"  - Total tool calls: {tool_call_count}")
        logger.info(f"  - Total LLM responses: {llm_response_count}")
        logger.info(f"  - Streaming content blocks: {len(streaming_content)}")
        logger.info(f"  - Final output length: {len(complete_report)} characters")
        
        return complete_report
        
    except Exception as e:
        logger.error(f"❌ Error in streaming investigation: {str(e)}")
        logger.exception("Streaming investigation error traceback:")
        
        # Return error information
        error_report = f"""# Investigation Error

## Request
{context.initial_request}

## Error Details
An error occurred during the investigation: {str(e)}

## Tool Calls Made
{len(context.tool_calls)} tool calls were made before the error occurred.

## Troubleshooting Steps
1. Check that MCP servers are running and accessible
2. Verify OpenShift cluster connectivity
3. Review application logs for more details
4. Try the investigation again with a more specific scope

## Raw Error
```
{str(e)}
```
"""
        return error_report

async def _run_real_streaming_investigation(
    agent: Agent,
    context: InvestigationContext,
    prompt: str
) -> AsyncIterator[str]:
    """
    Run the investigation with real-time streaming output using Agent.iter.
    
    Args:
        agent: The investigation agent
        context: Investigation context
        prompt: Investigation prompt
        
    Yields:
        Investigation content as it becomes available
    """
    logger.info("🔄 Starting real-time streaming investigation execution with Agent.iter...")
    
    try:
        # Use Agent.iter to get real-time streaming output
        logger.info("📡 Starting agent iteration for real-time streaming investigation...")
        
        # Track streaming state
        tool_call_count = 0
        llm_response_count = 0
        
        async with agent.iter(prompt) as agent_run:
            async for event in agent_run:
                # Log the event type for debugging
                event_type = type(event).__name__
                logger.debug(f"📨 Received streaming event: {event_type}")
                
                # Extract and yield content from different event types
                if event_type == "UserPromptNode":
                    # Initial user prompt - skip for streaming output
                    continue
                    
                elif event_type == "ModelRequestNode":
                    # LLM request - may contain tool calls and results
                    llm_response_count += 1
                    logger.debug(f"🧠 LLM Request #{llm_response_count}")
                    
                elif event_type == "CallToolsNode":
                    # Tool calls and LLM responses - extract and yield content
                    try:
                        # Extract model response content from CallToolsNode
                        if hasattr(event, 'model_response'):
                            model_response = getattr(event, 'model_response', None)
                            if model_response and hasattr(model_response, 'parts'):
                                for part in model_response.parts:
                                    # Check for TextPart content (LLM responses)
                                    if hasattr(part, 'content') and part.content:
                                        content = part.content
                                        logger.debug(f"💬 Streaming LLM Response: {content[:100]}...")
                                        context.add_llm_response(content)
                                        yield content
                                        
                                    # Check for ToolCallPart (tool calls)
                                    elif hasattr(part, 'tool_name'):
                                        tool_name = part.tool_name
                                        tool_call_count += 1
                                        logger.debug(f"🔧 Tool Call #{tool_call_count}: {tool_name}")
                                        
                                        # Extract tool arguments if available
                                        tool_args = {}
                                        if hasattr(part, 'args'):
                                            tool_args = part.args
                                        elif hasattr(part, 'tool_call'):
                                            tool_call = part.tool_call
                                            if hasattr(tool_call, 'args'):
                                                tool_args = tool_call.args
                                        
                                        context.add_tool_call(tool_name, tool_args)
                                        
                                        # Yield tool call information
                                        tool_info = f"\n🔧 **Using tool: {tool_name}**\n"
                                        yield tool_info
                                        
                                    # Check for ToolReturnPart (tool results)
                                    elif hasattr(part, 'tool_call_id'):
                                        tool_call_count += 1
                                        tool_name = getattr(part, 'tool_name', 'unknown_tool')
                                        logger.debug(f"🔧 Tool Result #{tool_call_count}: {tool_name}")
                                        
                                        # Extract tool result content
                                        tool_result = getattr(part, 'content', '')
                                        context.add_tool_call(tool_name, {}, tool_result)
                                        
                                        # Yield tool result summary (don't yield full result to avoid overwhelming)
                                        tool_summary = f"✅ **Tool {tool_name} completed**\n"
                                        yield tool_summary
                        
                    except Exception as e:
                        logger.debug(f"⚠️ Error extracting from CallToolsNode: {e}")
                                    
                elif event_type == "End":
                    # Final result - this should contain the complete output
                    logger.debug("✅ Investigation completed - processing final result")
                    try:
                        # Try to extract data from End event
                        if hasattr(event, 'data'):
                            final_data = getattr(event, 'data', None)
                            if final_data:
                                if hasattr(final_data, 'output'):
                                    final_output = final_data.output
                                    logger.debug(f"📄 Final output: {final_output[:200]}...")
                                    context.add_llm_response(final_output)
                                    yield final_output
                                elif hasattr(final_data, 'value'):
                                    final_value = getattr(final_data, 'value', None)
                                    if final_value:
                                        logger.debug(f"📄 Final value: {str(final_value)[:200]}...")
                                        context.add_llm_response(str(final_value))
                                        yield str(final_value)
                    except Exception as e:
                        logger.debug(f"⚠️ Error extracting from End event: {e}")
                        logger.debug("✅ Investigation completed (no extractable output)")
                
                # Store the event for debugging
                context.full_output.append(f"[{event_type}] {str(event)[:200]}...")
        
        # Mark investigation as completed
        context.mark_completed("Real-time streaming investigation completed successfully")
        
        # Log final statistics
        logger.info(f"📊 Real-time streaming investigation completed:")
        logger.info(f"  - Total tool calls: {tool_call_count}")
        logger.info(f"  - Total LLM responses: {llm_response_count}")
        
    except Exception as e:
        logger.error(f"❌ Error in real-time streaming investigation: {str(e)}")
        logger.exception("Real-time streaming investigation error traceback:")
        
        # Yield error information
        error_message = f"\n❌ **Investigation Error:** {str(e)}\n"
        yield error_message

async def get_investigation_agent() -> Agent:
    """
    Get a cached investigation agent instance.
    
    Returns:
        Cached investigation agent
    """
    # For now, create a new agent each time
    # In the future, we might want to cache this
    return await create_investigation_agent()

# Enhanced logging functions for better debugging
def log_tool_call(tool_name: str, args: Dict[str, Any]):
    """Log when a tool is called."""
    logger.info(f"🔧 Calling tool: {tool_name}")
    logger.debug(f"📋 Tool args: {args}")

def log_tool_response(tool_name: str, response: Any):
    """Log tool response."""
    logger.info(f"✅ Tool {tool_name} completed")
    logger.debug(f"📄 Tool response: {str(response)[:500]}...")

def log_investigation_step(step_name: str, details: str):
    """Log investigation step."""
    logger.info(f"📍 Investigation step: {step_name}")
    logger.debug(f"📝 Step details: {details}")

def log_llm_response(response: str):
    """Log LLM response."""
    logger.info(f"💬 LLM Response: {response[:100]}...")
    logger.debug(f"📝 Full LLM Response: {response}") 