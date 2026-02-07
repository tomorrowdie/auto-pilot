"""
Store management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def stores_health():
    """Health check for stores endpoints"""
    return {"status": "healthy", "service": "stores"}

@router.post("/")
async def create_store(store_data: dict, db: Session = Depends(get_db)):
    """
    Create a new store (for testing Store model)
    """
    from app.models.store import Store
    
    try:
        store = Store(
            shopify_domain=store_data.get("shopify_domain"),
            shopify_access_token=store_data.get("shopify_access_token"),
            store_name=store_data.get("store_name"),
            owner_email=store_data.get("owner_email"),
            plan_name=store_data.get("plan_name"),
            timezone=store_data.get("timezone", "UTC"),
            currency=store_data.get("currency", "USD")
        )
        
        db.add(store)
        db.commit()
        db.refresh(store)
        
        return store.to_dict()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{store_id}")
async def get_store(store_id: str, db: Session = Depends(get_db)):
    """
    Get store details and current sync status
    """
    from app.models.store import Store
    from uuid import UUID
    
    try:
        store_uuid = UUID(store_id)
        store = db.query(Store).filter(Store.id == store_uuid).first()
        
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        return store.to_dict()
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid store ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{store_id}/sync")
async def trigger_store_sync(store_id: str, db: Session = Depends(get_db)):
    """
    Trigger manual data synchronization
    TODO: Implement in task 4.3
    """
    return {
        "message": f"Trigger sync for store {store_id} endpoint",
        "status": "not_implemented",
        "next_task": "4.3 - Implement background tasks for data synchronization"
    }