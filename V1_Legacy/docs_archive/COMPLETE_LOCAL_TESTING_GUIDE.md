# Complete Local Testing Guide - Shopify SEO Analyzer

## 📍 Complete Testing Roadmap

This guide coordinates all testing steps for your Shopify SEO Analyzer project.

```
START HERE
    ↓
Step 1: Load Project Context
    ↓
Step 2: Update Environment Variables (.env)
    ↓
Step 3: Prepare Local Environment
    ├─ Create Python virtual environment
    ├─ Install dependencies
    ├─ Create PostgreSQL database
    ├─ Run migrations
    └─ Start Redis
    ↓
Step 4: Start Backend Services
    ├─ Start Redis (Terminal 1)
    ├─ Start FastAPI (Terminal 2)
    ├─ Start Celery Worker (Terminal 3)
    └─ Start Celery Beat (Terminal 4)
    ↓
Step 5: Test OAuth Flow
    ├─ Initiate OAuth installation
    ├─ Complete in Shopify
    └─ Verify store in database
    ↓
Step 6: Test Product Synchronization
    ├─ Trigger manual sync
    ├─ Monitor Celery worker
    └─ Verify products in database
    ↓
Step 7: Test Frontend (Optional but Recommended)
    ├─ Install Node dependencies
    ├─ Build React application
    └─ Test API connectivity
    ↓
COMPLETE TESTING ✅
```

---

## 🎯 Quick Start (TL;DR)

If you've already completed Steps 1-3, use these commands:

### Terminal 1: Redis
```bash
sudo systemctl start redis-server
redis-cli ping  # Should return PONG
```

### Terminal 2: FastAPI
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 3: Celery Worker
```bash
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker -l info
```

### Terminal 4: Celery Beat
```bash
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app beat -l info
```

### Terminal 5: Test
```bash
# Health check
curl http://localhost:8000/health

# Initiate OAuth
curl -X POST http://localhost:8000/api/v1/auth/shopify/install \
  -H "Content-Type: application/json" \
  -d '{"shop": "your-store.myshopify.com"}'

# After OAuth, check database
psql -U shopify_user -d shopify_seo_prod -c "SELECT shopify_domain FROM stores;"
```

---

## 📋 Detailed Testing Phases

### Phase 1: Environment Setup (30 minutes)

See: [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md)

**What you'll do:**
- [x] Copy `.env.example` to `.env`
- [x] Add Shopify API credentials
- [x] Generate SECRET_KEY and JWT_SECRET_KEY
- [x] Set database URL
- [x] Set Redis URL

**Verification:**
- [ ] `.env` file exists
- [ ] All critical variables are set
- [ ] `.env` is in `.gitignore`

---

### Phase 2: Infrastructure Setup (20 minutes)

See: [STEP3_LOCAL_ENVIRONMENT_TESTING.md](./STEP3_LOCAL_ENVIRONMENT_TESTING.md)

**What you'll do:**
- [x] Create Python virtual environment
- [x] Install all dependencies
- [x] Create PostgreSQL database
- [x] Create PostgreSQL user
- [x] Run database migrations
- [x] Start Redis

**Verification:**
- [ ] Virtual environment activated
- [ ] `pip list` shows 70+ packages
- [ ] PostgreSQL database exists
- [ ] Database migrations succeeded
- [ ] Redis is responding (`redis-cli ping`)

---

### Phase 3: Service Startup (10 minutes)

See: [STEP4_START_BACKEND_SERVICES.md](./STEP4_START_BACKEND_SERVICES.md)

**What you'll do:**
- [x] Start Redis
- [x] Start FastAPI backend
- [x] Start Celery worker
- [x] Start Celery Beat

**Verification in 4 Terminals:**
- [ ] Terminal 1: Redis running (`redis-cli ping` = PONG)
- [ ] Terminal 2: FastAPI running (`curl http://localhost:8000/health` = `{"status":"ok"}`)
- [ ] Terminal 3: Celery Worker ready (shows "ready" in logs)
- [ ] Terminal 4: Celery Beat ready (shows "ready" in logs)

---

### Phase 4: OAuth Testing (15-20 minutes)

See: [STEP5_TEST_OAUTH_FLOW.md](./STEP5_TEST_OAUTH_FLOW.md)

**What you'll do:**
1. Update Shopify Partner App redirect URL
2. Initiate OAuth via API
3. Complete OAuth in browser
4. Verify store saved in database
5. Verify token encrypted

**Commands:**
```bash
# Terminal 5: Initiate OAuth
curl -X POST http://localhost:8000/api/v1/auth/shopify/install \
  -H "Content-Type: application/json" \
  -d '{"shop": "your-test-store.myshopify.com"}'

# In browser: Open returned install_url
# Approve app installation

# Terminal 5: Verify store in database
psql -U shopify_user -d shopify_seo_prod -c "SELECT shopify_domain FROM stores;"
```

**Verification:**
- [ ] OAuth URL generated with state parameter
- [ ] Can approve app in Shopify
- [ ] Redirected back without error
- [ ] Store appears in database
- [ ] Token is encrypted (`gAAAAABl...` format)

---

### Phase 5: Product Sync Testing (20-30 minutes)

See: [STEP6_TEST_PRODUCT_SYNC.md](./STEP6_TEST_PRODUCT_SYNC.md)

**What you'll do:**
1. Get store ID from database
2. Trigger manual product sync
3. Monitor Celery worker execution
4. Verify products in database
5. Check sync status

**Commands:**
```bash
# Terminal 5: Get store ID
psql -U shopify_user -d shopify_seo_prod -c "SELECT id FROM stores LIMIT 1;"

# Trigger sync
STORE_ID="your-id-here"
curl -X POST http://localhost:8000/api/v1/stores/${STORE_ID}/sync

# Monitor Terminal 3 for Celery worker output

# Verify products
psql -U shopify_user -d shopify_seo_prod -c "SELECT COUNT(*) FROM products;"
```

**Verification:**
- [ ] Sync task initiated
- [ ] Celery worker executes task
- [ ] Task completes with SUCCESS
- [ ] Products appear in database (`count > 0`)
- [ ] Products have complete data
- [ ] Sync status shows correct product count

---

### Phase 6: Frontend Testing (Optional but Recommended)

See: [STEP7_TEST_FRONTEND.md](./STEP7_TEST_FRONTEND.md)

**What you'll do:**
1. Navigate to frontend directory
2. Install Node dependencies
3. Configure API URL
4. Build React application
5. Test API connectivity

**Commands:**
```bash
# Terminal 6: Frontend
cd frontend
npm install
REACT_APP_API_URL=http://localhost:8000/api/v1 npm start

# Opens on http://localhost:3000
```

**Verification:**
- [ ] Frontend builds without errors
- [ ] Frontend loads in browser
- [ ] Can see stores connected
- [ ] API calls succeed
- [ ] No CORS errors

---

## 📊 Complete Testing Checklist

### ✅ Environment Variables
- [ ] `.env` file created
- [ ] Shopify API Key set
- [ ] Shopify API Secret set
- [ ] Database URL correct
- [ ] Redis URL correct
- [ ] Secret keys generated
- [ ] `.env` in `.gitignore`

### ✅ Infrastructure
- [ ] Python virtual environment created
- [ ] Dependencies installed
- [ ] PostgreSQL running
- [ ] Database created
- [ ] Database user created
- [ ] Migrations run successfully
- [ ] Redis running

### ✅ Services
- [ ] Redis operational
- [ ] FastAPI responding to health check
- [ ] Celery worker registered
- [ ] Celery Beat ready
- [ ] All 4 terminals running without errors

### ✅ OAuth
- [ ] Shopify Partner App configured
- [ ] Redirect URL updated
- [ ] OAuth initiation works
- [ ] Can approve in Shopify
- [ ] Callback succeeds
- [ ] Store in database
- [ ] Token encrypted

### ✅ Product Sync
- [ ] Manual sync can be triggered
- [ ] Celery worker executes
- [ ] Sync completes successfully
- [ ] Products in database
- [ ] Product data complete
- [ ] Sync status updated
- [ ] Scheduled sync configured

### ✅ Frontend (Optional)
- [ ] Node dependencies installed
- [ ] Build succeeds
- [ ] Frontend serves on port 3000
- [ ] Can connect to API
- [ ] Stores display
- [ ] No errors in console

---

## 📈 Expected Results

When all testing is complete, you should have:

| Component | Status | Evidence |
|-----------|--------|----------|
| **Environment** | ✅ Ready | `.env` file with all variables |
| **Database** | ✅ Connected | Tables created, migrations run |
| **Services** | ✅ Running | 4+ terminals with services |
| **Authentication** | ✅ Working | Store connected via OAuth |
| **Sync System** | ✅ Working | 10+ products in database |
| **Frontend** | ✅ Optional | Dashboard loads (if completed) |

---

## 🚀 What's Next After Testing?

Once local testing is complete and working:

1. **AWS Deployment** - Deploy to Lightsail
2. **Production Setup** - Configure domain, SSL, monitoring
3. **User Testing** - Invite beta users
4. **Performance Optimization** - Profile and optimize
5. **Launch** - Go live!

See: [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md) for production deployment guide.

---

## 🆘 Troubleshooting Guide

### Common Issues by Step

#### Step 3 Issues
| Problem | Solution |
|---------|----------|
| PostgreSQL not found | `sudo apt-get install postgresql` |
| psycopg2 won't install | `pip install psycopg2-binary` |
| Migration fails | `alembic stamp head && alembic upgrade head` |

#### Step 4 Issues
| Problem | Solution |
|---------|----------|
| Port 8000 in use | `lsof -i :8000` then `kill -9 PID` |
| Redis connection refused | `sudo systemctl start redis-server` |
| Celery won't connect | `redis-cli ping` should return PONG |

#### Step 5 Issues
| Problem | Solution |
|---------|----------|
| Invalid redirect URL | Update in Shopify Partner Dashboard |
| Token decryption fails | Check SECRET_KEY in `.env` |
| HMAC validation error | Verify SHOPIFY_API_SECRET is exact copy |

#### Step 6 Issues
| Problem | Solution |
|---------|----------|
| Sync hangs | Check Celery worker in Terminal 3 |
| No products sync | Verify store has products in Shopify |
| 401 Unauthorized | Reconnect store via OAuth |

#### Step 7 Issues
| Problem | Solution |
|---------|----------|
| CORS errors | Ensure ALLOWED_HOSTS in `.env` is correct |
| API 404 errors | Check FastAPI is running and has reloaded |
| Build fails | Delete `node_modules` and `npm install` again |

---

## 📞 Support Resources

### Documentation Files
- `ENV_SETUP_GUIDE.md` - Environment variables
- `STEP3_LOCAL_ENVIRONMENT_TESTING.md` - Infrastructure setup
- `STEP4_START_BACKEND_SERVICES.md` - Service startup
- `STEP5_TEST_OAUTH_FLOW.md` - OAuth testing
- `STEP6_TEST_PRODUCT_SYNC.md` - Sync testing
- `STEP7_TEST_FRONTEND.md` - Frontend testing
- `COMPLETE_IMPLEMENTATION_REPORT.md` - Technical details
- `TESTING_GUIDE.md` - Comprehensive testing procedures

### Important URLs
- FastAPI Health: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`
- Frontend (after starting): `http://localhost:3000`
- Shopify Partner Dashboard: `https://partners.shopify.com/dashboard`

### Debug Commands
```bash
# Check all services
ps aux | grep -E "redis|postgres|celery|uvicorn"

# Check database
psql -U shopify_user -d shopify_seo_prod -c "\dt"

# Check logs
tail -f backend/logs/app.log

# Monitor Celery
celery -A app.tasks.celery_app inspect active
celery -A app.tasks.celery_app inspect stats
```

---

## ✅ Final Verification

Run this final verification script to confirm everything is ready:

```bash
#!/bin/bash

echo "=== Shopify SEO Analyzer - Testing Verification ==="
echo ""

echo "1. PostgreSQL:"
psql -U shopify_user -d shopify_seo_prod -c "SELECT 1;" && echo "   ✅ Connected" || echo "   ❌ Failed"

echo ""
echo "2. Redis:"
redis-cli ping | grep -q PONG && echo "   ✅ Running" || echo "   ❌ Not running"

echo ""
echo "3. FastAPI:"
curl -s http://localhost:8000/health | grep -q "ok" && echo "   ✅ Responding" || echo "   ❌ Not responding"

echo ""
echo "4. Database Tables:"
TABLES=$(psql -U shopify_user -d shopify_seo_prod -c "\dt" | grep -c "public")
echo "   Found $TABLES tables ✅"

echo ""
echo "5. Stores:"
COUNT=$(psql -U shopify_user -d shopify_seo_prod -c "SELECT COUNT(*) FROM stores;" | grep -oE "[0-9]+$" | head -1)
echo "   Stores connected: $COUNT"

echo ""
echo "6. Products:"
COUNT=$(psql -U shopify_user -d shopify_seo_prod -c "SELECT COUNT(*) FROM products;" | grep -oE "[0-9]+$" | head -1)
echo "   Products synced: $COUNT"

echo ""
echo "=== Status Summary ==="
echo "If all above show ✅, you're ready for production!"
```

---

## 📝 Session Notes

**Start Date**: October 26, 2024
**Version**: 1.0
**Status**: ✅ Ready for Testing

Record your testing progress:
- [ ] Started testing at: ________
- [ ] Completed Step 1 at: ________
- [ ] Completed Step 2 at: ________
- [ ] Completed Step 3 at: ________
- [ ] Completed Step 4 at: ________
- [ ] Completed Step 5 at: ________
- [ ] Completed Step 6 at: ________
- [ ] Completed Step 7 at: ________
- [ ] All tests passing: ________

---

**Next**: Follow [STEP3_LOCAL_ENVIRONMENT_TESTING.md](./STEP3_LOCAL_ENVIRONMENT_TESTING.md) to begin setup.

All files in this guide have been created and are ready to guide you through complete local testing of your Shopify SEO Analyzer application.

**Good luck! 🚀**
