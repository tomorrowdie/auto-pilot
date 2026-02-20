/**
 * Analysis service
 * Handles SEO analysis operations
 */

import { apiClient, getErrorMessage } from './api';
import { SEOAnalysis, PaginatedResponse } from '../types';

class AnalysisService {
  /**
   * Create a new analysis
   */
  async createAnalysis(analysisData: Partial<SEOAnalysis>): Promise<SEOAnalysis> {
    try {
      const response = await apiClient.post('/analysis/', analysisData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create analysis: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get a single analysis
   */
  async getAnalysis(analysisId: string): Promise<SEOAnalysis> {
    try {
      const response = await apiClient.get(`/analysis/${analysisId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch analysis: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Update an analysis
   */
  async updateAnalysis(analysisId: string, analysisData: Partial<SEOAnalysis>): Promise<SEOAnalysis> {
    try {
      const response = await apiClient.put(`/analysis/${analysisId}`, analysisData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to update analysis: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Delete an analysis
   */
  async deleteAnalysis(analysisId: string): Promise<void> {
    try {
      await apiClient.delete(`/analysis/${analysisId}`);
    } catch (error) {
      throw new Error(`Failed to delete analysis: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get all analyses for a store
   */
  async getStoreAnalyses(
    storeId: string,
    analysisType?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<PaginatedResponse<SEOAnalysis>> {
    try {
      const response = await apiClient.get(`/analysis/store/${storeId}/analyses`, {
        params: { analysis_type: analysisType, limit, offset },
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch store analyses: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get all analyses for a product
   */
  async getProductAnalyses(
    productId: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<PaginatedResponse<SEOAnalysis>> {
    try {
      const response = await apiClient.get(`/analysis/product/${productId}/analyses`, {
        params: { limit, offset },
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch product analyses: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Trigger analysis for a product
   */
  async analyzeProduct(productId: string): Promise<SEOAnalysis> {
    try {
      const response = await apiClient.post(`/analysis/product/${productId}/analyze`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to analyze product: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Trigger bulk analysis for a store
   */
  async analyzeManyProducts(storeId: string, productIds: string[]): Promise<string[]> {
    try {
      const response = await apiClient.post(`/analysis/store/${storeId}/analyze-bulk`, {
        product_ids: productIds,
      });
      return response.data.analysis_ids || response.data;
    } catch (error) {
      throw new Error(`Failed to trigger bulk analysis: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get analysis statistics for a store
   */
  async getStoreAnalysisStats(storeId: string): Promise<Record<string, unknown>> {
    try {
      const response = await apiClient.get(`/analysis/store/${storeId}/stats`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch analysis stats: ${getErrorMessage(error)}`);
    }
  }
}

export default new AnalysisService();
