"""
Pydantic request models for the Vibe OLS API.
Defines the structure and validation for incoming request data.
"""

from pydantic import BaseModel
from typing import Any, Dict, Optional

class QueryRequest(BaseModel):
    """Request model for query endpoints."""
    query: str
    context: Dict[str, Any] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "query": "My pods are stuck in CrashLoopBackOff state. How do I troubleshoot this?",
                "context": {"namespace": "my-app", "cluster_version": "4.12", "error_message": "container failed to start"}
            }
        }

class InvestigateRequest(BaseModel):
    """Request model for investigation endpoint."""
    topic: str
    parameters: Dict[str, Any] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "topic": "Security vulnerabilities in system",
                "parameters": {"severity": "high", "timeframe": "last_30_days"}
            }
        }

class InboxRequest(BaseModel):
    """Request model for inbox endpoint."""
    message: str
    metadata: Dict[str, Any] = {}
    
    class Config:
        schema_extra = {
            "example": {
                "message": "New alert from monitoring system",
                "metadata": {"priority": "high", "source": "monitoring", "timestamp": "2024-01-01T00:00:00Z"}
            }
        }

class InvestigationReportListRequest(BaseModel):
    """Request model for listing investigation reports."""
    limit: int = 50
    offset: int = 0
    search: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "limit": 50,
                "offset": 0,
                "search": "pod failures"
            }
        } 