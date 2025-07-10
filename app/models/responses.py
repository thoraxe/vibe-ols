"""
Pydantic response models for the Vibe OLS API.
Defines the structure for outgoing response data.
"""

from pydantic import BaseModel

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