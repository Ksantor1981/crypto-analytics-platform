'use client';

import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/contexts/AuthContext';
import apiClient from '@/lib/api';

export default function TestLoginPage() {
  const [email, setEmail] = useState('test@example.com');
  const [password, setPassword] = useState('password123');
  const [testResult, setTestResult] = useState<string>('');
  const { login, isLoading, error, isAuthenticated, user } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTestResult('Attempting login...');
    
    const success = await login(email, password);
    if (success) {
      setTestResult('✅ Login successful!');
      // router.push('/dashboard');
    } else {
      setTestResult('❌ Login failed');
    }
  };

  const testApiConnection = async () => {
    setTestResult('Testing API connection...');
    
    try {
      const healthResponse = await apiClient.healthCheck();
      const testResponse = await apiClient.testConnection();
      
      setTestResult(`
        ✅ API Connection Test:
        - Health: ${healthResponse.status} ${healthResponse.data ? '✅' : '❌'}
        - Root endpoint: ${testResponse.status} ${testResponse.data ? '✅' : '❌'}
        - Base URL: ${process.env.NEXT_PUBLIC_API_URL}
      `);
    } catch (error) {
      setTestResult(`❌ API Connection Failed: ${error}`);
    }
  };

  const testMlPrediction = async () => {
    setTestResult('Testing ML prediction...');
    
    try {
      const response = await apiClient.testPrediction();
      setTestResult(`
        ✅ ML Prediction Test:
        - Status: ${response.status}
        - Prediction: ${response.data?.prediction}
        - Confidence: ${response.data?.confidence}%
        - Recommendation: ${response.data?.recommendation}
      `);
    } catch (error) {
      setTestResult(`❌ ML Prediction Failed: ${error}`);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h1>🧪 API Test Page</h1>
      
      {/* API Connection Test */}
      <div style={{ marginBottom: '30px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
        <h2>1. API Connection Test</h2>
        <button 
          onClick={testApiConnection}
          style={{ padding: '10px 20px', marginRight: '10px', cursor: 'pointer' }}
        >
          Test API Connection
        </button>
        <p>Backend URL: <code>{process.env.NEXT_PUBLIC_API_URL}</code></p>
      </div>

      {/* Authentication Test */}
      <div style={{ marginBottom: '30px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
        <h2>2. Authentication Test</h2>
        <form onSubmit={handleSubmit} style={{ marginBottom: '15px' }}>
          <div style={{ marginBottom: '10px' }}>
            <label>Email:</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{ width: '100%', padding: '5px', marginTop: '5px' }}
              required
            />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{ width: '100%', padding: '5px', marginTop: '5px' }}
              required
            />
          </div>
          <button 
            type="submit" 
            disabled={isLoading}
            style={{ padding: '10px 20px', cursor: 'pointer' }}
          >
            {isLoading ? 'Logging in...' : 'Test Login'}
          </button>
        </form>
        
        {isAuthenticated && (
          <div style={{ color: 'green' }}>
            ✅ Authenticated as: {user?.email} (ID: {user?.id})
          </div>
        )}
        
        {error && (
          <div style={{ color: 'red', marginTop: '10px' }}>
            ❌ Error: {error}
          </div>
        )}
      </div>

      {/* ML Prediction Test */}
      <div style={{ marginBottom: '30px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
        <h2>3. ML Service Test</h2>
        <button 
          onClick={testMlPrediction}
          style={{ padding: '10px 20px', cursor: 'pointer' }}
        >
          Test ML Prediction
        </button>
        <p>ML Service URL: <code>{process.env.NEXT_PUBLIC_ML_API_URL}</code></p>
      </div>

      {/* Test Results */}
      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '5px' }}>
        <h3>Test Results:</h3>
        <pre style={{ whiteSpace: 'pre-wrap', fontSize: '14px' }}>
          {testResult || 'No tests run yet...'}
        </pre>
      </div>

      {/* Quick Actions */}
      <div style={{ marginTop: '30px' }}>
        <h3>Quick Actions:</h3>
        <button 
          onClick={() => console.log('API Client:', apiClient)}
          style={{ padding: '10px 20px', marginRight: '10px', cursor: 'pointer' }}
        >
          Log API Client to Console
        </button>
        <button 
          onClick={() => {
            apiClient.clearTokens();
            setTestResult('🔄 Tokens cleared');
          }}
          style={{ padding: '10px 20px', cursor: 'pointer' }}
        >
          Clear Tokens
        </button>
      </div>
    </div>
  );
}
