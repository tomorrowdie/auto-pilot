# Shopify SEO Analyzer – Full Stack Setup Guide

## 1. Project Overview
This document summarizes the **Shopify SEO Analyzer** app setup and deployment process. The backend uses **Python + FastAPI + Uvicorn**, hosted on **AWS Lightsail (Ubuntu)**, and connects to **Shopify Partner App** for OAuth 2.0 authentication.

**Purpose:** Enable the Shopify SEO Analyzer to be securely installed and tested across multiple Shopify stores.

---

## 2. GitHub & File Structure
Your current repository includes:
- `.env.example` → environment variable template
- `.gitignore` → excludes `.env`, logs, and local build files from Git tracking

This ensures sensitive credentials (Shopify API key, secret, database URLs) are not pushed to GitHub.

---

## 3. Claude Code Instructions – Environment Key Setup
Claude (or any developer agent) should perform the following steps before deployment:

```bash
# Step 1: Open the file `.env.example`

# Step 2: Update or append these Shopify API credentials:
SHOPIFY_API_KEY=00e0308488fd130c41f5de204a576b75
SHOPIFY_API_SECRET=8773c3e3052ae05c2d13b4ea3833d362
SHOPIFY_API_SCOPES=read_products,write_products,read_themes
SHOPIFY_REDIRECT_URL=https://<YOUR_LIGHTSAIL_IP>/auth/callback

# Step 3: Save the file as `.env` in the backend root directory
# (Do NOT commit `.env` to GitHub — `.gitignore` already excludes it.)
```

---

## 4. AWS Lightsail Environment Summary

**Environment:** Ubuntu / Linux (Node.js + Python3 + PostgreSQL + Redis)

**Installed Components:**
- Docker & Docker Compose
- Python 3.10 (with venv)
- Node.js 18 (for React frontend)
- PostgreSQL 14
- Redis server
- Nginx + Certbot (optional SSL setup)

### Steps Recap
1. **Connect to Lightsail Instance:**
   ```bash
   ssh -i your-key.pem ubuntu@your-lightsail-ip
   ```
2. **Clone Repository:**
   ```bash
   git clone https://github.com/tomorrowdie/shopify-seo-analyzer.git
   ```
3. **Backend Setup:**
   ```bash
   cd shopify-seo-analyzer/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Run API Server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   Test via: `http://<your-lightsail-ip>:8000`

---

## 5. Shopify Partner App Configuration
**App Name:** `seo-analyzer`

| Setting | Value |
|----------|--------|
| Client ID (API Key) | `00e0308488fd130c41f5de204a576b75` |
| Client Secret | `8773c3e3052ae05c2d13b4ea3833d362` |
| API Contact Email | `johnchin@pandaocean.com` |
| Allowed Redirect URL | `https://<YOUR_LIGHTSAIL_IP>/auth/callback` |
| App URL | `https://<YOUR_LIGHTSAIL_IP>` |
| Scopes | `read_products,write_products,read_themes` |

> ⚠️ Replace `<YOUR_LIGHTSAIL_IP>` with your actual public IP or domain (e.g., `https://44.254.100.52`).

---

## 6. Environment Variables Template (`.env.example`)
Below is a cleaned example based on your uploaded file structure:

```bash
# Shopify Configuration
SHOPIFY_API_KEY=
SHOPIFY_API_SECRET=
SHOPIFY_API_SCOPES=
SHOPIFY_REDIRECT_URL=

# Database & Redis
DATABASE_URL=postgresql://shopify_user:password@localhost:5432/shopify_seo_prod
REDIS_URL=redis://localhost:6379

# App Settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret
ALLOWED_HOSTS=["https://yourdomain.com", "https://your-static-ip"]
```

---

## 7. Testing & Verification Flow

### Step 1. Local OAuth Installation
Send a POST request to your install endpoint:
```bash
curl -X POST https://<your-lightsail-ip>/api/v1/auth/shopify/install \
  -H "Content-Type: application/json" \
  -d '{"shop": "test-store.myshopify.com"}'
```

### Step 2. Shopify Redirect
Shopify will redirect to:
```
https://<your-lightsail-ip>/auth/callback?shop=test-store.myshopify.com&code=XXXXX
```

Your backend exchanges the code for an access token.

### Step 3. Verify Connection
Check your FastAPI logs or call the `/api/v1/auth/shopify/verify/{shop}` endpoint.

### Step 4. Test Webhook
App uninstall webhook:
```
POST https://<your-lightsail-ip>/api/v1/auth/shopify/webhook
```
Expected JSON: `{ "success": true }`

---

## 8. Next Actions
- [ ] Confirm `.env` is properly loaded in the Lightsail environment.
- [ ] Add HTTPS using Certbot for your Lightsail domain.
- [ ] Re-deploy frontend (`npm run build`) and link it with Nginx.
- [ ] Test Shopify app installation from Partner Dashboard.

---

## 9. Security Checklist
- `.env` file **never** committed to GitHub.
- SSL certificate installed (`certbot --nginx -d yourdomain.com`).
- Lightsail firewall only opens ports **22**, **80**, **443**.
- PostgreSQL and Redis secured with passwords.

---

**Document Prepared For:** Claude Code Integration  
**Objective:** To finalize AWS + Shopify setup and enable end-to-end OAuth testing.

