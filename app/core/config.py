"""
Configuration module for the Vibe OLS application.
Handles environment variables and application settings.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "openai:gpt-4o-mini")
    OPENAI_ORG: str = os.getenv("OPENAI_ORG", "")
    
    # Application Configuration
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    VERBOSE_MODE: bool = os.getenv("VERBOSE_MODE", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # FastAPI Configuration
    APP_TITLE: str = "Vibe OLS API"
    APP_DESCRIPTION: str = "API for query, investigate, and inbox operations with comprehensive documentation"
    APP_VERSION: str = "1.0.0"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # MCP (Model Context Protocol) Configuration
    MCP_SERVERS: str = os.getenv("MCP_SERVERS", "")
    MCP_TIMEOUT: int = int(os.getenv("MCP_TIMEOUT", "30"))
    MCP_ENABLED: bool = os.getenv("MCP_ENABLED", "true").lower() == "true"
    
    @property
    def is_openai_configured(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.OPENAI_API_KEY)
    
    @property
    def mcp_servers_dict(self) -> dict[str, str]:
        """Parse MCP servers configuration into a dictionary."""
        if not self.MCP_SERVERS:
            return {}
        
        servers = {}
        try:
            # Parse format: server_name=base_endpoint_url,server2=endpoint2
            pairs = self.MCP_SERVERS.split(",")
            for pair in pairs:
                if "=" in pair:
                    name, endpoint = pair.strip().split("=", 1)
                    servers[name.strip()] = endpoint.strip() + "/mcp"
        except Exception:
            # Return empty dict if parsing fails
            pass
        
        return servers
    
    @property
    def is_mcp_configured(self) -> bool:
        """Check if MCP servers are configured and enabled."""
        return self.MCP_ENABLED and bool(self.mcp_servers_dict)

# Create settings instance
settings = Settings() 