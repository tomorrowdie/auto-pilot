/**
 * Store service
 * Handles CRUD operations for Shopify stores
 */

import { apiClient, getErrorMessage } from './api';
import { Store, StoreSyncStatus } from '../types';

class StoreService {
  /**
   * Get all stores for the current user
   */
  async getStores(): Promise<Store[]> {
    try {
      const response = await apiClient.get('/stores/');
      return response.data.stores || response.data;
    } catch (error) {
      throw new Error(`Failed to fetch stores: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get a single store by ID
   */
  async getStore(storeId: string): Promise<Store> {
    try {
      const response = await apiClient.get(`/stores/${storeId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch store: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Create a new store (testing only)
   */
  async createStore(storeData: Partial<Store>): Promise<Store> {
    try {
      const response = await apiClient.post('/stores/', storeData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create store: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Update a store
   */
  async updateStore(storeId: string, storeData: Partial<Store>): Promise<Store> {
    try {
      const response = await apiClient.put(`/stores/${storeId}`, storeData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to update store: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Delete a store
   */
  async deleteStore(storeId: string): Promise<void> {
    try {
      await apiClient.delete(`/stores/${storeId}`);
    } catch (error) {
      throw new Error(`Failed to delete store: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Trigger manual sync for a store
   */
  async syncStore(storeId: string): Promise<StoreSyncStatus> {
    try {
      const response = await apiClient.post(`/stores/${storeId}/sync`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to sync store: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Get store sync status
   */
  async getStoreSyncStatus(storeId: string): Promise<StoreSyncStatus> {
    try {
      const response = await apiClient.get(`/stores/${storeId}/sync-status`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to fetch sync status: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Check if store needs sync
   */
  async checkSyncNeeded(storeId: string): Promise<boolean> {
    try {
      const store = await this.getStore(storeId);
      const maxAgeHours = 24;
      const lastSync = store.last_sync_at ? new Date(store.last_sync_at) : null;
      const now = new Date();

      if (!lastSync) return true;

      const hoursSinceSync = (now.getTime() - lastSync.getTime()) / (1000 * 60 * 60);
      return hoursSinceSync > maxAgeHours;
    } catch (error) {
      console.error('Error checking sync needed:', getErrorMessage(error));
      return false;
    }
  }
}

export default new StoreService();
