# Shopify App Setup Guide

This guide explains how to set up your Shopify app credentials for development and testing.

## What You Need

To use the Shopify OAuth integration, you need to create a Shopify app and get API credentials. **You don't need to provide your store's API keys** - instead, you need to create a Shopify app that other stores (including your own) can install.

## Step 1: Create a Shopify Partner Account

1. Go to [Shopify Partners](https://partners.shopify.com/)
2. Sign up for a free Partner account
3. Complete the registration process

## Step 2: Create a Shopify App

1. In your Partner Dashboard, click "Apps" in the sidebar
2. Click "Create app"
3. Choose "Public app" (for apps that can be installed by any store)
4. Fill in your app details:
   - **App name**: "SEO Analyzer" (or your preferred name)
   - **App URL**: `http://localhost:8000` (for development)
   - **Allowed redirection URL(s)**: `http://localhost:8000/api/v1/auth/shopify/callback`

## Step 3: Configure App Settings

1. In your app settings, set the following:
   - **App URL**: `http://localhost:8000`
   - **Allowed redirection URL(s)**: `http://localhost:8000/api/v1/auth/shopify/callback`
   - **Webhook URL**: `http://localhost:8000/api/v1/auth/shopify/webhook` (optional for development)

2. Set the required scopes (permissions):
   - `read_products` - Read product data
   - `read_orders` - Read order data (for SEO insights)
   - `read_customers` - Read customer data (for analytics)
   - `read_content` - Read blog posts and pages
   - `read_themes` - Read theme files for technical SEO analysis

## Step 4: Get Your API Credentials

1. In your app dashboard, you'll find:
   - **API key** (Client ID)
   - **API secret key** (Client Secret)

2. Copy these values - you'll need them for your environment configuration.

## Step 5: Configure Your Development Environment

Create a `.env` file in the `backend` directory with your credentials:

```bash
# Shopify App Configuration
SHOPIFY_API_KEY=your_api_key_here
SHOPIFY_API_SECRET=your_api_secret_here
SHOPIFY_SCOPES=read_products,read_orders,read_customers,read_content,read_themes
SHOPIFY_APP_URL=http://localhost:8000

# Other required settings
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/shopify_seo
REDIS_URL=redis://localhost:6379
```

## Step 6: Test the OAuth Flow

1. Start your development server:
   ```bash
   cd shopify-seo-analyzer
   ./start-dev.sh  # or start-dev.bat on Windows
   ```

2. Test the OAuth installation endpoint:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/shopify/install \
     -H "Content-Type: application/json" \
     -d '{"shop": "your-test-store.myshopify.com"}'
   ```

3. The response will include an `install_url` that you can visit to test the OAuth flow.

## Development Store Setup (Optional)

If you want to test with a development store:

1. In your Partner Dashboard, click "Stores"
2. Click "Create store"
3. Choose "Development store"
4. Fill in the store details
5. Use this store's domain for testing

## Security Notes

- **Never commit your API credentials to version control**
- The `.env` file is already in `.gitignore`
- In production, use environment variables or a secure secrets manager
- The API secret is used for HMAC verification - keep it secure

## Troubleshooting

### Common Issues:

1. **"Invalid shop domain"**: Make sure you're using the full `.myshopify.com` domain
2. **"Invalid HMAC signature"**: Check that your API secret is correct
3. **"Callback URL not allowed"**: Verify the redirect URL in your app settings matches exactly

### Testing OAuth Flow:

1. Use the `/api/v1/auth/shopify/install` endpoint to generate install URLs
2. Visit the install URL in a browser
3. Complete the OAuth flow
4. Check that the callback endpoint receives the authorization code

## Next Steps

Once you have your credentials configured:

1. Test the OAuth flow with a development store
2. Verify that store data is being saved to your database
3. Test the webhook endpoints for app uninstall events
4. Move on to implementing the Shopify API client for product data

## Production Deployment

For production deployment:

1. Update your app settings with your production URLs
2. Set up proper SSL certificates
3. Configure environment variables securely
4. Set up webhook endpoints for real-time updates
5. Submit your app for review if making it publicly available