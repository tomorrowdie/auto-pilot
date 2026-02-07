"""
SEO analysis endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def analysis_health():
    """Health check for analysis endpoints"""
    return {"status": "healthy", "service": "analysis"}

@router.post("/")
async def create_analysis(analysis_data: dict, db: Session = Depends(get_db)):
    """
    Create a new SEO analysis (for testing SEOAnalysis model)
    """
    from app.models.seo_analysis import SEOAnalysis, AnalysisType, AnalysisStatus
    from uuid import UUID
    
    try:
        analysis = SEOAnalysis(
            store_id=UUID(analysis_data.get("store_id")),
            product_id=UUID(analysis_data.get("product_id")) if analysis_data.get("product_id") else None,
            analysis_type=AnalysisType(analysis_data.get("analysis_type", "product")),
            status=AnalysisStatus(analysis_data.get("status", "pending")),
            url=analysis_data.get("url"),
            seo_score=analysis_data.get("seo_score"),
            title_score=analysis_data.get("title_score"),
            description_score=analysis_data.get("description_score"),
            content_score=analysis_data.get("content_score"),
            technical_score=analysis_data.get("technical_score"),
            keyword_score=analysis_data.get("keyword_score")
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        return analysis.to_dict()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{analysis_id}")
async def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """
    Get SEO analysis details
    """
    from app.models.seo_analysis import SEOAnalysis
    from uuid import UUID
    
    try:
        analysis_uuid = UUID(analysis_id)
        analysis = db.query(SEOAnalysis).filter(SEOAnalysis.id == analysis_uuid).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return analysis.to_dict()
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid analysis ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/store/{store_id}")
async def get_store_analyses(store_id: str, db: Session = Depends(get_db)):
    """
    Get all analyses for a store
    """
    from app.models.seo_analysis import SEOAnalysis
    from uuid import UUID
    
    try:
        store_uuid = UUID(store_id)
        analyses = db.query(SEOAnalysis).filter(SEOAnalysis.store_id == store_uuid).all()
        
        return {
            "analyses": [analysis.to_dict() for analysis in analyses],
            "total": len(analyses)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid store ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))