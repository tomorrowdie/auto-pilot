/**
 * API service configuration and utilities
 * Provides a centralized HTTP client with interceptors, error handling, and retry logic
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse, AxiosRequestConfig } from 'axios';

/**
 * API response wrapper type
 */
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

/**
 * API error response type
 */
export interface ApiErrorResponse {
  detail?: string;
  message?: string;
  status?: number;
}

/**
 * Request retry configuration
 */
interface RetryConfig extends AxiosRequestConfig {
  retryCount?: number;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // ms

/**
 * Create and configure the API client
 */
export const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true,
  });

  // Request interceptor - add auth token if available
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor - handle errors and retries
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const config = error.config as RetryConfig;

      if (!config) {
        return Promise.reject(error);
      }

      // Don't retry on 4xx errors (except 429)
      if (error.response?.status && error.response.status < 500 && error.response.status !== 429) {
        if (error.response.status === 401) {
          // Clear token and redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/auth/login';
        }
        return Promise.reject(error);
      }

      // Retry logic for 5xx and rate limit errors
      config.retryCount = config.retryCount || 0;
      if (config.retryCount < MAX_RETRIES) {
        config.retryCount++;
        const delay = RETRY_DELAY * Math.pow(2, config.retryCount - 1);
        await new Promise((resolve) => setTimeout(resolve, delay));
        return client(config);
      }

      return Promise.reject(error);
    }
  );

  return client;
};

/**
 * Initialize API client
 */
export const apiClient = createApiClient();

/**
 * Extract error message from API error
 */
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const response = error.response?.data as ApiErrorResponse;
    return response?.detail || response?.message || error.message || 'An error occurred';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

/**
 * Type guard for API error response
 */
export const isApiError = (error: unknown): error is AxiosError<ApiErrorResponse> => {
  return axios.isAxiosError(error);
};
