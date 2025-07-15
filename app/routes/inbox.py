"""
Inbox route handlers for the Vibe OLS API.
Handles inbox message processing and investigation report CRUD operations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from ..models.requests import InboxRequest, InvestigationReportListRequest
from ..models.responses import (
    InboxResponse, 
    InvestigationReportListResponse,
    InvestigationReportDetail,
    InvestigationReportDeleteResponse,
    InvestigationReportSummary
)
from ..services.investigation_service import investigation_service
from ..core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/inbox", tags=["Inbox Operations"])

@router.post(
    "/", 
    response_model=InboxResponse,
    summary="Send message to inbox",
    description="Submit a message to the inbox with optional metadata",
    responses={
        200: {
            "description": "Message received and processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message_id": "msg_789",
                        "status": "received",
                        "processed": True
                    }
                }
            }
        },
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"}
    }
)
async def inbox_endpoint(request: InboxRequest):
    """
    Submit a message to the inbox for processing.
    
    - **message**: The message content to submit (required)
    - **metadata**: Optional metadata associated with the message
    
    Returns a unique message ID and processing status.
    """
    try:
        logger.info(f"📥 Processing inbox request (message length: {len(request.message)} chars)")
        logger.debug(f"Inbox message: {request.message}")
        
        if request.metadata:
            logger.info(f"📋 Inbox metadata provided: {len(request.metadata)} items")
            logger.debug(f"Inbox metadata: {request.metadata}")
        
        # Generate message ID
        message_id = f"msg_{hash(request.message) % 10000}"
        logger.info(f"📧 Generated message ID: {message_id}")
        
        # TODO: Implement actual inbox logic
        logger.info("⚙️ Processing inbox logic (placeholder)")
        
        response = InboxResponse(
            message_id=message_id,
            status="received",
            processed=True
        )
        
        logger.info(f"✅ Inbox message processed successfully: {message_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error processing inbox message: {str(e)}")
        logger.exception("Full inbox error traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/reports",
    response_model=InvestigationReportListResponse,
    summary="List investigation reports",
    description="Retrieve a list of investigation reports with optional search and pagination",
    responses={
        200: {
            "description": "List of investigation reports retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "reports": [
                            {
                                "id": "eeb5e242-c104-425b-9061-9a834e24c0f9",
                                "question": "Pod failures in production namespace",
                                "parameters": {"namespace": "production"},
                                "created_at": "2024-01-01T12:00:00Z",
                                "report_length": 5430
                            }
                        ],
                        "total": 1,
                        "limit": 50,
                        "offset": 0
                    }
                }
            }
        },
        500: {"description": "Internal Server Error"}
    }
)
async def list_investigation_reports(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of reports to return"),
    offset: int = Query(0, ge=0, description="Number of reports to skip"),
    search: Optional[str] = Query(None, description="Search term to filter by question content")
):
    """
    List investigation reports with optional search and pagination.
    
    - **limit**: Maximum number of reports to return (1-100, default: 50)
    - **offset**: Number of reports to skip (default: 0)
    - **search**: Optional search term to filter by question content
    
    Returns a list of investigation report summaries with pagination info.
    """
    try:
        logger.info(f"📋 Listing investigation reports (limit: {limit}, offset: {offset}, search: {search})")
        
        # Get reports and total count
        reports = await investigation_service.get_investigation_reports(
            limit=limit,
            offset=offset,
            search_query=search
        )
        
        total = await investigation_service.count_investigation_reports(search_query=search)
        
        # Convert to response format
        report_summaries = [
            InvestigationReportSummary(
                id=str(report.id),
                question=str(report.question),
                parameters=report.parameters_dict,
                created_at=datetime.fromisoformat(report.created_at.isoformat()) if hasattr(report.created_at, 'isoformat') else report.created_at,
                report_length=len(str(report.report_text))
            )
            for report in reports
        ]
        
        response = InvestigationReportListResponse(
            reports=report_summaries,
            total=total,
            limit=limit,
            offset=offset
        )
        
        logger.info(f"✅ Listed {len(report_summaries)} investigation reports (total: {total})")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error listing investigation reports: {str(e)}")
        logger.exception("Full listing error traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/reports/{report_id}",
    response_model=InvestigationReportDetail,
    summary="Get investigation report details",
    description="Retrieve detailed information about a specific investigation report",
    responses={
        200: {
            "description": "Investigation report details retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "eeb5e242-c104-425b-9061-9a834e24c0f9",
                        "question": "Pod failures in production namespace",
                        "parameters": {"namespace": "production", "severity": "high"},
                        "report_text": "# Investigation Report\n\n## Summary\nFound critical issues...",
                        "created_at": "2024-01-01T12:00:00Z"
                    }
                }
            }
        },
        404: {"description": "Investigation report not found"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_investigation_report(report_id: str):
    """
    Get detailed information about a specific investigation report.
    
    - **report_id**: UUID of the investigation report
    
    Returns the complete investigation report including the full report text.
    """
    try:
        logger.info(f"🔍 Getting investigation report details: {report_id}")
        
        # Get the report
        report = await investigation_service.get_investigation_report(report_id)
        
        if not report:
            logger.info(f"📭 Investigation report not found: {report_id}")
            raise HTTPException(status_code=404, detail=f"Investigation report not found: {report_id}")
        
        # Convert to response format
        response = InvestigationReportDetail(
            id=str(report.id),
            question=str(report.question),
            parameters=report.parameters_dict,
            report_text=str(report.report_text),
            created_at=report.created_at
        )
        
        logger.info(f"✅ Retrieved investigation report details: {report_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"❌ Error getting investigation report: {str(e)}")
        logger.exception("Full get error traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/reports/{report_id}",
    response_model=InvestigationReportDeleteResponse,
    summary="Delete investigation report",
    description="Delete a specific investigation report",
    responses={
        200: {
            "description": "Investigation report deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "eeb5e242-c104-425b-9061-9a834e24c0f9",
                        "status": "deleted",
                        "deleted": True
                    }
                }
            }
        },
        404: {"description": "Investigation report not found"},
        500: {"description": "Internal Server Error"}
    }
)
async def delete_investigation_report(report_id: str):
    """
    Delete a specific investigation report.
    
    - **report_id**: UUID of the investigation report to delete
    
    Returns confirmation of deletion.
    """
    try:
        logger.info(f"🗑️ Deleting investigation report: {report_id}")
        
        # Delete the report
        deleted = await investigation_service.delete_investigation_report(report_id)
        
        if not deleted:
            logger.info(f"📭 Investigation report not found for deletion: {report_id}")
            raise HTTPException(status_code=404, detail=f"Investigation report not found: {report_id}")
        
        # Return success response
        response = InvestigationReportDeleteResponse(
            id=report_id,
            status="deleted",
            deleted=True
        )
        
        logger.info(f"✅ Successfully deleted investigation report: {report_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting investigation report: {str(e)}")
        logger.exception("Full delete error traceback:")
        raise HTTPException(status_code=500, detail=str(e)) 