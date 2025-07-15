"""
Query route handlers for the Vibe OLS API.
Handles AI-powered OpenShift troubleshooting queries.
"""

import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..models.requests import QueryRequest
from ..models.responses import QueryResponse
from ..agents.openshift_agent import process_query_with_context
from ..core.logging import get_logger
from ..utils.helpers import generate_id, prepare_prompt_with_context

logger = get_logger(__name__)

router = APIRouter(prefix="/query", tags=["Query Operations"])

@router.post(
    "/", 
    response_model=QueryResponse,
    summary="Process a query",
    description="Submit a query for processing with optional context information",
    responses={
        200: {
            "description": "Query processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "result": "To troubleshoot CrashLoopBackOff pods...",
                        "status": "success",
                        "query_id": "query_a1b2c3d4"
                    }
                }
            }
        },
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"}
    }
)
async def query_endpoint(request: QueryRequest):
    """
    Process a query request with optional context using OpenShift AI agent.
    
    - **query**: The query text to process (required)
    - **context**: Optional context information as key-value pairs
    
    Returns the processed result along with a unique query ID.
    """
    try:
        logger.info(f"📝 Processing query request (length: {len(request.query)} chars)")
        logger.debug(f"Query text: {request.query}")
        
        # Prepare the full prompt with context if provided
        full_prompt = prepare_prompt_with_context(request.query, request.context)
        if request.context:
            logger.info(f"📋 Context provided: {len(request.context)} items")
            logger.debug(f"Context details: {request.context}")
        
        # Generate a simple query ID
        query_id = generate_id(request.query, "query")
        logger.info(f"🔍 Generated query ID: {query_id}")
        
        # Use Pydantic AI agent to process the query with MCP context
        logger.info("🤖 Sending query to OpenShift AI agent with MCP context...")
        result = await process_query_with_context(request.query, request.context)
        logger.info(f"✅ AI agent response received (length: {len(result)} chars)")
        logger.debug(f"AI response preview: {result[:200]}...")
        
        response = QueryResponse(
            result=result,
            status="success",
            query_id=query_id
        )
        
        logger.info(f"🎯 Query processed successfully: {query_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error processing query: {str(e)}")
        logger.exception("Full error traceback:")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.post(
    "/stream",
    summary="Process a query with streaming response",
    description="Submit a query for processing with real-time streaming response",
    responses={
        200: {
            "description": "Streaming query response",
            "content": {
                "text/plain": {
                    "example": "data: {\"type\": \"token\", \"content\": \"To troubleshoot\"}\n\ndata: {\"type\": \"token\", \"content\": \" CrashLoopBackOff\"}\n\n..."
                }
            }
        },
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"}
    }
)
async def query_stream_endpoint(request: QueryRequest):
    """
    Process a query request with streaming response for real-time AI interaction.
    
    - **query**: The query text to process (required)
    - **context**: Optional context information as key-value pairs
    
    Returns a streaming response with real-time AI generation.
    """
    try:
        logger.info(f"🌊 Processing streaming query request (length: {len(request.query)} chars)")
        logger.debug(f"Streaming query text: {request.query}")
        
        # Prepare the full prompt with context if provided
        full_prompt = prepare_prompt_with_context(request.query, request.context)
        if request.context:
            logger.info(f"📋 Context provided for streaming: {len(request.context)} items")
            logger.debug(f"Streaming context details: {request.context}")
        
        # Generate a query ID
        query_id = generate_id(request.query, "query")
        logger.info(f"🔍 Generated streaming query ID: {query_id}")
        
        async def generate_stream() -> AsyncGenerator[str, None]:
            try:
                logger.info(f"🚀 Starting stream generation for query: {query_id}")
                
                # Send initial message with query ID
                yield f"data: {json.dumps({'type': 'start', 'query_id': query_id})}\n\n"
                
                # TODO: this is broken. we should not be waiting for the full response and then simulating
                # streaming. we should be streaming the response as it is generated.

                # Get the full response first, then simulate streaming
                logger.info("🤖 Getting response from OpenShift AI agent for streaming...")
                response_text = await process_query_with_context(request.query, request.context)
                logger.info(f"✅ AI response received for streaming (length: {len(response_text)} chars)")
                
                # Simulate streaming by sending chunks of the response
                words = response_text.split()
                logger.info(f"🔄 Streaming {len(words)} words for query: {query_id}")
                
                for i, word in enumerate(words):
                    if i == 0:
                        yield f"data: {json.dumps({'type': 'token', 'content': word})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'token', 'content': ' ' + word})}\n\n"
                    await asyncio.sleep(0.05)  # Small delay to simulate streaming
                    
                    # Log progress every 50 words
                    if (i + 1) % 50 == 0:
                        logger.debug(f"📊 Streaming progress: {i + 1}/{len(words)} words")
                
                # Send completion message
                yield f"data: {json.dumps({'type': 'done', 'query_id': query_id})}\n\n"
                logger.info(f"🎯 Streaming completed successfully for query: {query_id}")
                
            except Exception as e:
                logger.error(f"❌ Error in stream generation: {str(e)}")
                logger.exception("Full streaming error traceback:")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        logger.info(f"🌊 Initiating streaming response for query: {query_id}")
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing streaming query: {str(e)}")
        logger.exception("Full streaming error traceback:")
        raise HTTPException(status_code=500, detail=f"Error processing streaming query: {str(e)}") 