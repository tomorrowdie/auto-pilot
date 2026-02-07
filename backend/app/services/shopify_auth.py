"""
Shopify OAuth 2.0 authentication service
"""

import hmac
import hashlib
import base64
import secrets
from urllib.parse import urlencode, parse_qs
from typing import Dict, Any, Optional, Tuple
import httpx
import logging
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.encryption import encrypt_token, decrypt_token
from app.models.store import Store
from app.core.database import get_db

logger = logging.getLogger(__name__)

class ShopifyAuthError(Exception):
    """Custom exception for Shopify authentication errors"""
    pass

class ShopifyOAuthService:
    """Service for handling Shopify OAuth 2.0 flow"""
    
    def __init__(self):
        self.api_key = settings.SHOPIFY_API_KEY
        self.api_secret = settings.SHOPIFY_API_SECRET
        self.scopes = settings.SHOPIFY_SCOPES
        self.app_url = settings.SHOPIFY_APP_URL or "http://localhost:8000"
        
        if not self.api_key or not self.api_secret:
            raise ShopifyAuthError("Shopify API credentials not configured")
    
    def generate_install_url(self, shop_domain: str, state: Optional[str] = None) -> Dict[str, str]:
        """
        Generate Shopify OAuth installation URL
        
        Args:
            shop_domain: The shop domain (e.g., 'example.myshopify.com')
            state: Optional state parameter for CSRF protection
            
        Returns:
            Dict containing install_url and state
        """
        # Normalize shop domain
        shop_domain = self._normalize_shop_domain(shop_domain)
        
        # Generate state if not provided
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Build OAuth parameters
        oauth_params = {
            'client_id': self.api_key,
            'scope': self.scopes,
            'redirect_uri': f"{self.app_url}/api/v1/auth/shopify/callback",
            'state': state,
            'grant_options[]': 'per-user'  # Optional: for per-user tokens
        }
        
        # Build install URL
        install_url = f"https://{shop_domain}/admin/oauth/authorize?{urlencode(oauth_params)}"
        
        logger.info(f"Generated install URL for shop: {shop_domain}")
        
        return {
            'install_url': install_url,
            'state': state,
            'shop_domain': shop_domain
        }
    
    async def handle_callback(self, shop: str, code: str, state: str, 
                            hmac_signature: str, timestamp: str) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for access token
        
        Args:
            shop: Shop domain
            code: Authorization code from Shopify
            state: State parameter for CSRF protection
            hmac_signature: HMAC signature for verification
            timestamp: Timestamp for replay attack protection
            
        Returns:
            Dict containing store information and access token
        """
        # Normalize shop domain
        shop = self._normalize_shop_domain(shop)
        
        # Verify HMAC signature
        if not self._verify_hmac({
            'shop': shop,
            'code': code,
            'state': state,
            'timestamp': timestamp
        }, hmac_signature):
            raise ShopifyAuthError("Invalid HMAC signature")
        
        # Check timestamp to prevent replay attacks (within 1 hour)
        try:
            callback_time = datetime.fromtimestamp(int(timestamp))
            if datetime.utcnow() - callback_time > timedelta(hours=1):
                raise ShopifyAuthError("Callback timestamp too old")
        except (ValueError, TypeError):
            raise ShopifyAuthError("Invalid timestamp")
        
        # Exchange code for access token
        access_token = await self._exchange_code_for_token(shop, code)
        
        # Get shop information
        shop_info = await self._get_shop_info(shop, access_token)
        
        # Store or update shop in database
        store = await self._create_or_update_store(shop, access_token, shop_info)
        
        logger.info(f"Successfully authenticated shop: {shop}")
        
        return {
            'store': store.to_dict(),
            'access_token': access_token,  # This will be redacted in store.to_dict()
            'shop_info': shop_info
        }
    
    def verify_webhook(self, data: bytes, hmac_header: str) -> bool:
        """
        Verify Shopify webhook HMAC signature
        
        Args:
            data: Raw webhook data
            hmac_header: HMAC signature from webhook header
            
        Returns:
            True if signature is valid
        """
        try:
            # Calculate expected signature
            expected_signature = base64.b64encode(
                hmac.new(
                    self.api_secret.encode('utf-8'),
                    data,
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, hmac_header)
            
        except Exception as e:
            logger.error(f"Webhook verification error: {e}")
            return False
    
    def _normalize_shop_domain(self, shop: str) -> str:
        """
        Normalize shop domain to standard format
        
        Args:
            shop: Shop domain in various formats
            
        Returns:
            Normalized shop domain
        """
        # Remove protocol if present
        shop = shop.replace('https://', '').replace('http://', '')
        
        # Remove trailing slash
        shop = shop.rstrip('/')
        
        # Add .myshopify.com if not present
        if not shop.endswith('.myshopify.com'):
            if '.' not in shop:
                shop = f"{shop}.myshopify.com"
            else:
                raise ShopifyAuthError(f"Invalid shop domain: {shop}")
        
        # Validate domain format
        if not self._is_valid_shop_domain(shop):
            raise ShopifyAuthError(f"Invalid shop domain format: {shop}")
        
        return shop.lower()
    
    def _is_valid_shop_domain(self, shop: str) -> bool:
        """
        Validate shop domain format
        
        Args:
            shop: Shop domain to validate
            
        Returns:
            True if domain is valid
        """
        import re
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]\.myshopify\.com$'
        return bool(re.match(pattern, shop))
    
    def _verify_hmac(self, params: Dict[str, str], hmac_signature: str) -> bool:
        """
        Verify HMAC signature for OAuth callback
        
        Args:
            params: Parameters to verify
            hmac_signature: HMAC signature to verify against
            
        Returns:
            True if signature is valid
        """
        try:
            # Remove hmac and signature from params
            filtered_params = {k: v for k, v in params.items() 
                             if k not in ['hmac', 'signature']}
            
            # Sort parameters and create query string
            sorted_params = sorted(filtered_params.items())
            query_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
            
            # Calculate expected HMAC
            expected_hmac = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_hmac, hmac_signature)
            
        except Exception as e:
            logger.error(f"HMAC verification error: {e}")
            return False
    
    async def _exchange_code_for_token(self, shop: str, code: str) -> str:
        """
        Exchange authorization code for access token
        
        Args:
            shop: Shop domain
            code: Authorization code
            
        Returns:
            Access token
        """
        token_url = f"https://{shop}/admin/oauth/access_token"
        
        payload = {
            'client_id': self.api_key,
            'client_secret': self.api_secret,
            'code': code
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, json=payload)
                response.raise_for_status()
                
                token_data = response.json()
                access_token = token_data.get('access_token')
                
                if not access_token:
                    raise ShopifyAuthError("No access token in response")
                
                return access_token
                
        except httpx.HTTPError as e:
            logger.error(f"Token exchange error: {e}")
            raise ShopifyAuthError(f"Failed to exchange code for token: {e}")
    
    async def _get_shop_info(self, shop: str, access_token: str) -> Dict[str, Any]:
        """
        Get shop information from Shopify API
        
        Args:
            shop: Shop domain
            access_token: Access token
            
        Returns:
            Shop information
        """
        shop_url = f"https://{shop}/admin/api/2023-10/shop.json"
        
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(shop_url, headers=headers)
                response.raise_for_status()
                
                shop_data = response.json()
                return shop_data.get('shop', {})
                
        except httpx.HTTPError as e:
            logger.error(f"Shop info error: {e}")
            raise ShopifyAuthError(f"Failed to get shop info: {e}")
    
    async def _create_or_update_store(self, shop: str, access_token: str, 
                                    shop_info: Dict[str, Any]) -> Store:
        """
        Create or update store in database
        
        Args:
            shop: Shop domain
            access_token: Access token
            shop_info: Shop information from Shopify
            
        Returns:
            Store model instance
        """
        # Encrypt access token (in production, use proper encryption)
        encrypted_token = self._encrypt_token(access_token)
        
        # Get database session
        db = next(get_db())
        
        try:
            # Check if store already exists
            existing_store = db.query(Store).filter(
                Store.shopify_domain == shop
            ).first()
            
            if existing_store:
                # Update existing store
                existing_store.shopify_access_token = encrypted_token
                existing_store.store_name = shop_info.get('name', shop)
                existing_store.owner_email = shop_info.get('email', '')
                existing_store.plan_name = shop_info.get('plan_name')
                existing_store.timezone = shop_info.get('timezone')
                existing_store.currency = shop_info.get('currency')
                
                db.commit()
                db.refresh(existing_store)
                
                logger.info(f"Updated existing store: {shop}")
                return existing_store
            else:
                # Create new store
                new_store = Store(
                    shopify_domain=shop,
                    shopify_access_token=encrypted_token,
                    store_name=shop_info.get('name', shop),
                    owner_email=shop_info.get('email', ''),
                    plan_name=shop_info.get('plan_name'),
                    timezone=shop_info.get('timezone', 'UTC'),
                    currency=shop_info.get('currency', 'USD')
                )
                
                db.add(new_store)
                db.commit()
                db.refresh(new_store)
                
                logger.info(f"Created new store: {shop}")
                return new_store
                
        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {e}")
            raise ShopifyAuthError(f"Failed to save store: {e}")
        finally:
            db.close()
    
    def _encrypt_token(self, token: str) -> str:
        """
        Encrypt access token for storage using Fernet encryption

        Args:
            token: Access token to encrypt

        Returns:
            Encrypted token
        """
        return encrypt_token(token)

    def _decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt access token for use

        Args:
            encrypted_token: Encrypted token

        Returns:
            Decrypted token
        """
        decrypted = decrypt_token(encrypted_token)
        if decrypted is None:
            raise ShopifyAuthError("Failed to decrypt access token")
        return decrypted
    
    async def revoke_token(self, shop: str, access_token: str) -> bool:
        """
        Revoke Shopify access token
        
        Args:
            shop: Shop domain
            access_token: Access token to revoke
            
        Returns:
            True if successful
        """
        # Shopify doesn't have a token revocation endpoint
        # We'll just remove the store from our database
        db = next(get_db())
        
        try:
            store = db.query(Store).filter(
                Store.shopify_domain == shop
            ).first()
            
            if store:
                db.delete(store)
                db.commit()
                logger.info(f"Revoked access for store: {shop}")
                return True
            
            return False
            
        except Exception as e:
            db.rollback()
            logger.error(f"Token revocation error: {e}")
            return False
        finally:
            db.close()

# Global instance
shopify_oauth = ShopifyOAuthService()