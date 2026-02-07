/**
 * Keyword service
 * Handles keyword research and management operations
 */

import { apiClient, getErrorMessage } from './api';
import { Keyword, ProductKeyword, PaginatedResponse } from '../types';

class KeywordService {
  /**
   * Create a new keyword
   */
  async createKeyword(keywordData: Partial<Keyword>): Promise<Keyword> {
    try {
      const response = await apiClient.post('/keywords/', keywordData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create keyword: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get a single keyword
   */
  async getKeyword(keywordId: string): Promise<Keyword> {
    try {
      const response = await apiClient.get(`/keywords/${keywordId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch keyword: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Update a keyword
   */
  async updateKeyword(keywordId: string, keywordData: Partial<Keyword>): Promise<Keyword> {
    try {
      const response = await apiClient.put(`/keywords/${keywordId}`, keywordData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to update keyword: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Delete a keyword
   */
  async deleteKeyword(keywordId: string): Promise<void> {
    try {
      await apiClient.delete(`/keywords/${keywordId}`);
    } catch (error) {
      throw new Error(`Failed to delete keyword: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Search keywords
   */
  async searchKeywords(
    query: string,
    source: string = 'all',
    limit: number = 50
  ): Promise<PaginatedResponse<Keyword>> {
    try {
      const response = await apiClient.get('/keywords/search', {
        params: { query, source, limit },
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to search keywords: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Create product-keyword relationship
   */
  async createProductKeyword(pkData: Partial<ProductKeyword>): Promise<ProductKeyword> {
    try {
      const response = await apiClient.post('/keywords/product-keywords/', pkData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create product-keyword: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get product keywords
   */
  async getProductKeywords(productId: string): Promise<ProductKeyword[]> {
    try {
      const response = await apiClient.get(`/keywords/product/${productId}/keywords`);
      return response.data.product_keywords || response.data;
    } catch (error) {
      throw new Error(`Failed to fetch product keywords: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Update product-keyword relationship
   */
  async updateProductKeyword(
    productId: string,
    keywordId: string,
    pkData: Partial<ProductKeyword>
  ): Promise<ProductKeyword> {
    try {
      const response = await apiClient.put(
        `/keywords/product/${productId}/keywords/${keywordId}`,
        pkData
      );
      return response.data;
    } catch (error) {
      throw new Error(`Failed to update product-keyword: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Delete product-keyword relationship
   */
  async deleteProductKeyword(productId: string, keywordId: string): Promise<void> {
    try {
      await apiClient.delete(`/keywords/product/${productId}/keywords/${keywordId}`);
    } catch (error) {
      throw new Error(`Failed to delete product-keyword: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get recommended keywords for a product
   */
  async getRecommendedKeywords(productId: string, limit: number = 20): Promise<Keyword[]> {
    try {
      const response = await apiClient.get(`/keywords/product/${productId}/recommendations`, {
        params: { limit },
      });
      return response.data.recommendations || response.data;
    } catch (error) {
      throw new Error(`Failed to fetch recommended keywords: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get trending keywords
   */
  async getTrendingKeywords(source: string = 'all', limit: number = 50): Promise<Keyword[]> {
    try {
      const response = await apiClient.get('/keywords/trending', {
        params: { source, limit },
      });
      return response.data.keywords || response.data;
    } catch (error) {
      throw new Error(`Failed to fetch trending keywords: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Import keywords from CSV
   */
  async importKeywords(file: File): Promise<{ imported_count: number }> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post('/keywords/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to import keywords: ${getErrorMessage(error)}`);
    }
  }
}

export default new KeywordService();
