# AWS Lightsail Deployment - Exact Configuration Answers

## 1. Backend Routes (Exact Paths)

Based on the current codebase analysis:

### Exact API Endpoints:
- **Install URL endpoint**: `/api/v1/auth/shopify/install` (POST)
- **OAuth callback endpoint**: `/api/v1/auth/shopify/callback` (GET)
- **Webhook endpoint**: `/api/v1/auth/shopify/webhook` (POST)
- **Health check**: `/api/v1/auth/health` (GET)
- **Logout**: `/api/v1/auth/logout` (POST)
- **Verify shop**: `/api/v1/auth/shopify/verify/{shop}` (GET)

### Route Structure:
- **Main app**: Routes are under `/api/v1/` prefix
- **Auth router**: Mounted at `/api/v1/auth/`
- **Keep this structure in production** - it's properly organized and follows REST conventions

### Shopify App Settings URLs:
```
App URL: https://yourdomain.com
Allowed redirection URL: https://yourdomain.com/api/v1/auth/shopify/callback
Webhook URL: https://yourdomain.com/api/v1/auth/shopify/webhook
```

## 2. Frontend Presence

**YES, we have a React frontend** that needs to be deployed alongside the backend.

### Frontend Details:
- **Framework**: React 18 with TypeScript
- **Build command**: `npm run build`
- **Output folder**: `build/` (standard Create React App)
- **Proxy**: Configured to proxy API calls to backend on port 8000

### Nginx Configuration Needed:
```nginx
# Serve React frontend
location / {
    root /opt/shopify-seo-analyzer/frontend/build;
    try_files $uri $uri/ /index.html;
}

# Proxy API calls to backend
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## 3. Environment Variables (Exact Keys)

### Required Production .env Variables:

```bash
# Application Settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key-here-make-it-long-and-random
ALLOWED_HOSTS=["https://yourdomain.com"]

# Database Configuration
DATABASE_URL=postgresql://shopify_user:your_secure_password@localhost:5432/shopify_seo_prod

# Redis Configuration
REDIS_URL=redis://localhost:6379

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-different-from-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Shopify Configuration (EXACT keys expected by code)
SHOPIFY_API_KEY=your_actual_client_id_here
SHOPIFY_API_SECRET=your_actual_client_secret_here
SHOPIFY_SCOPES=read_products,read_orders,read_customers,read_content,read_themes
SHOPIFY_APP_URL=https://yourdomain.com

# Optional but recommended
OPENAI_API_KEY=your_openai_key_if_you_have_one
LOG_LEVEL=INFO
API_RATE_LIMIT=100
WORKERS=4
RELOAD=false
```

### Key Notes:
- **SHOPIFY_APP_URL**: This is the single URL variable used by the OAuth service
- **No separate callback path variable** - it's constructed as `{SHOPIFY_APP_URL}/api/v1/auth/shopify/callback`
- **ALLOWED_HOSTS**: Must be a JSON array format for CORS

## 4. Database & Redis

### Recommendation: **Local on Lightsail Instance**

**PostgreSQL Configuration:**
```bash
# Database details for .env
DATABASE_URL=postgresql://shopify_user:your_secure_password@localhost:5432/shopify_seo_prod

# Setup commands:
sudo -u postgres createdb shopify_seo_prod
sudo -u postgres createuser shopify_user
sudo -u postgres psql -c "ALTER USER shopify_user PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE shopify_seo_prod TO shopify_user;"
```

**Redis Configuration:**
```bash
# Redis details for .env
REDIS_URL=redis://localhost:6379

# Redis will run on default port 6379
```

### Why Local vs External:
- **Local**: Simpler setup, lower latency, cost-effective for small-medium apps
- **External (RDS/ElastiCache)**: Better for high-traffic, multi-instance deployments
- **Recommendation**: Start local, migrate to external if needed

## 5. Uvicorn Settings

### Production Configuration:

```bash
# In systemd service file:
ExecStart=/opt/shopify-seo-analyzer/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Environment variables:
WORKERS=4
RELOAD=false
```

### Worker Recommendations:
- **Start with 4 workers** (good for most Lightsail instances)
- **Use standard Uvicorn workers** (not async workers - FastAPI handles async internally)
- **Scale based on CPU cores**: Generally `(2 x CPU cores) + 1`

### Lightsail Instance Sizing:
- **$10/month (2GB RAM, 1 vCPU)**: 2-3 workers
- **$20/month (4GB RAM, 2 vCPU)**: 4-5 workers
- **$40/month (8GB RAM, 2 vCPU)**: 4-6 workers

## 6. Webhook Registration

### Current Implementation: **Manual Setup Required**

The current code **does NOT auto-register webhooks** after OAuth. You need to:

1. **Set webhook URL in Shopify Partner Dashboard**:
   ```
   Webhook URL: https://yourdomain.com/api/v1/auth/shopify/webhook
   ```

2. **Configure webhook topics**:
   - `app/uninstalled` - When store uninstalls your app

### Webhook Topics to Configure:
```
app/uninstalled -> https://yourdomain.com/api/v1/auth/shopify/webhook
```

### Future Enhancement:
You could add auto-registration in a future task by calling Shopify's Webhook API after successful OAuth.

## 7. SSL & Domain

### Domain Setup Options:

**Option A: Custom Domain (Recommended)**
```
Domain: seo-analyzer.yourdomain.com
SSL: Let's Encrypt (free)
Shopify App URL: https://seo-analyzer.yourdomain.com
```

**Option B: Lightsail Static IP**
```
IP: 123.456.789.123 (your static IP)
SSL: Self-signed or Let's Encrypt with IP
Shopify App URL: https://123.456.789.123
```

### SSL Setup Commands:
```bash
# For custom domain:
sudo certbot --nginx -d seo-analyzer.yourdomain.com

# Update Shopify app settings with:
App URL: https://seo-analyzer.yourdomain.com
Callback URL: https://seo-analyzer.yourdomain.com/api/v1/auth/shopify/callback
```

## 8. Complete Deployment Checklist

### Pre-deployment:
- [ ] Domain/subdomain pointed to Lightsail static IP
- [ ] SSL certificate obtained
- [ ] Environment variables configured
- [ ] Database created and user configured

### Deployment Steps:
1. **Upload code** to `/opt/shopify-seo-analyzer/`
2. **Install Python dependencies** in virtual environment
3. **Build React frontend** with `npm run build`
4. **Run database migrations** with `alembic upgrade head`
5. **Configure Nginx** with provided config
6. **Create systemd service** for FastAPI app
7. **Update Shopify app settings** with production URLs
8. **Test OAuth flow** end-to-end

### Testing Commands:
```bash
# Test API health
curl https://yourdomain.com/api/v1/auth/health

# Test OAuth install URL generation
curl -X POST https://yourdomain.com/api/v1/auth/shopify/install \
  -H "Content-Type: application/json" \
  -d '{"shop": "your-test-store.myshopify.com"}'

# Test frontend
curl https://yourdomain.com/
```

## 9. Production Systemd Service File

```ini
[Unit]
Description=Shopify SEO Analyzer FastAPI App
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/shopify-seo-analyzer/backend
Environment=PATH=/opt/shopify-seo-analyzer/backend/venv/bin
EnvironmentFile=/opt/shopify-seo-analyzer/.env.production
ExecStart=/opt/shopify-seo-analyzer/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

This configuration matches exactly what your current codebase expects and provides a production-ready deployment setup.