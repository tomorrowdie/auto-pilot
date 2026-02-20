"""
Keyword models for SEO keyword research and tracking
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Numeric, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal

from app.models.base import BaseModel

class Keyword(BaseModel):
    """
    Keyword model for storing keyword research data
    """
    __tablename__ = "keywords"
    
    # Keyword data
    keyword = Column(
        Text,
        nullable=False,
        index=True,
        comment="The keyword phrase"
    )
    
    # Search metrics
    search_volume = Column(
        Integer,
        nullable=True,
        comment="Monthly search volume"
    )
    
    keyword_difficulty = Column(
        Integer,
        nullable=True,
        comment="Keyword difficulty score (0-100)"
    )
    
    cpc = Column(
        Numeric(10, 2),
        nullable=True,
        comment="Cost per click in USD"
    )
    
    competition_level = Column(
        String(20),
        nullable=True,
        comment="Competition level (low, medium, high)"
    )
    
    # Keyword classification
    search_intent = Column(
        String(50),
        nullable=True,
        comment="Search intent (informational, navigational, commercial, transactional)"
    )
    
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Keyword category or topic"
    )
    
    source = Column(
        String(50),
        nullable=False,
        default="manual",
        index=True,
        comment="Source of keyword data (amazon, google, manual, etc.)"
    )
    
    # Additional metrics
    trend_score = Column(
        Integer,
        nullable=True,
        comment="Trend score indicating if keyword is trending up/down"
    )
    
    seasonal_pattern = Column(
        String(100),
        nullable=True,
        comment="Seasonal pattern description"
    )
    
    # Relationships
    product_keywords = relationship("ProductKeyword", back_populates="keyword", cascade="all, delete-orphan")
    
    # Composite unique constraint on keyword and source
    __table_args__ = (
        Index('ix_keywords_keyword_source', 'keyword', 'source', unique=True),
        {"comment": "Keywords for SEO research and optimization"}
    )
    
    @validates('keyword_difficulty')
    def validate_keyword_difficulty(self, key: str, difficulty: int) -> int:
        """Validate keyword difficulty is between 0 and 100"""
        if difficulty is not None and (difficulty < 0 or difficulty > 100):
            raise ValueError("Keyword difficulty must be between 0 and 100")
        return difficulty
    
    @validates('competition_level')
    def validate_competition_level(self, key: str, level: str) -> str:
        """Validate competition level"""
        if level is not None:
            valid_levels = ['low', 'medium', 'high']
            if level.lower() not in valid_levels:
                raise ValueError(f"Competition level must be one of: {', '.join(valid_levels)}")
            return level.lower()
        return level
    
    @validates('search_intent')
    def validate_search_intent(self, key: str, intent: str) -> str:
        """Validate search intent"""
        if intent is not None:
            valid_intents = ['informational', 'navigational', 'commercial', 'transactional']
            if intent.lower() not in valid_intents:
                raise ValueError(f"Search intent must be one of: {', '.join(valid_intents)}")
            return intent.lower()
        return intent
    
    def calculate_opportunity_score(self) -> int:
        """Calculate keyword opportunity score based on various factors"""
        score = 0
        
        # Search volume component (40% weight)
        if self.search_volume:
            if self.search_volume >= 10000:
                score += 40
            elif self.search_volume >= 1000:
                score += 30
            elif self.search_volume >= 100:
                score += 20
            else:
                score += 10
        
        # Keyword difficulty component (30% weight) - lower difficulty = higher score
        if self.keyword_difficulty is not None:
            difficulty_score = max(0, 100 - self.keyword_difficulty)
            score += int(difficulty_score * 0.3)
        
        # Competition level component (20% weight)
        if self.competition_level:
            competition_scores = {'low': 20, 'medium': 10, 'high': 5}
            score += competition_scores.get(self.competition_level, 0)
        
        # Commercial intent bonus (10% weight)
        if self.search_intent in ['commercial', 'transactional']:
            score += 10
        elif self.search_intent == 'navigational':
            score += 5
        
        return min(score, 100)
    
    def is_long_tail(self) -> bool:
        """Check if keyword is long-tail (3+ words)"""
        return len(self.keyword.split()) >= 3
    
    def get_word_count(self) -> int:
        """Get number of words in keyword"""
        return len(self.keyword.split())
    
    def is_high_volume(self) -> bool:
        """Check if keyword has high search volume"""
        return self.search_volume and self.search_volume >= 1000
    
    def is_low_competition(self) -> bool:
        """Check if keyword has low competition"""
        return (self.competition_level == 'low' or 
                (self.keyword_difficulty is not None and self.keyword_difficulty <= 30))
    
    def is_commercial(self) -> bool:
        """Check if keyword has commercial intent"""
        return self.search_intent in ['commercial', 'transactional']
    
    def get_estimated_traffic(self, ranking_position: int = 1) -> int:
        """Estimate monthly traffic based on search volume and ranking position"""
        if not self.search_volume:
            return 0
        
        # CTR estimates based on ranking position
        ctr_by_position = {
            1: 0.28, 2: 0.15, 3: 0.11, 4: 0.08, 5: 0.06,
            6: 0.05, 7: 0.04, 8: 0.03, 9: 0.03, 10: 0.02
        }
        
        ctr = ctr_by_position.get(ranking_position, 0.01)
        return int(self.search_volume * ctr)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert keyword to dictionary with computed fields"""
        data = super().to_dict()
        
        # Add computed fields
        data['opportunity_score'] = self.calculate_opportunity_score()
        data['is_long_tail'] = self.is_long_tail()
        data['word_count'] = self.get_word_count()
        data['is_high_volume'] = self.is_high_volume()
        data['is_low_competition'] = self.is_low_competition()
        data['is_commercial'] = self.is_commercial()
        data['estimated_traffic'] = self.get_estimated_traffic()
        
        return data
    
    def __repr__(self) -> str:
        """String representation of the keyword"""
        return f"<Keyword(keyword='{self.keyword}', volume={self.search_volume})>"

class ProductKeyword(BaseModel):
    """
    Junction table for Product-Keyword relationships with additional metadata
    """
    __tablename__ = "product_keywords"
    
    # Foreign keys
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the product"
    )
    
    keyword_id = Column(
        UUID(as_uuid=True),
        ForeignKey("keywords.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the keyword"
    )
    
    # Relationship metadata
    relevance_score = Column(
        Numeric(3, 2),
        nullable=False,
        default=Decimal('0.5'),
        comment="Relevance score between product and keyword (0.00 to 1.00)"
    )
    
    current_ranking = Column(
        Integer,
        nullable=True,
        comment="Current search ranking position for this keyword"
    )
    
    target_ranking = Column(
        Integer,
        nullable=True,
        comment="Target ranking position for this keyword"
    )
    
    is_primary = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is a primary keyword for the product"
    )
    
    # Tracking data
    last_ranking_check = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When ranking was last checked"
    )
    
    ranking_history = Column(
        Text,
        nullable=True,
        comment="JSON string of ranking history"
    )
    
    # Performance metrics
    clicks = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of clicks from this keyword"
    )
    
    impressions = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of impressions for this keyword"
    )
    
    conversions = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of conversions from this keyword"
    )
    
    # Relationships
    product = relationship("Product", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="product_keywords")
    
    # Composite unique constraint
    __table_args__ = (
        Index('ix_product_keywords_product_keyword', 'product_id', 'keyword_id', unique=True),
        {"comment": "Product-Keyword relationships with performance tracking"}
    )
    
    @validates('relevance_score')
    def validate_relevance_score(self, key: str, score: Decimal) -> Decimal:
        """Validate relevance score is between 0 and 1"""
        if score < 0 or score > 1:
            raise ValueError("Relevance score must be between 0.00 and 1.00")
        return score
    
    @validates('current_ranking', 'target_ranking')
    def validate_ranking(self, key: str, ranking: int) -> int:
        """Validate ranking positions are positive"""
        if ranking is not None and ranking <= 0:
            raise ValueError(f"{key} must be a positive integer")
        return ranking
    
    def get_ctr(self) -> float:
        """Calculate click-through rate"""
        if self.impressions == 0:
            return 0.0
        return self.clicks / self.impressions
    
    def get_conversion_rate(self) -> float:
        """Calculate conversion rate"""
        if self.clicks == 0:
            return 0.0
        return self.conversions / self.clicks
    
    def is_performing_well(self) -> bool:
        """Check if keyword is performing well for this product"""
        ctr = self.get_ctr()
        conversion_rate = self.get_conversion_rate()
        
        # Good performance criteria
        return (ctr >= 0.02 and  # 2% CTR or better
                conversion_rate >= 0.01 and  # 1% conversion rate or better
                self.current_ranking and self.current_ranking <= 10)  # Top 10 ranking
    
    def needs_optimization(self) -> bool:
        """Check if keyword needs optimization"""
        return (self.current_ranking is None or 
                self.current_ranking > 20 or
                self.get_ctr() < 0.01 or
                (self.target_ranking and self.current_ranking and 
                 self.current_ranking > self.target_ranking))
    
    def get_ranking_improvement(self) -> Optional[int]:
        """Get ranking improvement needed to reach target"""
        if self.current_ranking and self.target_ranking:
            return max(0, self.current_ranking - self.target_ranking)
        return None
    
    def update_performance_metrics(self, clicks: int, impressions: int, conversions: int) -> None:
        """Update performance metrics"""
        self.clicks = clicks
        self.impressions = impressions
        self.conversions = conversions
    
    def update_ranking(self, new_ranking: int) -> None:
        """Update current ranking and timestamp"""
        self.current_ranking = new_ranking
        self.last_ranking_check = func.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product keyword to dictionary with computed fields"""
        data = super().to_dict()
        
        # Add computed fields
        data['ctr'] = self.get_ctr()
        data['conversion_rate'] = self.get_conversion_rate()
        data['is_performing_well'] = self.is_performing_well()
        data['needs_optimization'] = self.needs_optimization()
        data['ranking_improvement_needed'] = self.get_ranking_improvement()
        
        # Add keyword data
        if self.keyword:
            data['keyword_data'] = {
                'keyword': self.keyword.keyword,
                'search_volume': self.keyword.search_volume,
                'keyword_difficulty': self.keyword.keyword_difficulty,
                'search_intent': self.keyword.search_intent,
                'opportunity_score': self.keyword.calculate_opportunity_score()
            }
        
        return data
    
    def __repr__(self) -> str:
        """String representation of the product keyword relationship"""
        return f"<ProductKeyword(product_id={self.product_id}, keyword_id={self.keyword_id})>"