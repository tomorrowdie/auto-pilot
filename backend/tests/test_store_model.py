"""
Unit tests for Store model
"""

import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.store import Store
from app.core.database_utils import get_db_session, create_all_tables

class TestStoreModel:
    """Test cases for Store model"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup test database"""
        create_all_tables()
        yield
        # Cleanup is handled by test database teardown
    
    def test_store_creation_valid(self):
        """Test creating a store with valid data"""
        with get_db_session() as db:
            store = Store(
                shopify_domain="test-store.myshopify.com",
                shopify_access_token="shpat_test_token_12345678901234567890",
                store_name="Test Store",
                owner_email="owner@test.com",
                plan_name="Shopify",
                timezone="America/New_York",
                currency="USD"
            )
            
            db.add(store)
            db.commit()
            
            # Verify store was created
            assert store.id is not None
            assert store.created_at is not None
            assert store.updated_at is not None
            assert store.shopify_domain == "test-store.myshopify.com"
            assert store.store_name == "Test Store"
            assert store.owner_email == "owner@test.com"
            assert store.is_active is True
            assert store.product_count == 0
    
    def test_store_domain_validation(self):
        """Test Shopify domain validation"""
        with get_db_session() as db:
            # Test valid domain
            store = Store(
                shopify_domain="valid-store.myshopify.com",
                shopify_access_token="shpat_test_token",
                store_name="Test Store",
                owner_email="owner@test.com"
            )
            assert store.shopify_domain == "valid-store.myshopify.com"
            
            # Test domain without .myshopify.com (should be added)
            store.shopify_domain = "test-store"
            assert store.shopify_domain == "test-store.myshopify.com"
            
            # Test invalid domain format
            with pytest.raises(ValueError, match="Invalid Shopify domain format"):
                store.shopify_domain = "invalid..domain.myshopify.com"
            
            # Test non-Shopify domain
            with pytest.raises(ValueError, match="Domain must be a valid Shopify domain"):
                store.shopify_domain = "example.com"
    
    def test_email_validation(self):
        """Test email validation"""
        with get_db_session() as db:
            store = Store(
                shopify_domain="test-store.myshopify.com",
                shopify_access_token="shpat_test_token",
                store_name="Test Store",
                owner_email="valid@email.com"
            )
            assert store.owner_email == "valid@email.com"
            
            # Test invalid email
            with pytest.raises(ValueError, match="Invalid email format"):
                store.owner_email = "invalid-email"
            
            # Test empty email
            with pytest.raises(ValueError, match="Owner email cannot be empty"):
                store.owner_email = ""
    
    def test_currency_validation(self):
        """Test currency code validation"""
        with get_db_session() as db:
            store = Store(
                shopify_domain="test-store.myshopify.com",
                shopify_access_token="shpat_test_token",
                store_name="Test Store",
                owner_email="owner@test.com"
            )
            
            # Test valid currency
            store.currency = "USD"
            assert store.currency == "USD"
            
            # Test lowercase currency (should be uppercased)
            store.currency = "eur"
            assert store.currency == "EUR"
            
            # Test invalid currency length
            with pytest.raises(ValueError, match="Currency code must be 3 characters"):
                store.currency = "US"
            
            with pytest.raises(ValueError, match="Currency code must be 3 characters"):
                store.currency = "USDD"
    
    def test_unique_domain_constraint(self):
        """Test that shopify_domain must be unique"""
        # Create first store
        with get_db_session() as db:
            store1 = Store(
                shopify_domain="unique-store.myshopify.com",
                shopify_access_token="shpat_test_token_1",
                store_name="Store 1",
                owner_email="owner1@test.com"
            )
            db.add(store1)
            # Commit happens automatically in context manager
        
        # Try to create second store with same domain in separate session
        with pytest.raises(Exception):  # Will catch the database error
            with get_db_session() as db:
                store2 = Store(
                    shopify_domain="unique-store.myshopify.com",
                    shopify_access_token="shpat_test_token_2",
                    store_name="Store 2",
                    owner_email="owner2@test.com"
                )
                db.add(store2)
                # Commit will fail due to unique constraint
    
    def test_get_shop_name(self):
        """Test shop name extraction from domain"""
        store = Store(
            shopify_domain="my-awesome-store.myshopify.com",
            shopify_access_token="shpat_test_token",
            store_name="Test Store",
            owner_email="owner@test.com"
        )
        
        assert store.get_shop_name() == "my-awesome-store"
    
    def test_is_sync_needed(self):
        """Test sync needed logic"""
        store = Store(
            shopify_domain="test-store.myshopify.com",
            shopify_access_token="shpat_test_token",
            store_name="Test Store",
            owner_email="owner@test.com"
        )
        
        # No sync timestamp - should need sync
        assert store.is_sync_needed() is True
        
        # Recent sync - should not need sync
        store.last_sync_at = datetime.utcnow() - timedelta(hours=1)
        assert store.is_sync_needed() is False
        
        # Old sync - should need sync
        store.last_sync_at = datetime.utcnow() - timedelta(hours=25)
        assert store.is_sync_needed() is True
        
        # Custom max age
        store.last_sync_at = datetime.utcnow() - timedelta(hours=2)
        assert store.is_sync_needed(max_age_hours=1) is True
        assert store.is_sync_needed(max_age_hours=3) is False
    
    def test_settings_management(self):
        """Test settings JSONB field management"""
        store = Store(
            shopify_domain="test-store.myshopify.com",
            shopify_access_token="shpat_test_token",
            store_name="Test Store",
            owner_email="owner@test.com"
        )
        
        # Test default empty settings
        assert store.get_setting("non_existent") is None
        assert store.get_setting("non_existent", "default") == "default"
        
        # Test setting values
        store.set_setting("auto_sync", True)
        store.set_setting("sync_interval", 24)
        
        assert store.get_setting("auto_sync") is True
        assert store.get_setting("sync_interval") == 24
        
        # Test settings persistence
        assert "auto_sync" in store.settings
        assert "sync_interval" in store.settings
    
    def test_get_api_url(self):
        """Test API URL generation"""
        store = Store(
            shopify_domain="test-store.myshopify.com",
            shopify_access_token="shpat_test_token",
            store_name="Test Store",
            owner_email="owner@test.com"
        )
        
        expected_url = "https://test-store.myshopify.com/admin/api/2023-10"
        assert store.get_api_url() == expected_url
    
    def test_to_dict_excludes_sensitive_data(self):
        """Test that to_dict excludes sensitive information"""
        store = Store(
            shopify_domain="test-store.myshopify.com",
            shopify_access_token="shpat_secret_token_12345",
            store_name="Test Store",
            owner_email="owner@test.com"
        )
        
        data = store.to_dict()
        
        # Should exclude actual token
        assert data["shopify_access_token"] == "***REDACTED***"
        
        # Should include computed fields
        assert "shop_name" in data
        assert "sync_needed" in data
        assert "api_url" in data
        
        # Should include basic fields
        assert data["store_name"] == "Test Store"
        assert data["shopify_domain"] == "test-store.myshopify.com"
    
    def test_store_repr(self):
        """Test string representation"""
        store = Store(
            shopify_domain="test-store.myshopify.com",
            shopify_access_token="shpat_test_token",
            store_name="Test Store",
            owner_email="owner@test.com"
        )
        
        repr_str = repr(store)
        assert "Store" in repr_str
        assert "test-store.myshopify.com" in repr_str
        assert "Test Store" in repr_str