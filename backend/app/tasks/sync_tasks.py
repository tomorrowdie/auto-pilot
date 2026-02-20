"""
Background tasks for syncing Shopify store data
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from celery import shared_task

from app.core.database import SessionLocal
from app.models.store import Store
from app.models.product import Product
from app.services.shopify_client import ShopifyAdminClient, ShopifyClientError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_store_products(self, store_id: str) -> Dict[str, Any]:
    """
    Sync products for a specific store from Shopify

    Args:
        store_id: UUID of the store to sync

    Returns:
        Dict with sync results
    """
    db = SessionLocal()

    try:
        # Get store from database
        store = db.query(Store).filter(Store.id == store_id).first()

        if not store:
            logger.error(f"Store {store_id} not found")
            return {'status': 'error', 'message': 'Store not found'}

        if not store.is_active:
            logger.warning(f"Store {store_id} is not active, skipping sync")
            return {'status': 'skipped', 'message': 'Store is inactive'}

        logger.info(f"Starting product sync for store: {store.shopify_domain}")

        # Run async sync in sync context
        result = asyncio.run(sync_store_products_async(store_id))

        # Update store sync timestamp
        store.update_sync_timestamp()
        if 'products_synced' in result:
            store.product_count = result['products_synced']
        db.commit()

        logger.info(
            f"Completed product sync for {store.shopify_domain}: "
            f"{result.get('products_synced', 0)} synced, {result.get('products_updated', 0)} updated"
        )

        return result

    except Exception as e:
        logger.error(f"Error syncing store {store_id}: {e}")
        db.rollback()
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

    finally:
        db.close()


async def sync_store_products_async(store_id: str) -> Dict[str, Any]:
    """
    Async helper for syncing products

    Args:
        store_id: UUID of the store

    Returns:
        Sync results dictionary
    """
    db = SessionLocal()

    try:
        store = db.query(Store).filter(Store.id == store_id).first()

        if not store:
            return {'status': 'error', 'message': 'Store not found'}

        client = ShopifyAdminClient(store)

        products_synced = 0
        products_updated = 0
        after_cursor = None

        while True:
            try:
                result = await client.get_products(limit=250, after=after_cursor)
                products = result.get('products', [])

                if not products:
                    break

                for product_data in products:
                    try:
                        product_id = product_data.get('id')
                        shopify_product_id = int(product_id.split('/')[-1]) if '/' in str(product_id) else product_data.get('id')

                        existing_product = db.query(Product).filter(
                            Product.shopify_product_id == shopify_product_id,
                            Product.store_id == store_id
                        ).first()

                        if existing_product:
                            existing_product.title = product_data.get('title', '')
                            existing_product.description = product_data.get('description', '')
                            existing_product.vendor = product_data.get('vendor', '')
                            existing_product.product_type = product_data.get('productType', '')
                            existing_product.tags = ','.join(product_data.get('tags', []))
                            existing_product.handle = product_data.get('handle', '')
                            existing_product.shopify_data = product_data
                            products_updated += 1
                        else:
                            new_product = Product(
                                store_id=store_id,
                                shopify_product_id=shopify_product_id,
                                title=product_data.get('title', ''),
                                description=product_data.get('description', ''),
                                vendor=product_data.get('vendor', ''),
                                product_type=product_data.get('productType', ''),
                                tags=','.join(product_data.get('tags', [])),
                                handle=product_data.get('handle', ''),
                                shopify_data=product_data,
                                is_active=product_data.get('status') == 'ACTIVE'
                            )

                            seo_data = product_data.get('seo', {})
                            if seo_data:
                                new_product.seo_title = seo_data.get('title', '')
                                new_product.seo_description = seo_data.get('description', '')

                            db.add(new_product)
                            products_synced += 1

                    except Exception as e:
                        logger.error(f"Error processing product: {e}")
                        continue

                db.commit()
                after_cursor = result.get('next_cursor')

                if not after_cursor:
                    break

            except ShopifyClientError as e:
                logger.error(f"Error fetching products: {e}")
                break

        return {
            'status': 'success',
            'store_id': store_id,
            'products_synced': products_synced,
            'products_updated': products_updated
        }

    except Exception as e:
        logger.error(f"Error in async sync: {e}")
        return {'status': 'error', 'message': str(e)}

    finally:
        db.close()


@shared_task(bind=True)
def check_stores_api_health(self) -> Dict[str, Any]:
    """
    Check API health for all active stores

    Returns:
        Dict with health check results
    """
    db = SessionLocal()

    try:
        # Get all active stores
        stores = db.query(Store).filter(Store.is_active == True).all()

        healthy = 0
        unhealthy = 0
        errors = []

        for store in stores:
            try:
                # Run async health check
                is_valid = asyncio.run(check_store_api_access(store))

                if is_valid:
                    healthy += 1
                    logger.info(f"Store {store.shopify_domain} API is healthy")
                else:
                    unhealthy += 1
                    logger.warning(f"Store {store.shopify_domain} API check failed")
                    errors.append({
                        'store': store.shopify_domain,
                        'error': 'API check failed'
                    })

            except ShopifyClientError as e:
                unhealthy += 1
                logger.error(f"Error checking store {store.shopify_domain}: {e}")
                errors.append({
                    'store': store.shopify_domain,
                    'error': str(e)
                })

        logger.info(
            f"Health check complete: {healthy} healthy, {unhealthy} unhealthy"
        )

        return {
            'status': 'success',
            'healthy': healthy,
            'unhealthy': unhealthy,
            'errors': errors
        }

    except Exception as e:
        logger.error(f"Error during health check: {e}")
        return {'status': 'error', 'message': str(e)}

    finally:
        db.close()


async def check_store_api_access(store: Store) -> bool:
    """
    Check if store API access is valid

    Args:
        store: Store instance

    Returns:
        True if API access is valid, False otherwise
    """
    try:
        client = ShopifyAdminClient(store)
        return await client.check_api_access()
    except Exception as e:
        logger.error(f"Error checking API access for {store.shopify_domain}: {e}")
        return False


@shared_task
def sync_all_stores() -> Dict[str, Any]:
    """
    Sync all active stores that need syncing

    Returns:
        Dict with sync results for all stores
    """
    db = SessionLocal()

    try:
        # Get all active stores that need syncing
        stores = db.query(Store).filter(Store.is_active == True).all()

        synced_stores = []
        failed_stores = []

        for store in stores:
            if store.is_sync_needed(max_age_hours=24):
                try:
                    # Queue sync task
                    task = sync_store_products.delay(store_id=str(store.id))
                    synced_stores.append({
                        'store_id': str(store.id),
                        'domain': store.shopify_domain,
                        'task_id': task.id
                    })
                    logger.info(f"Queued sync for store: {store.shopify_domain}")

                except Exception as e:
                    logger.error(f"Error queuing sync for store {store.shopify_domain}: {e}")
                    failed_stores.append({
                        'store_id': str(store.id),
                        'domain': store.shopify_domain,
                        'error': str(e)
                    })

        return {
            'status': 'success',
            'synced_stores': len(synced_stores),
            'failed_stores': len(failed_stores),
            'details': {
                'synced': synced_stores,
                'failed': failed_stores
            }
        }

    except Exception as e:
        logger.error(f"Error in sync_all_stores: {e}")
        return {'status': 'error', 'message': str(e)}

    finally:
        db.close()
