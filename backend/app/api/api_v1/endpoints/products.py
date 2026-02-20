"""
Product management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def products_health():
    """Health check for products endpoints"""
    return {"status": "healthy", "service": "products"}

@router.post("/")
async def create_product(product_data: dict, db: Session = Depends(get_db)):
    """
    Create a new product (for testing Product model)
    """
    from app.models.product import Product
    from uuid import UUID
    
    try:
        product = Product(
            store_id=UUID(product_data.get("store_id")),
            shopify_product_id=product_data.get("shopify_product_id"),
            title=product_data.get("title"),
            handle=product_data.get("handle"),
            description=product_data.get("description"),
            product_type=product_data.get("product_type"),
            vendor=product_data.get("vendor"),
            tags=product_data.get("tags", []),
            status=product_data.get("status", "draft"),
            seo_title=product_data.get("seo_title"),
            seo_description=product_data.get("seo_description"),
            images=product_data.get("images", []),
            variants=product_data.get("variants", [])
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return product.to_dict()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{product_id}")
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """
    Get product details with SEO data
    """
    from app.models.product import Product
    from uuid import UUID
    
    try:
        product_uuid = UUID(product_id)
        product = db.query(Product).filter(Product.id == product_uuid).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product.to_dict()
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/store/{store_id}")
async def get_store_products(store_id: str, db: Session = Depends(get_db)):
    """
    Get all products for a store
    """
    from app.models.product import Product
    from uuid import UUID
    
    try:
        store_uuid = UUID(store_id)
        products = db.query(Product).filter(Product.store_id == store_uuid).all()
        
        return {
            "products": [product.to_dict() for product in products],
            "total": len(products)
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid store ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))