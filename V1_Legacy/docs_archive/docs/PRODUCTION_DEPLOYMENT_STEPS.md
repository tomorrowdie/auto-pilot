# Production Deployment Steps - AWS Lightsail

## Your Deployment Plan (Reviewed & Optimized)

Your plan is excellent! Here are a few small adjustments to ensure perfect compatibility with the current codebase:

### Step 6 – Create .env.production (Updated)

```bash
nano .env.production
```

**Updated .env with correct variable names:**

```bash
# Application Settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-random-secret-key-here-make-it-64-chars-long
JWT_SECRET_KEY=your-different-jwt-secret-key-also-64-chars-long
ALLOWED_HOSTS=["https://seo-analyzer.yourdomain.com"]

# Database Configuration
DATABASE_URL=postgresql://shopify_user:password@localhost:5432/shopify_seo_prod

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Shopify Configuration (exact variable names from code)
SHOPIFY_API_KEY=your_actual_client_id_here
SHOPIFY_API_SECRET=your_actual_client_secret_here
SHOPIFY_SCOPES=read_products,read_orders,read_customers,read_content,read_themes
SHOPIFY_APP_URL=https://seo-analyzer.yourdomain.com

# JWT Settings
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Production Settings
LOG_LEVEL=INFO
RELOAD=false
WORKERS=1
API_RATE_LIMIT=100
```

### Step 8.5 – Run Database Migrations (Add This Step)

After installing backend dependencies, run migrations:

```bash
# Still in backend directory with venv activated
export $(cat ../.env.production | xargs)
alembic upgrade head
```

### Step 9.5 – Build Frontend (Add This Step)

Before configuring Nginx, build the React frontend:

```bash
cd /opt/shopify-seo-analyzer/frontend
npm install
npm run build
```

### Step 12 – Test Your Deployment (Add This Step)

After everything is set up, test the deployment:

```bash
# Test API health
curl https://seo-analyzer.yourdomain.com/api/v1/auth/health

# Test OAuth install URL generation
curl -X POST https://seo-analyzer.yourdomain.com/api/v1/auth/shopify/install \
  -H "Content-Type: application/json" \
  -d '{"shop": "your-test-store.myshopify.com"}'

# Test frontend
curl https://seo-analyzer.yourdomain.com/

# Check service status
sudo systemctl status seo-analyzer

# Check logs
sudo journalctl -u seo-analyzer -f
```

## Why 1 Worker is Perfect for Now

✅ **Lower memory usage** (~200MB vs ~800MB with 4 workers)
✅ **Faster startup time**
✅ **Easier debugging** (single process)
✅ **Perfect for testing phase**
✅ **Easy to scale later** (just change the number)

### When to Scale Up:
- **2 workers**: When you have 2-3 concurrent users
- **4 workers**: When you have 5+ concurrent users
- **Monitor with**: `htop` or `sudo systemctl status seo-analyzer`

## Additional Monitoring Commands

```bash
# Monitor resource usage
htop

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Check application logs
sudo journalctl -u seo-analyzer -f

# Check database connections
sudo -u postgres psql -d shopify_seo_prod -c "SELECT count(*) FROM pg_stat_activity;"
```

## Troubleshooting Common Issues

### If API returns 502 Bad Gateway:
```bash
# Check if service is running
sudo systemctl status seo-analyzer

# Restart service
sudo systemctl restart seo-analyzer

# Check logs for errors
sudo journalctl -u seo-analyzer --no-pager -l
```

### If OAuth callback fails:
1. Verify Shopify app settings match exactly
2. Check SSL certificate is valid
3. Ensure firewall allows HTTPS traffic

### If database connection fails:
```bash
# Test database connection
sudo -u postgres psql -d shopify_seo_prod -U shopify_user

# Check PostgreSQL is running
sudo systemctl status postgresql
```

## Post-Deployment Checklist

- [ ] API health endpoint responds
- [ ] Frontend loads correctly
- [ ] OAuth install URL generates successfully
- [ ] SSL certificate is valid
- [ ] Database migrations completed
- [ ] Service starts automatically on reboot
- [ ] Logs are being written correctly
- [ ] Shopify app settings updated

## Ready for Development Continuation

Once your deployment is complete and tested, we can continue with the next development tasks:

1. **Task 3.2**: Create authentication middleware and JWT handling
2. **Task 3.3**: Build frontend authentication components
3. **Task 4.1**: Create Shopify Admin API client wrapper

Your deployment plan is solid and production-ready for internal testing!