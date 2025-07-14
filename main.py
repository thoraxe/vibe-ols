"""
Main FastAPI application for Vibe OLS.
This is the entry point that sets up the application with all routes and middleware.
"""

import uvicorn
from fastapi import FastAPI
import asyncio

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.middleware import log_requests
from app.routes import query, investigate, inbox, info

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",  # SwaggerUI endpoint
    redoc_url="/redoc",  # ReDoc endpoint
    openapi_url="/openapi.json"  # OpenAPI schema endpoint
)

# Add middleware for request/response logging
app.middleware("http")(log_requests)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Vibe OLS API...")
    logger.info(f"🔧 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🤖 OpenAI API Key configured: {'✅' if settings.is_openai_configured else '❌'}")
    logger.info(f"📊 Debug mode: {'✅' if settings.DEBUG_MODE else '❌'}")
    logger.info(f"🔧 MCP enabled: {'✅' if settings.MCP_ENABLED else '❌'}")
    if settings.MCP_ENABLED:
        logger.info(f"🔧 MCP servers: {settings.mcp_servers_dict}")
    logger.info("🎯 Available endpoints: /query, /query/stream, /investigate, /inbox")
    logger.info("📖 Documentation: /docs, /redoc")
    
    # Check OpenAI configuration
    if not settings.is_openai_configured:
        logger.warning("⚠️ OPENAI_API_KEY environment variable is not set.")
        logger.warning("❌ The /query endpoint will not work without this API key.")
        logger.warning("🔑 Please set your OpenAI API key in your environment or .env file.")
    else:
        logger.info("✅ OpenAI API key configured successfully")
    
    # Note: Agent initialization is deferred to first query to avoid startup issues
    logger.info("ℹ️ OpenShift AI Agent will be initialized on first query")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down Vibe OLS API...")
    
    # No explicit MCP cleanup needed - Pydantic AI handles it automatically
    
    logger.info("👋 Goodbye!")

# Include route handlers
app.include_router(info.router)
app.include_router(query.router)
app.include_router(investigate.router)
app.include_router(inbox.router)

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        log_level="info"
    ) 