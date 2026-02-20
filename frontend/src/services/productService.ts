/**
 * Product service
 * Handles operations related to Shopify products
 */

import { apiClient, getErrorMessage } from './api';
import { Product, PaginatedResponse } from '../types';

class ProductService {
  /**
   * Get all products for a store
   */
  async getStoreProducts(
    storeId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<PaginatedResponse<Product>> {
    try {
      const response = await apiClient.get(`/products/store/${storeId}`, {
        params: { limit, offset },
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch products: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get a single product
   */
  async getProduct(productId: string): Promise<Product> {
    try {
      const response = await apiClient.get(`/products/${productId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch product: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Create a product (testing only)
   */
  async createProduct(productData: Partial<Product>): Promise<Product> {
    try {
      const response = await apiClient.post('/products/', productData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create product: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Update a product
   */
  async updateProduct(productId: string, productData: Partial<Product>): Promise<Product> {
    try {
      const response = await apiClient.put(`/products/${productId}`, productData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to update product: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Search products by title or handle
   */
  async searchProducts(
    storeId: string,
    query: string,
    limit: number = 20
  ): Promise<Product[]> {
    try {
      const response = await apiClient.get(`/products/search`, {
        params: { store_id: storeId, query, limit },
      });
      return response.data.products || response.data;
    } catch (error) {
      throw new Error(`Failed to search products: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get products needing SEO analysis
   */
  async getProductsNeedingAnalysis(storeId: string, limit: number = 50): Promise<Product[]> {
    try {
      const response = await apiClient.get(`/products/store/${storeId}/needs-analysis`, {
        params: { limit },
      });
      return response.data.products || response.data;
    } catch (error) {
      throw new Error(`Failed to fetch products needing analysis: ${getErrorMessage(error)}`);
    }
  }
}

export default new ProductService();
