# Step 5: Test Shopify OAuth Flow

## 📍 You Are Here
- ✅ Step 1: Project Context Loaded
- ✅ Step 2: Environment Variables Updated
- ✅ Step 3: Local Environment Prepared
- ✅ Step 4: Backend Services Started
- ⏳ **Step 5: Test OAuth Flow** ← You are here
- 📋 Step 6: Test Product Synchronization
- 📋 Step 7: Test Frontend

---

## 🎯 Goal of This Step

Test the Shopify OAuth flow by:
1. Creating an OAuth installation request
2. Handling the Shopify redirect callback
3. Verifying the store is saved in the database with encrypted token

**Estimated Time**: 15-20 minutes

---

## 📋 Prerequisites

Before starting, ensure:
- ✅ FastAPI backend is running (`uvicorn app.main:app --reload`)
- ✅ Redis is running (`redis-cli ping` returns PONG)
- ✅ PostgreSQL is running and migrations completed
- ✅ Shopify Partner App is configured with correct redirect URL
- ✅ `.env` has Shopify API credentials
- ✅ A test Shopify store is available

---

## 🔗 Step 1: Update Shopify Partner App Configuration

Your Shopify Partner App needs to know where to redirect users after they approve access.

### 1.1 Get Your Lightsail IP or Local URL

If testing locally:
```bash
echo "Local URL: http://localhost:8000"
```

If testing on AWS Lightsail:
```bash
# Get your Lightsail public IP from AWS console
# Or use the domain you configured
echo "Lightsail URL: https://your-lightsail-ip-or-domain.com"
```

### 1.2 Configure Redirect URL in Shopify Partner Dashboard

1. Go to: https://partners.shopify.com/dashboard
2. Select your app
3. Find "App setup" → "URL configuration"
4. Update **Admin API redirect URLs** to:
   ```
   https://your-url/api/v1/auth/shopify/callback
   ```
   - For local: `http://localhost:8000/api/v1/auth/shopify/callback`
   - For Lightsail: `https://your-lightsail-ip:8000/api/v1/auth/shopify/callback`

5. Also set **App URL** to:
   ```
   https://your-url
   ```
   - For local: `http://localhost:8000`
   - For Lightsail: `https://your-lightsail-ip:8000`

6. Save changes

### 1.3 Update `.env` File

Make sure your `.env` matches the URLs you set:

```bash
# Edit .env
nano backend/.env

# Find and update:
SHOPIFY_APP_URL=http://localhost:8000  # For local
# OR
SHOPIFY_APP_URL=https://your-lightsail-ip:8000  # For Lightsail
```

Then restart FastAPI for changes to take effect.

---

## 🚀 Step 2: Test OAuth Flow via API

### 2.1 Initiate OAuth Installation

This endpoint generates the Shopify authorization URL.

**Using cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/shopify/install \
  -H "Content-Type: application/json" \
  -d '{
    "shop": "your-test-store.myshopify.com"
  }'
```

**Replace `your-test-store` with your actual test store name.**

**Expected Response:**
```json
{
  "install_url": "https://your-test-store.myshopify.com/admin/oauth/authorize?client_id=00e0308488fd130c41f5de204a576b75&scope=read_products%2Cwrite_products%2Cread_themes%2Cread_orders&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1%2Fauth%2Fshopify%2Fcallback&state=random_state_token_here",
  "state": "random_state_token_here"
}
```

**Save the `state` value** - you'll need it for the callback.

### 2.2 Complete OAuth in Browser

1. **Copy the `install_url`** from the response
2. **Open it in your browser**
3. **Log in with your Shopify test store credentials** (if not already logged in)
4. **Click "Install" to authorize the app**

You'll see a screen like:
```
[Shopify Logo]

Your Store wants to access your store to:
✓ Read your products
✓ Write your products
✓ Read your themes
✓ Read your orders

[Install App] [Cancel]
```

Click **[Install App]**

### 2.3 Handle OAuth Callback

After clicking Install, Shopify will redirect to:
```
http://localhost:8000/api/v1/auth/shopify/callback?code=XXXXX&hmac=XXXXX&shop=your-test-store.myshopify.com&timestamp=1234567890&state=XXXXX
```

The backend automatically handles this redirect and:
1. Exchanges the authorization code for an access token
2. Encrypts the access token with Fernet
3. Saves the store in the database
4. Redirects to frontend (or returns success message)

**If successful**, you'll see:
```json
{
  "status": "success",
  "message": "Store connected successfully",
  "store_id": "uuid-here",
  "store_name": "Your Test Store"
}
```

---

## ✅ Step 3: Verify Store in Database

After OAuth completes, verify the store was saved.

### 3.1 Check Database

```bash
# Connect to database
psql -U shopify_user -d shopify_seo_prod

# View all stores
SELECT id, shopify_domain, store_name, owner_email, created_at FROM stores;
```

**Expected Output:**
```
                   id                   |       shopify_domain       |  store_name   |      owner_email      |         created_at
----------------------------------------+----------------------------+---------------+-----------------------+-----------------------------
 550e8400-e29b-41d4-a716-446655440000 | your-test-store.myshopify.com | Your Test Store | admin@your-test-store.com | 2024-10-26 14:45:23.123456+00
(1 row)
```

**Key things to verify:**
- ✅ Store has a UUID `id`
- ✅ `shopify_domain` is correct
- ✅ `store_name` is populated
- ✅ `created_at` shows current timestamp

### 3.2 Verify Token is Encrypted

```bash
# Still in psql
SELECT id, shopify_access_token, created_at FROM stores;
```

**Expected Output:**
```
                   id                   |                    shopify_access_token
----------------------------------------+-----------------------------------------------------
 550e8400-e29b-41d4-a716-446655440000 | gAAAAABl3...encrypted_token_looks_like_gibberish...
(1 row)
```

**Key things to verify:**
- ✅ `shopify_access_token` is NOT plain text (looks like `gAAAAABl3...`)
- ✅ Token starts with `gAAAAABl` (Fernet format)
- ✅ Token is much longer than readable text

### 3.3 Exit psql

```bash
\q
```

---

## 🔍 Step 4: Test Token Decryption (Advanced)

Verify the encryption/decryption is working correctly.

### 4.1 Create Test Script

```bash
cd backend

# Create a test script
cat > test_encryption.py << 'EOF'
import asyncio
from app.core.database import SessionLocal
from app.models.store import Store

async def test_store_connection():
    db = SessionLocal()
    try:
        # Get the store we just created
        store = db.query(Store).first()

        if not store:
            print("❌ No stores found in database")
            return

        print(f"✅ Found store: {store.store_name}")
        print(f"   Domain: {store.shopify_domain}")
        print(f"   ID: {store.id}")

        # Test decryption
        print("\n🔐 Testing token decryption...")
        encrypted_token = store.shopify_access_token
        print(f"   Encrypted token (first 50 chars): {encrypted_token[:50]}...")

        decrypted_token = store.get_decrypted_token()
        if decrypted_token:
            print(f"   ✅ Token decrypted successfully!")
            print(f"   Decrypted token (first 30 chars): {decrypted_token[:30]}...")

            # Verify it looks like a Shopify token
            if decrypted_token.startswith('shpat_'):
                print(f"   ✅ Token is valid Shopify format (starts with 'shpat_')")
            else:
                print(f"   ⚠️ Token format may be incorrect (expected 'shpat_' prefix)")
        else:
            print(f"   ❌ Token decryption failed")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

asyncio.run(test_store_connection())
EOF

# Run the test
python test_encryption.py
```

**Expected Output:**
```
✅ Found store: Your Test Store
   Domain: your-test-store.myshopify.com
   ID: 550e8400-e29b-41d4-a716-446655440000

🔐 Testing token decryption...
   Encrypted token (first 50 chars): gAAAAABl3xZ...
   ✅ Token decrypted successfully!
   Decrypted token (first 30 chars): shpat_1234567890abcdefghijklmn...
   ✅ Token is valid Shopify format (starts with 'shpat_')
```

---

## 📊 Test Results

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| OAuth URL generated | URL with state | ✓ | |
| User can approve app | App install page | ✓ | |
| Callback succeeds | 200 response | ✓ | |
| Store in database | 1 row | ✓ | |
| Token encrypted | `gAAAAABl...` format | ✓ | |
| Token decrypts | `shpat_...` format | ✓ | |

---

## 🐛 Troubleshooting

### Issue 1: "Invalid OAuth callback"

```
Error: invalid_request
Description: The redirect_uri parameter does not match the whitelist
```

**Solution**: Redirect URL in Shopify Partner App doesn't match `.env`
1. Get your actual URL (local or Lightsail IP)
2. Go to Shopify Partner Dashboard
3. Update redirect URL to exactly match
4. Example: `http://localhost:8000/api/v1/auth/shopify/callback`

### Issue 2: "Store not created" or 404 error

```
Error: 404 Not Found
```

**Solution**: FastAPI backend not running
```bash
# In Terminal 2
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Issue 3: "Token decryption failed"

```
❌ Token decryption failed
```

**Solution**: Database or encryption key issue
```bash
# Check database migrations ran
cd backend
alembic upgrade head

# Restart FastAPI
# Ctrl+C to stop, then:
uvicorn app.main:app --reload
```

### Issue 4: "Permission denied" or store creation fails

```
Error: "You don't have permission to install this app"
```

**Solution**: Shopify Partner App scopes are wrong
1. Go to Shopify Partner Dashboard
2. Check "Admin API scopes"
3. Ensure these are selected:
   - `read_products`
   - `write_products`
   - `read_themes`
   - `read_orders`
4. Save changes
5. Try OAuth again

### Issue 5: HMAC validation failed

```
Error: Invalid HMAC signature
```

**Solution**: `SHOPIFY_API_SECRET` in `.env` is wrong
1. Go to Shopify Partner Dashboard
2. Copy the exact API Secret
3. Update `.env`:
   ```
   SHOPIFY_API_SECRET=exact-secret-from-dashboard
   ```
4. Restart FastAPI
5. Try OAuth again

---

## ✅ Success Criteria

You've successfully completed this step when:

- [ ] OAuth initiation endpoint returns valid URL with state
- [ ] Can open URL in browser
- [ ] Shopify shows app permissions screen
- [ ] Can click "Install App"
- [ ] Redirected back to localhost without error
- [ ] Store appears in database (`psql` query shows 1 row)
- [ ] `shopify_access_token` is encrypted (`gAAAAABl...` format)
- [ ] Token can be decrypted (test script succeeds)
- [ ] Decrypted token is valid format (`shpat_...`)

---

## ⏭️ Next Step

Once OAuth flow works end-to-end, proceed to **Step 6: Test Product Synchronization** where we'll:
1. Trigger manual product sync
2. Verify products appear in database
3. Monitor Celery worker task execution

See: [STEP6_TEST_PRODUCT_SYNC.md](./STEP6_TEST_PRODUCT_SYNC.md)

---

## 🎯 Quick Reference

### Test OAuth Flow (One-Line Summary)
```bash
# 1. Start backend (Terminal 2)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. Initiate OAuth
curl -X POST http://localhost:8000/api/v1/auth/shopify/install \
  -H "Content-Type: application/json" \
  -d '{"shop": "your-store.myshopify.com"}'

# 3. Open returned URL in browser and complete OAuth
# 4. Verify store in database
psql -U shopify_user -d shopify_seo_prod -c "SELECT shopify_domain FROM stores;"
```

---

**Status**: Ready to test OAuth
**Difficulty**: Medium
**Estimated Time**: 15-20 minutes
