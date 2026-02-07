# Step 3: Prepare Local Environment for Testing

## 📍 You Are Here
- ✅ Step 1: Project Context Loaded
- ✅ Step 2: Environment Variables Updated (`.env` created with Shopify credentials)
- ⏳ **Step 3: Prepare Local Environment for Testing** ← You are here
- 📋 Step 4: Start Backend Services
- 📋 Step 5: Test OAuth Flow
- 📋 Step 6: Test Product Synchronization
- 📋 Step 7: Test Frontend

---

## 🎯 Goal of This Step

Get your local development environment ready to run the complete Shopify SEO Analyzer application with all services (PostgreSQL, Redis, FastAPI, Celery).

**Estimated Time**: 20-30 minutes

---

## ✅ Pre-Flight Checklist

Before starting, verify you have:

- [x] `.env` file created with Shopify credentials (`backend/.env`)
- [ ] Python 3.9+ installed (`python --version`)
- [ ] Node.js 16+ installed (`node --version`)
- [ ] PostgreSQL installed and able to be started
- [ ] Redis installed or available via Docker
- [ ] Git bash or terminal ready

---

## 🔧 Setup Instructions

### Phase 1: Backend Python Environment (10 minutes)

#### 1.1 Navigate to Backend Directory

```bash
cd backend
pwd  # Verify you're in the backend directory
ls -la  # Should show: requirements.txt, app/, alembic/, etc.
```

**Expected Output:**
```
/path/to/shopify-seo-analyzer/backend
```

#### 1.2 Create Python Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate venv
# On macOS/Linux:
source venv/bin/activate

# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# On Windows (CMD):
venv\Scripts\activate.bat
```

**Verify activation** - you should see `(venv)` at the start of your terminal prompt:
```
(venv) $ _
```

#### 1.3 Install Python Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

**This will install:**
- FastAPI (web framework)
- SQLAlchemy (database ORM)
- Alembic (database migrations)
- Celery (background tasks)
- psycopg2 (PostgreSQL driver)
- httpx (async HTTP client)
- cryptography (encryption)
- pytest (testing)
- And 60+ other packages

**Expected Output:**
```
Successfully installed fastapi-0.104.1 sqlalchemy-2.0.23 celery-5.3.4 ...
```

**Verify installation:**
```bash
pip list | grep -E "fastapi|sqlalchemy|celery|psycopg2"
# Should show versions of FastAPI, SQLAlchemy, Celery, psycopg2
```

---

### Phase 2: Database Setup (5 minutes)

#### 2.1 Verify PostgreSQL is Running

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# If not running, start it:
sudo systemctl start postgresql

# Verify it's listening
psql --version
psql -U postgres -c "SELECT 1;"
```

**Expected Output:**
```
PostgreSQL is running at /var/run/postgresql
(1 row)
```

#### 2.2 Create Database and User

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Inside psql prompt (>):
CREATE DATABASE shopify_seo_prod;
CREATE USER shopify_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE shopify_seo_prod TO shopify_user;
\q
```

**Verify it worked:**
```bash
# Test connection
psql -U shopify_user -d shopify_seo_prod -c "SELECT NOW();"
```

**Expected Output:**
```
              now
-------------------------------
 2024-10-26 14:23:45.123456+00
(1 row)
```

#### 2.3 Run Database Migrations

```bash
# Make sure you're in backend directory and venv is activated
cd backend
source venv/bin/activate  # If not already activated

# Run migrations
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl with dialect postgresql
INFO  [alembic.runtime.migration] Will assume transactional DDL is supported by backend
INFO  [alembic.runtime.migration] Running upgrade  -> [migration_id], [migration_description]
...
INFO  [alembic.runtime.migration] Running upgrade [last_id] -> head
```

**Verify tables created:**
```bash
# Check what tables were created
psql -U shopify_user -d shopify_seo_prod -c "\dt"
```

**Expected Output:**
```
               List of relations
 Schema |              Name              | Type  | Owner
--------+--------------------------------+-------+---------------
 public | alembic_version                | table | shopify_user
 public | products                       | table | shopify_user
 public | seo_analyses                   | table | shopify_user
 public | stores                         | table | shopify_user
 public | keywords                       | table | shopify_user
 public | product_keywords               | table | shopify_user
(6 rows)
```

---

### Phase 3: Redis Setup (5 minutes)

Redis is required for Celery task queue and caching.

#### 3.1 Start Redis Server

**Option A: Using systemd (if installed)**
```bash
# Start Redis
sudo systemctl start redis-server

# Verify it's running
redis-cli ping
```

**Option B: Using Docker (if you have Docker)**
```bash
# Run Redis in Docker
docker run -d -p 6379:6379 --name redis-server redis:7

# Verify it's running
redis-cli ping
```

**Option C: Using Homebrew (macOS)**
```bash
# Install if not already
brew install redis

# Start Redis
brew services start redis

# Verify
redis-cli ping
```

**Expected Output:**
```
PONG
```

#### 3.2 Verify Redis Connection

```bash
# Test Redis connectivity
redis-cli INFO server | head -5
```

**Expected Output:**
```
# Server
redis_version:7.0.0
redis_git_sha1:00000000
redis_git_dirty:0
redis_build_id:0
```

---

### Phase 4: Verify All Services Are Ready

#### 4.1 Quick Service Check

```bash
# Create a test script to verify everything
cat > /tmp/verify_services.sh << 'EOF'
#!/bin/bash

echo "=== Service Verification ==="
echo ""

# Check PostgreSQL
echo "PostgreSQL:"
if psql -U shopify_user -d shopify_seo_prod -c "SELECT 1;" 2>/dev/null; then
    echo "✅ PostgreSQL is running and accessible"
else
    echo "❌ PostgreSQL is not accessible"
fi
echo ""

# Check Redis
echo "Redis:"
if redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "✅ Redis is running and accessible"
else
    echo "❌ Redis is not accessible"
fi
echo ""

# Check Python venv
echo "Python Virtual Environment:"
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment is activated: $VIRTUAL_ENV"
else
    echo "❌ Virtual environment is not activated"
fi
echo ""

# Check Python packages
echo "Python Packages:"
if python -c "import fastapi, sqlalchemy, celery" 2>/dev/null; then
    echo "✅ Required packages are installed"
else
    echo "❌ Required packages are not installed"
fi
echo ""

# Check .env file
echo ".env File:"
if [ -f "../.env" ]; then
    echo "✅ .env file exists"
else
    echo "❌ .env file not found"
fi

EOF

bash /tmp/verify_services.sh
```

**Expected Output:**
```
=== Service Verification ===

PostgreSQL:
✅ PostgreSQL is running and accessible

Redis:
✅ Redis is running and accessible

Python Virtual Environment:
✅ Virtual environment is activated: /path/to/venv

Python Packages:
✅ Required packages are installed

.env File:
✅ .env file exists
```

---

## 🚀 Services Startup Checklist

Before moving to Step 4 (Starting Services), verify:

- [ ] Python 3.9+ installed and working
- [ ] Virtual environment created and activated
- [ ] Python dependencies installed (`pip install -r requirements.txt` succeeded)
- [ ] PostgreSQL database created (`shopify_seo_prod`)
- [ ] PostgreSQL user created (`shopify_user`)
- [ ] Database migrations ran successfully (`alembic upgrade head`)
- [ ] Database tables exist (check with `\dt` in psql)
- [ ] Redis server is running (`redis-cli ping` returns PONG)
- [ ] `.env` file exists with Shopify credentials
- [ ] `.env` has `DATABASE_URL` pointing to correct PostgreSQL
- [ ] `.env` has `REDIS_URL=redis://localhost:6379`

---

## 📋 Current Status

| Component | Status | Action |
|-----------|--------|--------|
| **Python Environment** | ⏳ Setup | Run `python -m venv venv && source venv/bin/activate` |
| **Dependencies** | ⏳ Setup | Run `pip install -r requirements.txt` |
| **PostgreSQL Database** | ⏳ Setup | Run setup commands in Phase 2 |
| **Database Migrations** | ⏳ Setup | Run `alembic upgrade head` |
| **Redis Server** | ⏳ Setup | Start with systemctl or Docker |
| **Backend Ready** | ⏳ Pending | All above must complete |

---

## 🔍 Troubleshooting

### PostgreSQL Issues

**Problem**: `psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed`
```bash
# Solution: Start PostgreSQL
sudo systemctl start postgresql

# Or check if it's already running
sudo systemctl status postgresql
```

**Problem**: `FATAL: Ident authentication failed for user "shopify_user"`
```bash
# Solution: Check password in .env matches what was set
# Recreate the user:
sudo -u postgres psql
DROP USER shopify_user;
CREATE USER shopify_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE shopify_seo_prod TO shopify_user;
\q
```

**Problem**: `ERROR: database "shopify_seo_prod" does not exist`
```bash
# Solution: Create the database
sudo -u postgres psql -c "CREATE DATABASE shopify_seo_prod;"
```

### Redis Issues

**Problem**: `ConnectionRefusedError: [Errno 111] Connection refused`
```bash
# Solution: Start Redis
sudo systemctl start redis-server

# Or with Docker:
docker run -d -p 6379:6379 redis:7
```

**Problem**: `redis-cli: command not found`
```bash
# Solution: Install Redis
# Ubuntu/Debian:
sudo apt-get install redis-server

# macOS:
brew install redis

# Or use Docker:
docker run -d -p 6379:6379 redis:7
```

### Python/Virtual Environment Issues

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Solution: Ensure venv is activated and dependencies installed
source venv/bin/activate
pip install -r requirements.txt
```

**Problem**: `python: command not found`
```bash
# Solution: Install Python 3.9+
# Ubuntu/Debian:
sudo apt-get install python3.9 python3.9-venv

# macOS:
brew install python@3.9

# Then try again
python --version
```

### Database Migration Issues

**Problem**: `alembic.exc.CommandError: Can't locate revision identified by 'abc123'`
```bash
# Solution: Reset alembic version
alembic stamp head
alembic upgrade head
```

**Problem**: `ERROR: permission denied for schema public`
```bash
# Solution: Grant schema permissions
sudo -u postgres psql -d shopify_seo_prod -c "GRANT USAGE ON SCHEMA public TO shopify_user;"
sudo -u postgres psql -d shopify_seo_prod -c "GRANT CREATE ON SCHEMA public TO shopify_user;"
```

---

## ✅ Next Step

Once all services are verified as working, proceed to **Step 4: Start Backend Services** where we'll start:
1. FastAPI server
2. Celery worker
3. Celery beat scheduler

This guide will be available at: [STEP4_START_BACKEND_SERVICES.md](./STEP4_START_BACKEND_SERVICES.md)

---

## 📞 Quick Reference

### Start All Services (Quick Copy-Paste)

```bash
# Terminal 1: PostgreSQL (usually auto-starts)
sudo systemctl start postgresql

# Terminal 2: Redis
sudo systemctl start redis-server

# Terminal 3: Backend - Navigate to backend dir, activate venv, start server
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 4: Celery Worker
cd backend && source venv/bin/activate && celery -A app.tasks.celery_app worker -l info

# Terminal 5: Celery Beat
cd backend && source venv/bin/activate && celery -A app.tasks.celery_app beat -l info

# Terminal 6: Frontend
cd frontend && npm start
```

---

**Estimated Completion Time**: 30 minutes
**Difficulty**: Medium
**Next Step**: [STEP4_START_BACKEND_SERVICES.md](./STEP4_START_BACKEND_SERVICES.md)
