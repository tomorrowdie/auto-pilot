"""
Authentication endpoints for Shopify OAuth and JWT management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.config import settings
from app.models.store import Store
from app.services.shopify_auth import shopify_oauth, ShopifyAuthError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def auth_health():
    """Health check for auth endpoints"""
    return {"status": "healthy", "service": "authentication"}

@router.post("/shopify/install")
async def initiate_shopify_oauth(request_data: dict):
    """
    Initiate Shopify OAuth installation flow
    
    Expected payload:
    {
        "shop": "example.myshopify.com"
    }
    """
    try:
        shop = request_data.get("shop")
        if not shop:
            raise HTTPException(status_code=400, detail="Shop domain is required")
        
        # Generate install URL
        oauth_data = shopify_oauth.generate_install_url(shop)
        
        return {
            "install_url": oauth_data["install_url"],
            "state": oauth_data["state"],
            "shop_domain": oauth_data["shop_domain"],
            "message": "Redirect user to install_url to complete OAuth flow"
        }
        
    except ShopifyAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"OAuth initiation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth flow")

@router.get("/shopify/callback")
async def handle_shopify_callback(
    shop: str,
    code: str,
    state: str,
    hmac: str,
    timestamp: str
):
    """
    Handle Shopify OAuth callback
    
    This endpoint receives the OAuth callback from Shopify
    """
    try:
        # Handle the OAuth callback
        result = await shopify_oauth.handle_callback(
            shop=shop,
            code=code,
            state=state,
            hmac_signature=hmac,
            timestamp=timestamp
        )
        
        # In a real app, you might redirect to a success page
        # For API testing, we'll return the result
        return {
            "message": "OAuth flow completed successfully",
            "store": result["store"],
            "shop_info": result["shop_info"],
            "success": True
        }
        
    except ShopifyAuthError as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected callback error: {e}")
        raise HTTPException(status_code=500, detail="OAuth callback failed")

@router.post("/shopify/webhook")
async def handle_shopify_webhook(request: Request):
    """
    Handle Shopify webhooks (app uninstall, etc.)
    """
    try:
        # Get raw body and HMAC header
        body = await request.body()
        hmac_header = request.headers.get("X-Shopify-Hmac-Sha256", "")
        
        # Verify webhook signature
        if not shopify_oauth.verify_webhook(body, hmac_header):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse webhook data
        import json
        webhook_data = json.loads(body.decode('utf-8'))
        
        # Handle different webhook types
        webhook_topic = request.headers.get("X-Shopify-Topic", "")
        shop_domain = request.headers.get("X-Shopify-Shop-Domain", "")
        
        if webhook_topic == "app/uninstalled":
            # Handle app uninstall
            logger.info(f"App uninstalled from shop: {shop_domain}")
            # You might want to clean up data or mark store as inactive
            
        return {"status": "webhook processed", "topic": webhook_topic}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@router.post("/logout")
async def logout(request_data: dict, db: Session = Depends(get_db)):
    """
    Logout user and revoke tokens
    
    Expected payload:
    {
        "shop": "example.myshopify.com"
    }
    """
    try:
        shop = request_data.get("shop")
        if not shop:
            raise HTTPException(status_code=400, detail="Shop domain is required")
        
        # Find store and revoke access
        store = db.query(Store).filter(Store.shopify_domain == shop).first()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
        
        # Revoke token (this will delete the store record)
        success = await shopify_oauth.revoke_token(shop, store.shopify_access_token)
        
        if success:
            return {"message": "Successfully logged out", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to revoke access")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/shopify/verify/{shop}")
async def verify_shop_access(shop: str, db: Session = Depends(get_db)):
    """
    Verify if shop has valid access token
    """
    try:
        store = db.query(Store).filter(Store.shopify_domain == shop).first()
        
        if not store:
            return {"verified": False, "message": "Store not found"}
        
        # In a real implementation, you might test the token against Shopify API
        return {
            "verified": True,
            "store": store.to_dict(),
            "message": "Store access verified"
        }
        
    except Exception as e:
        logger.error(f"Verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")