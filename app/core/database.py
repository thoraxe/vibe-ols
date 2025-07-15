"""
Database initialization and configuration for the Vibe OLS application.
Handles database setup, connection, and table creation.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from ..models.database import Base
from .config import settings
from .logging import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """Manager for database operations and initialization."""
    
    def __init__(self):
        """Initialize the database manager."""
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database connection and create tables."""
        try:
            # Create the database engine
            self.engine = create_engine(
                settings.DATABASE_URL,
                echo=settings.DATABASE_ECHO,
                connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            logger.info(f"✅ Database initialized successfully: {settings.DATABASE_URL}")
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to initialize database: {str(e)}")
            raise
    
    def get_session(self):
        """Get a database session."""
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        if self.engine is None:
            logger.error("❌ Database engine not initialized")
            return False
            
        try:
            from sqlalchemy import text
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("✅ Database health check passed")
            return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Database health check failed: {str(e)}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("🔒 Database connection closed")

# Create a global database manager instance
db_manager = DatabaseManager()

def get_db():
    """Dependency to get database session for FastAPI."""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()

def initialize_database():
    """Initialize database tables and connections."""
    logger.info("🗄️ Initializing database...")
    
    # The DatabaseManager already initializes the database in __init__
    # This function is provided for explicit initialization if needed
    if not db_manager.health_check():
        logger.warning("⚠️ Database health check failed during initialization")
        return False
    
    logger.info("✅ Database initialization completed successfully")
    return True 