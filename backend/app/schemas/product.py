"""
Pydantic schemas for Product model validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class ProductBase(BaseModel):
    """Base product schema with common fields"""
    
    shopify_product_id: int = Field(
        ...,
        description="Shopify product ID from the API",
        example=123456789
    )
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Product title",
        example="Premium Cotton T-Shirt"
    )
    
    handle: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Product handle (URL slug)",
        example="premium-cotton-t-shirt"
    )
    
    description: Optional[str] = Field(
        None,
        description="Product description (HTML)",
        example="<p>High-quality cotton t-shirt perfect for everyday wear.</p>"
    )
    
    product_type: Optional[str] = Field(
        None,
        max_length=255,
        description="Product type/category",
        example="T-Shirts"
    )
    
    vendor: Optional[str] = Field(
        None,
        max_length=255,
        description="Product vendor/brand",
        example="Premium Clothing Co."
    )
    
    tags: Optional[List[str]] = Field(
        default_factory=list,
        description="Product tags array",
        example=["cotton", "casual", "comfortable"]
    )
    
    status: str = Field(
        "draft",
        description="Product status",
        example="active"
    )
    
    seo_title: Optional[str] = Field(
        None,
        max_length=70,
        description="SEO meta title (max 70 chars recommended)",
        example="Premium Cotton T-Shirt - Comfortable & Stylish"
    )
    
    seo_description: Optional[str] = Field(
        None,
        max_length=160,
        description="SEO meta description (max 160 chars recommended)",
        example="Shop our premium cotton t-shirt. Soft, comfortable, and perfect for any occasion. Available in multiple colors and sizes."
    )
    
    images: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Product images array with URLs and metadata"
    )
    
    variants: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Product variants with pricing and inventory data"
    )
    
    published_at: Optional[datetime] = Field(
        None,
        description="When the product was published"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Validate product status"""
        valid_statuses = ['active', 'draft', 'archived']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v
    
    @validator('seo_title')
    def validate_seo_title(cls, v):
        """Validate SEO title length"""
        if v and len(v) > 70:
            raise ValueError("SEO title should not exceed 70 characters")
        return v
    
    @validator('seo_description')
    def validate_seo_description(cls, v):
        """Validate SEO description length"""
        if v and len(v) > 160:
            raise ValueError("SEO description should not exceed 160 characters")
        return v

class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    
    store_id: UUID = Field(
        ...,
        description="Store ID this product belongs to"
    )

class ProductUpdate(BaseModel):
    """Schema for updating an existing product"""
    
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Product title"
    )
    
    handle: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Product handle (URL slug)"
    )
    
    description: Optional[str] = Field(
        None,
        description="Product description (HTML)"
    )
    
    product_type: Optional[str] = Field(
        None,
        max_length=255,
        description="Product type/category"
    )
    
    vendor: Optional[str] = Field(
        None,
        max_length=255,
        description="Product vendor/brand"
    )
    
    tags: Optional[List[str]] = Field(
        None,
        description="Product tags array"
    )
    
    status: Optional[str] = Field(
        None,
        description="Product status"
    )
    
    seo_title: Optional[str] = Field(
        None,
        max_length=70,
        description="SEO meta title"
    )
    
    seo_description: Optional[str] = Field(
        None,
        max_length=160,
        description="SEO meta description"
    )
    
    images: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Product images array"
    )
    
    variants: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Product variants array"
    )
    
    published_at: Optional[datetime] = Field(
        None,
        description="When the product was published"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Validate product status"""
        if v is not None:
            valid_statuses = ['active', 'draft', 'archived']
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v
    
    @validator('seo_title')
    def validate_seo_title(cls, v):
        """Validate SEO title length"""
        if v and len(v) > 70:
            raise ValueError("SEO title should not exceed 70 characters")
        return v
    
    @validator('seo_description')
    def validate_seo_description(cls, v):
        """Validate SEO description length"""
        if v and len(v) > 160:
            raise ValueError("SEO description should not exceed 160 characters")
        return v

class ProductResponse(ProductBase):
    """Schema for product API responses"""
    
    id: UUID = Field(..., description="Unique product identifier")
    store_id: UUID = Field(..., description="Store ID this product belongs to")
    created_at: datetime = Field(..., description="Product creation timestamp")
    updated_at: datetime = Field(..., description="Product last update timestamp")
    
    # SEO analysis fields
    current_seo_score: Optional[int] = Field(None, description="Current SEO score (0-100)")
    last_analyzed_at: Optional[datetime] = Field(None, description="Last SEO analysis timestamp")
    
    # Performance metrics
    view_count: int = Field(0, description="Product view count")
    conversion_rate: Optional[Decimal] = Field(None, description="Product conversion rate")
    
    # Computed fields
    primary_image: Optional[Dict[str, Any]] = Field(None, description="Primary product image")
    price_range: Optional[Dict[str, Any]] = Field(None, description="Price range from variants")
    inventory_total: Optional[int] = Field(None, description="Total inventory across variants")
    in_stock: Optional[bool] = Field(None, description="Whether product is in stock")
    variant_count: Optional[int] = Field(None, description="Number of variants")
    has_seo_data: Optional[bool] = Field(None, description="Whether product has SEO data")
    needs_seo_analysis: Optional[bool] = Field(None, description="Whether product needs SEO analysis")
    shopify_url: Optional[str] = Field(None, description="Shopify admin URL")
    storefront_url: Optional[str] = Field(None, description="Storefront URL")
    calculated_seo_score: Optional[int] = Field(None, description="Calculated SEO score")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
            Decimal: lambda v: float(v) if v else None
        }

class ProductList(BaseModel):
    """Schema for paginated product list responses"""
    
    products: List[ProductResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products")
    page: int = Field(1, description="Current page number")
    per_page: int = Field(50, description="Items per page")
    has_next: bool = Field(False, description="Whether there are more pages")
    has_prev: bool = Field(False, description="Whether there are previous pages")

class ProductSEOAnalysis(BaseModel):
    """Schema for product SEO analysis results"""
    
    product_id: UUID = Field(..., description="Product identifier")
    seo_score: int = Field(..., description="SEO score (0-100)")
    title_score: int = Field(..., description="Title optimization score")
    description_score: int = Field(..., description="Description optimization score")
    image_score: int = Field(..., description="Image optimization score")
    
    issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="SEO issues found"
    )
    
    recommendations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="SEO improvement recommendations"
    )
    
    analyzed_at: datetime = Field(..., description="Analysis timestamp")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

class ProductVariant(BaseModel):
    """Schema for product variant data"""
    
    id: Optional[int] = Field(None, description="Shopify variant ID")
    title: Optional[str] = Field(None, description="Variant title")
    price: Optional[str] = Field(None, description="Variant price")
    sku: Optional[str] = Field(None, description="Variant SKU")
    inventory_quantity: Optional[int] = Field(None, description="Inventory quantity")
    weight: Optional[float] = Field(None, description="Variant weight")
    option1: Optional[str] = Field(None, description="Option 1 value (e.g., Size)")
    option2: Optional[str] = Field(None, description="Option 2 value (e.g., Color)")
    option3: Optional[str] = Field(None, description="Option 3 value")

class ProductImage(BaseModel):
    """Schema for product image data"""
    
    id: Optional[int] = Field(None, description="Shopify image ID")
    src: str = Field(..., description="Image URL")
    alt: Optional[str] = Field(None, description="Image alt text")
    width: Optional[int] = Field(None, description="Image width")
    height: Optional[int] = Field(None, description="Image height")
    position: Optional[int] = Field(None, description="Image position")