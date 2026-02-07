"""
Shopify Admin API client for REST and GraphQL calls
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode

from app.core.config import settings
from app.models.store import Store

logger = logging.getLogger(__name__)


class ShopifyClientError(Exception):
    """Custom exception for Shopify API errors"""
    pass


class ShopifyAdminClient:
    """Client for Shopify Admin API REST endpoints"""

    # API version - configurable
    API_VERSION = "2024-01"  # Latest stable version as of 2024

    def __init__(self, store: Store):
        """
        Initialize Shopify Admin API client

        Args:
            store: Store model instance with shop domain and access token
        """
        self.store = store
        self.shop_domain = store.shopify_domain
        self.access_token = store.get_decrypted_token()  # This method needs to be added to Store model

        if not self.access_token:
            raise ShopifyClientError("No valid access token for store")

    @property
    def base_url(self) -> str:
        """Get base URL for API calls"""
        return f"https://{self.shop_domain}/admin/api/{self.API_VERSION}"

    @property
    def headers(self) -> Dict[str, str]:
        """Get headers for API calls"""
        return {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }

    async def get_shop(self) -> Dict[str, Any]:
        """
        Get shop information

        Returns:
            Shop information dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/shop.json",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json().get('shop', {})
        except httpx.HTTPError as e:
            logger.error(f"Failed to get shop info for {self.shop_domain}: {e}")
            raise ShopifyClientError(f"Failed to get shop info: {e}")

    async def get_products(self, limit: int = 250, status: str = "active",
                          fields: Optional[List[str]] = None,
                          after: Optional[str] = None) -> Dict[str, Any]:
        """
        Get products from store

        Args:
            limit: Number of products to fetch (max 250)
            status: Product status (active, draft, archived)
            fields: Specific fields to return (None = all)
            after: Cursor for pagination

        Returns:
            Dictionary with products list and pagination info
        """
        limit = min(limit, 250)  # Shopify max is 250

        params = {
            'limit': limit,
            'status': status,
            'fields': ','.join(fields) if fields else None,
            'after': after
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/products.json"
                if params:
                    url += f"?{urlencode(params)}"

                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                data = response.json()
                products = data.get('products', [])

                # Extract pagination info from Link header
                next_cursor = self._extract_next_cursor(response.headers.get('Link', ''))

                return {
                    'products': products,
                    'next_cursor': next_cursor,
                    'count': len(products)
                }

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch products for {self.shop_domain}: {e}")
            raise ShopifyClientError(f"Failed to fetch products: {e}")

    async def get_product(self, product_id: int) -> Dict[str, Any]:
        """
        Get a specific product by ID

        Args:
            product_id: Shopify product ID

        Returns:
            Product information dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/products/{product_id}.json",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json().get('product', {})
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch product {product_id} from {self.shop_domain}: {e}")
            raise ShopifyClientError(f"Failed to fetch product: {e}")

    async def update_product(self, product_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a product

        Args:
            product_id: Shopify product ID
            data: Product data to update

        Returns:
            Updated product information
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/products/{product_id}.json",
                    headers=self.headers,
                    json={'product': data}
                )
                response.raise_for_status()
                return response.json().get('product', {})
        except httpx.HTTPError as e:
            logger.error(f"Failed to update product {product_id} in {self.shop_domain}: {e}")
            raise ShopifyClientError(f"Failed to update product: {e}")

    async def get_product_variants(self, product_id: int,
                                   limit: int = 250) -> Dict[str, Any]:
        """
        Get variants for a product

        Args:
            product_id: Shopify product ID
            limit: Number of variants to fetch

        Returns:
            Dictionary with variants list
        """
        limit = min(limit, 250)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/products/{product_id}/variants.json?limit={limit}",
                    headers=self.headers
                )
                response.raise_for_status()
                return {
                    'variants': response.json().get('variants', []),
                    'count': len(response.json().get('variants', []))
                }
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch variants for product {product_id}: {e}")
            raise ShopifyClientError(f"Failed to fetch variants: {e}")

    async def get_orders(self, limit: int = 250, status: str = "any",
                        after: Optional[str] = None) -> Dict[str, Any]:
        """
        Get orders from store

        Args:
            limit: Number of orders to fetch (max 250)
            status: Order status (any, cancelled, fulfilled, pending, refunded, unshipped)
            after: Cursor for pagination

        Returns:
            Dictionary with orders list and pagination info
        """
        limit = min(limit, 250)

        params = {
            'limit': limit,
            'status': status,
            'after': after
        }

        params = {k: v for k, v in params.items() if v is not None}

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/orders.json"
                if params:
                    url += f"?{urlencode(params)}"

                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                data = response.json()
                orders = data.get('orders', [])
                next_cursor = self._extract_next_cursor(response.headers.get('Link', ''))

                return {
                    'orders': orders,
                    'next_cursor': next_cursor,
                    'count': len(orders)
                }

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch orders for {self.shop_domain}: {e}")
            raise ShopifyClientError(f"Failed to fetch orders: {e}")

    async def get_customers(self, limit: int = 250,
                           after: Optional[str] = None) -> Dict[str, Any]:
        """
        Get customers from store

        Args:
            limit: Number of customers to fetch (max 250)
            after: Cursor for pagination

        Returns:
            Dictionary with customers list and pagination info
        """
        limit = min(limit, 250)

        params = {
            'limit': limit,
            'after': after
        }

        params = {k: v for k, v in params.items() if v is not None}

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/customers.json"
                if params:
                    url += f"?{urlencode(params)}"

                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                data = response.json()
                customers = data.get('customers', [])
                next_cursor = self._extract_next_cursor(response.headers.get('Link', ''))

                return {
                    'customers': customers,
                    'next_cursor': next_cursor,
                    'count': len(customers)
                }

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch customers for {self.shop_domain}: {e}")
            raise ShopifyClientError(f"Failed to fetch customers: {e}")

    async def graphql_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            GraphQL response data
        """
        payload = {
            'query': query,
            'variables': variables or {}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/graphql.json",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()

                # Check for GraphQL errors
                if 'errors' in data:
                    errors = data['errors']
                    logger.error(f"GraphQL errors: {errors}")
                    raise ShopifyClientError(f"GraphQL error: {errors}")

                return data.get('data', {})

        except httpx.HTTPError as e:
            logger.error(f"Failed to execute GraphQL query: {e}")
            raise ShopifyClientError(f"Failed to execute GraphQL query: {e}")

    def _extract_next_cursor(self, link_header: str) -> Optional[str]:
        """
        Extract next cursor from Link header for pagination

        Args:
            link_header: Link header from response

        Returns:
            Next cursor if available, None otherwise
        """
        if not link_header:
            return None

        # Parse Link header: <url?after=cursor>; rel="next"
        links = link_header.split(',')
        for link in links:
            if 'rel="next"' in link:
                # Extract URL
                url_part = link.split(';')[0].strip()
                if '<' in url_part and '>' in url_part:
                    url = url_part[1:-1]  # Remove < and >
                    # Extract cursor from URL
                    if 'after=' in url:
                        return url.split('after=')[1].split('&')[0]

        return None

    async def check_api_access(self) -> bool:
        """
        Check if API token is valid by making a simple request

        Returns:
            True if token is valid, False otherwise
        """
        try:
            await self.get_shop()
            return True
        except ShopifyClientError:
            return False


class ShopifyGraphQLClient:
    """Helper class for GraphQL queries with common queries"""

    @staticmethod
    def get_products_query() -> str:
        """Get GraphQL query for fetching products with SEO fields"""
        return """
        query($first: Int!, $after: String) {
            products(first: $first, after: $after) {
                edges {
                    node {
                        id
                        title
                        handle
                        description
                        vendor
                        productType
                        status
                        seo {
                            title
                            description
                        }
                        images(first: 10) {
                            edges {
                                node {
                                    id
                                    url
                                    altText
                                }
                            }
                        }
                        variants(first: 10) {
                            edges {
                                node {
                                    id
                                    title
                                    sku
                                    barcode
                                    price
                                    inventoryQuantity
                                }
                            }
                        }
                        metafields(first: 10) {
                            edges {
                                node {
                                    key
                                    value
                                    namespace
                                }
                            }
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """

    @staticmethod
    def get_shop_query() -> str:
        """Get GraphQL query for shop information"""
        return """
        query {
            shop {
                id
                name
                email
                primaryDomain {
                    url
                    host
                }
                currencyCode
                timezoneOffset
                plan {
                    displayName
                }
                productCount
                customerCount
                shippingOrigin {
                    address1
                    city
                    country
                    province
                    zip
                }
            }
        }
        """

    @staticmethod
    def update_product_seo_query() -> str:
        """Get GraphQL mutation for updating product SEO"""
        return """
        mutation($input: ProductInput!) {
            productUpdate(input: $input) {
                product {
                    id
                    title
                    seo {
                        title
                        description
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
