import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Components (to be implemented in later tasks)
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ConnectStore from './pages/ConnectStore';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <Toaster position="top-right" />
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="connect" element={<ConnectStore />} />
              <Route path="dashboard" element={<Dashboard />} />
              {/* More routes will be added in later tasks */}
            </Route>
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;