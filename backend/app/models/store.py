"""
Store model for Shopify store data and configuration
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from typing import Dict, Any, Optional, List
import re
from datetime import datetime

from app.models.base import BaseModel

class Store(BaseModel):
    """
    Store model representing a connected Shopify store
    """
    __tablename__ = "stores"
    
    # Shopify store identification
    shopify_domain = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Shopify store domain (e.g., example.myshopify.com)"
    )
    
    shopify_access_token = Column(
        Text,
        nullable=False,
        comment="Encrypted Shopify access token for API calls"
    )
    
    # Store information
    store_name = Column(
        String(255),
        nullable=False,
        comment="Display name of the Shopify store"
    )
    
    owner_email = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Email address of the store owner"
    )
    
    plan_name = Column(
        String(100),
        nullable=True,
        comment="Shopify plan name (Basic, Shopify, Advanced, Plus)"
    )
    
    timezone = Column(
        String(100),
        nullable=True,
        default="UTC",
        comment="Store timezone"
    )
    
    currency = Column(
        String(10),
        nullable=True,
        default="USD",
        comment="Store primary currency code"
    )
    
    # Sync and status tracking
    last_sync_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful data synchronization"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the store is active and should be processed"
    )
    
    # Store configuration and settings
    settings = Column(
        JSONB,
        default=lambda: {},
        nullable=False,
        comment="Store-specific settings and configuration"
    )
    
    # Statistics and metrics (denormalized for performance)
    product_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Cached count of products in the store"
    )
    
    last_analysis_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last SEO analysis"
    )
    
    # Relationships
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    seo_analyses = relationship("SEOAnalysis", back_populates="store", cascade="all, delete-orphan")
    
    @validates('shopify_domain')
    def validate_shopify_domain(self, key: str, domain: str) -> str:
        """
        Validate Shopify domain format
        """
        if not domain:
            raise ValueError("Shopify domain cannot be empty")
        
        # Remove protocol if present
        domain = domain.replace('https://', '').replace('http://', '')
        
        # Check if it's a valid Shopify domain
        if not domain.endswith('.myshopify.com'):
            if '.' not in domain:
                # Assume it's just the shop name, add .myshopify.com
                domain = f"{domain}.myshopify.com"
            else:
                raise ValueError("Domain must be a valid Shopify domain (*.myshopify.com)")
        
        # Validate domain format
        domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]\.myshopify\.com$'
        if not re.match(domain_pattern, domain):
            raise ValueError("Invalid Shopify domain format")
        
        return domain.lower()
    
    @validates('owner_email')
    def validate_owner_email(self, key: str, email: str) -> str:
        """
        Validate email format
        """
        if not email:
            raise ValueError("Owner email cannot be empty")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email.lower()
    
    @validates('currency')
    def validate_currency(self, key: str, currency: str) -> str:
        """
        Validate currency code format
        """
        if currency and len(currency) != 3:
            raise ValueError("Currency code must be 3 characters (ISO 4217)")
        
        return currency.upper() if currency else currency
    
    @validates('plan_name')
    def validate_plan_name(self, key: str, plan: str) -> str:
        """
        Validate Shopify plan name
        """
        valid_plans = [
            'Basic Shopify', 'Shopify', 'Advanced Shopify', 'Shopify Plus',
            'Basic', 'Professional', 'Unlimited', 'Plus',  # Legacy names
            'Starter', 'Development'  # Special plans
        ]
        
        if plan and plan not in valid_plans:
            # Don't raise error, just log warning for unknown plans
            # This allows for new plans that we haven't seen yet
            pass
        
        return plan
    
    def get_shop_name(self) -> str:
        """
        Extract shop name from domain
        """
        if self.shopify_domain:
            return self.shopify_domain.replace('.myshopify.com', '')
        return ""
    
    def is_sync_needed(self, max_age_hours: int = 24) -> bool:
        """
        Check if store data sync is needed
        """
        if not self.last_sync_at:
            return True
        
        from datetime import timedelta
        max_age = timedelta(hours=max_age_hours)
        return datetime.utcnow() - self.last_sync_at > max_age
    
    def update_sync_timestamp(self) -> None:
        """
        Update the last sync timestamp to now
        """
        self.last_sync_at = func.now()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value from the settings JSONB field
        """
        if not self.settings:
            return default
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a setting value in the settings JSONB field
        """
        if not self.settings:
            self.settings = {}
        
        # Create a new dict to trigger SQLAlchemy change detection
        new_settings = dict(self.settings)
        new_settings[key] = value
        self.settings = new_settings
    
    def get_api_url(self) -> str:
        """
        Get the Shopify Admin API URL for this store
        """
        return f"https://{self.shopify_domain}/admin/api/2023-10"

    def get_decrypted_token(self) -> Optional[str]:
        """
        Get decrypted access token for API calls

        Returns:
            Decrypted access token or None if not available
        """
        if not self.shopify_access_token:
            return None

        try:
            from app.core.encryption import decrypt_token
            return decrypt_token(self.shopify_access_token)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to decrypt token for {self.shopify_domain}: {e}")
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert store to dictionary, excluding sensitive data
        """
        data = super().to_dict()
        
        # Remove sensitive information
        if 'shopify_access_token' in data:
            data['shopify_access_token'] = '***REDACTED***'
        
        # Add computed fields
        data['shop_name'] = self.get_shop_name()
        data['sync_needed'] = self.is_sync_needed()
        data['api_url'] = self.get_api_url()
        
        return data
    
    def __repr__(self) -> str:
        """
        String representation of the store
        """
        return f"<Store(domain={self.shopify_domain}, name={self.store_name})>"