"""
Investigation route handlers for the Vibe OLS API.
Handles investigation requests with optional parameters.
"""

from fastapi import APIRouter, HTTPException

from ..models.requests import InvestigateRequest
from ..models.responses import InvestigateResponse
from ..agents.investigation_agent import conduct_investigation
from ..core.logging import get_logger
from ..utils.helpers import generate_id

logger = get_logger(__name__)

router = APIRouter(prefix="/investigate", tags=["Investigation Operations"])

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