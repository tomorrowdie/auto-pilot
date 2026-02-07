"""
Unit tests for SEO Analysis model
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.models.seo_analysis import SEOAnalysis, AnalysisType, AnalysisStatus, IssueSeverity
from app.models.store import Store
from app.models.product import Product
from app.core.database_utils import get_db_session, create_all_tables

class TestSEOAnalysisModel:
    """Test cases for SEO Analysis model"""
    
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
    
    def test_seo_analysis_creation_valid(self, test_store, test_product):
        """Test creating SEO analysis with valid data"""
        with get_db_session() as db:
            analysis = SEOAnalysis(
                store_id=test_store.id,
                product_id=test_product.id,
                analysis_type=AnalysisType.PRODUCT,
                status=AnalysisStatus.PENDING,
                url="https://example.com/product",
                seo_score=85,
                title_score=90,
                description_score=80,
                content_score=85,
                technical_score=75,
                keyword_score=88
            )
            
            db.add(analysis)
            db.commit()
            
            assert analysis.id is not None
            assert analysis.store_id == test_store.id
            assert analysis.product_id == test_product.id
            assert analysis.analysis_type == AnalysisType.PRODUCT
            assert analysis.status == AnalysisStatus.PENDING
            assert analysis.seo_score == 85
    
    def test_score_validation(self, test_store):
        """Test score validation"""
        analysis = SEOAnalysis(
            store_id=test_store.id,
            analysis_type=AnalysisType.SITE,
            status=AnalysisStatus.PENDING
        )
        
        # Test valid scores
        analysis.seo_score = 0
        assert analysis.seo_score == 0
        
        analysis.seo_score = 100
        assert analysis.seo_score == 100
        
        # Test invalid scores
        with pytest.raises(ValueError, match="seo_score must be between 0 and 100"):
            analysis.seo_score = -1
        
        with pytest.raises(ValueError, match="seo_score must be between 0 and 100"):
            analysis.seo_score = 101
    
    def test_add_issue(self, test_store):
        """Test adding SEO issues"""
        analysis = SEOAnalysis(
            store_id=test_store.id,
            analysis_type=AnalysisType.TECHNICAL,
            status=AnalysisStatus.PROCESSING
        )
        
        analysis.add_issue(
            issue_type="meta_description",
            severity=IssueSeverity.HIGH,
            title="Missing meta description",
            description="Page is missing meta description",
            affected_elements=["page1.html", "page2.html"],
            recommendation="Add unique meta descriptions to all pages"
        )
        
        assert len(analysis.issues) == 1
        issue = analysis.issues[0]
        assert issue["type"] == "meta_description"
        assert issue["severity"] == "high"
        assert issue["title"] == "Missing meta description"
        assert len(issue["affected_elements"]) == 2
    
    def test_add_recommendation(self, test_store):
        """Test adding SEO recommendations"""
        analysis = SEOAnalysis(
            store_id=test_store.id,
            analysis_type=AnalysisType.CONTENT,
            status=AnalysisStatus.PROCESSING
        )
        
        analysis.add_recommendation(
            category="title",
            priority="high",
            title="Optimize page title",
            description="Page title should be more descriptive",
            impact="high",
            effort="low",
            current_value="Product",
            suggested_value="Premium Product - Best Quality"
        )
        
        assert len(analysis.recommendations) == 1
        rec = analysis.recommendations[0]
        assert rec["category"] == "title"
        assert rec["priority"] == "high"
        assert rec["current_value"] == "Product"
        assert rec["suggested_value"] == "Premium Product - Best Quality"
    
    def test_set_metrics(self, test_store):
        """Test setting various metrics"""
        analysis = SEOAnalysis(
            store_id=test_store.id,
            analysis_type=AnalysisType.TECHNICAL,
            status=AnalysisStatus.PROCESSING
        )
        
        # Test technical metrics
        analysis.set_technical_metric("page_speed", 85)
        analysis.set_technical_metric("mobile_friendly", True)
        
        assert analysis.technical_metrics["page_speed"] == 85
        assert analysis.technical_metrics["mobile_friendly"] is True
        
        # Test content metrics
        analysis.set_content_metric("word_count", 500)
        analysis.set_content_metric("readability_score", 75)
        
        assert analysis.content_metrics["word_count"] == 500
        assert analysis.content_metrics["readability_score"] == 75
        
        # Test keyword metrics
        analysis.set_keyword_metric("keyword_density", 0.02)
        analysis.set_keyword_metric("primary_keyword", "test product")
        
        assert analysis.keyword_metrics["keyword_density"] == 0.02
        assert analysis.keyword_metrics["primary_keyword"] == "test product"
    
    def test_get_issues_by_severity(self, test_store):
        """Test filtering issues by severity"""
        analysis = SEOAnalysis(
            store_id=test_store.id,
            analysis_type=AnalysisType.SITE,
            status=AnalysisStatus.PROCESSING
        )
        
        # Add issues of different severities
        analysis.add_issue("issue1", IssueSeverity.CRITICAL, "Critical Issue", "Description")
        analysis.add_issue("issue2", IssueSeverity.HIGH, "High Issue", "Description")
        analysis.add_issue("issue3", IssueSeverity.CRITICAL, "Another Critical", "Description")
        analysis.add_issue("issue4", IssueSeverity.LOW, "Low Issue", "Description")
        
        critical_issues = analysis.get_issues_by_severity(IssueSeverity.CRITICAL)
        high_issues = analysis.get_issues_by_severity(IssueSeverity.HIGH)
        
        assert len(critical_issues) == 2
        assert len(high_issues) == 1
        assert analysis.get_critical_issues_count() == 2
        assert analysis.get_high_issues_count() == 1
        assert analysis.get_total_issues_count() == 4
    
    def test_calculate_overall_score(self, test_store):
        """Test overall score calculation"""
        analysis = SEOAnalysis(
            store_id=test_store.id,
            analysis_type=AnalysisType.PRODUCT,
            status=AnalysisStatus.PROCESSING,
            title_score=80,
            description_score=70,
            content_score=90,
            technical_score=85,
            keyword_score=75
        )
        
        overall_score = analysis.calculate_overall_score()
        
        # Expected: (80*0.25 + 70*0.20 + 90*0.25 + 85*0.20 + 75*0.10) = 80.5 -> 80
        assert overall_score == 80
        assert analysis.seo_score == 80
    
    def test_mark_completed(self, test_store):
        """Test marking analysis as completed"""
        analysis = SEOAnalysis(
            store_id=test_store.id,
            analysis_type=AnalysisType.PRODUCT,
            status=AnalysisStatus.PROCESSING,
            title_score=85,
            description_score=80
        )
        
        analysis.mark_completed(duration_seconds=120)
        
        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.analysis_duration == 120
        assert analysis.is_completed() is True
        assert analysis.is_failed() is False
    
    def test_mark_failed(self, test_store):
        """Test marking analysis as failed"""
        analysis = SEOAnalysis(
            store_id=test_store.id,
            analysis_type=AnalysisType.SITE,
            status=AnalysisStatus.PROCESSING
        )
        
        analysis.mark_failed("Network timeout error")
        
        assert analysis.status == AnalysisStatus.FAILED
        assert analysis.error_message == "Network timeout error"
        assert analysis.is_failed() is True
        assert analysis.is_completed() is False
    
    def test_needs_attention(self, test_store):
        """Test needs attention logic"""
        analysis = SEOAnalysis(
            store_id=test_store.id,
            analysis_type=AnalysisType.SITE,
            status=AnalysisStatus.COMPLETED
        )
        
        # No issues - should not need attention
        assert analysis.needs_attention() is False
        
        # Add critical issue - should need attention
        analysis.add_issue("critical", IssueSeverity.CRITICAL, "Critical", "Description")
        assert analysis.needs_attention() is True
        
        # Remove critical, add 3 high issues - should need attention
        analysis.issues = []
        for i in range(3):
            analysis.add_issue(f"high{i}", IssueSeverity.HIGH, f"High {i}", "Description")
        assert analysis.needs_attention() is True
        
        # Only 2 high issues - should not need attention
        analysis.issues = analysis.issues[:2]
        assert analysis.needs_attention() is False
    
    def test_to_dict_includes_computed_fields(self, test_store):
        """Test that to_dict includes computed fields"""
        analysis = SEOAnalysis(
            store_id=test_store.id,
            analysis_type=AnalysisType.PRODUCT,
            status=AnalysisStatus.COMPLETED,
            seo_score=85,
            title_score=90,
            description_score=80
        )
        
        # Add some issues
        analysis.add_issue("issue1", IssueSeverity.CRITICAL, "Critical", "Description")
        analysis.add_issue("issue2", IssueSeverity.HIGH, "High", "Description")
        
        data = analysis.to_dict()
        
        # Should include computed fields
        assert "critical_issues_count" in data
        assert "high_issues_count" in data
        assert "total_issues_count" in data
        assert "needs_attention" in data
        assert "is_completed" in data
        assert "is_failed" in data
        assert "analysis_summary" in data
        
        assert data["critical_issues_count"] == 1
        assert data["high_issues_count"] == 1
        assert data["total_issues_count"] == 2
        assert data["is_completed"] is True
        assert data["analysis_summary"]["overall_score"] == 85
    
    def test_analysis_repr(self, test_store):
        """Test string representation"""
        analysis = SEOAnalysis(
            store_id=test_store.id,
            analysis_type=AnalysisType.PRODUCT,
            status=AnalysisStatus.COMPLETED,
            seo_score=85
        )
        
        repr_str = repr(analysis)
        assert "SEOAnalysis" in repr_str
        assert "PRODUCT" in repr_str
        assert "85" in repr_str