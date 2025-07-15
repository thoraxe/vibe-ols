"""
Investigation route handlers for the Vibe OLS API.
Handles investigation requests with optional parameters.
"""

import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..models.requests import InvestigateRequest
from ..models.responses import InvestigateResponse
from ..agents.investigation_agent import conduct_investigation, conduct_investigation_stream
from ..core.logging import get_logger
from ..utils.helpers import generate_id
from ..services.investigation_service import investigation_service

logger = get_logger(__name__)

router = APIRouter(prefix="/investigate", tags=["Investigation Operations"])

# TODO: investigating may take a long time, so this endpoint should return immediately
#       an acknowledgement that the investigation has started and return the unique ID.
#       The rest of the investigation should be done in the background.
@router.post(
    "/", 
    response_model=InvestigateResponse,
    summary="Start an investigation",
    description="Submit a topic for investigation with optional parameters",
    responses={
        200: {
            "description": "Investigation completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "findings": "Found 3 high-severity vulnerabilities requiring immediate attention",
                        "status": "success",
                        "investigation_id": "inv_456"
                    }
                }
            }
        },
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"}
    }
)
async def investigate_endpoint(request: InvestigateRequest):
    """
    Start an investigation on a specified topic.
    
    - **topic**: The topic to investigate (required)
    - **parameters**: Optional parameters to guide the investigation
    
    Returns investigation findings along with a unique investigation ID.
    """
    try:
        logger.info(f"🔍 Processing investigation request for topic: {request.topic}")
        logger.debug(f"Investigation topic: {request.topic}")
        
        if request.parameters:
            logger.info(f"📋 Investigation parameters provided: {len(request.parameters)} items")
            logger.debug(f"Investigation parameters: {request.parameters}")
        
        # Generate investigation ID
        investigation_id = generate_id(request.topic, "inv")
        logger.info(f"🔍 Generated investigation ID: {investigation_id}")
        
        # Process investigation with specialized investigation agent
        logger.info("🤖 Processing investigation with OpenShift Investigation Agent...")
        findings = await conduct_investigation(request.topic, request.parameters)
        
        # Store the investigation report in the database
        try:
            stored_report = await investigation_service.store_investigation_report(
                question=request.topic,
                parameters=request.parameters,
                report_text=findings,
                investigation_id=investigation_id
            )
            logger.info(f"💾 Investigation report stored in database: {stored_report.id}")
        except Exception as e:
            logger.error(f"❌ Failed to store investigation report: {str(e)}")
            # Continue with response even if database storage fails
        
        response = InvestigateResponse(
            findings=findings,
            status="success",
            investigation_id=investigation_id
        )
        
        logger.info(f"✅ Investigation completed successfully: {investigation_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error processing investigation: {str(e)}")
        logger.exception("Full investigation error traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/stream",
    summary="Start an investigation with streaming response",
    description="Submit a topic for investigation with real-time streaming response",
    responses={
        200: {
            "description": "Streaming investigation response",
            "content": {
                "text/plain": {
                    "example": "data: {\"type\": \"token\", \"content\": \"# Investigation Report\"}\n\ndata: {\"type\": \"token\", \"content\": \" Analysis shows...\"}\n\n..."
                }
            }
        },
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"}
    }
)
async def investigate_stream_endpoint(request: InvestigateRequest):
    """
    Start an investigation with streaming response for real-time updates.
    
    - **topic**: The topic to investigate (required)
    - **parameters**: Optional parameters to guide the investigation
    
    Returns a streaming response with real-time investigation progress.
    """
    try:
        logger.info(f"🌊 Processing streaming investigation request for topic: {request.topic}")
        logger.debug(f"Streaming investigation topic: {request.topic}")
        
        if request.parameters:
            logger.info(f"📋 Investigation parameters provided for streaming: {len(request.parameters)} items")
            logger.debug(f"Streaming investigation parameters: {request.parameters}")
        
        # Generate investigation ID
        investigation_id = generate_id(request.topic, "inv")
        logger.info(f"🔍 Generated streaming investigation ID: {investigation_id}")
        
        async def generate_stream() -> AsyncGenerator[str, None]:
            try:
                logger.info(f"🚀 Starting real-time stream generation for investigation: {investigation_id}")
                
                # Send initial message with investigation ID
                yield f"data: {json.dumps({'type': 'start', 'investigation_id': investigation_id})}\n\n"
                
                # Use real-time streaming investigation
                logger.info("🤖 Starting real-time investigation streaming from OpenShift Investigation Agent...")
                
                # Accumulate the complete report for database storage
                complete_report = ""
                
                async for content_chunk in conduct_investigation_stream(request.topic, request.parameters):
                    # Stream each content chunk as it becomes available
                    if content_chunk:
                        complete_report += content_chunk
                        yield f"data: {json.dumps({'type': 'token', 'content': content_chunk})}\n\n"
                        await asyncio.sleep(0.01)  # Small delay to prevent overwhelming the client
                
                # Store the complete investigation report in the database
                try:
                    stored_report = await investigation_service.store_investigation_report(
                        question=request.topic,
                        parameters=request.parameters,
                        report_text=complete_report,
                        investigation_id=investigation_id
                    )
                    logger.info(f"💾 Streaming investigation report stored in database: {stored_report.id}")
                except Exception as e:
                    logger.error(f"❌ Failed to store streaming investigation report: {str(e)}")
                    # Continue with response even if database storage fails
                
                # Send completion message
                yield f"data: {json.dumps({'type': 'done', 'investigation_id': investigation_id})}\n\n"
                logger.info(f"🎯 Real-time investigation streaming completed successfully for: {investigation_id}")
                
            except Exception as e:
                logger.error(f"❌ Error in real-time investigation stream generation: {str(e)}")
                logger.exception("Full real-time investigation streaming error traceback:")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        logger.info(f"🌊 Initiating streaming investigation response for: {investigation_id}")
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
        logger.error(f"❌ Error processing streaming investigation: {str(e)}")
        logger.exception("Full streaming investigation error traceback:")
        raise HTTPException(status_code=500, detail=f"Error processing streaming investigation: {str(e)}") 