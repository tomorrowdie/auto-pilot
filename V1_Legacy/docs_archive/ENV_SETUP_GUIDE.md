# Environment Variables Setup Guide

## ✅ Status: COMPLETED

The `.env` file has been created at `backend/.env` with all required variables populated for local testing.

---

## 📋 What Was Done

### Step 1: Created .env File
- **Location**: `backend/.env`
- **Status**: ✅ Created with all 53 environment variables
- **Populated Shopify Credentials**:
  - `SHOPIFY_API_KEY=00e0308488fd130c41f5de204a576b75`
  - `SHOPIFY_API_SECRET=8773c3e3052ae05c2d13b4ea3833d362`
  - `SHOPIFY_SCOPES=read_products,write_products,read_themes,read_orders`
  - `SHOPIFY_APP_URL=https://localhost:8000` (needs to be updated with your Lightsail IP/domain)

### Step 2: Verified .env in .gitignore
- **Status**: ✅ Already protected
- `.env` file is listed on line 2 of `.gitignore`
- Credentials will NOT be committed to git

### Step 3: Generated Secure Keys
- **SECRET_KEY**: Generated 56-character random key
- **JWT_SECRET_KEY**: Generated 56-character random key
- Both keys are cryptographically secure for local testing

---

## 🔧 Environment Variables Reference

### Critical Variables (Must Be Updated)

| Variable | Current Value | What To Do | Example |
|----------|---------------|-----------|---------|
| `DATABASE_URL` | `postgresql://shopify_user:your_secure_password@localhost:5432/shopify_seo_prod` | Change password to match your PostgreSQL setup | `postgresql://shopify_user:MySecurePass123@localhost:5432/shopify_seo_prod` |
| `SHOPIFY_APP_URL` | `https://localhost:8000` | Update with your Lightsail IP or domain | `https://192.168.1.100:8000` OR `https://myapp.example.com` |

### Important Variables (Pre-Configured for Testing)

| Variable | Value | Purpose |
|----------|-------|---------|
| `SHOPIFY_API_KEY` | `00e0308488fd130c41f5de204a576b75` | Shopify Partner App API key |
| `SHOPIFY_API_SECRET` | `8773c3e3052ae05c2d13b4ea3833d362` | Shopify Partner App API secret |
| `SHOPIFY_SCOPES` | `read_products,write_products,read_themes,read_orders` | Permissions for your app |
| `SECRET_KEY` | Random 56-char string | Django/FastAPI secret key |
| `JWT_SECRET_KEY` | Random 56-char string | JWT token signing key |
| `REDIS_URL` | `redis://localhost:6379` | Celery task broker |

### Optional Variables (Skip for Now)

| Variable | Purpose | Status |
|----------|---------|--------|
| `OPENAI_API_KEY` | AI-powered recommendations | Optional - skip for basic testing |
| `GOOGLE_CLIENT_ID` | Google integration | Optional - skip for basic testing |
| `SMTP_HOST` | Email notifications | Optional - skip for basic testing |

---

## 📝 Before Running Services

### 1. Create PostgreSQL Database

```bash
# Connect to PostgreSQL as admin
sudo -u postgres psql

# Create database
CREATE DATABASE shopify_seo_prod;

# Create user
CREATE USER shopify_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE shopify_seo_prod TO shopify_user;

# Exit
\q
```

**Verify it worked:**
```bash
psql -U shopify_user -d shopify_seo_prod -c "SELECT 1;"
# Should return: 1
```

### 2. Start Redis Server

```bash
# Start Redis (Linux/Mac)
sudo systemctl start redis-server

# Or if using Docker
docker run -d -p 6379:6379 redis:7

# Verify it's running
redis-cli ping
# Should return: PONG
```

### 3. Update SHOPIFY_APP_URL (Important!)

The `SHOPIFY_APP_URL` in `.env` currently points to `https://localhost:8000` for local testing.

**For local testing on same machine:**
- Keep as: `https://localhost:8000`

**For testing on AWS Lightsail:**
- Get your Lightsail public IP from AWS console
- Update to: `https://<YOUR_LIGHTSAIL_IP>:8000`
- Example: `https://192.0.2.123:8000`

**For production with domain:**
- Update to: `https://your-domain.com`

Then update this same URL in your Shopify Partner Dashboard:
1. Go to Shopify Partner Dashboard
2. Select your app
3. Set redirect URL to exactly match `SHOPIFY_APP_URL` + `/api/v1/auth/shopify/callback`
4. Example: `https://192.0.2.123:8000/api/v1/auth/shopify/callback`

---

## 🚀 Quick Start Command

Once PostgreSQL and Redis are running, you're ready to start the backend:

```bash
cd backend

# Create virtual environment if not exists
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## ✅ Verification Checklist

- [ ] `.env` file exists at `backend/.env`
- [ ] `.env` contains all Shopify credentials
- [ ] `.env` is listed in `.gitignore`
- [ ] PostgreSQL database created with correct user
- [ ] Redis server is running (`redis-cli ping` returns PONG)
- [ ] `SHOPIFY_APP_URL` updated with your IP/domain
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Migrations run (`alembic upgrade head`)
- [ ] FastAPI starts without errors (`uvicorn app.main:app --reload`)

---

## 🔐 Security Notes

⚠️ **IMPORTANT**:
1. Never commit `.env` to git - it's in `.gitignore`
2. Never share the Shopify API Secret in messages or emails
3. In production, use AWS Secrets Manager or similar service
4. Rotate API keys every 90 days
5. The `SECRET_KEY` and `JWT_SECRET_KEY` should be changed before production deployment

---

## Next Step

Once environment variables are set up, proceed to **Step 3: Prepare Local Environment for Testing** in the [DEPLOYMENT_AND_TESTING_ACTION_PLAN.md](./DEPLOYMENT_AND_TESTING_ACTION_PLAN.md).

---

## Troubleshooting

**Problem**: `psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed`
- **Solution**: PostgreSQL is not running. Start it: `sudo systemctl start postgresql`

**Problem**: `ConnectionRefusedError: [Errno 111] Connection refused` when starting backend
- **Solution**: Redis is not running. Start it: `sudo systemctl start redis-server`

**Problem**: `FATAL: Ident authentication failed for user "shopify_user"`
- **Solution**: Check PostgreSQL user and password match `.env`. Recreate user if needed.

**Problem**: `ModuleNotFoundError: No module named 'app'`
- **Solution**: Make sure you're in the `backend` directory and virtual environment is activated

---

**Status**: ✅ Environment variables configured and ready for service startup
