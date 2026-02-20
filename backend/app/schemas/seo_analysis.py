"""
Pydantic schemas for SEO Analysis model validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

class AnalysisTypeEnum(str, Enum):
    """Types of SEO analysis"""
    PRODUCT = "product"
    PAGE = "page"
    SITE = "site"
    TECHNICAL = "technical"
    CONTENT = "content"
    KEYWORD = "keyword"

class AnalysisStatusEnum(str, Enum):
    """Status of SEO analysis"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class IssueSeverityEnum(str, Enum):
    """Severity levels for SEO issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SEOIssue(BaseModel):
    """Schema for SEO issue"""
    type: str = Field(..., description="Type of SEO issue")
    severity: IssueSeverityEnum = Field(..., description="Issue severity level")
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Issue description")
    affected_elements: List[str] = Field(default_factory=list, description="Affected elements")
    recommendation: Optional[str] = Field(None, description="Recommendation to fix the issue")
    detected_at: str = Field(..., description="When the issue was detected")

class SEORecommendation(BaseModel):
    """Schema for SEO recommendation"""
    category: str = Field(..., description="Recommendation category")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Recommendation description")
    impact: str = Field(..., description="Expected impact")
    effort: str = Field(..., description="Implementation effort required")
    current_value: Optional[str] = Field(None, description="Current value")
    suggested_value: Optional[str] = Field(None, description="Suggested value")
    created_at: str = Field(..., description="When the recommendation was created")

class SEOAnalysisBase(BaseModel):
    """Base SEO analysis schema"""
    
    analysis_type: AnalysisTypeEnum = Field(..., description="Type of analysis")
    url: Optional[str] = Field(None, max_length=500, description="URL analyzed")
    
    # Scores
    seo_score: Optional[int] = Field(None, ge=0, le=100, description="Overall SEO score")
    title_score: Optional[int] = Field(None, ge=0, le=100, description="Title score")
    description_score: Optional[int] = Field(None, ge=0, le=100, description="Description score")
    content_score: Optional[int] = Field(None, ge=0, le=100, description="Content score")
    technical_score: Optional[int] = Field(None, ge=0, le=100, description="Technical score")
    keyword_score: Optional[int] = Field(None, ge=0, le=100, description="Keyword score")
    
    # Analysis data
    issues: List[SEOIssue] = Field(default_factory=list, description="SEO issues found")
    recommendations: List[SEORecommendation] = Field(default_factory=list, description="SEO recommendations")
    technical_metrics: Dict[str, Any] = Field(default_factory=dict, description="Technical metrics")
    content_metrics: Dict[str, Any] = Field(default_factory=dict, description="Content metrics")
    keyword_metrics: Dict[str, Any] = Field(default_factory=dict, description="Keyword metrics")

class SEOAnalysisCreate(SEOAnalysisBase):
    """Schema for creating SEO analysis"""
    
    store_id: UUID = Field(..., description="Store ID")
    product_id: Optional[UUID] = Field(None, description="Product ID (optional)")

class SEOAnalysisUpdate(BaseModel):
    """Schema for updating SEO analysis"""
    
    status: Optional[AnalysisStatusEnum] = Field(None, description="Analysis status")
    url: Optional[str] = Field(None, max_length=500, description="URL analyzed")
    
    # Scores
    seo_score: Optional[int] = Field(None, ge=0, le=100, description="Overall SEO score")
    title_score: Optional[int] = Field(None, ge=0, le=100, description="Title score")
    description_score: Optional[int] = Field(None, ge=0, le=100, description="Description score")
    content_score: Optional[int] = Field(None, ge=0, le=100, description="Content score")
    technical_score: Optional[int] = Field(None, ge=0, le=100, description="Technical score")
    keyword_score: Optional[int] = Field(None, ge=0, le=100, description="Keyword score")
    
    # Analysis data
    issues: Optional[List[SEOIssue]] = Field(None, description="SEO issues found")
    recommendations: Optional[List[SEORecommendation]] = Field(None, description="SEO recommendations")
    technical_metrics: Optional[Dict[str, Any]] = Field(None, description="Technical metrics")
    content_metrics: Optional[Dict[str, Any]] = Field(None, description="Content metrics")
    keyword_metrics: Optional[Dict[str, Any]] = Field(None, description="Keyword metrics")
    
    error_message: Optional[str] = Field(None, description="Error message if failed")

class SEOAnalysisResponse(SEOAnalysisBase):
    """Schema for SEO analysis responses"""
    
    id: UUID = Field(..., description="Analysis ID")
    store_id: UUID = Field(..., description="Store ID")
    product_id: Optional[UUID] = Field(None, description="Product ID")
    status: AnalysisStatusEnum = Field(..., description="Analysis status")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    analyzed_at: datetime = Field(..., description="Analysis timestamp")
    analysis_duration: Optional[int] = Field(None, description="Analysis duration in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Computed fields
    critical_issues_count: Optional[int] = Field(None, description="Count of critical issues")
    high_issues_count: Optional[int] = Field(None, description="Count of high priority issues")
    total_issues_count: Optional[int] = Field(None, description="Total issues count")
    needs_attention: Optional[bool] = Field(None, description="Whether analysis needs attention")
    is_completed: Optional[bool] = Field(None, description="Whether analysis is completed")
    is_failed: Optional[bool] = Field(None, description="Whether analysis failed")
    analysis_summary: Optional[Dict[str, Any]] = Field(None, description="Analysis summary")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

class SEOAnalysisList(BaseModel):
    """Schema for paginated SEO analysis list"""
    
    analyses: List[SEOAnalysisResponse] = Field(..., description="List of analyses")
    total: int = Field(..., description="Total number of analyses")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(50, description="Items per page")
    has_next: bool = Field(False, description="Whether there are more pages")
    has_prev: bool = Field(False, description="Whether there are previous pages")

class SEOAnalysisTask(BaseModel):
    """Schema for SEO analysis task creation"""
    
    task_id: str = Field(..., description="Background task ID")
    analysis_id: UUID = Field(..., description="Analysis ID")
    status: str = Field(..., description="Task status")
    estimated_duration: Optional[str] = Field(None, description="Estimated completion time")
    progress: int = Field(0, description="Task progress percentage")
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: lambda v: str(v)
        }

class SEOScoreBreakdown(BaseModel):
    """Schema for SEO score breakdown"""
    
    overall_score: int = Field(..., ge=0, le=100, description="Overall SEO score")
    title_score: int = Field(..., ge=0, le=100, description="Title optimization score")
    description_score: int = Field(..., ge=0, le=100, description="Meta description score")
    content_score: int = Field(..., ge=0, le=100, description="Content quality score")
    technical_score: int = Field(..., ge=0, le=100, description="Technical SEO score")
    keyword_score: int = Field(..., ge=0, le=100, description="Keyword optimization score")
    
    score_factors: Dict[str, Any] = Field(..., description="Factors affecting each score")
    improvement_potential: int = Field(..., description="Potential score improvement")
    priority_areas: List[str] = Field(..., description="Areas needing priority attention")

class SEOComparisonReport(BaseModel):
    """Schema for SEO comparison report"""
    
    current_analysis: SEOAnalysisResponse = Field(..., description="Current analysis")
    previous_analysis: Optional[SEOAnalysisResponse] = Field(None, description="Previous analysis")
    
    score_changes: Dict[str, int] = Field(..., description="Score changes")
    new_issues: List[SEOIssue] = Field(..., description="New issues found")
    resolved_issues: List[SEOIssue] = Field(..., description="Issues that were resolved")
    improvement_summary: str = Field(..., description="Summary of improvements")
    
    class Config:
        from_attributes = True