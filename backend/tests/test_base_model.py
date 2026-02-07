"""
Unit tests for base model functionality
"""

import pytest
from datetime import datetime
import uuid
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import Session

from app.models.base import BaseModel
from app.core.database import SessionLocal, engine
from app.core.database_utils import get_db_session

# Create a test model for testing
class TestModel(BaseModel):
    __tablename__ = "test_models"
    
    name = Column(String(100), nullable=False)
    value = Column(Integer, default=0)

class TestBaseModel:
    """Test cases for BaseModel functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test"""
        # Create tables
        BaseModel.metadata.create_all(bind=engine)
        yield
        # Drop tables
        BaseModel.metadata.drop_all(bind=engine)
    
    def test_model_creation(self):
        """Test basic model creation"""
        with get_db_session() as db:
            # Create a test instance
            test_instance = TestModel(name="Test Item", value=42)
            db.add(test_instance)
            db.commit()
            
            # Verify the instance was created
            assert test_instance.id is not None
            assert isinstance(test_instance.id, uuid.UUID)
            assert test_instance.name == "Test Item"
            assert test_instance.value == 42
            assert isinstance(test_instance.created_at, datetime)
            assert isinstance(test_instance.updated_at, datetime)
    
    def test_tablename_generation(self):
        """Test automatic table name generation"""
        assert TestModel.__tablename__ == "test_models"
        
        # Test with different class names
        class UserProfile(BaseModel):
            pass
        
        assert UserProfile.__tablename__ == "user_profiles"
    
    def test_to_dict_method(self):
        """Test model to dictionary conversion"""
        with get_db_session() as db:
            test_instance = TestModel(name="Test Item", value=42)
            db.add(test_instance)
            db.commit()
            
            # Convert to dictionary
            data = test_instance.to_dict()
            
            # Verify dictionary contents
            assert "id" in data
            assert "name" in data
            assert "value" in data
            assert "created_at" in data
            assert "updated_at" in data
            
            assert data["name"] == "Test Item"
            assert data["value"] == 42
            assert isinstance(data["id"], str)  # UUID converted to string
            assert isinstance(data["created_at"], str)  # datetime converted to ISO string
    
    def test_update_from_dict_method(self):
        """Test updating model from dictionary"""
        with get_db_session() as db:
            test_instance = TestModel(name="Original", value=1)
            db.add(test_instance)
            db.commit()
            
            # Update from dictionary
            update_data = {"name": "Updated", "value": 99}
            test_instance.update_from_dict(update_data)
            db.commit()
            
            # Verify updates
            assert test_instance.name == "Updated"
            assert test_instance.value == 99
    
    def test_repr_method(self):
        """Test string representation"""
        test_instance = TestModel(name="Test", value=1)
        repr_str = repr(test_instance)
        
        assert "TestModel" in repr_str
        assert "id=" in repr_str
    
    def test_timestamps_auto_update(self):
        """Test that updated_at is automatically updated"""
        with get_db_session() as db:
            test_instance = TestModel(name="Test", value=1)
            db.add(test_instance)
            db.commit()
            
            original_updated_at = test_instance.updated_at
            
            # Update the instance
            test_instance.name = "Updated"
            db.commit()
            
            # Verify updated_at changed
            assert test_instance.updated_at > original_updated_at
    
    def test_unique_ids(self):
        """Test that each instance gets a unique ID"""
        with get_db_session() as db:
            instance1 = TestModel(name="Test1", value=1)
            instance2 = TestModel(name="Test2", value=2)
            
            db.add_all([instance1, instance2])
            db.commit()
            
            assert instance1.id != instance2.id
            assert isinstance(instance1.id, uuid.UUID)
            assert isinstance(instance2.id, uuid.UUID)

if __name__ == "__main__":
    pytest.main([__file__])