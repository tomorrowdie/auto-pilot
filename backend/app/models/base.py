"""
Base model class with common fields and functionality
"""

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime
from typing import Any

# Create the base class
Base = declarative_base()

class BaseModel(Base):
    """
    Base model class that provides common fields and functionality
    for all database models
    """
    __abstract__ = True
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True
    )
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Automatically generate table name from class name
        Convert CamelCase to snake_case
        """
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
    
    def update_from_dict(self, data: dict[str, Any]) -> None:
        """
        Update model instance from dictionary
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """
        String representation of the model
        """
        return f"<{self.__class__.__name__}(id={self.id})>"