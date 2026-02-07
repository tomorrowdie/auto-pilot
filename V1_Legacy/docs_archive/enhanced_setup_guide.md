# ENHANCED_SETUP.md

## 1. Project Purpose
This enhanced guide builds upon `shopify_aws_setup.md` to provide a **complete hands-on setup and testing guide** for the Shopify SEO Analyzer app. It includes real credential setup, database initialization, Celery configuration, frontend deployment, and testing workflows.

---

## 2. Shopify Credentials Setup

### Step 1. Access Your Shopify Partner Dashboard
1. Go to [Shopify Partner Dashboard](https://partners.shopify.com/)
2. Select your app: **seo-analyzer**
3. Click **Configuration → API Access**
4. Copy these values:
   - **API key (Client ID)**
   - **API secret key (Client Secret)**
   - **App URL**
   - **Allowed redirection URL**

### Step 2. Update Your `.env`
In your backend folder, create a `.env` file (if missing) and insert:

```bash
SHOPIFY_API_KEY=<YOUR_SHOPIFY_API_KEY>
SHOPIFY_API_SECRET=<YOUR_SHOPIFY_API_SECRET>
SHOPIFY_API_SCOPES=read_products,write_products,read_themes,read_orders
SHOPIFY_REDIRECT_URL=https://<YOUR_DOMAIN_OR_IP>/api/v1/auth/shopify/callback
```

Ensure `.env` is listed in `.gitignore` to prevent accidental commits.

---

## 3. Database Setup (PostgreSQL)

### Step 1. Create Database and User
```bash
sudo -u postgres psql
CREATE DATABASE shopify_seo_prod;
CREATE USER shopify_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE shopify_seo_prod TO shopify_user;
```

### Step 2. Apply Migrations
```bash
cd /opt/shopify-seo-analyzer/backend
source venv/bin/activate
export $(cat ../.env | xargs)
alembic upgrade head
```

This ensures all database tables are created correctly.

---

## 4. Celery and Background Task Setup

### Step 1. Install Redis (if not already installed)
```bash
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### Step 2. Configure Celery Worker and Beat Scheduler
In your `.env`, ensure these are present:
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

Start both services:
```bash
# Start Celery worker
celery -A app.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.celery_app beat --loglevel=info
```

---

## 5. Frontend (React) Deployment

### Step 1. Build Frontend
```bash
cd /opt/shopify-seo-analyzer/frontend
npm install
npm run build
```

### Step 2. Configure Nginx to Serve Frontend
Edit Nginx site config:
```bash
sudo nano /etc/nginx/sites-available/shopify-seo-analyzer
```
Add:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        root /opt/shopify-seo-analyzer/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable and reload:
```bash
sudo ln -s /etc/nginx/sites-available/shopify-seo-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. Testing Procedures

### Step 1. Run Backend Locally
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2. Test OAuth Installation
```bash
curl -X POST https://<your-domain>/api/v1/auth/shopify/install \
  -H "Content-Type: application/json" \
  -d '{"shop": "your-test-store.myshopify.com"}'
```

Expect Shopify to redirect to your callback URL.

### Step 3. Verify Database Connection
```bash
sudo -u postgres psql -d shopify_seo_prod
\dt  # Should show created tables
```

### Step 4. Verify Webhook Functionality
```bash
curl -X POST https://<your-domain>/api/v1/auth/shopify/webhook \
  -H "Content-Type: application/json" \
  -d '{"topic": "app/uninstalled", "shop": "your-test-store.myshopify.com"}'
```
Expected response:
```json
{"success": true}
```

---

## 7. Troubleshooting
| Issue | Cause | Fix |
|--------|--------|-----|
| **OAuth fails (invalid_redirect_uri)** | Redirect URL not matching in Partner Dashboard | Update Shopify settings to match `.env` URL |
| **502 Bad Gateway** | FastAPI service not running | Check `sudo systemctl status shopify-seo-analyzer` |
| **CORS Errors** | Missing allowed hosts | Add IP/domain to `ALLOWED_HOSTS` in `.env` |
| **Redis connection refused** | Redis not started | Run `sudo systemctl start redis-server` |
| **Certbot renewal issues** | Expired SSL | Run `sudo certbot renew` |

---

## 8. Verification Checklist
- [x] Shopify Partner app keys added to `.env`
- [x] PostgreSQL database created & migrated
- [x] Redis running for Celery tasks
- [x] Frontend built and served via Nginx
- [x] FastAPI backend reachable on port 8000
- [x] OAuth tested successfully

---

**This guide now provides a full path to test and deploy Shopify SEO Analyzer locally and on AWS Lightsail.**

