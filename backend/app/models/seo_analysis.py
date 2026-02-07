"""
SEO Analysis model for storing SEO audit results and recommendations
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from app.models.base import BaseModel

class AnalysisType(str, Enum):
    """Types of SEO analysis"""
    PRODUCT = "product"
    PAGE = "page"
    SITE = "site"
    TECHNICAL = "technical"
    CONTENT = "content"
    KEYWORD = "keyword"

class AnalysisStatus(str, Enum):
    """Status of SEO analysis"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class IssueSeverity(str, Enum):
    """Severity levels for SEO issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SEOAnalysis(BaseModel):
    """
    SEO Analysis model for storing analysis results and recommendations
    """
    __tablename__ = "seo_analyses"
    
    # Foreign keys
    store_id = Column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the store this analysis belongs to"
    )
    
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Reference to the product (null for site-wide analysis)"
    )
    
    # Analysis metadata
    analysis_type = Column(
        SQLEnum(AnalysisType),
        nullable=False,
        index=True,
        comment="Type of SEO analysis performed"
    )
    
    status = Column(
        SQLEnum(AnalysisStatus),
        default=AnalysisStatus.PENDING,
        nullable=False,
        index=True,
        comment="Current status of the analysis"
    )
    
    url = Column(
        String(500),
        nullable=True,
        comment="URL that was analyzed (if applicable)"
    )
    
    # Analysis results
    seo_score = Column(
        Integer,
        nullable=True,
        comment="Overall SEO score (0-100)"
    )
    
    title_score = Column(
        Integer,
        nullable=True,
        comment="Title optimization score (0-100)"
    )
    
    description_score = Column(
        Integer,
        nullable=True,
        comment="Meta description score (0-100)"
    )
    
    content_score = Column(
        Integer,
        nullable=True,
        comment="Content quality score (0-100)"
    )
    
    technical_score = Column(
        Integer,
        nullable=True,
        comment="Technical SEO score (0-100)"
    )
    
    keyword_score = Column(
        Integer,
        nullable=True,
        comment="Keyword optimization score (0-100)"
    )
    
    # Detailed analysis data
    issues = Column(
        JSONB,
        default=lambda: [],
        nullable=False,
        comment="List of SEO issues found"
    )
    
    recommendations = Column(
        JSONB,
        default=lambda: [],
        nullable=False,
        comment="List of SEO recommendations"
    )
    
    technical_metrics = Column(
        JSONB,
        default=lambda: {},
        nullable=False,
        comment="Technical SEO metrics (page speed, mobile-friendly, etc.)"
    )
    
    content_metrics = Column(
        JSONB,
        default=lambda: {},
        nullable=False,
        comment="Content analysis metrics (word count, readability, etc.)"
    )
    
    keyword_metrics = Column(
        JSONB,
        default=lambda: {},
        nullable=False,
        comment="Keyword analysis metrics (density, relevance, etc.)"
    )
    
    # Analysis metadata
    analyzed_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        comment="When the analysis was performed"
    )
    
    analysis_duration = Column(
        Integer,
        nullable=True,
        comment="Analysis duration in seconds"
    )
    
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if analysis failed"
    )
    
    # Relationships
    store = relationship("Store", back_populates="seo_analyses")
    product = relationship("Product", back_populates="seo_analyses")
    
    @validates('seo_score', 'title_score', 'description_score', 'content_score', 'technical_score', 'keyword_score')
    def validate_score(self, key: str, score: int) -> int:
        """Validate that scores are between 0 and 100"""
        if score is not None and (score < 0 or score > 100):
            raise ValueError(f"{key} must be between 0 and 100")
        return score
    
    def add_issue(self, issue_type: str, severity: IssueSeverity, title: str, 
                  description: str, affected_elements: Optional[List[str]] = None,
                  recommendation: Optional[str] = None) -> None:
        """Add an SEO issue to the analysis"""
        issue = {
            "type": issue_type,
            "severity": severity.value,
            "title": title,
            "description": description,
            "affected_elements": affected_elements or [],
            "recommendation": recommendation,
            "detected_at": datetime.utcnow().isoformat()
        }
        
        if not self.issues:
            self.issues = []
        
        # Create a new list to trigger SQLAlchemy change detection
        new_issues = list(self.issues)
        new_issues.append(issue)
        self.issues = new_issues
    
    def add_recommendation(self, category: str, priority: str, title: str,
                          description: str, impact: str, effort: str,
                          current_value: Optional[str] = None,
                          suggested_value: Optional[str] = None) -> None:
        """Add an SEO recommendation to the analysis"""
        recommendation = {
            "category": category,
            "priority": priority,
            "title": title,
            "description": description,
            "impact": impact,
            "effort": effort,
            "current_value": current_value,
            "suggested_value": suggested_value,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if not self.recommendations:
            self.recommendations = []
        
        # Create a new list to trigger SQLAlchemy change detection
        new_recommendations = list(self.recommendations)
        new_recommendations.append(recommendation)
        self.recommendations = new_recommendations
    
    def set_technical_metric(self, key: str, value: Any) -> None:
        """Set a technical SEO metric"""
        if not self.technical_metrics:
            self.technical_metrics = {}
        
        new_metrics = dict(self.technical_metrics)
        new_metrics[key] = value
        self.technical_metrics = new_metrics
    
    def set_content_metric(self, key: str, value: Any) -> None:
        """Set a content analysis metric"""
        if not self.content_metrics:
            self.content_metrics = {}
        
        new_metrics = dict(self.content_metrics)
        new_metrics[key] = value
        self.content_metrics = new_metrics
    
    def set_keyword_metric(self, key: str, value: Any) -> None:
        """Set a keyword analysis metric"""
        if not self.keyword_metrics:
            self.keyword_metrics = {}
        
        new_metrics = dict(self.keyword_metrics)
        new_metrics[key] = value
        self.keyword_metrics = new_metrics
    
    def get_issues_by_severity(self, severity: IssueSeverity) -> List[Dict[str, Any]]:
        """Get issues filtered by severity"""
        if not self.issues:
            return []
        
        return [issue for issue in self.issues if issue.get("severity") == severity.value]
    
    def get_critical_issues_count(self) -> int:
        """Get count of critical issues"""
        return len(self.get_issues_by_severity(IssueSeverity.CRITICAL))
    
    def get_high_issues_count(self) -> int:
        """Get count of high priority issues"""
        return len(self.get_issues_by_severity(IssueSeverity.HIGH))
    
    def get_total_issues_count(self) -> int:
        """Get total count of issues"""
        return len(self.issues) if self.issues else 0
    
    def get_recommendations_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """Get recommendations filtered by priority"""
        if not self.recommendations:
            return []
        
        return [rec for rec in self.recommendations if rec.get("priority") == priority]
    
    def calculate_overall_score(self) -> int:
        """Calculate overall SEO score from component scores"""
        scores = []
        weights = {
            'title_score': 0.25,
            'description_score': 0.20,
            'content_score': 0.25,
            'technical_score': 0.20,
            'keyword_score': 0.10
        }
        
        total_weight = 0
        weighted_sum = 0
        
        for score_field, weight in weights.items():
            score = getattr(self, score_field)
            if score is not None:
                weighted_sum += score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0
        
        overall_score = int(weighted_sum / total_weight)
        self.seo_score = overall_score
        return overall_score
    
    def mark_completed(self, duration_seconds: Optional[int] = None) -> None:
        """Mark analysis as completed"""
        self.status = AnalysisStatus.COMPLETED
        self.analyzed_at = func.now()
        if duration_seconds:
            self.analysis_duration = duration_seconds
        
        # Calculate overall score if component scores exist
        self.calculate_overall_score()
    
    def mark_failed(self, error_message: str) -> None:
        """Mark analysis as failed with error message"""
        self.status = AnalysisStatus.FAILED
        self.error_message = error_message
        self.analyzed_at = func.now()
    
    def is_completed(self) -> bool:
        """Check if analysis is completed"""
        return self.status == AnalysisStatus.COMPLETED
    
    def is_failed(self) -> bool:
        """Check if analysis failed"""
        return self.status == AnalysisStatus.FAILED
    
    def needs_attention(self) -> bool:
        """Check if analysis needs attention (has critical or high issues)"""
        critical_count = self.get_critical_issues_count()
        high_count = self.get_high_issues_count()
        return critical_count > 0 or high_count > 2
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary with computed fields"""
        data = super().to_dict()
        
        # Add computed fields
        data['critical_issues_count'] = self.get_critical_issues_count()
        data['high_issues_count'] = self.get_high_issues_count()
        data['total_issues_count'] = self.get_total_issues_count()
        data['needs_attention'] = self.needs_attention()
        data['is_completed'] = self.is_completed()
        data['is_failed'] = self.is_failed()
        
        # Add analysis summary
        if self.is_completed():
            data['analysis_summary'] = {
                'overall_score': self.seo_score,
                'component_scores': {
                    'title': self.title_score,
                    'description': self.description_score,
                    'content': self.content_score,
                    'technical': self.technical_score,
                    'keyword': self.keyword_score
                },
                'issues_by_severity': {
                    'critical': self.get_critical_issues_count(),
                    'high': self.get_high_issues_count(),
                    'medium': len(self.get_issues_by_severity(IssueSeverity.MEDIUM)),
                    'low': len(self.get_issues_by_severity(IssueSeverity.LOW))
                }
            }
        
        return data
    
    def __repr__(self) -> str:
        """String representation of the analysis"""
        return f"<SEOAnalysis(id={self.id}, type={self.analysis_type}, score={self.seo_score})>"