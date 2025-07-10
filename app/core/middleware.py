"""
Middleware for the Vibe OLS application.
Handles request/response logging and processing time tracking.
"""

import time
from fastapi import Request
from .logging import get_logger

logger = get_logger(__name__)

async def log_requests(request: Request, call_next):
    """
    Middleware to log all incoming requests and responses.
    
    Args:
        request: The incoming HTTP request
        call_next: The next function in the middleware chain
        
    Returns:
        Response with additional processing time header
    """
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"🔄 Incoming request: {request.method} {request.url}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    # Get client info
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    logger.debug(f"Client: {client_ip}, User-Agent: {user_agent}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(f"✅ Response: {response.status_code} | {process_time:.3f}s | {request.method} {request.url}")
    
    # Add processing time to response headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response 