/**
 * TypeScript types and interfaces for the application
 */

/**
 * Store type - represents a connected Shopify store
 */
export interface Store {
  id: string;
  shopify_domain: string;
  store_name: string;
  owner_email: string;
  plan_name: string | null;
  timezone: string;
  currency: string;
  is_active: boolean;
  last_sync_at: string | null;
  last_analysis_at: string | null;
  product_count: number;
  created_at: string;
  updated_at: string;
}

/**
 * Product type - represents a Shopify product
 */
export interface Product {
  id: string;
  store_id: string;
  shopify_product_id: number;
  title: string;
  handle: string;
  description: string | null;
  vendor: string | null;
  product_type: string | null;
  tags: string;
  seo_title: string | null;
  seo_description: string | null;
  is_active: boolean;
  views: number;
  conversion_rate: number | null;
  created_at: string;
  updated_at: string;
}

/**
 * SEO Analysis type
 */
export interface SEOAnalysis {
  id: string;
  store_id: string;
  product_id: string | null;
  analysis_type: 'product' | 'page' | 'store';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  url: string | null;
  seo_score: number | null;
  title_score: number | null;
  description_score: number | null;
  content_score: number | null;
  technical_score: number | null;
  keyword_score: number | null;
  recommendations: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

/**
 * Keyword type
 */
export interface Keyword {
  id: string;
  keyword: string;
  search_volume: number | null;
  keyword_difficulty: number | null;
  cpc: number | null;
  competition_level: string | null;
  search_intent: string | null;
  category: string | null;
  source: string;
  trend_score: number | null;
  seasonal_pattern: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Product-Keyword relationship
 */
export interface ProductKeyword {
  id: string;
  product_id: string;
  keyword_id: string;
  relevance_score: number;
  current_ranking: number | null;
  target_ranking: number | null;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Authentication response
 */
export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
}

/**
 * Pagination type
 */
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Store sync status
 */
export interface StoreSyncStatus {
  store_id: string;
  status: 'pending' | 'syncing' | 'completed' | 'failed';
  last_sync_at: string | null;
  products_synced: number;
  products_updated: number;
  error_message?: string;
}

/**
 * API Error type
 */
export interface ApiError {
  detail?: string;
  message?: string;
  status?: number;
  field?: string;
}

/**
 * User session type
 */
export interface UserSession {
  id: string;
  email: string;
  name: string;
  stores: Store[];
  permissions: string[];
}
