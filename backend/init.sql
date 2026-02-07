-- Initial database setup for Shopify SEO Analyzer
-- This file is executed when the PostgreSQL container starts

-- Create database if it doesn't exist (handled by POSTGRES_DB env var)
-- CREATE DATABASE IF NOT EXISTS shopify_seo;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for text search (will be used for keyword search)
-- Additional setup will be done through Alembic migrations