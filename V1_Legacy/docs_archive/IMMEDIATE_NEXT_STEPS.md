# 🚀 Immediate Next Steps - Action Plan

## Where You Are Now
✅ Code built and working locally
✅ AWS Lightsail instance ready
✅ Shopify Partner account ready

## What You Need to Do Next (In Priority Order)

---

## 🎯 WEEK 1: SETUP & DEPLOYMENT

### Day 1: Preparation (2-3 hours)

#### Task 1.1: Gather Your Information
Collect all the information you'll need:

**From AWS:**
- [ ] Lightsail instance IP address
- [ ] SSH key file (.pem file)
- [ ] Lightsail region (e.g., us-east-1)

**From Domain Provider:**
- [ ] Your domain name (if using custom domain)
- [ ] Domain registrar login

**From Shopify Partner:**
- [ ] Shopify API Client ID
- [ ] Shopify API Client Secret
- [ ] Shopify app name

**Generate Secrets:**
```bash
# Generate secure SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate secure JWT_SECRET_KEY
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

#### Task 1.2: Create a Deployment Notes Document
Create a file `DEPLOYMENT_NOTES.txt` and save:
```
AWS Lightsail IP: __________________
SSH Key Location: __________________
Domain Name: __________________
Database Password: __________________
SECRET_KEY: __________________
JWT_SECRET_KEY: __________________
Shopify API Key: __________________
Shopify API Secret: __________________
```

#### Task 1.3: Download SSH Key from AWS
1. Go to AWS Lightsail Console
2. Click "Account" → "SSH keys"
3. Download your private key (.pem file)
4. Save to safe location
5. Run: `chmod 600 /path/to/your-key.pem`

---

### Day 2-3: Server Setup (4-6 hours)

#### Task 2.1: Connect to Lightsail via SSH
```bash
# Using the key you downloaded
ssh -i ~/Downloads/your-lightsail-key.pem ubuntu@your-lightsail-ip

# Example:
ssh -i ~/Downloads/shopify-seo.pem ubuntu@192.0.2.123

# You should see a prompt like:
# ubuntu@ip-192-0-2-123:~$
```

#### Task 2.2: Run Server Setup Script
Copy-paste this entire command block into your terminal (all at once):

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install all dependencies at once
sudo apt install -y \
  curl wget git nano htop \
  docker.io docker-compose \
  postgresql postgresql-contrib \
  redis-server \
  python3 python3-pip python3-venv \
  nginx

# Enable services to auto-start
sudo systemctl enable docker postgresql redis-server

# Start services
sudo systemctl start docker postgresql redis-server

# Add current user to docker group
sudo usermod -aG docker $USER

# Verify installations
docker --version
psql --version
redis-cli --version
```

#### Task 2.3: Create Database
```bash
# Set a strong password for your database
sudo -u postgres psql << EOF
CREATE DATABASE shopify_seo_prod;
CREATE USER shopify_user WITH PASSWORD 'YourVerySecurePassword123!';
ALTER ROLE shopify_user SET client_encoding TO 'utf8';
ALTER ROLE shopify_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE shopify_user SET default_transaction_deferrable TO on;
ALTER ROLE shopify_user SET default_transaction_read_committed TO on;
ALTER USER shopify_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE shopify_seo_prod TO shopify_user;
\q
EOF

# Test connection
psql -U shopify_user -d shopify_seo_prod -h localhost -c "SELECT version();"
```

**Save this password!** You'll need it for .env file.

#### Task 2.4: Clone Your Code
```bash
# Create app directory
mkdir -p /opt/shopify-seo-analyzer
cd /opt/shopify-seo-analyzer

# Option A: Clone from GitHub
git clone https://github.com/YOUR-USERNAME/shopify-seo-analyzer.git .

# Option B: Copy from local machine (from your local terminal, not SSH)
scp -i your-key.pem -r /path/to/local/shopify-seo-analyzer/* \
  ubuntu@your-lightsail-ip:/opt/shopify-seo-analyzer/
```

---

### Day 4: Configuration (2-3 hours)

#### Task 3.1: Create Production .env File

On your Lightsail instance, create the configuration file:

```bash
cd /opt/shopify-seo-analyzer
nano .env.production
```

**Copy-paste this** (replacing the placeholders with YOUR values):

```
# Application Settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=PASTE_YOUR_SECRET_KEY_HERE
ALLOWED_HOSTS=["https://yourdomain.com","https://www.yourdomain.com"]

# Database (use the password you created earlier)
DATABASE_URL=postgresql://shopify_user:YourVerySecurePassword123!@localhost:5432/shopify_seo_prod

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=PASTE_YOUR_JWT_SECRET_KEY_HERE
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Shopify (from your Partner account)
SHOPIFY_API_KEY=your-shopify-client-id-here
SHOPIFY_API_SECRET=your-shopify-client-secret-here
SHOPIFY_SCOPES=read_products,read_orders,read_customers,read_content,read_themes
SHOPIFY_APP_URL=https://yourdomain.com

# Storage (use local for now)
STORAGE_TYPE=local
```

**To save in nano:**
- Press `Ctrl + X`
- Press `Y` for yes
- Press `Enter` to confirm filename

#### Task 3.2: Set Up Domain & SSL

**OPTION A: If using custom domain** (Recommended)
```bash
# Point domain to your Lightsail IP in domain registrar
# (Ask your domain registrar support if needed)
# Wait 5-15 minutes for DNS to propagate

# Install SSL certificate (replace yourdomain.com)
sudo apt install -y certbot python3-certbot-nginx

# Get free SSL cert from Let's Encrypt
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# This creates certificates in: /etc/letsencrypt/live/yourdomain.com/
```

**OPTION B: If using static IP** (Quick method)
```bash
# Just use: https://your-lightsail-ip-address
# Create self-signed cert for testing
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/self-signed.key \
  -out /etc/ssl/certs/self-signed.crt
```

#### Task 3.3: Configure Nginx Reverse Proxy

```bash
# Backup original
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# Edit nginx config
sudo nano /etc/nginx/sites-available/default
```

**Delete everything and paste this** (replace yourdomain.com if using custom domain):

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend
    root /opt/shopify-seo-analyzer/frontend/build;
    index index.html;

    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # React routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
}
```

**Test and apply:**
```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

### Day 5-6: Application Deployment (4-5 hours)

#### Task 4.1: Deploy Backend

```bash
cd /opt/shopify-seo-analyzer/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
export DATABASE_URL="postgresql://shopify_user:YourVerySecurePassword123!@localhost:5432/shopify_seo_prod"
alembic upgrade head

# Test start (Ctrl+C to stop)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Task 4.2: Deploy Frontend

```bash
cd /opt/shopify-seo-analyzer/frontend

# Install dependencies
npm install

# Build for production
npm run build

# Verify build exists
ls -la build/
```

#### Task 4.3: Create Auto-Start Services

Create backend service:
```bash
sudo tee /etc/systemd/system/shopify-seo-backend.service > /dev/null << EOF
[Unit]
Description=Shopify SEO Analyzer Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/shopify-seo-analyzer/backend
Environment="PATH=/opt/shopify-seo-analyzer/backend/venv/bin"
EnvironmentFile=/opt/shopify-seo-analyzer/.env.production
ExecStart=/opt/shopify-seo-analyzer/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

Create Celery worker:
```bash
sudo tee /etc/systemd/system/shopify-seo-celery.service > /dev/null << EOF
[Unit]
Description=Shopify SEO Analyzer Celery Worker
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/shopify-seo-analyzer/backend
Environment="PATH=/opt/shopify-seo-analyzer/backend/venv/bin"
EnvironmentFile=/opt/shopify-seo-analyzer/.env.production
ExecStart=/opt/shopify-seo-analyzer/backend/venv/bin/celery -A app.tasks.celery_app worker -l info
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

Create Celery beat:
```bash
sudo tee /etc/systemd/system/shopify-seo-beat.service > /dev/null << EOF
[Unit]
Description=Shopify SEO Analyzer Celery Beat
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/shopify-seo-analyzer/backend
Environment="PATH=/opt/shopify-seo-analyzer/backend/venv/bin"
EnvironmentFile=/opt/shopify-seo-analyzer/.env.production
ExecStart=/opt/shopify-seo-analyzer/backend/venv/bin/celery -A app.tasks.celery_app beat -l info
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

**Enable and start all services:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
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

### Day 7: Testing & Verification (2-3 hours)

#### Task 5.1: Test Backend API
```bash
curl https://yourdomain.com/health

# Expected response: {"status":"ok"}
```

#### Task 5.2: Test Frontend
Open browser and go to:
```
https://yourdomain.com
```
You should see the dashboard.

#### Task 5.3: Test Shopify OAuth
1. Click "Connect Store"
2. Enter your Shopify test store domain
3. Complete OAuth flow
4. Verify it redirects back to your app

#### Task 5.4: Check Database
```bash
psql -U shopify_user -d shopify_seo_prod << EOF
SELECT * FROM stores;
EOF
```

You should see your test store.

#### Task 5.5: Test Background Jobs
```bash
# Check Celery is running
sudo journalctl -u shopify-seo-celery.service -f

# Should see "Worker online" messages
```

---

## ✅ Quick Checklist

### Before You Start
- [ ] Have Lightsail IP address
- [ ] Have SSH key downloaded
- [ ] Have Shopify API credentials
- [ ] Have domain name (or know you're using IP)

### Deployment
- [ ] Connected to Lightsail via SSH
- [ ] System dependencies installed
- [ ] Database created and tested
- [ ] Code cloned to `/opt/shopify-seo-analyzer`
- [ ] .env.production file created with all credentials
- [ ] SSL certificate obtained
- [ ] Nginx configured
- [ ] Backend deployed and running
- [ ] Frontend built
- [ ] Systemd services created and running

### Testing
- [ ] Backend API responds to /health
- [ ] Frontend loads at your domain
- [ ] OAuth flow works end-to-end
- [ ] Store appears in database
- [ ] Celery tasks running in logs

---

## 💡 If You Get Stuck

### Check Logs
```bash
# Backend
sudo journalctl -u shopify-seo-backend.service -f

# Celery
sudo journalctl -u shopify-seo-celery.service -f

# Nginx
sudo tail -f /var/log/nginx/error.log
```

### Common Issues

**Backend won't start:**
- Check .env.production has correct DATABASE_URL
- Check PostgreSQL is running: `sudo systemctl status postgresql`

**Frontend not loading:**
- Check Nginx: `sudo nginx -t`
- Check backend is running: `sudo systemctl status shopify-seo-backend.service`

**OAuth fails:**
- Check Shopify API credentials in .env
- Check redirect URI is correct in Shopify Partner account
- Check Nginx is proxying /api/ correctly

**Database not working:**
- Check you can connect: `psql -U shopify_user -d shopify_seo_prod`
- Check database URL in .env matches your password

---

## 📞 Need Help?

1. Check DEPLOYMENT_CHECKLIST.md for detailed steps
2. Check logs with `journalctl` commands
3. Verify .env.production has all correct values
4. Verify Shopify credentials in Partner account

---

**Estimated Time**: 20-25 hours of work over 7 days
**Difficulty**: Medium (technical but following step-by-step guide)
**You've got this! 🚀**
