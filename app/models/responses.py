"""
Pydantic response models for the Vibe OLS API.
Defines the structure for outgoing response data.
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class QueryResponse(BaseModel):
    """Response model for query endpoints."""
    result: str
    status: str
    query_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "result": "To troubleshoot CrashLoopBackOff pods:\n\n1. Check pod logs: `oc logs <pod-name> -n my-app`\n2. Describe the pod: `oc describe pod <pod-name> -n my-app`\n3. Check events: `oc get events -n my-app --sort-by='.lastTimestamp'`\n4. Verify resource limits and requests\n5. Check for image pull issues or configuration errors",
                "status": "success",
                "query_id": "query_a1b2c3d4"
            }
        }

class InvestigateResponse(BaseModel):
    """Response model for investigation endpoint."""
    findings: str
    status: str
    investigation_id: str
    
    class Config:
        schema_extra = {
            "example": {
                "findings": "Found 3 high-severity vulnerabilities requiring immediate attention",
                "status": "success",
                "investigation_id": "inv_456"
            }
        }

class InboxResponse(BaseModel):
    """Response model for inbox endpoint."""
    message_id: str
    status: str
    processed: bool
    
    class Config:
        schema_extra = {
            "example": {
                "message_id": "msg_789",
                "status": "received",
                "processed": True
            }
        }

class InvestigationReportSummary(BaseModel):
    """Summary model for investigation report in lists."""
    id: str
    question: str
    parameters: Dict[str, Any]
    created_at: datetime
    report_length: int
    
    class Config:
        schema_extra = {
            "example": {
                "id": "eeb5e242-c104-425b-9061-9a834e24c0f9",
                "question": "Pod failures in production namespace",
                "parameters": {"namespace": "production", "severity": "high"},
                "created_at": "2024-01-01T12:00:00Z",
                "report_length": 5430
            }
        }

class InvestigationReportDetail(BaseModel):
    """Detailed model for investigation report."""
    id: str
    question: str
    parameters: Dict[str, Any]
    report_text: str
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "eeb5e242-c104-425b-9061-9a834e24c0f9",
                "question": "Pod failures in production namespace",
                "parameters": {"namespace": "production", "severity": "high"},
                "report_text": "# Investigation Report\n\n## Summary\nFound critical issues...",
                "created_at": "2024-01-01T12:00:00Z"
            }
        }

class InvestigationReportListResponse(BaseModel):
    """Response model for listing investigation reports."""
    reports: List[InvestigationReportSummary]
    total: int
    limit: int
    offset: int
    
    class Config:
        schema_extra = {
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

class InvestigationReportDeleteResponse(BaseModel):
    """Response model for deleting investigation reports."""
    id: str
    status: str
    deleted: bool
    
    class Config:
        schema_extra = {
            "example": {
                "id": "eeb5e242-c104-425b-9061-9a834e24c0f9",
                "status": "deleted",
                "deleted": True
            }
        } 