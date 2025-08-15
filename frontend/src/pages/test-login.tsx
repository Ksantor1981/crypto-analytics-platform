'use client';

import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';

export default function TestLoginPage() {
  const [email, setEmail] = useState('test@example.com');
  const [password, setPassword] = useState('test123');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  
  const { login, user, isAuthenticated } = useAuth();
  const router = useRouter();

  const handleTestLogin = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const success = await login(email, password);
      if (success) {
        setResult({ success: true, message: 'Login successful' });
      } else {
        setError('Login failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestAPI = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const healthCheck = await apiClient.healthCheck();
      const channels = await apiClient.getChannels();
      const signals = await apiClient.getSignals();
      
      setResult({
        healthCheck,
        channels: channels?.length || 0,
        signals: signals?.length || 0
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'API test failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    // Logout logic would be here
    setResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md mx-auto">
        <div className="bg-white shadow rounded-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">API Test Page</h1>
          
          {/* Login Form */}
          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
            <button
              onClick={handleTestLogin}
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Testing...' : 'Test Login'}
            </button>
          </div>

          {/* API Test */}
          <div className="space-y-4 mb-6">
            <button
              onClick={handleTestAPI}
              disabled={isLoading}
              className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {isLoading ? 'Testing...' : 'Test API Calls'}
            </button>
          </div>

          {/* Status */}
          <div className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-md">
              <h3 className="font-medium text-gray-900 mb-2">Status</h3>
              <p className="text-sm text-gray-600">
                Authenticated: {isAuthenticated ? 'Yes' : 'No'}
              </p>
              {user && (
                <p className="text-sm text-gray-600">
                  User: {user.email}
                </p>
              )}
            </div>

            {/* Results */}
            {result && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-md">
                <h3 className="font-medium text-green-900 mb-2">Success</h3>
                <pre className="text-sm text-green-700 overflow-auto">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            )}

            {/* Errors */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                <h3 className="font-medium text-red-900 mb-2">Error</h3>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
