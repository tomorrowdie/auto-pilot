"""
Unit tests for Product model
"""

import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from uuid import uuid4
from decimal import Decimal

from app.models.product import Product
from app.models.store import Store
from app.core.database_utils import get_db_session, create_all_tables

class TestProductModel:
    """Test cases for Product model"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup test database"""
        create_all_tables()
        yield
        # Cleanup is handled by test database teardown
    
    @pytest.fixture
    def test_store(self):
        """Create a test store for product tests"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        with get_db_session() as db:
            store = Store(
                shopify_domain=f"test-store-{unique_id}.myshopify.com",
                shopify_access_token="shpat_test_token",
                store_name="Test Store",
                owner_email=f"owner-{unique_id}@test.com"
            )
            db.add(store)
            db.commit()
            db.refresh(store)
            return store
    
    def test_product_creation_valid(self, test_store):
        """Test creating a product with valid data"""
        with get_db_session() as db:
            product = Product(
                store_id=test_store.id,
                shopify_product_id=123456789,
                title="Test Product",
                handle="test-product",
                description="<p>This is a test product</p>",
                product_type="T-Shirts",
                vendor="Test Vendor",
                tags=["test", "product"],
                status="active",
                seo_title="Test Product - SEO Title",
                seo_description="This is a test product for SEO testing purposes.",
                images=[{"src": "https://example.com/image.jpg", "alt": "Test image"}],
                variants=[{"id": 1, "title": "Default", "price": "19.99", "inventory_quantity": 10}]
            )
            
            db.add(product)
            db.commit()
            
            # Verify product was created
            assert product.id is not None
            assert product.created_at is not None
            assert product.updated_at is not None
            assert product.store_id == test_store.id
            assert product.shopify_product_id == 123456789
            assert product.title == "Test Product"
            assert product.handle == "test-product"
            assert product.status == "active"
            assert product.view_count == 0
    
    def test_product_status_validation(self, test_store):
        """Test product status validation"""
        with get_db_session() as db:
            product = Product(
                store_id=test_store.id,
                shopify_product_id=123456789,
                title="Test Product",
                handle="test-product",
                status="active"
            )
            assert product.status == "active"
            
            # Test valid statuses
            product.status = "draft"
            assert product.status == "draft"
            
            product.status = "archived"
            assert product.status == "archived"
            
            # Test invalid status
            with pytest.raises(ValueError, match="Status must be one of"):
                product.status = "invalid_status"
    
    def test_seo_title_validation(self, test_store):
        """Test SEO title length validation"""
        with get_db_session() as db:
            product = Product(
                store_id=test_store.id,
                shopify_product_id=123456789,
                title="Test Product",
                handle="test-product"
            )
            
            # Test valid SEO title
            product.seo_title = "Valid SEO Title"
            assert product.seo_title == "Valid SEO Title"
            
            # Test SEO title too long
            with pytest.raises(ValueError, match="SEO title should not exceed 70 characters"):
                product.seo_title = "This is a very long SEO title that exceeds the 70 character limit for SEO titles"
    
    def test_seo_description_validation(self, test_store):
        """Test SEO description length validation"""
        with get_db_session() as db:
            product = Product(
                store_id=test_store.id,
                shopify_product_id=123456789,
                title="Test Product",
                handle="test-product"
            )
            
            # Test valid SEO description
            product.seo_description = "Valid SEO description"
            assert product.seo_description == "Valid SEO description"
            
            # Test SEO description too long
            long_description = "This is a very long SEO description that exceeds the 160 character limit for meta descriptions and should trigger a validation error when set"
            with pytest.raises(ValueError, match="SEO description should not exceed 160 characters"):
                product.seo_description = long_description
    
    def test_seo_score_validation(self, test_store):
        """Test SEO score validation"""
        with get_db_session() as db:
            product = Product(
                store_id=test_store.id,
                shopify_product_id=123456789,
                title="Test Product",
                handle="test-product"
            )
            
            # Test valid SEO scores
            product.current_seo_score = 0
            assert product.current_seo_score == 0
            
            product.current_seo_score = 50
            assert product.current_seo_score == 50
            
            product.current_seo_score = 100
            assert product.current_seo_score == 100
            
            # Test invalid SEO scores
            with pytest.raises(ValueError, match="SEO score must be between 0 and 100"):
                product.current_seo_score = -1
            
            with pytest.raises(ValueError, match="SEO score must be between 0 and 100"):
                product.current_seo_score = 101
    
    def test_conversion_rate_validation(self, test_store):
        """Test conversion rate validation"""
        with get_db_session() as db:
            product = Product(
                store_id=test_store.id,
                shopify_product_id=123456789,
                title="Test Product",
                handle="test-product"
            )
            
            # Test valid conversion rates
            product.conversion_rate = Decimal('0.0')
            assert product.conversion_rate == Decimal('0.0')
            
            product.conversion_rate = Decimal('0.5')
            assert product.conversion_rate == Decimal('0.5')
            
            product.conversion_rate = Decimal('1.0')
            assert product.conversion_rate == Decimal('1.0')
            
            # Test invalid conversion rates
            with pytest.raises(ValueError, match="Conversion rate must be between 0 and 1"):
                product.conversion_rate = Decimal('-0.1')
            
            with pytest.raises(ValueError, match="Conversion rate must be between 0 and 1"):
                product.conversion_rate = Decimal('1.1')
    
    def test_unique_store_product_constraint(self, test_store):
        """Test that store_id + shopify_product_id must be unique"""
        # Create first product
        with get_db_session() as db:
            product1 = Product(
                store_id=test_store.id,
                shopify_product_id=123456789,
                title="Product 1",
                handle="product-1"
            )
            db.add(product1)
            # Commit happens automatically
        
        # Try to create second product with same store_id and shopify_product_id
        with pytest.raises(Exception):  # Will catch the database error
            with get_db_session() as db:
                product2 = Product(
                    store_id=test_store.id,
                    shopify_product_id=123456789,  # Same as product1
                    title="Product 2",
                    handle="product-2"
                )
                db.add(product2)
                # Commit will fail due to unique constraint
    
    def test_get_primary_image(self, test_store):
        """Test getting primary image"""
        product = Product(
            store_id=test_store.id,
            shopify_product_id=123456789,
            title="Test Product",
            handle="test-product",
            images=[
                {"src": "https://example.com/image1.jpg", "alt": "Image 1"},
                {"src": "https://example.com/image2.jpg", "alt": "Image 2"}
            ]
        )
        
        primary_image = product.get_primary_image()
        assert primary_image is not None
        assert primary_image["src"] == "https://example.com/image1.jpg"
        
        # Test with no images
        product.images = []
        assert product.get_primary_image() is None
    
    def test_get_price_range(self, test_store):
        """Test getting price range from variants"""
        product = Product(
            store_id=test_store.id,
            shopify_product_id=123456789,
            title="Test Product",
            handle="test-product",
            variants=[
                {"id": 1, "price": "19.99", "currency": "USD"},
                {"id": 2, "price": "29.99", "currency": "USD"},
                {"id": 3, "price": "15.99", "currency": "USD"}
            ]
        )
        
        price_range = product.get_price_range()
        assert price_range["min"] == 15.99
        assert price_range["max"] == 29.99
        assert price_range["currency"] == "USD"
        
        # Test with no variants
        product.variants = []
        price_range = product.get_price_range()
        assert price_range["min"] is None
        assert price_range["max"] is None
    
    def test_get_inventory_total(self, test_store):
        """Test getting total inventory"""
        product = Product(
            store_id=test_store.id,
            shopify_product_id=123456789,
            title="Test Product",
            handle="test-product",
            variants=[
                {"id": 1, "inventory_quantity": 10},
                {"id": 2, "inventory_quantity": 5},
                {"id": 3, "inventory_quantity": 15}
            ]
        )
        
        assert product.get_inventory_total() == 30
        assert product.is_in_stock() is True
        
        # Test with no inventory
        product.variants = [{"id": 1, "inventory_quantity": 0}]
        assert product.get_inventory_total() == 0
        assert product.is_in_stock() is False
    
    def test_has_seo_data(self, test_store):
        """Test checking if product has SEO data"""
        product = Product(
            store_id=test_store.id,
            shopify_product_id=123456789,
            title="Test Product",
            handle="test-product"
        )
        
        # No SEO data
        assert product.has_seo_data() is False
        
        # Only SEO title
        product.seo_title = "SEO Title"
        assert product.has_seo_data() is False
        
        # Both SEO title and description
        product.seo_description = "SEO Description"
        assert product.has_seo_data() is True
    
    def test_needs_seo_analysis(self, test_store):
        """Test checking if product needs SEO analysis"""
        product = Product(
            store_id=test_store.id,
            shopify_product_id=123456789,
            title="Test Product",
            handle="test-product"
        )
        
        # No analysis timestamp - should need analysis
        assert product.needs_seo_analysis() is True
        
        # Recent analysis - should not need analysis
        product.last_analyzed_at = datetime.utcnow() - timedelta(hours=1)
        assert product.needs_seo_analysis() is False
        
        # Old analysis - should need analysis
        product.last_analyzed_at = datetime.utcnow() - timedelta(hours=200)
        assert product.needs_seo_analysis() is True
    
    def test_calculate_seo_score(self, test_store):
        """Test SEO score calculation"""
        product = Product(
            store_id=test_store.id,
            shopify_product_id=123456789,
            title="Good Product Title",
            handle="test-product",
            description="This is a good product description with enough content to score points.",
            seo_title="SEO Title",
            seo_description="SEO Description",
            images=[{"src": "https://example.com/image.jpg"}],
            tags=["tag1", "tag2"]
        )
        
        score = product.calculate_seo_score()
        
        # Should get points for:
        # - Title length (15 + 15 = 30)
        # - SEO title (20)
        # - SEO description (20)
        # - Description (15)
        # - Images (10)
        # - Tags (5)
        # Total: 100
        assert score == 100
    
    def test_get_urls(self, test_store):
        """Test URL generation"""
        product = Product(
            store_id=test_store.id,
            shopify_product_id=123456789,
            title="Test Product",
            handle="test-product"
        )
        
        shopify_url = product.get_shopify_url()
        assert "test-store.myshopify.com" in shopify_url
        assert "123456789" in shopify_url
        
        storefront_url = product.get_storefront_url()
        assert "test-store.com" in storefront_url
        assert "test-product" in storefront_url
    
    def test_to_dict_includes_computed_fields(self, test_store):
        """Test that to_dict includes computed fields"""
        product = Product(
            store_id=test_store.id,
            shopify_product_id=123456789,
            title="Test Product",
            handle="test-product",
            images=[{"src": "https://example.com/image.jpg"}],
            variants=[{"id": 1, "price": "19.99", "inventory_quantity": 10}]
        )
        
        data = product.to_dict()
        
        # Should include computed fields
        assert "primary_image" in data
        assert "price_range" in data
        assert "inventory_total" in data
        assert "in_stock" in data
        assert "variant_count" in data
        assert "has_seo_data" in data
        assert "needs_seo_analysis" in data
        assert "shopify_url" in data
        assert "storefront_url" in data
        
        # Should include basic fields
        assert data["title"] == "Test Product"
        assert data["handle"] == "test-product"
    
    def test_product_repr(self, test_store):
        """Test string representation"""
        product = Product(
            store_id=test_store.id,
            shopify_product_id=123456789,
            title="Test Product with a Long Title",
            handle="test-product"
        )
        
        repr_str = repr(product)
        assert "Product" in repr_str
        assert "Test Product with a Long Title"[:30] in repr_str