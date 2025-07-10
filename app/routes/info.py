"""
Info route handlers for the Vibe OLS API.
Provides API information and health status.
"""

from fastapi import APIRouter

from ..core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["API Information"])

@router.get(
    "/",
    summary="API Information",
    description="Get basic information about the API and available endpoints",
    responses={
        200: {
            "description": "API information retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Vibe OLS API",
                        "version": "1.0.0",
                        "endpoints": ["/query", "/query/stream", "/investigate", "/inbox"],
                        "docs_url": "/docs",
                        "redoc_url": "/redoc"
                    }
                }
            }
        }
    }
)
async def root():
    """
    Get API information and available endpoints.
    
    Returns basic information about the API including version and available endpoints.
    """
    logger.info("ℹ️ API information requested")
    
    api_info = {
        "message": "Vibe OLS API",
        "version": "1.0.0",
        "endpoints": ["/query", "/query/stream", "/investigate", "/inbox"],
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
    
    logger.debug(f"Returning API info: {api_info}")
    return api_info 