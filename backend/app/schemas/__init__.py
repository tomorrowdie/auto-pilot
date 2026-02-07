"""
Pydantic schemas for API request/response validation
"""

from .store import StoreCreate, StoreUpdate, StoreResponse, StoreList
from .product import ProductCreate, ProductUpdate, ProductResponse, ProductList, ProductSEOAnalysis
from .seo_analysis import (
    SEOAnalysisCreate, SEOAnalysisUpdate, SEOAnalysisResponse, SEOAnalysisList,
    SEOAnalysisTask, SEOScoreBreakdown, SEOComparisonReport
)
from .keyword import (
    KeywordCreate, KeywordUpdate, KeywordResponse, KeywordList,
    ProductKeywordCreate, ProductKeywordUpdate, ProductKeywordResponse, ProductKeywordList,
    KeywordResearch, KeywordGapAnalysis
)

__all__ = [
    # Store schemas
    "StoreCreate", "StoreUpdate", "StoreResponse", "StoreList",
    # Product schemas
    "ProductCreate", "ProductUpdate", "ProductResponse", "ProductList", "ProductSEOAnalysis",
    # SEO Analysis schemas
    "SEOAnalysisCreate", "SEOAnalysisUpdate", "SEOAnalysisResponse", "SEOAnalysisList",
    "SEOAnalysisTask", "SEOScoreBreakdown", "SEOComparisonReport",
    # Keyword schemas
    "KeywordCreate", "KeywordUpdate", "KeywordResponse", "KeywordList",
    "ProductKeywordCreate", "ProductKeywordUpdate", "ProductKeywordResponse", "ProductKeywordList",
    "KeywordResearch", "KeywordGapAnalysis"
]