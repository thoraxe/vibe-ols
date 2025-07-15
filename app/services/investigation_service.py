"""
Investigation service for managing investigation reports in the database.
Provides functions to store and retrieve investigation reports.
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from ..models.database import InvestigationReport, Base
from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)

class InvestigationService:
    """Service class for managing investigation reports in the database."""
    
    def __init__(self):
        """Initialize the investigation service with database connection."""
        self.engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
        logger.info("🗄️ Investigation service initialized with database connection")
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    async def store_investigation_report(
        self,
        question: str,
        parameters: Optional[Dict[str, Any]],
        report_text: str,
        investigation_id: Optional[str] = None
    ) -> InvestigationReport:
        """
        Store an investigation report in the database.
        
        Args:
            question: The original investigation question/topic
            parameters: Optional parameters that were provided with the request
            report_text: The generated investigation report text
            investigation_id: Optional UUID to use, otherwise generate new one
            
        Returns:
            The stored InvestigationReport instance
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        session = self.get_session()
        try:
            # Create the investigation report
            report = InvestigationReport(
                question=question,
                parameters=json.dumps(parameters) if parameters else None,
                report_text=report_text,
                created_at=datetime.utcnow()
            )
            
            # Note: SQLAlchemy will automatically generate UUID for the id field
            # based on the column definition with default=uuid.uuid4
            
            session.add(report)
            session.commit()
            session.refresh(report)
            
            logger.info(f"📝 Stored investigation report with ID: {report.id}")
            return report
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Failed to store investigation report: {str(e)}")
            raise
        finally:
            session.close()
    
    async def get_investigation_report(self, report_id: str) -> Optional[InvestigationReport]:
        """
        Retrieve an investigation report by ID.
        
        Args:
            report_id: The UUID of the investigation report
            
        Returns:
            InvestigationReport instance if found, None otherwise
        """
        session = self.get_session()
        try:
            report_uuid = uuid.UUID(report_id)
            report = session.query(InvestigationReport).filter(
                InvestigationReport.id == report_uuid
            ).first()
            
            if report:
                logger.info(f"📖 Retrieved investigation report: {report_id}")
            else:
                logger.info(f"🔍 Investigation report not found: {report_id}")
                
            return report
            
        except ValueError:
            logger.warning(f"Invalid UUID format: {report_id}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to retrieve investigation report: {str(e)}")
            return None
        finally:
            session.close()
    
    async def get_investigation_reports(
        self,
        limit: int = 50,
        offset: int = 0,
        search_query: Optional[str] = None
    ) -> List[InvestigationReport]:
        """
        Retrieve multiple investigation reports with optional search.
        
        Args:
            limit: Maximum number of reports to return
            offset: Number of reports to skip
            search_query: Optional search term to filter by question content
            
        Returns:
            List of InvestigationReport instances
        """
        session = self.get_session()
        try:
            query = session.query(InvestigationReport)
            
            # Apply search filter if provided
            if search_query:
                query = query.filter(
                    InvestigationReport.question.contains(search_query)
                )
            
            # Order by most recent first
            query = query.order_by(desc(InvestigationReport.created_at))
            
            # Apply pagination
            reports = query.offset(offset).limit(limit).all()
            
            logger.info(f"📋 Retrieved {len(reports)} investigation reports")
            return reports
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to retrieve investigation reports: {str(e)}")
            return []
        finally:
            session.close()
    
    async def count_investigation_reports(self, search_query: Optional[str] = None) -> int:
        """
        Count the total number of investigation reports.
        
        Args:
            search_query: Optional search term to filter by question content
            
        Returns:
            Total count of investigation reports
        """
        session = self.get_session()
        try:
            query = session.query(InvestigationReport)
            
            # Apply search filter if provided
            if search_query:
                query = query.filter(
                    InvestigationReport.question.contains(search_query)
                )
            
            count = query.count()
            logger.info(f"🔢 Total investigation reports: {count}")
            return count
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Failed to count investigation reports: {str(e)}")
            return 0
        finally:
            session.close()
    
    async def delete_investigation_report(self, report_id: str) -> bool:
        """
        Delete an investigation report by ID.
        
        Args:
            report_id: The UUID of the investigation report to delete
            
        Returns:
            True if successfully deleted, False otherwise
        """
        session = self.get_session()
        try:
            report_uuid = uuid.UUID(report_id)
            report = session.query(InvestigationReport).filter(
                InvestigationReport.id == report_uuid
            ).first()
            
            if not report:
                logger.info(f"🔍 Investigation report not found for deletion: {report_id}")
                return False
            
            session.delete(report)
            session.commit()
            
            logger.info(f"🗑️ Successfully deleted investigation report: {report_id}")
            return True
            
        except ValueError:
            logger.warning(f"Invalid UUID format for deletion: {report_id}")
            return False
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Failed to delete investigation report: {str(e)}")
            return False
        finally:
            session.close()

# Create a global instance of the service
investigation_service = InvestigationService() 