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
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # FastAPI Configuration
    APP_TITLE: str = "Vibe OLS API"
    APP_DESCRIPTION: str = "API for query, investigate, and inbox operations with comprehensive documentation"
    APP_VERSION: str = "1.0.0"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    @property
    def is_openai_configured(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.OPENAI_API_KEY)

# Create settings instance
settings = Settings() 