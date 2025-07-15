"""
Database models for the Vibe OLS application.
Contains SQLAlchemy models for investigation reports storage.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
import json

Base = declarative_base()

class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36).
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value

class InvestigationReport(Base):
    """
    SQLAlchemy model for investigation reports.
    
    Stores investigation reports with UUID, original question and parameters,
    the output of the investigation report, and a timestamp.
    """
    __tablename__ = "investigation_reports"
    
    # Primary key - UUID
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    # Original question/topic that was investigated
    question = Column(Text, nullable=False)
    
    # Parameters provided with the investigation request (stored as JSON string)
    parameters = Column(Text, nullable=True)
    
    # Investigation report output/findings
    report_text = Column(Text, nullable=False)
    
    # Timestamp when the investigation was completed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<InvestigationReport(id={self.id}, question='{self.question[:50]}...', created_at={self.created_at})>"
    
    @property
    def parameters_dict(self):
        """Get parameters as a dictionary."""
        if self.parameters is not None:
            try:
                return json.loads(str(self.parameters))
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def to_dict(self):
        """Convert the model to a dictionary for JSON serialization."""
        return {
            'id': str(self.id),
            'question': self.question,
            'parameters': self.parameters_dict,
            'report_text': self.report_text,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create an instance from a dictionary."""
        instance = cls(
            question=data['question'],
            parameters=json.dumps(data.get('parameters', {})) if data.get('parameters') else None,
            report_text=data['report_text']
        )
        if 'id' in data:
            instance.id = uuid.UUID(data['id'])
        if 'created_at' in data:
            instance.created_at = datetime.fromisoformat(data['created_at'])
        return instance 