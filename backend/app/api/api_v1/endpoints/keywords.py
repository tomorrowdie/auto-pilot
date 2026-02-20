"""
Keyword research and analysis endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def keywords_health():
    """Health check for keywords endpoints"""
    return {"status": "healthy", "service": "keywords"}

@router.post("/")
async def create_keyword(keyword_data: dict, db: Session = Depends(get_db)):
    """
    Create a new keyword (for testing Keyword model)
    """
    from app.models.keyword import Keyword
    from decimal import Decimal
    
    try:
        keyword = Keyword(
            keyword=keyword_data.get("keyword"),
            search_volume=keyword_data.get("search_volume"),
            keyword_difficulty=keyword_data.get("keyword_difficulty"),
            cpc=Decimal(str(keyword_data.get("cpc"))) if keyword_data.get("cpc") else None,
            competition_level=keyword_data.get("competition_level"),
            search_intent=keyword_data.get("search_intent"),
            category=keyword_data.get("category"),
            source=keyword_data.get("source", "manual"),
            trend_score=keyword_data.get("trend_score"),
            seasonal_pattern=keyword_data.get("seasonal_pattern")
        )
        
        db.add(keyword)
        db.commit()
        db.refresh(keyword)
        
        return keyword.to_dict()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{keyword_id}")
async def get_keyword(keyword_id: str, db: Session = Depends(get_db)):
    """
    Get keyword details
    """
    from app.models.keyword import Keyword
    from uuid import UUID
    
    try:
        keyword_uuid = UUID(keyword_id)
        keyword = db.query(Keyword).filter(Keyword.id == keyword_uuid).first()
        
        if not keyword:
            raise HTTPException(status_code=404, detail="Keyword not found")
        
        return keyword.to_dict()
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid keyword ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/product-keywords/")
async def create_product_keyword(pk_data: dict, db: Session = Depends(get_db)):
    """
    Create a product-keyword relationship (for testing ProductKeyword model)
    """
    from app.models.keyword import ProductKeyword
    from uuid import UUID
    from decimal import Decimal
    
    try:
        product_keyword = ProductKeyword(
            product_id=UUID(pk_data.get("product_id")),
            keyword_id=UUID(pk_data.get("keyword_id")),
            relevance_score=Decimal(str(pk_data.get("relevance_score", "0.5"))),
            current_ranking=pk_data.get("current_ranking"),
            target_ranking=pk_data.get("target_ranking"),
            is_primary=pk_data.get("is_primary", False)
        )
        
        db.add(product_keyword)
        db.commit()
        db.refresh(product_keyword)
        
        return product_keyword.to_dict()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search")
async def search_keywords(
    query: str = Query(..., description="Search term"),
    source: str = Query("all", description="Keyword source: amazon, google, or all"),
    limit: int = Query(50, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """
    Search keywords in database
    """
    from app.models.keyword import Keyword
    
    try:
        # Simple search implementation
        keywords_query = db.query(Keyword)
        
        if query:
            keywords_query = keywords_query.filter(Keyword.keyword.ilike(f"%{query}%"))
        
        if source != "all":
            keywords_query = keywords_query.filter(Keyword.source == source)
        
        keywords = keywords_query.limit(limit).all()
        
        return {
            "keywords": [keyword.to_dict() for keyword in keywords],
            "total": len(keywords),
            "query": query,
            "source": source
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))