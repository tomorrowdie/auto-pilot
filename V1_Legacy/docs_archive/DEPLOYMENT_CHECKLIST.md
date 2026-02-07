# Shopify SEO Analyzer - Deployment & Next Steps Checklist

## 🎯 Your Current Status

✅ **Completed**:
- Code is written and tested locally
- AWS Lightsail instance is set up
- Shopify Partner account is ready
- All backend/frontend components finished

❓ **What's Left**:
- Configure production environment
- Deploy to AWS
- Test with real Shopify store
- Go live!

---

## 📋 Step-by-Step Deployment Guide

### Phase 1: Prepare AWS Environment (30 minutes)

#### Step 1.1: Connect to Your Lightsail Instance
```bash
# Use the key pair you created in AWS Lightsail
ssh -i your-lightsail-key.pem ubuntu@your-lightsail-ip-address

# Example:
ssh -i ~/Downloads/shopify-seo-key.pem ubuntu@192.0.2.123
```

**What to do:**
1. Download your private key from AWS Lightsail console
2. Save it securely (don't commit to git!)
3. Set proper permissions: `chmod 600 your-key.pem`
4. Connect via SSH (command above)

#### Step 1.2: Update System & Install Dependencies
```bash
# Login to instance, then run:
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
  curl \
  wget \
  git \
  nano \
  htop

# Install Docker and Docker Compose
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Verify Docker
docker --version
docker-compose --version

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Redis
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Install Python
sudo apt install -y python3 python3-pip python3-venv

# Install Nginx (for reverse proxy)
sudo apt install -y nginx
```

#### Step 1.3: Set Up PostgreSQL Database
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE shopify_seo_prod;
CREATE USER shopify_user WITH PASSWORD 'your-secure-password-here';
ALTER ROLE shopify_user SET client_encoding TO 'utf8';
ALTER ROLE shopify_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE shopify_user SET default_transaction_deferrable TO on;
ALTER ROLE shopify_user SET default_transaction_read_committed TO on;
ALTER USER shopify_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE shopify_seo_prod TO shopify_user;
\q
EOF

# Verify connection
psql -U shopify_user -d shopify_seo_prod -h localhost
```

**Note the credentials**:
- Username: `shopify_user`
- Password: (what you set above)
- Database: `shopify_seo_prod`
- Host: `localhost`
- Port: `5432`

#### Step 1.4: Clone Your Repository
```bash
# Create app directory
mkdir -p /opt/shopify-seo-analyzer
cd /opt/shopify-seo-analyzer

# Clone your GitHub repository
git clone https://github.com/your-username/shopify-seo-analyzer.git .

# If not using GitHub, transfer files via SCP
# From your local machine:
scp -i your-key.pem -r ./shopify-seo-analyzer/* ubuntu@your-ip:/opt/shopify-seo-analyzer/
```

---

### Phase 2: Configure Production Environment (20 minutes)

#### Step 2.1: Create Production .env File
```bash
cd /opt/shopify-seo-analyzer

# Create .env.production file
nano .env.production
```

**Paste this configuration** (update with YOUR values):
```bash
# Application Settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-random-secret-key-make-this-at-least-32-characters
ALLOWED_HOSTS=["https://yourdomain.com","https://www.yourdomain.com"]

# Database Configuration
DATABASE_URL=postgresql://shopify_user:your-secure-password@localhost:5432/shopify_seo_prod

# Redis Configuration
REDIS_URL=redis://localhost:6379

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-different-from-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Shopify Configuration (From your Partner Account)
SHOPIFY_API_KEY=your-shopify-api-key-here
SHOPIFY_API_SECRET=your-shopify-api-secret-here
SHOPIFY_SCOPES=read_products,read_orders,read_customers,read_content,read_themes
SHOPIFY_APP_URL=https://yourdomain.com

# Optional: OpenAI (for AI recommendations)
OPENAI_API_KEY=your-openai-key-if-using

# Optional: AWS S3
STORAGE_TYPE=local
AWS_ACCESS_KEY_ID=optional
AWS_SECRET_ACCESS_KEY=optional
AWS_BUCKET_NAME=optional
AWS_REGION=us-east-1
```

**To generate secure random keys**:
```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Step 2.2: Get Your Shopify Credentials
**From your Shopify Partner Account:**
1. Go to https://partners.shopify.com
2. Navigate to "Apps" → Your app
3. Go to "Configuration"
4. Copy:
   - Client ID (SHOPIFY_API_KEY)
   - Client Secret (SHOPIFY_API_SECRET)
5. Set Redirect URI to: `https://yourdomain.com/api/v1/auth/shopify/callback`

#### Step 2.3: Set Up Domain & SSL Certificate

**Option A: Use Lightsail Static IP** (Quick, less professional)
```bash
# Create static IP in Lightsail console
# Your app URL: https://123.45.67.89
```

**Option B: Use Custom Domain** (Recommended)
```bash
# 1. Point domain to Lightsail static IP
#    In your domain registrar DNS settings:
#    A record → your-lightsail-static-ip

# 2. Install Certbot for SSL
sudo apt install -y certbot python3-certbot-nginx

# 3. Get free SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 4. Verify certificate was created
ls -la /etc/letsencrypt/live/yourdomain.com/
```

---

### Phase 3: Build & Deploy Application (30 minutes)

#### Step 3.1: Set Up Backend

```bash
cd /opt/shopify-seo-analyzer/backend

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
export DATABASE_URL="postgresql://shopify_user:your-password@localhost:5432/shopify_seo_prod"
alembic upgrade head

# Test backend starts
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Press Ctrl+C to stop
```

#### Step 3.2: Set Up Frontend

```bash
cd /opt/shopify-seo-analyzer/frontend

# Install dependencies
npm install

# Create .env file for production
nano .env.production
```

**Add this**:
```
REACT_APP_API_URL=https://yourdomain.com/api/v1
```

**Build for production**:
```bash
npm run build

# This creates a 'build' folder with optimized files
```

#### Step 3.3: Configure Nginx as Reverse Proxy

```bash
# Backup original nginx config
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# Create new config
sudo nano /etc/nginx/sites-available/default
```

**Paste this Nginx configuration** (replace yourdomain.com):
```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Certificate
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Frontend (React build)
    root /opt/shopify-seo-analyzer/frontend/build;
    index index.html;

    # API requests to backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend routes (React Router)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
}
```

**Test and apply**:
```bash
# Test nginx config
sudo nginx -t

# If OK, restart nginx
sudo systemctl restart nginx
```

#### Step 3.4: Set Up Systemd Services (Auto-start on reboot)

**Create Backend Service**:
```bash
sudo nano /etc/systemd/system/shopify-seo-backend.service
```

**Paste this**:
```ini
[Unit]
Description=Shopify SEO Analyzer Backend
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/opt/shopify-seo-analyzer/backend
Environment="PATH=/opt/shopify-seo-analyzer/backend/venv/bin"
Environment="DATABASE_URL=postgresql://shopify_user:your-password@localhost:5432/shopify_seo_prod"
Environment="REDIS_URL=redis://localhost:6379"
EnvironmentFile=/opt/shopify-seo-analyzer/.env.production
ExecStart=/opt/shopify-seo-analyzer/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Create Celery Worker Service**:
```bash
sudo nano /etc/systemd/system/shopify-seo-celery.service
```

**Paste this**:
```ini
[Unit]
Description=Shopify SEO Analyzer Celery Worker
After=network.target redis-server.service

[Service]
Type=forking
User=ubuntu
WorkingDirectory=/opt/shopify-seo-analyzer/backend
Environment="PATH=/opt/shopify-seo-analyzer/backend/venv/bin"
EnvironmentFile=/opt/shopify-seo-analyzer/.env.production
ExecStart=/opt/shopify-seo-analyzer/backend/venv/bin/celery -A app.tasks.celery_app worker -l info
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Create Celery Beat Service** (scheduler):
```bash
sudo nano /etc/systemd/system/shopify-seo-beat.service
```

**Paste this**:
```ini
[Unit]
Description=Shopify SEO Analyzer Celery Beat
After=network.target redis-server.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/shopify-seo-analyzer/backend
Environment="PATH=/opt/shopify-seo-analyzer/backend/venv/bin"
EnvironmentFile=/opt/shopify-seo-analyzer/.env.production
ExecStart=/opt/shopify-seo-analyzer/backend/venv/bin/celery -A app.tasks.celery_app beat -l info
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start services**:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (auto-start on reboot)
sudo systemctl enable shopify-seo-backend.service
sudo systemctl enable shopify-seo-celery.service
sudo systemctl enable shopify-seo-beat.service

# Start services
sudo systemctl start shopify-seo-backend.service
sudo systemctl start shopify-seo-celery.service
sudo systemctl start shopify-seo-beat.service

# Check status
sudo systemctl status shopify-seo-backend.service
sudo systemctl status shopify-seo-celery.service
sudo systemctl status shopify-seo-beat.service
```

---

### Phase 4: Verification & Testing (20 minutes)

#### Step 4.1: Verify Backend API
```bash
# Test API health check
curl https://yourdomain.com/health

# Expected response: {"status": "ok"}
```

#### Step 4.2: Verify Frontend
```bash
# Open in browser
https://yourdomain.com

# You should see the Shopify SEO Analyzer dashboard
```

#### Step 4.3: Test Shopify OAuth Flow
```bash
1. Go to https://yourdomain.com
2. Click "Connect Store"
3. Enter your Shopify test store domain
4. Complete OAuth flow
5. Verify store is created in database
```

**Check database:**
```bash
psql -U shopify_user -d shopify_seo_prod << EOF
SELECT * FROM stores;
EOF
```

#### Step 4.4: Monitor Logs
```bash
# Backend logs
sudo journalctl -u shopify-seo-backend.service -f

# Celery worker logs
sudo journalctl -u shopify-seo-celery.service -f

# Celery beat logs
sudo journalctl -u shopify-seo-beat.service -f
```

---

## 🔍 Your Shopify Partner Setup

### Get Shopify API Credentials

**From Shopify Partner Dashboard:**
1. Go to https://partners.shopify.com
2. Click "Apps" → Select your app
3. Click "Configuration"
4. Under "App Credentials":
   - **Client ID** = SHOPIFY_API_KEY
   - **Client Secret** = SHOPIFY_API_SECRET
5. Set **Redirect URIs** to:
   ```
   https://yourdomain.com/api/v1/auth/shopify/callback
   ```
6. Save

### Set Required Scopes
The app needs these scopes (already configured):
- `read_products` - Read product data
- `read_orders` - Read order data
- `read_customers` - Read customer data
- `read_content` - Read pages/content
- `read_themes` - Read theme data

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] AWS Lightsail instance created
- [ ] Shopify Partner account setup
- [ ] Shopify app credentials obtained
- [ ] Domain name purchased (or using static IP)
- [ ] SSH key pair downloaded and saved

### Installation
- [ ] Connected to Lightsail instance via SSH
- [ ] System dependencies installed (Docker, Python, PostgreSQL, Redis, Nginx)
- [ ] Repository cloned to `/opt/shopify-seo-analyzer`
- [ ] PostgreSQL database created
- [ ] Production .env file configured with all credentials

### Configuration
- [ ] Domain DNS configured (if using custom domain)
- [ ] SSL certificate installed via Let's Encrypt
- [ ] Nginx reverse proxy configured
- [ ] Shopify OAuth redirect URI set correctly
- [ ] All environment variables set in .env.production

### Deployment
- [ ] Backend installed and dependencies resolved
- [ ] Database migrations run successfully
- [ ] Frontend built for production
- [ ] Systemd services created and enabled
- [ ] All services started and running

### Testing
- [ ] Backend API responds to /health request
- [ ] Frontend loads at https://yourdomain.com
- [ ] Shopify OAuth flow completes successfully
- [ ] Test store is created in database
- [ ] Celery tasks running (check via logs)
- [ ] Can view dashboard and connect store

### Post-Deployment
- [ ] Set up monitoring/alerts
- [ ] Configure backups
- [ ] Document credentials securely
- [ ] Test auto-restart on instance reboot
- [ ] Plan maintenance schedule

---

## 🚨 Troubleshooting

### Backend Won't Start
```bash
# Check logs
sudo journalctl -u shopify-seo-backend.service

# Common issues:
# 1. Database connection error → Check DATABASE_URL
# 2. Port already in use → Kill process on port 8000
# 3. Missing environment variable → Check .env.production
```

### Frontend Not Loading
```bash
# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Rebuild frontend
cd /opt/shopify-seo-analyzer/frontend
npm run build

# Restart Nginx
sudo systemctl restart nginx
```

### OAuth Flow Fails
```bash
# Check backend logs
sudo journalctl -u shopify-seo-backend.service -f

# Verify redirect URI in Shopify Partner Dashboard matches exactly:
# https://yourdomain.com/api/v1/auth/shopify/callback
```

### Celery Tasks Not Running
```bash
# Check Redis is running
redis-cli ping

# Check Celery logs
sudo journalctl -u shopify-seo-celery.service -f

# Check Beat logs
sudo journalctl -u shopify-seo-beat.service -f
```

---

## 📊 Production Monitoring

### Check Service Status
```bash
# All services
sudo systemctl status shopify-seo-*

# Individual services
sudo systemctl status shopify-seo-backend.service
```

### Monitor Database
```bash
# Check database size
psql -U shopify_user -d shopify_seo_prod << EOF
SELECT pg_size_pretty(pg_database_size('shopify_seo_prod'));
EOF

# Count records
psql -U shopify_user -d shopify_seo_prod << EOF
SELECT
  (SELECT COUNT(*) FROM stores) as stores,
  (SELECT COUNT(*) FROM products) as products,
  (SELECT COUNT(*) FROM seo_analyses) as analyses;
EOF
```

### Monitor Disk Space
```bash
df -h

# Should have at least 10GB free
```

### Monitor Memory/CPU
```bash
# Real-time monitoring
htop

# Check process memory usage
ps aux | grep uvicorn
```

---

## 🎯 Your Next Steps (In Order)

### TODAY:
1. ✅ Read this entire guide
2. Connect to your Lightsail instance (Phase 1)
3. Install dependencies (Phase 1)
4. Set up PostgreSQL (Phase 1)
5. Clone your code (Phase 1)

### TOMORROW:
6. Configure .env.production (Phase 2)
7. Get Shopify API credentials (Phase 2)
8. Set up SSL certificate (Phase 2)
9. Build and deploy application (Phase 3)
10. Configure Nginx (Phase 3)

### NEXT DAY:
11. Create systemd services (Phase 3)
12. Verify everything works (Phase 4)
13. Test Shopify OAuth (Phase 4)
14. Monitor logs and verify (Phase 4)

### FINAL STEPS:
15. Invite test users
16. Test complete workflow
17. Fix any issues
18. Go live! 🎉

---

## 📞 Support Resources

- **AWS Lightsail Docs**: https://lightsail.aws.amazon.com/ls/docs/
- **Shopify API Docs**: https://shopify.dev/api/admin
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Let's Encrypt**: https://letsencrypt.org/
- **Nginx Docs**: https://nginx.org/en/docs/

---

## 💰 Estimated Costs (Monthly)

- **AWS Lightsail Instance**: $10-30/month (depending on size)
- **Domain Name**: $10-15/year
- **SSL Certificate**: FREE (Let's Encrypt)
- **Database Backups**: FREE (built into Lightsail) or $5-20 for RDS
- **Total Monthly**: $10-50/month

---

**Version**: 1.0
**Last Updated**: October 26, 2024
**Status**: Ready for deployment

Good luck with your deployment! 🚀
