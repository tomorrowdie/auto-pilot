import React from 'react';

const ConnectStore: React.FC = () => {
  return (
    <div className="max-w-md mx-auto">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Connect Your Shopify Store
          </h2>
          <p className="text-gray-600 mb-6">
            Connect your Shopify store to start analyzing and optimizing your SEO.
          </p>
          
          <div className="space-y-4">
            <div>
              <label htmlFor="shop-domain" className="block text-sm font-medium text-gray-700">
                Shop Domain
              </label>
              <div className="mt-1 flex rounded-md shadow-sm">
                <input
                  type="text"
                  name="shop-domain"
                  id="shop-domain"
                  className="flex-1 min-w-0 block w-full px-3 py-2 rounded-none rounded-l-md border border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="your-store"
                />
                <span className="inline-flex items-center px-3 rounded-r-md border border-l-0 border-gray-300 bg-gray-50 text-gray-500 sm:text-sm">
                  .myshopify.com
                </span>
              </div>
            </div>
            
            <button
              type="button"
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              disabled
            >
              Connect Store (Coming Soon)
            </button>
          </div>
          
          <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Development Mode
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    Shopify OAuth integration will be implemented in Task 3.1. 
                    This is a placeholder interface for the connection flow.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConnectStore;