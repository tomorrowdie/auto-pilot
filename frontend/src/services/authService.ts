/**
 * Authentication service
 * Handles OAuth flow, token management, and session verification
 */

import { apiClient, getErrorMessage } from './api';
import { AuthResponse, UserSession } from '../types';

class AuthService {
  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly USER_KEY = 'user_session';

  /**
   * Initiate Shopify OAuth flow
   */
  async initiateShopifyAuth(shopDomain: string): Promise<{ install_url: string; state: string }> {
    try {
      const response = await apiClient.post('/auth/shopify/install', { shop: shopDomain });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to initiate Shopify auth: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Handle Shopify OAuth callback
   */
  async handleShopifyCallback(
    shop: string,
    code: string,
    state: string,
    hmac: string,
    timestamp: string
  ): Promise<AuthResponse> {
    try {
      const response = await apiClient.get('/auth/shopify/callback', {
        params: { shop, code, state, hmac, timestamp },
      });
      const { access_token } = response.data;
      this.setToken(access_token);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to complete Shopify auth: ${getErrorMessage(error)}`);
    }
  }

  /**
   * Verify store access
   */
  async verifyStoreAccess(shopDomain: string): Promise<boolean> {
    try {
      const response = await apiClient.get(`/auth/shopify/verify/${shopDomain}`);
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  /**
   * Logout and revoke token
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Error during logout:', getErrorMessage(error));
    } finally {
      this.clearAuth();
    }
  }

  /**
   * Get stored access token
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Set access token
   */
  setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  /**
   * Get refresh token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * Set refresh token
   */
  setRefreshToken(token: string): void {
    localStorage.setItem(this.REFRESH_TOKEN_KEY, token);
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  /**
   * Clear all authentication data
   */
  clearAuth(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  /**
   * Get user session
   */
  getUserSession(): UserSession | null {
    const session = localStorage.getItem(this.USER_KEY);
    return session ? JSON.parse(session) : null;
  }

  /**
   * Set user session
   */
  setUserSession(session: UserSession): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(session));
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) {
        return false;
      }

      const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
      const { access_token } = response.data;
      this.setToken(access_token);
      return true;
    } catch (error) {
      this.clearAuth();
      return false;
    }
  }
}

export default new AuthService();
