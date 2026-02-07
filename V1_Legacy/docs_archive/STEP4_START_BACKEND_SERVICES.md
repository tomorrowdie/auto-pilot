# Step 4: Start Backend Services

## 📍 You Are Here
- ✅ Step 1: Project Context Loaded
- ✅ Step 2: Environment Variables Updated
- ✅ Step 3: Local Environment Prepared
- ⏳ **Step 4: Start Backend Services** ← You are here
- 📋 Step 5: Test OAuth Flow
- 📋 Step 6: Test Product Synchronization
- 📋 Step 7: Test Frontend

---

## 🎯 Goal of This Step

Start all backend services in the correct order:
1. **Redis** (Celery message broker) - must be running first
2. **FastAPI Backend** (REST API server) - handles HTTP requests
3. **Celery Worker** (background task processor) - executes async jobs
4. **Celery Beat** (task scheduler) - schedules recurring jobs

**Estimated Time**: 10 minutes to start all services

---

## 📋 What Each Service Does

| Service | Port | Purpose | Terminal |
|---------|------|---------|----------|
| **Redis** | 6379 | Message broker for Celery | Terminal 1 |
| **FastAPI** | 8000 | REST API server | Terminal 2 |
| **Celery Worker** | - | Executes background tasks | Terminal 3 |
| **Celery Beat** | - | Schedules recurring tasks | Terminal 4 |

---

## 🚀 Startup Instructions

### Step 1: Verify Prerequisites (2 minutes)

Before starting services, verify everything is ready:

```bash
# Terminal 1: Verify PostgreSQL is running
psql -U shopify_user -d shopify_seo_prod -c "SELECT 1;"

# Should output:
# (1 row)

# Terminal 1: Verify Redis is running
redis-cli ping

# Should output:
# PONG

# Terminal 1: Verify .env file exists
ls -la backend/.env

# Should show the file exists
```

**If any of these fail, go back to Step 3 and fix them.**

---

### Step 2: Start Redis (Terminal 1)

Redis must be running before FastAPI and Celery start.

```bash
# Terminal 1
# If using systemd (Linux)
sudo systemctl start redis-server

# Or if using Docker
docker run -d -p 6379:6379 --name redis-server redis:7

# Or if using Homebrew (macOS)
brew services start redis

# Verify it's running
redis-cli PING
```

**Expected Output:**
```
PONG
```

**Keep this terminal open or let the service run in background.**

---

### Step 3: Start FastAPI Backend (Terminal 2)

The FastAPI server handles all HTTP requests from the frontend.

```bash
# Terminal 2
cd backend

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate.bat  # Windows CMD
# OR
venv\Scripts\Activate.ps1  # Windows PowerShell

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify it's working:**
```bash
# Open another terminal (Terminal 2b) and test:
curl http://localhost:8000/health

# Expected response:
# {"status":"ok"}
```

**Keep Terminal 2 open** - The backend server must stay running.

---

### Step 4: Start Celery Worker (Terminal 3)

Celery worker executes background tasks like product syncing.

```bash
# Terminal 3
cd backend

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate.bat  # Windows CMD
# OR
venv\Scripts\Activate.ps1  # Windows PowerShell

# Start Celery worker
celery -A app.tasks.celery_app worker -l info
```

**Expected Output:**
```
 -------------- celery@your-machine v5.3.4 (emoji)
--- ***** -----
-- ******* ----
- *** --- * ---
- ** ---------- [config]
- ** ----------
- ** ----------
oot@your-machine celery:apps:AppHelpFormatter
- *** --- * ---
-- ******* ----
--- ***** -----
 -------------- [Tasks]
. app.tasks.sync_tasks.check_stores_api_health
. app.tasks.sync_tasks.sync_all_stores
. app.tasks.sync_tasks.sync_store_products
. celery.backend_cleanup
. celery.chain
. celery.chord
. celery.group
. celery.map
. celery.starmap

[2024-10-26 14:30:00,123] WARNING/MainProcess] celery@your-machine ready.
```

**Key indicators of success:**
- Shows list of registered tasks
- Says "ready"
- No error messages

**Keep Terminal 3 open** - Celery worker must stay running.

---

### Step 5: Start Celery Beat (Terminal 4)

Celery Beat schedules recurring tasks like daily product syncs.

```bash
# Terminal 4
cd backend

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate.bat  # Windows CMD
# OR
venv\Scripts\Activate.ps1  # Windows PowerShell

# Start Celery Beat
celery -A app.tasks.celery_app beat -l info
```

**Expected Output:**
```
celery beat v5.3.4 (emoji)
Using scheduler: celery.beat.PersistentScheduler
LocalTime -> 2024-10-26 14:32:15.123456
Scheduler -> celery.beat.PersistentScheduler
Scheduler -> app.tasks.celery_app.PersistentScheduler
Instance -> celery@your-machine

 ----------- [Scheduler]
Timezone   -> UTC
Scheduler  -> celery.beat.PersistentScheduler

[Routers] -> ({'sync-stores-daily': {'task': 'app.tasks.sync_tasks.sync_all_stores', 'schedule': ...}})

[2024-10-26 14:32:15,456] WARNING/MainProcess [celery.beat] celery beat ready.
```

**Key indicators of success:**
- Shows scheduled tasks
- Says "ready"
- No error messages

**Keep Terminal 4 open** - Celery Beat must stay running.

---

## ✅ Verify All Services Are Running

Open a new terminal (Terminal 5) and run these checks:

```bash
# Terminal 5

# Check FastAPI is responding
echo "=== FastAPI Health Check ==="
curl http://localhost:8000/health
# Expected: {"status":"ok"}

echo ""
echo "=== Redis Check ==="
redis-cli PING
# Expected: PONG

echo ""
echo "=== Celery Check ==="
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app inspect active
# Expected: Dictionary of active tasks (may be empty)

echo ""
echo "=== Database Check ==="
psql -U shopify_user -d shopify_seo_prod -c "SELECT COUNT(*) FROM stores;"
# Expected: (1 row) with count - usually 0 initially

echo ""
echo "=== All checks complete ==="
```

**Expected Output Summary:**
```
=== FastAPI Health Check ===
{"status":"ok"}

=== Redis Check ===
PONG

=== Celery Check ===
{'celery@machine-name': {...}}

=== Database Check ===
 count
-------
     0
(1 row)

=== All checks complete ===
```

---

## 📊 Service Status Dashboard

Create a quick reference showing all your open terminals:

| Terminal | Service | Command | Port | Status |
|----------|---------|---------|------|--------|
| Terminal 1 | Redis | `redis-server` or `docker run` | 6379 | Should be running |
| Terminal 2 | FastAPI | `uvicorn app.main:app --reload` | 8000 | Should be running |
| Terminal 3 | Celery Worker | `celery -A app.tasks.celery_app worker` | - | Should show "ready" |
| Terminal 4 | Celery Beat | `celery -A app.tasks.celery_app beat` | - | Should show "ready" |
| Terminal 5 | Testing | Various curl/psql commands | - | For verification |

---

## 🔗 Access Backend Services

Once all services are running, you can access:

### 1. API Health Endpoint
```bash
curl http://localhost:8000/health
```
**Response**: `{"status":"ok"}`

### 2. Swagger UI (API Documentation)
```
http://localhost:8000/docs
```
Open in browser to see all API endpoints with try-it-out functionality.

### 3. ReDoc (Alternative API Docs)
```
http://localhost:8000/redoc
```

### 4. Check Celery Tasks
```bash
# List all active tasks
celery -A app.tasks.celery_app inspect active

# List scheduled tasks
celery -A app.tasks.celery_app inspect scheduled

# Get stats
celery -A app.tasks.celery_app inspect stats
```

### 5. Check Database
```bash
# Connect to database
psql -U shopify_user -d shopify_seo_prod

# View all stores
SELECT id, shopify_domain, store_name, created_at FROM stores;

# View all products
SELECT id, title, created_at FROM products LIMIT 10;

# Exit
\q
```

---

## 🐛 Common Issues & Solutions

### Issue 1: "Address already in use" on port 8000

```
ERROR: [Errno 98] Address already in use
```

**Solution**: Another process is using port 8000
```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### Issue 2: Celery Worker Won't Start - "Can't connect to Redis"

```
Error: [Errno 111] Connection refused
```

**Solution**: Redis is not running
```bash
# Start Redis
sudo systemctl start redis-server

# Verify
redis-cli ping  # Should return PONG
```

### Issue 3: FastAPI Won't Start - "ModuleNotFoundError"

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution**: Virtual environment not activated or dependencies not installed
```bash
# Ensure you're in backend directory
cd backend

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Try again
uvicorn app.main:app --reload
```

### Issue 4: Database Connection Failed

```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: Ident authentication failed
```

**Solution**: Check database credentials in .env
```bash
# Verify .env has correct DATABASE_URL
grep DATABASE_URL backend/.env

# Test connection
psql -U shopify_user -d shopify_seo_prod -c "SELECT 1;"

# If fails, check if PostgreSQL is running
sudo systemctl status postgresql
```

### Issue 5: Celery Tasks Not Running - "BROKER_TRANSPORT_OPTIONS"

```
Error: Connection refused
```

**Solution**: Redis not started or URL in .env is wrong
```bash
# Check Redis
redis-cli ping  # Should return PONG

# Check .env
grep REDIS_URL backend/.env  # Should show redis://localhost:6379

# If URL is wrong, update it
nano backend/.env  # Edit REDIS_URL
```

---

## 📋 Startup Checklist

Before moving to Step 5, verify:

- [ ] Terminal 1: Redis is running (`redis-cli ping` returns PONG)
- [ ] Terminal 2: FastAPI is running (shows "Application startup complete")
- [ ] Terminal 3: Celery Worker is running (shows "ready")
- [ ] Terminal 4: Celery Beat is running (shows "ready")
- [ ] Terminal 5: Health check passes (`curl http://localhost:8000/health` returns `{"status":"ok"}`)
- [ ] No errors in any terminal
- [ ] All 4 service terminals remain open

---

## ⏭️ Next Step

Once all services are running and verified, proceed to **Step 5: Test OAuth Flow** where we'll:
1. Initiate Shopify OAuth
2. Connect a test store
3. Verify the store is saved in the database

This is where the actual testing begins!

See: [STEP5_TEST_OAUTH_FLOW.md](./STEP5_TEST_OAUTH_FLOW.md)

---

## 🎯 Quick Start (Copy-Paste All at Once)

If you have 4 terminals open already:

```bash
# Terminal 1 - Redis
sudo systemctl start redis-server

# Terminal 2 - FastAPI
cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3 - Celery Worker
cd backend && source venv/bin/activate && celery -A app.tasks.celery_app worker -l info

# Terminal 4 - Celery Beat
cd backend && source venv/bin/activate && celery -A app.tasks.celery_app beat -l info

# Then in Terminal 5, verify:
curl http://localhost:8000/health
redis-cli ping
```

---

**Status**: Ready to start services
**Difficulty**: Low
**Estimated Time**: 10 minutes
