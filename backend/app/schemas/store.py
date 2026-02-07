"""
Pydantic schemas for Store model validation
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import re

class StoreBase(BaseModel):
    """Base store schema with common fields"""
    
    shopify_domain: str = Field(
        ...,
        description="Shopify store domain (e.g., example.myshopify.com)",
        example="example.myshopify.com"
    )
    
    store_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Display name of the Shopify store",
        example="Example Store"
    )
    
    owner_email: EmailStr = Field(
        ...,
        description="Email address of the store owner",
        example="owner@example.com"
    )
    
    plan_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Shopify plan name",
        example="Shopify"
    )
    
    timezone: Optional[str] = Field(
        "UTC",
        max_length=100,
        description="Store timezone",
        example="America/New_York"
    )
    
    currency: Optional[str] = Field(
        "USD",
        min_length=3,
        max_length=3,
        description="Store primary currency code (ISO 4217)",
        example="USD"
    )
    
    is_active: Optional[bool] = Field(
        True,
        description="Whether the store is active"
    )
    
    settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Store-specific settings and configuration"
    )
    
    @validator('shopify_domain')
    def validate_shopify_domain(cls, v):
        """Validate Shopify domain format"""
        if not v:
            raise ValueError("Shopify domain cannot be empty")
        
        # Remove protocol if present
        v = v.replace('https://', '').replace('http://', '')
        
        # Check if it's a valid Shopify domain
        if not v.endswith('.myshopify.com'):
            if '.' not in v:
                # Assume it's just the shop name, add .myshopify.com
                v = f"{v}.myshopify.com"
            else:
                raise ValueError("Domain must be a valid Shopify domain (*.myshopify.com)")
        
        # Validate domain format
        domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]\.myshopify\.com$'
        if not re.match(domain_pattern, v):
            raise ValueError("Invalid Shopify domain format")
        
        return v.lower()
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code"""
        if v and len(v) != 3:
            raise ValueError("Currency code must be 3 characters (ISO 4217)")
        return v.upper() if v else v

class StoreCreate(StoreBase):
    """Schema for creating a new store"""
    
    shopify_access_token: str = Field(
        ...,
        description="Shopify access token for API calls",
        example="shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    )
    
    @validator('shopify_access_token')
    def validate_access_token(cls, v):
        """Validate Shopify access token format"""
        if not v:
            raise ValueError("Access token cannot be empty")
        
        # Basic validation - Shopify tokens typically start with 'shpat_'
        if not v.startswith('shpat_') and not v.startswith('shpca_'):
            raise ValueError("Invalid Shopify access token format")
        
        if len(v) < 20:
            raise ValueError("Access token appears to be too short")
        
        return v

class StoreUpdate(BaseModel):
    """Schema for updating an existing store"""
    
    store_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Display name of the Shopify store"
    )
    
    owner_email: Optional[EmailStr] = Field(
        None,
        description="Email address of the store owner"
    )
    
    plan_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Shopify plan name"
    )
    
    timezone: Optional[str] = Field(
        None,
        max_length=100,
        description="Store timezone"
    )
    
    currency: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3,
        description="Store primary currency code"
    )
    
    is_active: Optional[bool] = Field(
        None,
        description="Whether the store is active"
    )
    
    settings: Optional[Dict[str, Any]] = Field(
        None,
        description="Store-specific settings and configuration"
    )
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code"""
        if v and len(v) != 3:
            raise ValueError("Currency code must be 3 characters (ISO 4217)")
        return v.upper() if v else v

class StoreResponse(StoreBase):
    """Schema for store API responses"""
    
    id: UUID = Field(..., description="Unique store identifier")
    created_at: datetime = Field(..., description="Store creation timestamp")
    updated_at: datetime = Field(..., description="Store last update timestamp")
    last_sync_at: Optional[datetime] = Field(None, description="Last sync timestamp")
    last_analysis_at: Optional[datetime] = Field(None, description="Last analysis timestamp")
    product_count: int = Field(0, description="Number of products in the store")
    
    # Computed fields
    shop_name: Optional[str] = Field(None, description="Shop name extracted from domain")
    sync_needed: Optional[bool] = Field(None, description="Whether sync is needed")
    api_url: Optional[str] = Field(None, description="Shopify Admin API URL")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

class StoreList(BaseModel):
    """Schema for paginated store list responses"""
    
    stores: List[StoreResponse] = Field(..., description="List of stores")
    total: int = Field(..., description="Total number of stores")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(50, description="Items per page")
    has_next: bool = Field(False, description="Whether there are more pages")
    has_prev: bool = Field(False, description="Whether there are previous pages")

class StoreSyncStatus(BaseModel):
    """Schema for store sync status"""
    
    store_id: UUID = Field(..., description="Store identifier")
    sync_status: str = Field(..., description="Current sync status")
    last_sync_at: Optional[datetime] = Field(None, description="Last sync timestamp")
    sync_progress: Optional[int] = Field(None, description="Sync progress percentage")
    sync_message: Optional[str] = Field(None, description="Current sync message")
    products_synced: Optional[int] = Field(None, description="Number of products synced")
    errors: Optional[List[str]] = Field(None, description="Sync errors if any")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }