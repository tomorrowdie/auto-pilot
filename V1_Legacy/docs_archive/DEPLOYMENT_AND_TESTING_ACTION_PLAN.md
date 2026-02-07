# Deployment & Testing Action Plan - Shopify SEO Analyzer

**Status**: Ready to Execute
**Timeline**: 4-6 hours for complete local testing

---

## 📋 PROJECT CONTEXT CONFIRMED

✅ **Architecture Understanding**:
- Backend: FastAPI (Python) + SQLAlchemy ORM
- Frontend: React (TypeScript)
- Database: PostgreSQL 14
- Message Queue: Redis
- Task Queue: Celery (worker + beat)
- Server: AWS Lightsail (Ubuntu 20.04+)

✅ **Shopify Integration**:
- OAuth 2.0 authentication flow
- API Key: `00e0308488fd130c41f5de204a576b75`
- API Secret: `8773c3e3052ae05c2d13b4ea3833d362`
- Redirect URL: `/api/v1/auth/shopify/callback`
- Scopes: `read_products,write_products,read_themes,read_orders`

✅ **Environment**: AWS Lightsail ready with all dependencies

---

## 🎯 STEP-BY-STEP EXECUTION PLAN

### PHASE 1: ENVIRONMENT SETUP (30 minutes)

#### Step 1.1: Create .env File

```bash
# Navigate to backend directory
cd /path/to/shopify-seo-analyzer/backend

# Copy .env.example to .env
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Update these values in .env:**

```bash
# ============ SHOPIFY CONFIGURATION ============
SHOPIFY_API_KEY=00e0308488fd130c41f5de204a576b75
SHOPIFY_API_SECRET=8773c3e3052ae05c2d13b4ea3833d362
SHOPIFY_SCOPES=read_products,write_products,read_themes,read_orders
SHOPIFY_APP_URL=https://<YOUR_LIGHTSAIL_IP_OR_DOMAIN>

# ============ DATABASE CONFIGURATION ============
DATABASE_URL=postgresql://shopify_user:your_secure_password@localhost:5432/shopify_seo_prod

# ============ REDIS CONFIGURATION ============
REDIS_URL=redis://localhost:6379

# ============ APP SETTINGS ============
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key-minimum-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-minimum-32-chars

# ============ ALLOWED HOSTS ============
ALLOWED_HOSTS=["https://<YOUR_LIGHTSAIL_IP>","https://<YOUR_DOMAIN>"]

# ============ CELERY CONFIGURATION ============
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Generate Secure Keys:**
```bash
# Generate SECRET_KEY (32+ character random string)
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

#### Step 1.2: Verify .env is in .gitignore

```bash
# Check if .env is ignored
grep "^\.env" .gitignore

# If not, add it
echo ".env" >> .gitignore

# Verify it was added
tail -5 .gitignore
```

---

### PHASE 2: DATABASE SETUP (20 minutes)

#### Step 2.1: Create PostgreSQL Database

```bash
# Connect to PostgreSQL as admin
sudo -u postgres psql

# Execute these commands in psql:
CREATE DATABASE shopify_seo_prod;
CREATE USER shopify_user WITH PASSWORD 'your_secure_password';

-- Grant all privileges to the user
GRANT ALL PRIVILEGES ON DATABASE shopify_seo_prod TO shopify_user;

-- Exit psql
\q
```

#### Step 2.2: Verify Database Connection

```bash
# Test connection with your new credentials
psql -U shopify_user -d shopify_seo_prod -h localhost

# You should see the psql prompt. Exit with:
\q
```

#### Step 2.3: Run Database Migrations

```bash
# Navigate to backend directory
cd /opt/shopify-seo-analyzer/backend

# Activate virtual environment
source venv/bin/activate

# Export environment variables from .env
export $(cat ../.env | xargs)

# Run Alembic migrations
alembic upgrade head

# Expected output: Successfully upgraded database
```

#### Step 2.4: Verify Tables Created

```bash
# Connect to database and list tables
psql -U shopify_user -d shopify_seo_prod -h localhost

# List all tables:
\dt

# You should see:
# - stores
# - products
# - seo_analyses
# - keywords
# - product_keywords
# - (other tables)

# Exit
\q
```

---

### PHASE 3: START REQUIRED SERVICES (15 minutes)

#### Step 3.1: Verify Redis is Running

```bash
# Start Redis if not running
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping

# Expected response: PONG
```

#### Step 3.2: Start Celery Worker (Terminal 1)

```bash
# Navigate to backend
cd /opt/shopify-seo-analyzer/backend

# Activate virtual environment
source venv/bin/activate

# Start Celery worker
celery -A app.tasks.celery_app worker -l info

# Expected output:
# celery@hostname ready.
# mingle: sync with 0 workers
# [*] Connected to redis://localhost:6379/0
```

**Keep this terminal open!**

#### Step 3.3: Start Celery Beat (Terminal 2)

```bash
# Navigate to backend
cd /opt/shopify-seo-analyzer/backend

# Activate virtual environment
source venv/bin/activate

# Start Celery beat scheduler
celery -A app.tasks.celery_app beat -l info

# Expected output:
# celery beat v5.3.4 starts
# [*] synced
```

**Keep this terminal open!**

#### Step 3.4: Start FastAPI Backend (Terminal 3)

```bash
# Navigate to backend
cd /opt/shopify-seo-analyzer/backend

# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Expected output:
# Uvicorn running on http://0.0.0.0:8000
# Application startup complete
```

**Keep this terminal open!**

---

### PHASE 4: VERIFY BACKEND IS WORKING (10 minutes)

#### Step 4.1: Test API Health Endpoint

```bash
# Test the health endpoint (from new terminal)
curl http://localhost:8000/health

# Expected response:
# {"status":"ok"}
```

#### Step 4.2: Check FastAPI Docs

Open in browser:
```
http://localhost:8000/docs
```

You should see Swagger UI with all API endpoints listed.

#### Step 4.3: Verify Celery Connection

Check Terminal 1 (Celery Worker). You should see:
```
[*] Connected to redis://localhost:6379/0
```

And in Terminal 2 (Celery Beat), you should see:
```
[*] synced
```

---

### PHASE 5: UPDATE SHOPIFY PARTNER CONFIG (10 minutes)

#### Step 5.1: Get Your Lightsail IP/Domain

```bash
# Get your public IP
curl -s http://169.254.169.254/latest/meta-data/public-ipv4

# Or check in AWS Lightsail console
# Note: If using domain, make sure DNS is pointing to this IP
```

#### Step 5.2: Update Shopify Partner Dashboard

1. Go to https://partners.shopify.com
2. Select your app: **seo-analyzer**
3. Click **Configuration**
4. Find **"Allowed redirection URLs"**
5. Update to:
   ```
   https://<YOUR_LIGHTSAIL_IP>/api/v1/auth/shopify/callback
   ```
6. Save

**Important**: This URL must match EXACTLY what's in your `.env` file.

---

### PHASE 6: TEST SHOPIFY OAUTH FLOW (15 minutes)

#### Step 6.1: Test Install Endpoint

```bash
# Test OAuth install endpoint
curl -X POST http://localhost:8000/api/v1/auth/shopify/install \
  -H "Content-Type: application/json" \
  -d '{"shop": "your-test-store.myshopify.com"}'

# Expected response:
# {
#   "install_url": "https://your-test-store.myshopify.com/admin/oauth/authorize?...",
#   "state": "random_state_token"
# }
```

#### Step 6.2: Complete OAuth in Browser

1. Copy the `install_url` from the response above
2. Paste it into your browser
3. You'll be redirected to your Shopify store's OAuth approval screen
4. Click "Approve"
5. Shopify redirects you back to your callback URL

#### Step 6.3: Verify Store in Database

```bash
# Check if store was saved in database
psql -U shopify_user -d shopify_seo_prod -h localhost << EOF
SELECT * FROM stores;
\q
EOF

# You should see your test store with:
# - shopify_domain
# - store_name
# - shopify_access_token (encrypted)
# - created_at timestamp
```

#### Step 6.4: Test Verify Endpoint

```bash
# Verify store connection
curl http://localhost:8000/api/v1/auth/shopify/verify/your-test-store.myshopify.com

# Expected response:
# {"status": "success"}
```

---

### PHASE 7: TEST PRODUCT SYNC (10 minutes)

#### Step 7.1: Trigger Manual Product Sync

```bash
# Queue product sync task
curl -X POST http://localhost:8000/api/v1/stores/your-store-id/sync

# Expected response:
# {
#   "status": "success",
#   "task_id": "unique-task-id"
# }
```

**Note**: Replace `your-store-id` with the actual UUID from the stores table.

#### Step 7.2: Monitor Sync in Celery Worker

Watch Terminal 1 (Celery Worker). You should see:
```
[*] Received task: app.tasks.sync_tasks.sync_store_products
[*] Task succeeded in 5.23s
```

#### Step 7.3: Verify Products in Database

```bash
# Check if products were synced
psql -U shopify_user -d shopify_seo_prod -h localhost << EOF
SELECT COUNT(*) as product_count FROM products;
\q
EOF

# Should return a count > 0
```

---

### PHASE 8: BUILD FRONTEND (10 minutes)

#### Step 8.1: Install Frontend Dependencies

```bash
# Navigate to frontend
cd /opt/shopify-seo-analyzer/frontend

# Install npm packages
npm install
```

#### Step 8.2: Build for Production

```bash
# Build React for production
npm run build

# This creates a 'build' folder with optimized files
# Check if build was successful:
ls -la build/
# Should see: index.html, static/, etc.
```

---

### PHASE 9: FRONTEND TESTING (10 minutes)

#### Step 9.1: Start Frontend Dev Server (Terminal 4)

```bash
# Navigate to frontend
cd /opt/shopify-seo-analyzer/frontend

# Start dev server (for testing)
npm start

# This starts a dev server on http://localhost:3000
```

#### Step 9.2: Test Frontend in Browser

Open in browser:
```
http://localhost:3000
```

You should see:
- ✅ Dashboard loads
- ✅ "Connect Store" button visible
- ✅ Can click without errors
- ✅ No 404 errors in console

#### Step 9.3: Test Store Connection Flow

1. Click "Connect Store"
2. Enter your test store domain
3. You should be redirected to Shopify OAuth
4. Complete the OAuth flow
5. Redirected back to dashboard
6. Store should appear in the list

---

### PHASE 10: COMPLETE WORKFLOW TEST (20 minutes)

#### Step 10.1: Full End-to-End Test

**Checklist**:
- [ ] Backend API running on port 8000
- [ ] Frontend running on port 3000
- [ ] Redis running (Celery connected)
- [ ] PostgreSQL database working
- [ ] Can access `/health` endpoint
- [ ] Can initiate OAuth
- [ ] OAuth completes successfully
- [ ] Store appears in database
- [ ] Can verify store connection
- [ ] Can trigger product sync
- [ ] Products appear in database
- [ ] Frontend connects to backend API
- [ ] Can see dashboard in frontend
- [ ] Can trigger "Connect Store" from UI

#### Step 10.2: Test API Endpoints

```bash
# Test different endpoints
curl http://localhost:8000/docs  # Should see Swagger UI

# Get stores
curl http://localhost:8000/api/v1/stores/

# Get products
curl http://localhost:8000/api/v1/products/

# Get analyses
curl http://localhost:8000/api/v1/analysis/
```

#### Step 10.3: Monitor Logs

Check each terminal for any errors:
- Terminal 1 (Celery Worker): Any task failures?
- Terminal 2 (Celery Beat): Any scheduler errors?
- Terminal 3 (FastAPI): Any 500 errors?
- Browser console: Any JavaScript errors?

---

## ✅ SUCCESS CRITERIA

Your setup is successful when ALL of these pass:

**Database & Services**
- [ ] PostgreSQL running and accessible
- [ ] Redis running and accessible
- [ ] Celery worker online and ready
- [ ] Celery beat scheduler running
- [ ] FastAPI backend responding

**Shopify Integration**
- [ ] OAuth install URL generates correctly
- [ ] OAuth flow redirects properly
- [ ] Store is saved to database after OAuth
- [ ] Can verify store connection
- [ ] API token is encrypted in database

**Data Sync**
- [ ] Product sync task executes
- [ ] Products appear in database
- [ ] Task completion is logged in Celery worker

**Frontend**
- [ ] React frontend builds without errors
- [ ] Frontend loads in browser at localhost:3000
- [ ] Can click "Connect Store" button
- [ ] Can complete OAuth from frontend
- [ ] Dashboard displays correctly

**End-to-End**
- [ ] Full workflow: Login → Connect Store → See Products → View Analysis
- [ ] No error messages in logs
- [ ] All database queries work
- [ ] All API endpoints respond correctly

---

## 🚨 TROUBLESHOOTING

### Issue: OAuth Fails (invalid_redirect_uri)
**Cause**: Redirect URL doesn't match in Shopify Partner Dashboard
**Fix**:
1. Check URL in Shopify Partner Dashboard exactly matches `.env`
2. Clear browser cookies
3. Try OAuth again

### Issue: Database Connection Error
**Cause**: PostgreSQL not running or wrong credentials
**Fix**:
```bash
# Start PostgreSQL
sudo systemctl start postgresql

# Test connection
psql -U shopify_user -d shopify_seo_prod -h localhost

# Check credentials in .env
```

### Issue: Celery Tasks Not Running
**Cause**: Redis not running or Celery not connected
**Fix**:
```bash
# Start Redis
sudo systemctl start redis-server
redis-cli ping  # Should return PONG

# Restart Celery worker
# Kill terminal and restart
```

### Issue: Frontend Won't Build
**Cause**: Missing dependencies or npm issues
**Fix**:
```bash
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue: Port Already in Use
**Cause**: Service already running on port
**Fix**:
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Then restart the service
```

---

## 📊 FINAL VERIFICATION CHECKLIST

Before declaring deployment complete:

**Services**
- [ ] `curl http://localhost:8000/health` returns 200 OK
- [ ] `redis-cli ping` returns PONG
- [ ] `psql -U shopify_user -d shopify_seo_prod -c "SELECT 1"` works
- [ ] Celery worker shows "ready" message
- [ ] Celery beat shows "synced" message

**OAuth**
- [ ] Can generate install URL
- [ ] OAuth flow completes without errors
- [ ] Store appears in database with correct data
- [ ] Verify endpoint returns success

**Data**
- [ ] Can sync products from Shopify
- [ ] Products appear in database
- [ ] Can query products table

**Frontend**
- [ ] Frontend builds successfully
- [ ] Frontend loads in browser
- [ ] Can interact with UI (click buttons, etc)
- [ ] No console errors

**API**
- [ ] All endpoints in Swagger UI are accessible
- [ ] GET requests return 200 OK
- [ ] POST requests return 201 Created
- [ ] Error responses include error messages

---

## 🎯 NEXT STEPS AFTER TESTING

Once all tests pass:

1. **Set up SSL/HTTPS**:
   ```bash
   sudo certbot certonly --standalone -d yourdomain.com
   ```

2. **Configure Nginx**:
   - Follow steps in `enhanced_setup_guide.md`
   - Serve frontend via Nginx
   - Proxy API requests to FastAPI

3. **Deploy to AWS**:
   - Create systemd services for auto-start
   - Set up monitoring and alerts
   - Configure backups
   - Go live!

4. **Add Users**:
   - Invite beta testers
   - Monitor logs for issues
   - Iterate based on feedback

---

## 📞 SUPPORT

**Quick Reference**:
- API Docs: `http://localhost:8000/docs`
- Celery Logs: Check terminal running `celery worker`
- Database Logs: Check PostgreSQL service logs
- Frontend Logs: Check browser console (F12)
- Backend Logs: Check FastAPI server terminal

**Documentation**:
- `shopify_aws_setup.md` - Setup overview
- `enhanced_setup_guide.md` - Detailed setup
- `TESTING_GUIDE.md` - Full testing procedures
- `IMMEDIATE_NEXT_STEPS.md` - AWS deployment

---

**Version**: 1.0
**Status**: Ready to Execute
**Time Estimate**: 4-6 hours for complete setup and testing
**Difficulty**: Medium (follow steps exactly)

**Good luck with your deployment! 🚀**
