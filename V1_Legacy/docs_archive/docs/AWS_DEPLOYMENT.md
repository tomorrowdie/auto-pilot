# AWS Lightsail Deployment Guide

This guide explains how to deploy your Shopify SEO Analyzer app to AWS Lightsail.

## Prerequisites

- AWS Lightsail instance (Ubuntu/Linux)
- Domain name or use Lightsail's static IP
- Shopify Partner app credentials (Client ID & Secret)

## Step 1: Prepare Your Lightsail Instance

### Connect to Your Instance
```bash
# Connect via SSH (replace with your instance details)
ssh -i your-key.pem ubuntu@your-lightsail-ip
```

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Required Software
```bash
# Install Docker and Docker Compose
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker

# Install Node.js (for frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install PostgreSQL (or use RDS)
sudo apt install postgresql postgresql-contrib -y

# Install Redis
sudo apt install redis-server -y
```

## Step 2: Set Up Domain and SSL

### Option A: Use Lightsail Static IP
1. Go to Lightsail console
2. Create a static IP and attach to your instance
3. Your app URL will be: `https://your-static-ip`

### Option B: Use Custom Domain (Recommended)
1. Point your domain to Lightsail static IP
2. Set up SSL certificate using Let's Encrypt

```bash
# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx -y

# Install Nginx
sudo apt install nginx -y

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com
```

## Step 3: Configure Environment Variables

Create production environment file:

```bash
# Create app directory
sudo mkdir -p /opt/shopify-seo-analyzer
sudo chown $USER:$USER /opt/shopify-seo-analyzer
cd /opt/shopify-seo-analyzer

# Create production .env file
nano .env.production
```

Add your production configuration:

```bash
# Production Environment Configuration

# Application Settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key-here-make-it-long-and-random
ALLOWED_HOSTS=["https://yourdomain.com", "https://your-static-ip"]

# Database Configuration (use your Lightsail PostgreSQL or RDS)
DATABASE_URL=postgresql://username:password@localhost:5432/shopify_seo_prod

# Redis Configuration
REDIS_URL=redis://localhost:6379

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-different-from-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Shopify Configuration (your actual credentials)
SHOPIFY_API_KEY=your_actual_client_id_here
SHOPIFY_API_SECRET=your_actual_client_secret_here
SHOPIFY_SCOPES=read_products,read_orders,read_customers,read_content,read_themes
SHOPIFY_APP_URL=https://yourdomain.com

# OpenAI Configuration (if you have it)
OPENAI_API_KEY=your_openai_key_if_you_have_one

# Email Configuration (for reports)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com

# Production Settings
LOG_LEVEL=INFO
API_RATE_LIMIT=100
RELOAD=false
WORKERS=4
```

## Step 4: Deploy Your Application

### Upload Your Code
```bash
# Option 1: Git clone (recommended)
git clone https://github.com/yourusername/shopify-seo-analyzer.git .

# Option 2: Upload via SCP
# scp -r shopify-seo-analyzer/ ubuntu@your-ip:/opt/shopify-seo-analyzer/
```

### Set Up Database
```bash
# Create PostgreSQL database
sudo -u postgres createdb shopify_seo_prod
sudo -u postgres createuser shopify_user
sudo -u postgres psql -c "ALTER USER shopify_user PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE shopify_seo_prod TO shopify_user;"
```

### Install Python Dependencies
```bash
cd /opt/shopify-seo-analyzer/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Database Migrations
```bash
# Set environment variables
export $(cat ../.env.production | xargs)

# Run migrations
alembic upgrade head
```

### Build Frontend
```bash
cd /opt/shopify-seo-analyzer/frontend
npm install
npm run build
```

## Step 5: Configure Nginx

Create Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/shopify-seo-analyzer
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;  # Replace with your domain or IP
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;  # Replace with your domain or IP

    # SSL Configuration (if using Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend (React app)
    location / {
        root /opt/shopify-seo-analyzer/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /opt/shopify-seo-analyzer/backend/static/;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/shopify-seo-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 6: Create Systemd Service

Create a service file for your FastAPI app:

```bash
sudo nano /etc/systemd/system/shopify-seo-analyzer.service
```

Add this configuration:

```ini
[Unit]
Description=Shopify SEO Analyzer FastAPI App
After=network.target

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/shopify-seo-analyzer/backend
Environment=PATH=/opt/shopify-seo-analyzer/backend/venv/bin
EnvironmentFile=/opt/shopify-seo-analyzer/.env.production
ExecStart=/opt/shopify-seo-analyzer/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable shopify-seo-analyzer
sudo systemctl start shopify-seo-analyzer
sudo systemctl status shopify-seo-analyzer
```

## Step 7: Update Shopify App Settings

Now update your Shopify Partner app with your production URLs:

1. Go to your Shopify Partner Dashboard
2. Select your app
3. Update these settings:
   - **App URL**: `https://yourdomain.com`
   - **Allowed redirection URL(s)**: `https://yourdomain.com/api/v1/auth/shopify/callback`
   - **Webhook URL**: `https://yourdomain.com/api/v1/auth/shopify/webhook`

## Step 8: Test Your Deployment

### Test the API
```bash
curl https://yourdomain.com/api/v1/auth/health
```

### Test OAuth Flow
```bash
curl -X POST https://yourdomain.com/api/v1/auth/shopify/install \
  -H "Content-Type: application/json" \
  -d '{"shop": "your-test-store.myshopify.com"}'
```

## Step 9: Set Up Monitoring (Optional)

### Log Monitoring
```bash
# View application logs
sudo journalctl -u shopify-seo-analyzer -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Set Up Automatic Backups
```bash
# Create backup script
sudo nano /opt/backup-db.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump shopify_seo_prod > /opt/backups/db_backup_$DATE.sql
# Keep only last 7 days of backups
find /opt/backups -name "db_backup_*.sql" -mtime +7 -delete
```

```bash
sudo chmod +x /opt/backup-db.sh
sudo mkdir -p /opt/backups

# Add to crontab for daily backups
sudo crontab -e
# Add: 0 2 * * * /opt/backup-db.sh
```

## Security Checklist

- ✅ SSL certificate installed
- ✅ Firewall configured (only ports 22, 80, 443 open)
- ✅ Strong passwords for database
- ✅ Environment variables secured
- ✅ Regular security updates
- ✅ Database backups configured

## Troubleshooting

### Common Issues:

1. **502 Bad Gateway**: Check if FastAPI service is running
   ```bash
   sudo systemctl status shopify-seo-analyzer
   ```

2. **Database Connection Error**: Verify database credentials and connection
   ```bash
   psql -h localhost -U shopify_user -d shopify_seo_prod
   ```

3. **SSL Issues**: Check certificate validity
   ```bash
   sudo certbot certificates
   ```

Your AWS Lightsail instance is now ready to host your Shopify app!