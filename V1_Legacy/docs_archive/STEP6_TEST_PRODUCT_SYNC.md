# Step 6: Test Product Synchronization

## 📍 You Are Here
- ✅ Step 1: Project Context Loaded
- ✅ Step 2: Environment Variables Updated
- ✅ Step 3: Local Environment Prepared
- ✅ Step 4: Backend Services Started
- ✅ Step 5: OAuth Flow Tested
- ⏳ **Step 6: Test Product Sync** ← You are here
- 📋 Step 7: Test Frontend

---

## 🎯 Goal of This Step

Test the product synchronization system by:
1. Triggering a manual product sync via API
2. Monitoring Celery worker execution
3. Verifying products are saved in database
4. Checking sync status and metrics

**Estimated Time**: 20-30 minutes

---

## 📋 Prerequisites

Before starting, ensure:
- ✅ Store is connected via OAuth (Step 5 completed)
- ✅ FastAPI backend is running
- ✅ Celery worker is running (`celery -A app.tasks.celery_app worker -l info`)
- ✅ Celery Beat is running (`celery -A app.tasks.celery_app beat -l info`)
- ✅ Redis is running (`redis-cli ping` returns PONG)
- ✅ PostgreSQL is running
- ✅ Store has products in Shopify (test store should have sample products)

---

## 🚀 Step 1: Get Store ID

First, retrieve the store ID from the database for use in sync request.

### 1.1 Query Database

```bash
# Connect to database
psql -U shopify_user -d shopify_seo_prod

# Get store ID
SELECT id, shopify_domain, store_name FROM stores;

# Example output:
#                     id                   |       shopify_domain       |  store_name
# ----------------------------------------+----------------------------+-------------
#  550e8400-e29b-41d4-a716-446655440000 | your-test-store.myshopify.com | Your Test Store

# Copy the ID (550e8400-e29b-41d4-a716-446655440000)

\q
```

**Save the store ID** - you'll use it in the next step.

---

## 🔄 Step 2: Trigger Manual Product Sync

There are two ways to trigger a sync: via API or directly via Celery.

### Option A: Via API Endpoint (Recommended)

```bash
# Replace STORE_ID with actual ID from Step 1
STORE_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X POST http://localhost:8000/api/v1/stores/${STORE_ID}/sync \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Product sync started",
  "task_id": "abc123def456ghi789jkl",
  "store_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Note the `task_id`** - you can use it to check task status.

### Option B: Direct Python/Celery

```bash
cd backend
source venv/bin/activate

python << 'EOF'
from app.tasks.sync_tasks import sync_store_products
from app.core.database import SessionLocal
from app.models.store import Store

# Get store
db = SessionLocal()
store = db.query(Store).first()
db.close()

if store:
    print(f"Syncing store: {store.store_name}")
    task = sync_store_products.delay(store_id=str(store.id))
    print(f"Task ID: {task.id}")
    print(f"Task Status: {task.status}")
else:
    print("No stores found")
EOF
```

**Expected Output:**
```
Syncing store: Your Test Store
Task ID: abc123def456ghi789jkl
Task Status: PENDING
```

---

## 📊 Step 3: Monitor Celery Worker

Watch the Celery worker terminal (Terminal 3) for task execution.

### 3.1 Watch Terminal 3

In the terminal where Celery worker is running, you should see:

```
[2024-10-26 14:50:00,000] INFO/MainProcess [app.tasks.sync_tasks.sync_store_products] Syncing products for store: 550e8400...
[2024-10-26 14:50:01,234] INFO/MainProcess [app.tasks.sync_tasks.sync_store_products] Fetching products from Shopify...
[2024-10-26 14:50:02,456] INFO/MainProcess [app.tasks.sync_tasks.sync_store_products] Retrieved 10 products
[2024-10-26 14:50:03,789] INFO/MainProcess [app.tasks.sync_tasks.sync_store_products] Saving products to database...
[2024-10-26 14:50:05,012] INFO/MainProcess [app.tasks.sync_tasks.sync_store_products] Successfully synced 10 products
[2024-10-26 14:50:05,234] INFO/MainProcess Task task-id-here succeeded in 5.234s: {'status': 'success', ...}
```

**Key indicators:**
- ✅ Task started (shows task name)
- ✅ Products fetched (shows count)
- ✅ Products saved (shows confirmation)
- ✅ Task succeeded (shows duration)

### 3.2 Check Task Status via API

```bash
# While sync is running, check status
TASK_ID="abc123def456ghi789jkl"

curl http://localhost:8000/api/v1/tasks/${TASK_ID}/status
```

**Expected Response (while running):**
```json
{
  "task_id": "abc123def456ghi789jkl",
  "status": "PROGRESS",
  "current": 5,
  "total": 10,
  "percent": 50
}
```

**Expected Response (after completion):**
```json
{
  "task_id": "abc123def456ghi789jkl",
  "status": "SUCCESS",
  "result": {
    "products_synced": 10,
    "products_created": 7,
    "products_updated": 3,
    "duration_seconds": 5.2
  }
}
```

---

## 🗄️ Step 4: Verify Products in Database

Once sync completes, verify products are in the database.

### 4.1 Count Products

```bash
# Connect to database
psql -U shopify_user -d shopify_seo_prod

# Count all products
SELECT COUNT(*) FROM products;

# Example output:
#  count
# -------
#     10
# (1 row)
```

### 4.2 View Product Details

```bash
# View first 10 products
SELECT id, title, shopify_product_id, product_type, created_at
FROM products
LIMIT 10;

# Example output:
#                    id                   |           title            | shopify_product_id | product_type |         created_at
# ----------------------------------------+----------------------------+--------------------+--------------+-----------------------------
#  550e8400-e29b-41d4-a716-446655440001 | Vintage Coffee Maker       | 12345678901234567  | Coffee       | 2024-10-26 14:50:05.123456+00
#  550e8400-e29b-41d4-a716-446655440002 | Espresso Machine           | 12345678901234568  | Coffee       | 2024-10-26 14:50:05.234567+00
#  ... (8 more products)
```

### 4.3 Check Sync Status

```bash
# View sync status for store
SELECT
  id,
  shopify_domain,
  store_name,
  last_sync_at,
  product_count
FROM stores;

# Example output:
#                    id                   |       shopify_domain       |  store_name   |        last_sync_at         | product_count
# ----------------------------------------+----------------------------+---------------+-----------------------------+---------------
#  550e8400-e29b-41d4-a716-446655440000 | your-test-store.myshopify.com | Your Test Store | 2024-10-26 14:50:05.000000+00 |            10
# (1 row)
```

### 4.4 View Product Content

```bash
-- View details of a specific product
SELECT
  id,
  title,
  description,
  product_type,
  handle,
  status
FROM products
WHERE title LIKE 'Vintage%'
LIMIT 1;

-- Exit
\q
```

---

## 🔍 Step 5: Verify Product Data Quality

Ensure products have all required data.

### 5.1 Check for Missing Data

```bash
cd backend
source venv/bin/activate

python << 'EOF'
from app.core.database import SessionLocal
from app.models.product import Product
from sqlalchemy import func

db = SessionLocal()

# Count products with missing fields
print("=== Data Quality Check ===\n")

total = db.query(func.count(Product.id)).scalar()
print(f"Total products: {total}")

missing_description = db.query(func.count(Product.id)).filter(
    (Product.description == None) | (Product.description == '')
).scalar()
print(f"Missing descriptions: {missing_description}")

missing_handle = db.query(func.count(Product.id)).filter(
    (Product.handle == None) | (Product.handle == '')
).scalar()
print(f"Missing handles: {missing_handle}")

products_with_variants = db.query(func.count(Product.id)).filter(
    Product.variants != None
).scalar()
print(f"Products with variants: {products_with_variants}")

# Show sample product
sample = db.query(Product).first()
if sample:
    print(f"\n=== Sample Product ===")
    print(f"ID: {sample.id}")
    print(f"Title: {sample.title}")
    print(f"Type: {sample.product_type}")
    print(f"Handle: {sample.handle}")
    print(f"Description: {sample.description[:100]}..." if sample.description else "None")
    print(f"Images: {len(sample.images) if sample.images else 0}")
    print(f"Variants: {len(sample.variants) if sample.variants else 0}")

db.close()
EOF
```

**Expected Output:**
```
=== Data Quality Check ===

Total products: 10
Missing descriptions: 0
Missing handles: 0
Products with variants: 10

=== Sample Product ===
ID: 550e8400-e29b-41d4-a716-446655440001
Title: Vintage Coffee Maker
Type: Coffee
Handle: vintage-coffee-maker
Description: High-quality vintage coffee maker from the 1970s...
Images: 3
Variants: 2
```

---

## ⏰ Step 6: Test Scheduled Sync

Celery Beat should automatically run syncs daily. Verify it's scheduled.

### 6.1 Check Scheduled Tasks

```bash
cd backend
source venv/bin/activate

python << 'EOF'
from app.tasks.celery_app import celery_app

# Get scheduled tasks
inspect = celery_app.control.inspect()

# List scheduled tasks
scheduled = inspect.scheduled()
if scheduled:
    print("=== Scheduled Tasks ===\n")
    for worker, tasks in scheduled.items():
        print(f"Worker: {worker}")
        for task in tasks:
            print(f"  - {task['request']['id']}")
            print(f"    Task: {task['request']['task']}")
            print(f"    ETA: {task['eta']}")
else:
    print("No scheduled tasks")

# List all beat schedule
from app.tasks.celery_app import celery_app
print("\n=== Beat Schedule ===")
print(f"Timezone: {celery_app.conf.timezone}")
for task_name, task_config in celery_app.conf.beat_schedule.items():
    print(f"\n{task_name}:")
    print(f"  Task: {task_config['task']}")
    print(f"  Schedule: {task_config['schedule']}")
    if hasattr(task_config['schedule'], 'hour'):
        print(f"  Hour: {task_config['schedule'].hour}")
    if hasattr(task_config['schedule'], 'minute'):
        print(f"  Minute: {task_config['schedule'].minute}")
EOF
```

**Expected Output:**
```
=== Beat Schedule ===
Timezone: UTC

sync-stores-daily:
  Task: app.tasks.sync_tasks.sync_all_stores
  Schedule: crontab(hour=0, minute=0)
  Hour: 0
  Minute: 0

check-api-health-hourly:
  Task: app.tasks.sync_tasks.check_stores_api_health
  Schedule: crontab(minute=0)
  Minute: 0
```

---

## 📊 Sync Results Checklist

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| **Sync initiated** | Task queued in Celery | ✓ | |
| **Celery worker runs task** | Task shows in worker logs | ✓ | |
| **Products fetched** | API returns product count | ✓ | |
| **Products saved** | Count in products table > 0 | ✓ | |
| **Sync completes** | Task status = SUCCESS | ✓ | |
| **Data quality** | No NULL required fields | ✓ | |
| **Scheduled sync** | Beat schedule configured | ✓ | |

---

## 🐛 Troubleshooting

### Issue 1: Task Fails - "No Store Found"

```
Error: Store not found
```

**Solution**: Store was not connected via OAuth
1. Go back to Step 5
2. Complete OAuth flow
3. Verify store exists: `SELECT id FROM stores;`
4. Try sync again with correct store ID

### Issue 2: Task Hangs - "No Activity for 5 Minutes"

```
WARNING: No activity from Celery worker
```

**Solution**: Celery worker not running or Redis disconnected
```bash
# Check Redis
redis-cli ping  # Should return PONG

# Check Celery worker terminal
# Should show "ready" and no errors

# Restart Celery worker
celery -A app.tasks.celery_app worker -l info
```

### Issue 3: API Returns 404 - "Sync Endpoint Not Found"

```
Error: 404 Not Found: /api/v1/stores/{store_id}/sync
```

**Solution**: Endpoint not implemented or FastAPI not reloaded
```bash
# Make sure FastAPI is running with --reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Wait 2-3 seconds for hot reload
```

### Issue 4: Products Not Appearing - "Sync Says Success But No Products"

```
Database shows 0 products after sync
```

**Solution**: Check for errors in Celery worker logs
```bash
# In Terminal 3 (Celery worker), look for ERROR lines
# Common reasons:
# 1. Shopify API token expired
# 2. Product fetch API call failed
# 3. Database insert failed

# Try syncing again with verbose logging
celery -A app.tasks.sync_tasks.sync_store_products.delay(store_id='id') inspect active
```

### Issue 5: Shopify API Error - "Unauthorized"

```
Error: 401 Unauthorized from Shopify API
```

**Solution**: Access token is invalid or expired
1. Go to OAuth step (Step 5)
2. Disconnect and reconnect the store
3. OAuth will fetch a new token
4. Try sync again

---

## ✅ Success Criteria

You've successfully completed this step when:

- [ ] Sync task can be triggered via API
- [ ] Celery worker executes task (shows in Terminal 3 logs)
- [ ] Task completes with SUCCESS status
- [ ] Products table has entries (`SELECT COUNT(*) FROM products;` > 0)
- [ ] Products have complete data (title, description, variants, etc.)
- [ ] Store's `last_sync_at` timestamp is updated
- [ ] Scheduled tasks are configured (daily sync at midnight UTC)
- [ ] No errors in Celery worker logs

---

## ⏭️ Next Step

Once product sync is working, proceed to **Step 7: Test Frontend** where we'll:
1. Install frontend dependencies
2. Build React application
3. Test connection to backend API
4. Verify data displays correctly

See: [STEP7_TEST_FRONTEND.md](./STEP7_TEST_FRONTEND.md)

---

## 🎯 Quick Reference

### Manual Sync Commands

```bash
# Method 1: Via API
STORE_ID="550e8400-e29b-41d4-a716-446655440000"
curl -X POST http://localhost:8000/api/v1/stores/${STORE_ID}/sync

# Method 2: Direct Python
cd backend && source venv/bin/activate
python -c "from app.tasks.sync_tasks import sync_store_products; task = sync_store_products.delay(store_id='550e8400-e29b-41d4-a716-446655440000'); print(f'Task: {task.id}')"

# Check Task Status
curl http://localhost:8000/api/v1/tasks/abc123/status

# View Products in Database
psql -U shopify_user -d shopify_seo_prod -c "SELECT COUNT(*) FROM products; SELECT title FROM products LIMIT 5;"
```

---

**Status**: Ready to test product sync
**Difficulty**: Medium
**Estimated Time**: 20-30 minutes
