"""
Unit tests for Keyword models
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from app.models.keyword import Keyword, ProductKeyword
from app.models.store import Store
from app.models.product import Product
from app.core.database_utils import get_db_session, create_all_tables

class TestKeywordModel:
    """Test cases for Keyword model"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup test database"""
        create_all_tables()
        yield
    
    def test_keyword_creation_valid(self):
        """Test creating keyword with valid data"""
        with get_db_session() as db:
            keyword = Keyword(
                keyword="premium cotton t-shirt",
                search_volume=1200,
                keyword_difficulty=45,
                cpc=Decimal('1.25'),
                competition_level="medium",
                search_intent="commercial",
                category="clothing",
                source="amazon",
                trend_score=15
            )
            
            db.add(keyword)
            db.commit()
            
            assert keyword.id is not None
            assert keyword.keyword == "premium cotton t-shirt"
            assert keyword.search_volume == 1200
            assert keyword.keyword_difficulty == 45
            assert keyword.competition_level == "medium"
            assert keyword.search_intent == "commercial"
    
    def test_keyword_difficulty_validation(self):
        """Test keyword difficulty validation"""
        keyword = Keyword(keyword="test keyword", source="manual")
        
        # Test valid difficulties
        keyword.keyword_difficulty = 0
        assert keyword.keyword_difficulty == 0
        
        keyword.keyword_difficulty = 100
        assert keyword.keyword_difficulty == 100
        
        # Test invalid difficulties
        with pytest.raises(ValueError, match="Keyword difficulty must be between 0 and 100"):
            keyword.keyword_difficulty = -1
        
        with pytest.raises(ValueError, match="Keyword difficulty must be between 0 and 100"):
            keyword.keyword_difficulty = 101
    
    def test_competition_level_validation(self):
        """Test competition level validation"""
        keyword = Keyword(keyword="test keyword", source="manual")
        
        # Test valid levels
        keyword.competition_level = "low"
        assert keyword.competition_level == "low"
        
        keyword.competition_level = "HIGH"  # Should be lowercased
        assert keyword.competition_level == "high"
        
        # Test invalid level
        with pytest.raises(ValueError, match="Competition level must be one of"):
            keyword.competition_level = "invalid"
    
    def test_search_intent_validation(self):
        """Test search intent validation"""
        keyword = Keyword(keyword="test keyword", source="manual")
        
        # Test valid intents
        keyword.search_intent = "commercial"
        assert keyword.search_intent == "commercial"
        
        keyword.search_intent = "INFORMATIONAL"  # Should be lowercased
        assert keyword.search_intent == "informational"
        
        # Test invalid intent
        with pytest.raises(ValueError, match="Search intent must be one of"):
            keyword.search_intent = "invalid"
    
    def test_calculate_opportunity_score(self):
        """Test opportunity score calculation"""
        keyword = Keyword(
            keyword="high opportunity keyword",
            search_volume=5000,  # Should get 30 points
            keyword_difficulty=20,  # Should get 24 points (80 * 0.3)
            competition_level="low",  # Should get 20 points
            search_intent="commercial",  # Should get 10 points
            source="amazon"
        )
        
        score = keyword.calculate_opportunity_score()
        # Expected: 30 + 24 + 20 + 10 = 84
        assert score == 84
    
    def test_is_long_tail(self):
        """Test long-tail keyword detection"""
        short_keyword = Keyword(keyword="shirt", source="manual")
        medium_keyword = Keyword(keyword="cotton shirt", source="manual")
        long_keyword = Keyword(keyword="premium cotton t-shirt", source="manual")
        
        assert short_keyword.is_long_tail() is False
        assert medium_keyword.is_long_tail() is False
        assert long_keyword.is_long_tail() is True
        
        assert short_keyword.get_word_count() == 1
        assert medium_keyword.get_word_count() == 2
        assert long_keyword.get_word_count() == 3
    
    def test_keyword_classification(self):
        """Test keyword classification methods"""
        keyword = Keyword(
            keyword="buy premium shirt",
            search_volume=2000,
            keyword_difficulty=25,
            competition_level="low",
            search_intent="transactional",
            source="google"
        )
        
        assert keyword.is_high_volume() is True
        assert keyword.is_low_competition() is True
        assert keyword.is_commercial() is True
    
    def test_get_estimated_traffic(self):
        """Test estimated traffic calculation"""
        keyword = Keyword(
            keyword="test keyword",
            search_volume=1000,
            source="manual"
        )
        
        # Position 1 should get ~28% CTR
        traffic_pos1 = keyword.get_estimated_traffic(ranking_position=1)
        assert traffic_pos1 == 280  # 1000 * 0.28
        
        # Position 5 should get ~6% CTR
        traffic_pos5 = keyword.get_estimated_traffic(ranking_position=5)
        assert traffic_pos5 == 60  # 1000 * 0.06
        
        # Position beyond 10 should get ~1% CTR
        traffic_pos15 = keyword.get_estimated_traffic(ranking_position=15)
        assert traffic_pos15 == 10  # 1000 * 0.01
    
    def test_unique_keyword_source_constraint(self):
        """Test that keyword + source must be unique"""
        # Create first keyword
        with get_db_session() as db:
            keyword1 = Keyword(
                keyword="unique keyword",
                source="amazon"
            )
            db.add(keyword1)
            db.commit()
        
        # Try to create second keyword with same keyword + source
        with pytest.raises(Exception):  # Will catch the database error
            with get_db_session() as db:
                keyword2 = Keyword(
                    keyword="unique keyword",
                    source="amazon"  # Same source
                )
                db.add(keyword2)
                # Commit will fail due to unique constraint
    
    def test_to_dict_includes_computed_fields(self):
        """Test that to_dict includes computed fields"""
        keyword = Keyword(
            keyword="premium cotton t-shirt",
            search_volume=1500,
            keyword_difficulty=30,
            competition_level="low",
            search_intent="commercial",
            source="amazon"
        )
        
        data = keyword.to_dict()
        
        # Should include computed fields
        assert "opportunity_score" in data
        assert "is_long_tail" in data
        assert "word_count" in data
        assert "is_high_volume" in data
        assert "is_low_competition" in data
        assert "is_commercial" in data
        assert "estimated_traffic" in data
        
        # Should include basic fields
        assert data["keyword"] == "premium cotton t-shirt"
        assert data["search_volume"] == 1500
        assert data["is_long_tail"] is True
        assert data["word_count"] == 3

class TestProductKeywordModel:
    """Test cases for ProductKeyword model"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup test database"""
        create_all_tables()
        yield
    
    @pytest.fixture
    def test_store(self):
        """Create a test store"""
        unique_id = str(uuid4())[:8]
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
    
    @pytest.fixture
    def test_product(self, test_store):
        """Create a test product"""
        with get_db_session() as db:
            product = Product(
                store_id=test_store.id,
                shopify_product_id=123456789,
                title="Test Product",
                handle="test-product"
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            return product
    
    @pytest.fixture
    def test_keyword(self):
        """Create a test keyword"""
        with get_db_session() as db:
            keyword = Keyword(
                keyword="test product keyword",
                search_volume=800,
                keyword_difficulty=40,
                source="manual"
            )
            db.add(keyword)
            db.commit()
            db.refresh(keyword)
            return keyword
    
    def test_product_keyword_creation_valid(self, test_product, test_keyword):
        """Test creating product keyword relationship"""
        with get_db_session() as db:
            product_keyword = ProductKeyword(
                product_id=test_product.id,
                keyword_id=test_keyword.id,
                relevance_score=Decimal('0.85'),
                current_ranking=15,
                target_ranking=5,
                is_primary=True
            )
            
            db.add(product_keyword)
            db.commit()
            
            assert product_keyword.id is not None
            assert product_keyword.product_id == test_product.id
            assert product_keyword.keyword_id == test_keyword.id
            assert product_keyword.relevance_score == Decimal('0.85')
            assert product_keyword.current_ranking == 15
            assert product_keyword.is_primary is True
    
    def test_relevance_score_validation(self, test_product, test_keyword):
        """Test relevance score validation"""
        product_keyword = ProductKeyword(
            product_id=test_product.id,
            keyword_id=test_keyword.id,
            relevance_score=Decimal('0.5')
        )
        
        # Test valid scores
        product_keyword.relevance_score = Decimal('0.0')
        assert product_keyword.relevance_score == Decimal('0.0')
        
        product_keyword.relevance_score = Decimal('1.0')
        assert product_keyword.relevance_score == Decimal('1.0')
        
        # Test invalid scores
        with pytest.raises(ValueError, match="Relevance score must be between 0.00 and 1.00"):
            product_keyword.relevance_score = Decimal('-0.1')
        
        with pytest.raises(ValueError, match="Relevance score must be between 0.00 and 1.00"):
            product_keyword.relevance_score = Decimal('1.1')
    
    def test_ranking_validation(self, test_product, test_keyword):
        """Test ranking validation"""
        product_keyword = ProductKeyword(
            product_id=test_product.id,
            keyword_id=test_keyword.id,
            relevance_score=Decimal('0.5')
        )
        
        # Test valid rankings
        product_keyword.current_ranking = 1
        assert product_keyword.current_ranking == 1
        
        product_keyword.target_ranking = 100
        assert product_keyword.target_ranking == 100
        
        # Test invalid rankings
        with pytest.raises(ValueError, match="current_ranking must be a positive integer"):
            product_keyword.current_ranking = 0
        
        with pytest.raises(ValueError, match="target_ranking must be a positive integer"):
            product_keyword.target_ranking = -1
    
    def test_performance_metrics(self, test_product, test_keyword):
        """Test performance metric calculations"""
        product_keyword = ProductKeyword(
            product_id=test_product.id,
            keyword_id=test_keyword.id,
            relevance_score=Decimal('0.8'),
            clicks=100,
            impressions=5000,
            conversions=5
        )
        
        # Test CTR calculation
        ctr = product_keyword.get_ctr()
        assert ctr == 0.02  # 100/5000
        
        # Test conversion rate calculation
        conversion_rate = product_keyword.get_conversion_rate()
        assert conversion_rate == 0.05  # 5/100
    
    def test_is_performing_well(self, test_product, test_keyword):
        """Test performance evaluation"""
        product_keyword = ProductKeyword(
            product_id=test_product.id,
            keyword_id=test_keyword.id,
            relevance_score=Decimal('0.8'),
            current_ranking=5,
            clicks=250,
            impressions=10000,  # CTR = 2.5%
            conversions=5  # Conversion rate = 2%
        )
        
        # Should be performing well (good CTR, conversion rate, and ranking)
        assert product_keyword.is_performing_well() is True
        
        # Test poor performance
        product_keyword.clicks = 50  # CTR = 0.5% (too low)
        assert product_keyword.is_performing_well() is False
    
    def test_needs_optimization(self, test_product, test_keyword):
        """Test optimization need detection"""
        product_keyword = ProductKeyword(
            product_id=test_product.id,
            keyword_id=test_keyword.id,
            relevance_score=Decimal('0.8'),
            current_ranking=25,  # Poor ranking
            target_ranking=10,
            clicks=10,
            impressions=5000  # Low CTR
        )
        
        # Should need optimization (poor ranking and low CTR)
        assert product_keyword.needs_optimization() is True
        
        # Test good performance
        product_keyword.current_ranking = 5
        product_keyword.clicks = 150  # Better CTR
        assert product_keyword.needs_optimization() is False
    
    def test_get_ranking_improvement(self, test_product, test_keyword):
        """Test ranking improvement calculation"""
        product_keyword = ProductKeyword(
            product_id=test_product.id,
            keyword_id=test_keyword.id,
            relevance_score=Decimal('0.8'),
            current_ranking=20,
            target_ranking=5
        )
        
        improvement = product_keyword.get_ranking_improvement()
        assert improvement == 15  # 20 - 5
        
        # Test when already at target
        product_keyword.current_ranking = 3
        improvement = product_keyword.get_ranking_improvement()
        assert improvement == 0  # max(0, 3 - 5)
    
    def test_update_performance_metrics(self, test_product, test_keyword):
        """Test updating performance metrics"""
        product_keyword = ProductKeyword(
            product_id=test_product.id,
            keyword_id=test_keyword.id,
            relevance_score=Decimal('0.8')
        )
        
        product_keyword.update_performance_metrics(
            clicks=200,
            impressions=8000,
            conversions=10
        )
        
        assert product_keyword.clicks == 200
        assert product_keyword.impressions == 8000
        assert product_keyword.conversions == 10
    
    def test_update_ranking(self, test_product, test_keyword):
        """Test updating ranking"""
        product_keyword = ProductKeyword(
            product_id=test_product.id,
            keyword_id=test_keyword.id,
            relevance_score=Decimal('0.8')
        )
        
        product_keyword.update_ranking(8)
        
        assert product_keyword.current_ranking == 8
        assert product_keyword.last_ranking_check is not None
    
    def test_unique_product_keyword_constraint(self, test_product, test_keyword):
        """Test that product + keyword must be unique"""
        # Create first relationship
        with get_db_session() as db:
            pk1 = ProductKeyword(
                product_id=test_product.id,
                keyword_id=test_keyword.id,
                relevance_score=Decimal('0.8')
            )
            db.add(pk1)
            db.commit()
        
        # Try to create second relationship with same product + keyword
        with pytest.raises(Exception):  # Will catch the database error
            with get_db_session() as db:
                pk2 = ProductKeyword(
                    product_id=test_product.id,
                    keyword_id=test_keyword.id,  # Same combination
                    relevance_score=Decimal('0.5')
                )
                db.add(pk2)
                # Commit will fail due to unique constraint
    
    def test_to_dict_includes_computed_fields(self, test_product, test_keyword):
        """Test that to_dict includes computed fields"""
        product_keyword = ProductKeyword(
            product_id=test_product.id,
            keyword_id=test_keyword.id,
            relevance_score=Decimal('0.85'),
            current_ranking=12,
            target_ranking=5,
            clicks=150,
            impressions=6000,
            conversions=8
        )
        
        data = product_keyword.to_dict()
        
        # Should include computed fields
        assert "ctr" in data
        assert "conversion_rate" in data
        assert "is_performing_well" in data
        assert "needs_optimization" in data
        assert "ranking_improvement_needed" in data
        assert "keyword_data" in data
        
        # Should include basic fields
        assert data["product_id"] == str(test_product.id)
        assert data["keyword_id"] == str(test_keyword.id)
        assert float(data["relevance_score"]) == 0.85
        assert data["current_ranking"] == 12