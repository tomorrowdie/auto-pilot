"""
Pydantic schemas for Keyword model validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class KeywordBase(BaseModel):
    """Base keyword schema"""
    
    keyword: str = Field(..., min_length=1, description="The keyword phrase")
    search_volume: Optional[int] = Field(None, ge=0, description="Monthly search volume")
    keyword_difficulty: Optional[int] = Field(None, ge=0, le=100, description="Keyword difficulty score")
    cpc: Optional[Decimal] = Field(None, ge=0, description="Cost per click in USD")
    competition_level: Optional[str] = Field(None, description="Competition level")
    search_intent: Optional[str] = Field(None, description="Search intent")
    category: Optional[str] = Field(None, description="Keyword category")
    source: str = Field("manual", description="Source of keyword data")
    trend_score: Optional[int] = Field(None, ge=-100, le=100, description="Trend score")
    seasonal_pattern: Optional[str] = Field(None, description="Seasonal pattern")
    
    @validator('competition_level')
    def validate_competition_level(cls, v):
        """Validate competition level"""
        if v is not None:
            valid_levels = ['low', 'medium', 'high']
            if v.lower() not in valid_levels:
                raise ValueError(f"Competition level must be one of: {', '.join(valid_levels)}")
            return v.lower()
        return v
    
    @validator('search_intent')
    def validate_search_intent(cls, v):
        """Validate search intent"""
        if v is not None:
            valid_intents = ['informational', 'navigational', 'commercial', 'transactional']
            if v.lower() not in valid_intents:
                raise ValueError(f"Search intent must be one of: {', '.join(valid_intents)}")
            return v.lower()
        return v

class KeywordCreate(KeywordBase):
    """Schema for creating a keyword"""
    pass

class KeywordUpdate(BaseModel):
    """Schema for updating a keyword"""
    
    search_volume: Optional[int] = Field(None, ge=0, description="Monthly search volume")
    keyword_difficulty: Optional[int] = Field(None, ge=0, le=100, description="Keyword difficulty score")
    cpc: Optional[Decimal] = Field(None, ge=0, description="Cost per click in USD")
    competition_level: Optional[str] = Field(None, description="Competition level")
    search_intent: Optional[str] = Field(None, description="Search intent")
    category: Optional[str] = Field(None, description="Keyword category")
    trend_score: Optional[int] = Field(None, ge=-100, le=100, description="Trend score")
    seasonal_pattern: Optional[str] = Field(None, description="Seasonal pattern")
    
    @validator('competition_level')
    def validate_competition_level(cls, v):
        """Validate competition level"""
        if v is not None:
            valid_levels = ['low', 'medium', 'high']
            if v.lower() not in valid_levels:
                raise ValueError(f"Competition level must be one of: {', '.join(valid_levels)}")
            return v.lower()
        return v
    
    @validator('search_intent')
    def validate_search_intent(cls, v):
        """Validate search intent"""
        if v is not None:
            valid_intents = ['informational', 'navigational', 'commercial', 'transactional']
            if v.lower() not in valid_intents:
                raise ValueError(f"Search intent must be one of: {', '.join(valid_intents)}")
            return v.lower()
        return v

class KeywordResponse(KeywordBase):
    """Schema for keyword responses"""
    
    id: UUID = Field(..., description="Keyword ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    
    # Computed fields
    opportunity_score: Optional[int] = Field(None, description="Keyword opportunity score")
    is_long_tail: Optional[bool] = Field(None, description="Whether keyword is long-tail")
    word_count: Optional[int] = Field(None, description="Number of words in keyword")
    is_high_volume: Optional[bool] = Field(None, description="Whether keyword has high volume")
    is_low_competition: Optional[bool] = Field(None, description="Whether keyword has low competition")
    is_commercial: Optional[bool] = Field(None, description="Whether keyword has commercial intent")
    estimated_traffic: Optional[int] = Field(None, description="Estimated monthly traffic")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
            Decimal: lambda v: float(v) if v else None
        }

class KeywordList(BaseModel):
    """Schema for paginated keyword list"""
    
    keywords: List[KeywordResponse] = Field(..., description="List of keywords")
    total: int = Field(..., description="Total number of keywords")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(50, description="Items per page")
    has_next: bool = Field(False, description="Whether there are more pages")
    has_prev: bool = Field(False, description="Whether there are previous pages")

class ProductKeywordBase(BaseModel):
    """Base product keyword schema"""
    
    relevance_score: Decimal = Field(..., ge=0, le=1, description="Relevance score")
    current_ranking: Optional[int] = Field(None, gt=0, description="Current ranking position")
    target_ranking: Optional[int] = Field(None, gt=0, description="Target ranking position")
    is_primary: bool = Field(False, description="Whether this is a primary keyword")

class ProductKeywordCreate(ProductKeywordBase):
    """Schema for creating product keyword relationship"""
    
    product_id: UUID = Field(..., description="Product ID")
    keyword_id: UUID = Field(..., description="Keyword ID")

class ProductKeywordUpdate(BaseModel):
    """Schema for updating product keyword relationship"""
    
    relevance_score: Optional[Decimal] = Field(None, ge=0, le=1, description="Relevance score")
    current_ranking: Optional[int] = Field(None, gt=0, description="Current ranking position")
    target_ranking: Optional[int] = Field(None, gt=0, description="Target ranking position")
    is_primary: Optional[bool] = Field(None, description="Whether this is a primary keyword")
    clicks: Optional[int] = Field(None, ge=0, description="Number of clicks")
    impressions: Optional[int] = Field(None, ge=0, description="Number of impressions")
    conversions: Optional[int] = Field(None, ge=0, description="Number of conversions")

class ProductKeywordResponse(ProductKeywordBase):
    """Schema for product keyword responses"""
    
    id: UUID = Field(..., description="Product keyword ID")
    product_id: UUID = Field(..., description="Product ID")
    keyword_id: UUID = Field(..., description="Keyword ID")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    last_ranking_check: Optional[datetime] = Field(None, description="Last ranking check")
    
    # Performance metrics
    clicks: int = Field(0, description="Number of clicks")
    impressions: int = Field(0, description="Number of impressions")
    conversions: int = Field(0, description="Number of conversions")
    
    # Computed fields
    ctr: Optional[float] = Field(None, description="Click-through rate")
    conversion_rate: Optional[float] = Field(None, description="Conversion rate")
    is_performing_well: Optional[bool] = Field(None, description="Whether keyword is performing well")
    needs_optimization: Optional[bool] = Field(None, description="Whether keyword needs optimization")
    ranking_improvement_needed: Optional[int] = Field(None, description="Ranking improvement needed")
    keyword_data: Optional[Dict[str, Any]] = Field(None, description="Associated keyword data")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
            Decimal: lambda v: float(v) if v else None
        }

class ProductKeywordList(BaseModel):
    """Schema for paginated product keyword list"""
    
    product_keywords: List[ProductKeywordResponse] = Field(..., description="List of product keywords")
    total: int = Field(..., description="Total number of product keywords")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(50, description="Items per page")
    has_next: bool = Field(False, description="Whether there are more pages")
    has_prev: bool = Field(False, description="Whether there are previous pages")

class KeywordResearch(BaseModel):
    """Schema for keyword research request"""
    
    seed_keywords: List[str] = Field(..., description="Seed keywords for research")
    store_id: UUID = Field(..., description="Store ID")
    product_id: Optional[UUID] = Field(None, description="Product ID (optional)")
    sources: List[str] = Field(["amazon", "google"], description="Research sources")
    max_results: int = Field(100, description="Maximum results per source")
    min_search_volume: int = Field(10, description="Minimum search volume")
    max_keyword_difficulty: int = Field(80, description="Maximum keyword difficulty")

class KeywordResearchResponse(BaseModel):
    """Schema for keyword research response"""
    
    task_id: str = Field(..., description="Background task ID")
    status: str = Field(..., description="Research status")
    seed_keywords: List[str] = Field(..., description="Seed keywords used")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    progress: int = Field(0, description="Research progress percentage")

class KeywordGapAnalysis(BaseModel):
    """Schema for keyword gap analysis"""
    
    store_id: UUID = Field(..., description="Store ID")
    competitor_domains: List[str] = Field(..., description="Competitor domains")
    product_categories: Optional[List[str]] = Field(None, description="Product categories to analyze")
    max_results: int = Field(100, description="Maximum results")

class KeywordGapAnalysisResponse(BaseModel):
    """Schema for keyword gap analysis response"""
    
    missing_opportunities: List[Dict[str, Any]] = Field(..., description="Missing keyword opportunities")
    competitive_keywords: List[Dict[str, Any]] = Field(..., description="Competitive keywords")
    untapped_keywords: List[Dict[str, Any]] = Field(..., description="Untapped keywords")
    analysis_summary: Dict[str, Any] = Field(..., description="Analysis summary")
    
    class Config:
        from_attributes = True

class KeywordPerformanceReport(BaseModel):
    """Schema for keyword performance report"""
    
    product_id: UUID = Field(..., description="Product ID")
    date_range: Dict[str, str] = Field(..., description="Date range for report")
    
    top_performing_keywords: List[ProductKeywordResponse] = Field(..., description="Top performing keywords")
    underperforming_keywords: List[ProductKeywordResponse] = Field(..., description="Underperforming keywords")
    keyword_opportunities: List[KeywordResponse] = Field(..., description="Keyword opportunities")
    
    performance_summary: Dict[str, Any] = Field(..., description="Performance summary")
    recommendations: List[str] = Field(..., description="Optimization recommendations")
    
    class Config:
        from_attributes = True