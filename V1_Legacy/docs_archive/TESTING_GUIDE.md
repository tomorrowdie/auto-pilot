# Shopify SEO Analyzer - Testing Guide

## Setup Instructions

### 1. Prerequisites

Ensure you have:
- PostgreSQL running on localhost:5432
- Redis running on localhost:6379
- Python 3.9+
- Node.js 16+
- Shopify test store or development credentials

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your Shopify API credentials

# Run database migrations
alembic upgrade head

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file if needed
echo "REACT_APP_API_URL=http://localhost:8000/api/v1" > .env

# Start development server
npm start
```

### 4. Celery Setup (for background tasks)

```bash
cd backend

# Terminal 1: Start Celery Worker
celery -A app.tasks.celery_app worker -l info

# Terminal 2: Start Celery Beat (for scheduled tasks)
celery -A app.tasks.celery_app beat -l info
```

---

## Testing the Components

### 1. Test Shopify OAuth Flow

**Endpoint**: `POST /api/v1/auth/shopify/install`

```bash
curl -X POST http://localhost:8000/api/v1/auth/shopify/install \
  -H "Content-Type: application/json" \
  -d '{"shop": "your-store.myshopify.com"}'
```

**Expected Response**:
```json
{
  "install_url": "https://your-store.myshopify.com/admin/oauth/authorize?...",
  "state": "random_state_token"
}
```

### 2. Test Store Creation

**Endpoint**: `POST /api/v1/stores/`

```bash
curl -X POST http://localhost:8000/api/v1/stores/ \
  -H "Content-Type: application/json" \
  -d '{
    "shopify_domain": "test.myshopify.com",
    "store_name": "Test Store",
    "owner_email": "owner@example.com",
    "shopify_access_token": "shpat_xxxxx"
  }'
```

### 3. Test Shopify API Client

Create a Python script `test_api_client.py`:

```python
import asyncio
from app.core.database import SessionLocal
from app.models.store import Store
from app.services.shopify_client import ShopifyAdminClient

async def test_api_client():
    db = SessionLocal()

    # Get first store from database
    store = db.query(Store).first()
    if not store:
        print("No stores found in database")
        return

    try:
        # Create client
        client = ShopifyAdminClient(store)

        # Test shop info
        print("Testing get_shop()...")
        shop = await client.get_shop()
        print(f"Shop: {shop.get('name')}")

        # Test products
        print("\nTesting get_products()...")
        result = await client.get_products(limit=10)
        products = result.get('products', [])
        print(f"Found {len(products)} products")

        # Test API access
        print("\nTesting check_api_access()...")
        is_valid = await client.check_api_access()
        print(f"API Access Valid: {is_valid}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

# Run the test
asyncio.run(test_api_client())
```

Run it:
```bash
cd backend
python test_api_client.py
```

### 4. Test Token Encryption

Create `test_encryption.py`:

```python
from app.core.encryption import encrypt_token, decrypt_token

# Test encryption
original_token = "shpat_1234567890abcdef"
encrypted = encrypt_token(original_token)
decrypted = decrypt_token(encrypted)

print(f"Original:  {original_token}")
print(f"Encrypted: {encrypted}")
print(f"Decrypted: {decrypted}")
print(f"Match: {original_token == decrypted}")
```

### 5. Test Background Tasks

Create `test_celery_tasks.py`:

```python
from app.tasks.sync_tasks import sync_store_products, check_stores_api_health
from app.core.database import SessionLocal
from app.models.store import Store

# Get a store ID from database
db = SessionLocal()
store = db.query(Store).first()
db.close()

if store:
    store_id = str(store.id)

    # Queue a sync task
    print(f"Queuing sync for store {store_id}")
    task = sync_store_products.delay(store_id=store_id)
    print(f"Task ID: {task.id}")
    print(f"Task Status: {task.status}")

    # Wait for result (blocking)
    try:
        result = task.get(timeout=60)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("No stores found")

# Test health check
print("\nQueuing health check...")
health_task = check_stores_api_health.delay()
print(f"Health check task ID: {health_task.id}")
```

### 6. Test API Endpoints (Manual)

Use the built-in Swagger UI:
```
http://localhost:8000/docs
```

Or use cURL:

**Create Analysis**:
```bash
curl -X POST http://localhost:8000/api/v1/analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "store-uuid-here",
    "product_id": "product-uuid-here",
    "analysis_type": "product",
    "seo_score": 75.5
  }'
```

**Get Store Analyses**:
```bash
curl http://localhost:8000/api/v1/analysis/store/store-uuid-here/analyses
```

**Search Keywords**:
```bash
curl "http://localhost:8000/api/v1/keywords/search?query=seo&source=all&limit=10"
```

### 7. Test Frontend API Services

Create a test React component in `src/components/ServiceTest.tsx`:

```typescript
import React, { useEffect, useState } from 'react';
import { storeService, productService, authService } from '../services';
import { Store } from '../types';

export const ServiceTest: React.FC = () => {
  const [stores, setStores] = useState<Store[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const testServices = async () => {
      setLoading(true);
      try {
        // Check if authenticated
        if (!authService.isAuthenticated()) {
          setError('Not authenticated');
          return;
        }

        // Fetch stores
        const storesData = await storeService.getStores();
        setStores(storesData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    testServices();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Stores ({stores.length})</h2>
      <ul>
        {stores.map((store) => (
          <li key={store.id}>{store.store_name}</li>
        ))}
      </ul>
    </div>
  );
};
```

---

## Database Inspection

### View Stores in Database

```bash
cd backend
python

>>> from app.core.database import SessionLocal
>>> from app.models.store import Store
>>> db = SessionLocal()
>>> stores = db.query(Store).all()
>>> for store in stores:
...     print(f"{store.store_name} ({store.shopify_domain})")
```

### View Products

```python
>>> from app.models.product import Product
>>> products = db.query(Product).limit(10).all()
>>> for product in products:
...     print(f"{product.title}")
```

### View Analyses

```python
>>> from app.models.seo_analysis import SEOAnalysis
>>> analyses = db.query(SEOAnalysis).limit(10).all()
>>> for analysis in analyses:
...     print(f"Score: {analysis.seo_score}")
```

---

## Monitoring and Debugging

### Check Celery Tasks

```bash
# In a Python shell:
from app.tasks.celery_app import celery_app

# Get active tasks
inspect = celery_app.control.inspect()
active_tasks = inspect.active()
print(active_tasks)

# Get registered tasks
registered_tasks = inspect.registered()
print(registered_tasks)
```

### View Logs

```bash
# Backend logs
tail -f backend/logs/app.log

# Celery logs (from terminal running worker)
# Check the terminal output
```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

---

## Common Issues and Fixes

### Issue: Shopify API returns 401 Unauthorized

**Cause**: Invalid or expired access token

**Fix**:
```python
from app.services.shopify_auth import ShopifyOAuthService

oauth = ShopifyOAuthService()
# Re-authenticate with shop
```

### Issue: Celery tasks not running

**Cause**: Redis not running or Celery worker not started

**Fix**:
```bash
# Check Redis
redis-cli ping  # Should return PONG

# Restart Celery worker
celery -A app.tasks.celery_app worker -l info --purge
```

### Issue: Token decryption fails

**Cause**: SECRET_KEY changed or token encrypted with different key

**Fix**:
- Don't change SECRET_KEY in production
- Re-encrypt tokens if you must change the key
- Use same SECRET_KEY across all instances

### Issue: Products not syncing

**Check**:
1. API token is valid: `await client.check_api_access()`
2. Redis is running: `redis-cli ping`
3. Celery worker is running: `celery -A app.tasks.celery_app worker -l info`
4. Check logs for errors

---

## Performance Testing

### Load Testing with Apache Bench

```bash
# Test API health
ab -n 100 -c 10 http://localhost:8000/health

# Test store listing
ab -n 100 -c 10 \
  -H "Authorization: Bearer your_token" \
  http://localhost:8000/api/v1/stores/
```

### Test Product Sync Performance

```bash
# Sync a large store
python -c "
import asyncio
from app.tasks.sync_tasks import sync_store_products
task = sync_store_products.delay(store_id='your-store-id')
print(f'Task: {task.id}')
"
```

---

## Cleanup

### Reset Database

```bash
cd backend

# Drop all tables
python -c "
from app.core.database_utils import drop_tables
from app.core.database import engine
drop_tables(engine)
"

# Recreate from migrations
alembic upgrade head
```

### Clear Redis Cache

```bash
redis-cli FLUSHALL
```

### Clear Celery Tasks

```bash
# From Python:
from app.tasks.celery_app import celery_app
celery_app.control.purge()
```

---

## Success Criteria

You know everything is working when:

1. ✅ OAuth flow completes and store is created
2. ✅ Shopify API client fetches products without errors
3. ✅ Tokens are properly encrypted/decrypted
4. ✅ Background sync tasks run and populate database
5. ✅ Frontend fetches stores and products
6. ✅ Analysis endpoints create and retrieve analyses
7. ✅ Keyword endpoints work correctly
8. ✅ No critical errors in logs

---

## Next Steps

After testing:

1. Deploy to AWS Lightsail
2. Configure production environment variables
3. Set up automated backups
4. Configure monitoring and alerts
5. Document API for end users
