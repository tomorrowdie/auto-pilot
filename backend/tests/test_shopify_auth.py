"""
Unit tests for Shopify OAuth service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from app.services.shopify_auth import ShopifyOAuthService, ShopifyAuthError
from app.models.store import Store
from app.core.database_utils import get_db_session, create_all_tables

class TestShopifyOAuthService:
    """Test cases for Shopify OAuth service"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup test database"""
        create_all_tables()
        yield
    
    @pytest.fixture
    def oauth_service(self):
        """Create OAuth service instance"""
        with patch('app.services.shopify_auth.settings') as mock_settings:
            mock_settings.SHOPIFY_API_KEY = "test_api_key"
            mock_settings.SHOPIFY_API_SECRET = "test_api_secret"
            mock_settings.SHOPIFY_SCOPES = "read_products,write_products"
            mock_settings.SHOPIFY_APP_URL = "https://test-app.com"
            
            return ShopifyOAuthService()
    
    def test_oauth_service_initialization(self, oauth_service):
        """Test OAuth service initialization"""
        assert oauth_service.api_key == "test_api_key"
        assert oauth_service.api_secret == "test_api_secret"
        assert oauth_service.scopes == "read_products,write_products"
        assert oauth_service.app_url == "https://test-app.com"
    
    def test_oauth_service_missing_credentials(self):
        """Test OAuth service with missing credentials"""
        with patch('app.services.shopify_auth.settings') as mock_settings:
            mock_settings.SHOPIFY_API_KEY = None
            mock_settings.SHOPIFY_API_SECRET = None
            
            with pytest.raises(ShopifyAuthError, match="Shopify API credentials not configured"):
                ShopifyOAuthService()
    
    def test_normalize_shop_domain(self, oauth_service):
        """Test shop domain normalization"""
        # Test various domain formats
        assert oauth_service._normalize_shop_domain("test-shop") == "test-shop.myshopify.com"
        assert oauth_service._normalize_shop_domain("test-shop.myshopify.com") == "test-shop.myshopify.com"
        assert oauth_service._normalize_shop_domain("https://test-shop.myshopify.com") == "test-shop.myshopify.com"
        assert oauth_service._normalize_shop_domain("TEST-SHOP.MYSHOPIFY.COM") == "test-shop.myshopify.com"
        
        # Test invalid domains
        with pytest.raises(ShopifyAuthError, match="Invalid shop domain"):
            oauth_service._normalize_shop_domain("invalid.com")
        
        with pytest.raises(ShopifyAuthError, match="Invalid shop domain format"):
            oauth_service._normalize_shop_domain("invalid..domain.myshopify.com")
    
    def test_is_valid_shop_domain(self, oauth_service):
        """Test shop domain validation"""
        # Valid domains
        assert oauth_service._is_valid_shop_domain("test-shop.myshopify.com") is True
        assert oauth_service._is_valid_shop_domain("a.myshopify.com") is True
        assert oauth_service._is_valid_shop_domain("test123.myshopify.com") is True
        
        # Invalid domains
        assert oauth_service._is_valid_shop_domain("-test.myshopify.com") is False
        assert oauth_service._is_valid_shop_domain("test-.myshopify.com") is False
        assert oauth_service._is_valid_shop_domain("test..shop.myshopify.com") is False
        assert oauth_service._is_valid_shop_domain("test.com") is False
    
    def test_generate_install_url(self, oauth_service):
        """Test OAuth install URL generation"""
        result = oauth_service.generate_install_url("test-shop")
        
        assert "install_url" in result
        assert "state" in result
        assert "shop_domain" in result
        assert result["shop_domain"] == "test-shop.myshopify.com"
        assert "test-shop.myshopify.com/admin/oauth/authorize" in result["install_url"]
        assert "client_id=test_api_key" in result["install_url"]
        assert "scope=read_products,write_products" in result["install_url"]
        assert f"state={result['state']}" in result["install_url"]
    
    def test_generate_install_url_with_custom_state(self, oauth_service):
        """Test OAuth install URL generation with custom state"""
        custom_state = "custom_state_123"
        result = oauth_service.generate_install_url("test-shop", custom_state)
        
        assert result["state"] == custom_state
        assert f"state={custom_state}" in result["install_url"]
    
    def test_verify_hmac_valid(self, oauth_service):
        """Test HMAC verification with valid signature"""
        import hmac
        import hashlib
        
        params = {
            "shop": "test-shop.myshopify.com",
            "code": "test_code",
            "state": "test_state",
            "timestamp": "1234567890"
        }
        
        # Generate valid HMAC
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        expected_hmac = hmac.new(
            "test_api_secret".encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        assert oauth_service._verify_hmac(params, expected_hmac) is True
    
    def test_verify_hmac_invalid(self, oauth_service):
        """Test HMAC verification with invalid signature"""
        params = {
            "shop": "test-shop.myshopify.com",
            "code": "test_code",
            "state": "test_state",
            "timestamp": "1234567890"
        }
        
        invalid_hmac = "invalid_signature"
        assert oauth_service._verify_hmac(params, invalid_hmac) is False
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self, oauth_service):
        """Test successful code exchange for access token"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {"access_token": "test_access_token"}
            mock_response.raise_for_status = Mock()
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            token = await oauth_service._exchange_code_for_token("test-shop.myshopify.com", "test_code")
            assert token == "test_access_token"
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_failure(self, oauth_service):
        """Test failed code exchange"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("HTTP Error")
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(ShopifyAuthError, match="Failed to exchange code for token"):
                await oauth_service._exchange_code_for_token("test-shop.myshopify.com", "test_code")
    
    @pytest.mark.asyncio
    async def test_get_shop_info_success(self, oauth_service):
        """Test successful shop info retrieval"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "shop": {
                    "name": "Test Shop",
                    "email": "test@example.com",
                    "plan_name": "basic",
                    "timezone": "America/New_York",
                    "currency": "USD"
                }
            }
            mock_response.raise_for_status = Mock()
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            shop_info = await oauth_service._get_shop_info("test-shop.myshopify.com", "test_token")
            
            assert shop_info["name"] == "Test Shop"
            assert shop_info["email"] == "test@example.com"
            assert shop_info["plan_name"] == "basic"
    
    @pytest.mark.asyncio
    async def test_get_shop_info_failure(self, oauth_service):
        """Test failed shop info retrieval"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("HTTP Error")
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(ShopifyAuthError, match="Failed to get shop info"):
                await oauth_service._get_shop_info("test-shop.myshopify.com", "test_token")
    
    def test_verify_webhook_valid(self, oauth_service):
        """Test webhook signature verification with valid signature"""
        import base64
        import hmac
        import hashlib
        
        webhook_data = b'{"test": "data"}'
        
        # Generate valid signature
        expected_signature = base64.b64encode(
            hmac.new(
                "test_api_secret".encode('utf-8'),
                webhook_data,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        assert oauth_service.verify_webhook(webhook_data, expected_signature) is True
    
    def test_verify_webhook_invalid(self, oauth_service):
        """Test webhook signature verification with invalid signature"""
        webhook_data = b'{"test": "data"}'
        invalid_signature = "invalid_signature"
        
        assert oauth_service.verify_webhook(webhook_data, invalid_signature) is False
    
    def test_encrypt_decrypt_token(self, oauth_service):
        """Test token encryption and decryption"""
        original_token = "test_access_token_123"
        
        encrypted = oauth_service._encrypt_token(original_token)
        decrypted = oauth_service._decrypt_token(encrypted)
        
        assert encrypted != original_token  # Should be encrypted
        assert decrypted == original_token  # Should decrypt back to original
    
    @pytest.mark.asyncio
    async def test_handle_callback_success(self, oauth_service):
        """Test successful OAuth callback handling"""
        with patch.object(oauth_service, '_verify_hmac', return_value=True), \
             patch.object(oauth_service, '_exchange_code_for_token', return_value="test_token"), \
             patch.object(oauth_service, '_get_shop_info', return_value={"name": "Test Shop"}), \
             patch.object(oauth_service, '_create_or_update_store') as mock_create_store:
            
            mock_store = Mock()
            mock_store.to_dict.return_value = {"id": 1, "shopify_domain": "test-shop.myshopify.com"}
            mock_create_store.return_value = mock_store
            
            result = await oauth_service.handle_callback(
                shop="test-shop.myshopify.com",
                code="test_code",
                state="test_state",
                hmac_signature="test_hmac",
                timestamp="1234567890"
            )
            
            assert "store" in result
            assert "access_token" in result
            assert "shop_info" in result
    
    @pytest.mark.asyncio
    async def test_handle_callback_invalid_hmac(self, oauth_service):
        """Test OAuth callback with invalid HMAC"""
        with patch.object(oauth_service, '_verify_hmac', return_value=False):
            
            with pytest.raises(ShopifyAuthError, match="Invalid HMAC signature"):
                await oauth_service.handle_callback(
                    shop="test-shop.myshopify.com",
                    code="test_code",
                    state="test_state",
                    hmac_signature="invalid_hmac",
                    timestamp="1234567890"
                )
    
    @pytest.mark.asyncio
    async def test_handle_callback_old_timestamp(self, oauth_service):
        """Test OAuth callback with old timestamp"""
        from datetime import datetime, timedelta
        
        # Create timestamp that's more than 1 hour old
        old_timestamp = str(int((datetime.utcnow() - timedelta(hours=2)).timestamp()))
        
        with patch.object(oauth_service, '_verify_hmac', return_value=True):
            
            with pytest.raises(ShopifyAuthError, match="Callback timestamp too old"):
                await oauth_service.handle_callback(
                    shop="test-shop.myshopify.com",
                    code="test_code",
                    state="test_state",
                    hmac_signature="test_hmac",
                    timestamp=old_timestamp
                )shopify.com") is False
        assert oauth_service._is_valid_shop_domain("test.com") is False
        assert oauth_service._is_valid_shop_domain("") is False
    
    def test_generate_install_url(self, oauth_service):
        """Test OAuth install URL generation"""
        result = oauth_service.generate_install_url("test-shop")
        
        assert "install_url" in result
        assert "state" in result
        assert "shop_domain" in result
        assert result["shop_domain"] == "test-shop.myshopify.com"
        assert "https://test-shop.myshopify.com/admin/oauth/authorize" in result["install_url"]
        assert "client_id=test_api_key" in result["install_url"]
        assert "scope=read_products%2Cwrite_products" in result["install_url"]
        assert f"state={result['state']}" in result["install_url"]
    
    def test_generate_install_url_with_state(self, oauth_service):
        """Test OAuth install URL generation with custom state"""
        custom_state = "custom_state_123"
        result = oauth_service.generate_install_url("test-shop", state=custom_state)
        
        assert result["state"] == custom_state
        assert f"state={custom_state}" in result["install_url"]
    
    def test_verify_hmac_valid(self, oauth_service):
        """Test HMAC verification with valid signature"""
        import hmac
        import hashlib
        
        params = {
            "shop": "test-shop.myshopify.com",
            "code": "test_code",
            "state": "test_state",
            "timestamp": "1234567890"
        }
        
        # Generate valid HMAC
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        expected_hmac = hmac.new(
            "test_api_secret".encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        assert oauth_service._verify_hmac(params, expected_hmac) is True
    
    def test_verify_hmac_invalid(self, oauth_service):
        """Test HMAC verification with invalid signature"""
        params = {
            "shop": "test-shop.myshopify.com",
            "code": "test_code",
            "state": "test_state",
            "timestamp": "1234567890"
        }
        
        invalid_hmac = "invalid_signature"
        assert oauth_service._verify_hmac(params, invalid_hmac) is False
    
    def test_verify_webhook_valid(self, oauth_service):
        """Test webhook verification with valid signature"""
        import hmac
        import hashlib
        import base64
        
        webhook_data = b'{"test": "data"}'
        
        # Generate valid signature
        expected_signature = base64.b64encode(
            hmac.new(
                "test_api_secret".encode('utf-8'),
                webhook_data,
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        
        result = oauth_service.verify_webhook(webhook_data, expected_signature)
        assert result is True
    
    def test_verify_webhook_invalid(self, oauth_service):
        """Test webhook verification with invalid signature"""
        webhook_data = b'{"test": "data"}'
        invalid_signature = "invalid_signature"
        
        result = oauth_service.verify_webhook(webhook_data, invalid_signature)
        assert result is False
    
    def test_encrypt_decrypt_token(self, oauth_service):
        """Test token encryption and decryption"""
        original_token = "test_access_token_123"
        
        encrypted = oauth_service._encrypt_token(original_token)
        decrypted = oauth_service._decrypt_token(encrypted)
        
        assert encrypted != original_token  # Should be encrypted
        assert decrypted == original_token  # Should decrypt back to original
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self, oauth_service):
        """Test successful code exchange for access token"""
        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "test_access_token"}
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            token = await oauth_service._exchange_code_for_token("test-shop.myshopify.com", "test_code")
            assert token == "test_access_token"
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_failure(self, oauth_service):
        """Test failed code exchange"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(ShopifyAuthError, match="Failed to exchange code for token"):
                await oauth_service._exchange_code_for_token("test-shop.myshopify.com", "test_code")
    
    @pytest.mark.asyncio
    async def test_get_shop_info_success(self, oauth_service):
        """Test successful shop info retrieval"""
        mock_shop_data = {
            "shop": {
                "name": "Test Shop",
                "email": "test@example.com",
                "plan_name": "basic",
                "timezone": "America/New_York",
                "currency": "USD"
            }
        }
        
        mock_response = Mock()
        mock_response.json.return_value = mock_shop_data
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            shop_info = await oauth_service._get_shop_info("test-shop.myshopify.com", "test_token")
            assert shop_info == mock_shop_data["shop"]
    
    @pytest.mark.asyncio
    async def test_get_shop_info_failure(self, oauth_service):
        """Test failed shop info retrieval"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            with pytest.raises(ShopifyAuthError, match="Failed to get shop info"):
                await oauth_service._get_shop_info("test-shop.myshopify.com", "test_token")
    
    @pytest.mark.asyncio
    async def test_handle_callback_success(self, oauth_service):
        """Test successful OAuth callback handling"""
        # Mock all the async methods
        with patch.object(oauth_service, '_verify_hmac', return_value=True), \
             patch.object(oauth_service, '_exchange_code_for_token', return_value="test_token"), \
             patch.object(oauth_service, '_get_shop_info', return_value={"name": "Test Shop"}), \
             patch.object(oauth_service, '_create_or_update_store') as mock_create_store:
            
            mock_store = Mock()
            mock_store.to_dict.return_value = {"id": 1, "shopify_domain": "test-shop.myshopify.com"}
            mock_create_store.return_value = mock_store
            
            result = await oauth_service.handle_callback(
                shop="test-shop.myshopify.com",
                code="test_code",
                state="test_state",
                hmac_signature="test_hmac",
                timestamp="1234567890"
            )
            
            assert "store" in result
            assert "access_token" in result
            assert "shop_info" in result
            assert result["access_token"] == "test_token"
    
    @pytest.mark.asyncio
    async def test_handle_callback_invalid_hmac(self, oauth_service):
        """Test OAuth callback with invalid HMAC"""
        with patch.object(oauth_service, '_verify_hmac', return_value=False):
            with pytest.raises(ShopifyAuthError, match="Invalid HMAC signature"):
                await oauth_service.handle_callback(
                    shop="test-shop.myshopify.com",
                    code="test_code",
                    state="test_state",
                    hmac_signature="invalid_hmac",
                    timestamp="1234567890"
                )
    
    @pytest.mark.asyncio
    async def test_handle_callback_old_timestamp(self, oauth_service):
        """Test OAuth callback with old timestamp"""
        import time
        old_timestamp = str(int(time.time()) - 7200)  # 2 hours ago
        
        with patch.object(oauth_service, '_verify_hmac', return_value=True):
            with pytest.raises(ShopifyAuthError, match="Callback timestamp too old"):
                await oauth_service.handle_callback(
                    shop="test-shop.myshopify.com",
                    code="test_code",
                    state="test_state",
                    hmac_signature="test_hmac",
                    timestamp=old_timestamp
                )
    
    @pytest.mark.asyncio
    async def test_revoke_token_success(self, oauth_service):
        """Test successful token revocation"""
        mock_store = Mock()
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store
        
        with patch('app.services.shopify_auth.get_db', return_value=iter([mock_db])):
            result = await oauth_service.revoke_token("test-shop.myshopify.com", "test_token")
            assert result is True
            mock_db.delete.assert_called_once_with(mock_store)
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_token_store_not_found(self, oauth_service):
        """Test token revocation when store not found"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.services.shopify_auth.get_db', return_value=iter([mock_db])):
            result = await oauth_service.revoke_token("test-shop.myshopify.com", "test_token")
            assert result is False