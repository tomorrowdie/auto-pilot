"""
Product model for Shopify product data with SEO fields
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID

from app.models.base import BaseModel

class Product(BaseModel):
    """
    Product model representing a Shopify product with SEO data
    """
    __tablename__ = "products"
    
    # Foreign key to store
    store_id = Column(
        "store_id",
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the store this product belongs to"
    )
    
    # Shopify product identification
    shopify_product_id = Column(
        "shopify_product_id",
        Integer,
        nullable=False,
        index=True,
        comment="Shopify product ID from the API"
    )
    
    # Basic product information
    title = Column(
        String(500),
        nullable=False,
        index=True,
        comment="Product title"
    )
    
    handle = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Product handle (URL slug)"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Product description (HTML)"
    )
    
    product_type = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Product type/category"
    )
    
    vendor = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Product vendor/brand"
    )
    
    tags = Column(
        ARRAY(String),
        default=lambda: [],
        nullable=False,
        comment="Product tags array"
    )
    
    status = Column(
        String(50),
        nullable=False,
        default="draft",
        index=True,
        comment="Product status (active, draft, archived)"
    )
    
    # SEO-specific fields
    seo_title = Column(
        String(70),
        nullable=True,
        comment="SEO meta title (max 70 chars recommended)"
    )
    
    seo_description = Column(
        String(160),
        nullable=True,
        comment="SEO meta description (max 160 chars recommended)"
    )
    
    # Product media and variants (stored as JSONB for flexibility)
    images = Column(
        JSONB,
        default=lambda: [],
        nullable=False,
        comment="Product images array with URLs and metadata"
    )
    
    variants = Column(
        JSONB,
        default=lambda: [],
        nullable=False,
        comment="Product variants with pricing and inventory data"
    )
    
    # Shopify timestamps
    published_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the product was published"
    )
    
    # SEO analysis fields
    current_seo_score = Column(
        Integer,
        nullable=True,
        comment="Current SEO score (0-100)"
    )
    
    last_analyzed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When SEO analysis was last performed"
    )
    
    # Performance metrics (denormalized for quick access)
    view_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Cached view count"
    )
    
    conversion_rate = Column(
        Numeric(5, 4),
        nullable=True,
        comment="Product conversion rate (0.0000 to 1.0000)"
    )
    
    # Relationships
    store = relationship("Store", back_populates="products")
    seo_analyses = relationship("SEOAnalysis", back_populates="product", cascade="all, delete-orphan")
    keywords = relationship("ProductKeyword", back_populates="product", cascade="all, delete-orphan")
    
    # Composite unique constraint on store_id and shopify_product_id
    __table_args__ = (
        {"comment": "Products from Shopify stores with SEO analysis data"}
    )
    
    @validates('status')
    def validate_status(self, key: str, status: str) -> str:
        """Validate product status"""
        valid_statuses = ['active', 'draft', 'archived']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return status
    
    @validates('seo_title')
    def validate_seo_title(self, key: str, title: str) -> str:
        """Validate SEO title length"""
        if title and len(title) > 70:
            raise ValueError("SEO title should not exceed 70 characters")
        return title
    
    @validates('seo_description')
    def validate_seo_description(self, key: str, description: str) -> str:
        """Validate SEO description length"""
        if description and len(description) > 160:
            raise ValueError("SEO description should not exceed 160 characters")
        return description
    
    @validates('current_seo_score')
    def validate_seo_score(self, key: str, score: int) -> int:
        """Validate SEO score range"""
        if score is not None and (score < 0 or score > 100):
            raise ValueError("SEO score must be between 0 and 100")
        return score
    
    @validates('conversion_rate')
    def validate_conversion_rate(self, key: str, rate: float) -> float:
        """Validate conversion rate range"""
        if rate is not None and (rate < 0 or rate > 1):
            raise ValueError("Conversion rate must be between 0 and 1")
        return rate
    
    def get_primary_image(self) -> Optional[Dict[str, Any]]:
        """Get the primary product image"""
        if self.images and len(self.images) > 0:
            return self.images[0]
        return None
    
    def get_price_range(self) -> Dict[str, Any]:
        """Get price range from variants"""
        if not self.variants:
            return {"min": None, "max": None, "currency": None}
        
        prices = []
        currency = None
        
        for variant in self.variants:
            if variant.get('price'):
                try:
                    price = float(variant['price'])
                    prices.append(price)
                    if not currency and variant.get('currency'):
                        currency = variant['currency']
                except (ValueError, TypeError):
                    continue
        
        if not prices:
            return {"min": None, "max": None, "currency": currency}
        
        return {
            "min": min(prices),
            "max": max(prices),
            "currency": currency
        }
    
    def get_inventory_total(self) -> int:
        """Get total inventory across all variants"""
        total = 0
        for variant in self.variants:
            if variant.get('inventory_quantity'):
                try:
                    total += int(variant['inventory_quantity'])
                except (ValueError, TypeError):
                    continue
        return total
    
    def is_in_stock(self) -> bool:
        """Check if product has any inventory"""
        return self.get_inventory_total() > 0
    
    def get_variant_count(self) -> int:
        """Get number of variants"""
        return len(self.variants) if self.variants else 0
    
    def has_seo_data(self) -> bool:
        """Check if product has SEO title and description"""
        return bool(self.seo_title and self.seo_description)
    
    def needs_seo_analysis(self, max_age_hours: int = 168) -> bool:  # 1 week default
        """Check if product needs SEO analysis"""
        if not self.last_analyzed_at:
            return True
        
        from datetime import timedelta
        max_age = timedelta(hours=max_age_hours)
        return datetime.utcnow() - self.last_analyzed_at > max_age
    
    def get_shopify_url(self) -> str:
        """Get the Shopify admin URL for this product"""
        if self.store and self.shopify_product_id:
            return f"https://{self.store.shopify_domain}/admin/products/{self.shopify_product_id}"
        return ""
    
    def get_storefront_url(self) -> str:
        """Get the storefront URL for this product"""
        if self.store and self.handle:
            domain = self.store.shopify_domain.replace('.myshopify.com', '')
            return f"https://{domain}.com/products/{self.handle}"
        return ""
    
    def calculate_seo_score(self) -> int:
        """Calculate basic SEO score based on available data"""
        score = 0
        
        # Title optimization (30 points)
        if self.title:
            if len(self.title) >= 10:
                score += 15
            if len(self.title) <= 60:
                score += 15
        
        # SEO title (20 points)
        if self.seo_title:
            score += 20
        
        # SEO description (20 points)
        if self.seo_description:
            score += 20
        
        # Product description (15 points)
        if self.description and len(self.description.strip()) > 50:
            score += 15
        
        # Images (10 points)
        if self.images and len(self.images) > 0:
            score += 10
        
        # Tags (5 points)
        if self.tags and len(self.tags) > 0:
            score += 5
        
        return min(score, 100)
    
    def update_seo_score(self) -> None:
        """Update the current SEO score"""
        self.current_seo_score = self.calculate_seo_score()
        self.last_analyzed_at = func.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary with computed fields"""
        data = super().to_dict()
        
        # Add computed fields
        data['primary_image'] = self.get_primary_image()
        data['price_range'] = self.get_price_range()
        data['inventory_total'] = self.get_inventory_total()
        data['in_stock'] = self.is_in_stock()
        data['variant_count'] = self.get_variant_count()
        data['has_seo_data'] = self.has_seo_data()
        data['needs_seo_analysis'] = self.needs_seo_analysis()
        data['shopify_url'] = self.get_shopify_url()
        data['storefront_url'] = self.get_storefront_url()
        
        # Calculate SEO score if not set
        if not self.current_seo_score:
            data['calculated_seo_score'] = self.calculate_seo_score()
        
        return data
    
    def __repr__(self) -> str:
        """String representation of the product"""
        return f"<Product(id={self.id}, title={self.title[:30]}...)>"