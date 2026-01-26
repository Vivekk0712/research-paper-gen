import { apiService } from '../config/api';

/**
 * Test connection to backend API
 * @returns {Promise<Object>} - Connection test result
 */
export const testBackendConnection = async () => {
  try {
    console.log('Testing backend connection...');
    
    // Test basic connectivity
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    return {
      success: true,
      message: 'Backend connection successful',
      data: data,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    console.error('Backend connection failed:', error);
    
    return {
      success: false,
      message: `Backend connection failed: ${error.message}`,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
};

/**
 * Check system status including embedding model readiness
 * @returns {Promise<Object>} - System status
 */
export const checkSystemStatus = async () => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/system/status`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    return {
      success: true,
      embeddingModelReady: data.embedding_model_ready,
      latexAvailable: data.latex_available,
      message: data.message,
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    console.error('System status check failed:', error);
    
    return {
      success: false,
      embeddingModelReady: false,
      latexAvailable: false,
      error: error.message,
      timestamp: new Date().toISOString()
    };
  }
};

/**
 * Test API endpoints
 * @returns {Promise<Object>} - API test results
 */
export const testApiEndpoints = async () => {
  const results = {
    connection: null,
    endpoints: {}
  };

  // Test basic connection first
  results.connection = await testBackendConnection();
  
  if (!results.connection.success) {
    return results;
  }

  // Test individual endpoints (without authentication)
  const endpointsToTest = [
    { name: 'root', url: '/', method: 'GET' },
    { name: 'docs', url: '/docs', method: 'GET' },
  ];

  for (const endpoint of endpointsToTest) {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${endpoint.url}`,
        { method: endpoint.method }
      );
      
      results.endpoints[endpoint.name] = {
        success: response.ok,
        status: response.status,
        statusText: response.statusText
      };
    } catch (error) {
      results.endpoints[endpoint.name] = {
        success: false,
        error: error.message
      };
    }
  }

  return results;
};

/**
 * Display connection status in console
 */
export const logConnectionStatus = async () => {
  console.group('🔗 Frontend-Backend Connection Test');
  
  const results = await testApiEndpoints();
  
  if (results.connection.success) {
    console.log('✅ Backend connection: SUCCESS');
    console.log('📡 API Base URL:', import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');
    console.log('📊 Backend response:', results.connection.data);
    
    // Check system status
    const systemStatus = await checkSystemStatus();
    if (systemStatus.success) {
      console.log('🧠 Embedding Model:', systemStatus.embeddingModelReady ? '✅ Ready' : '⏳ Loading...');
      console.log('📄 LaTeX/PDF:', systemStatus.latexAvailable ? '✅ Available' : '❌ Not Available');
    }
    
    results.systemStatus = systemStatus;
  } else {
    console.error('❌ Backend connection: FAILED');
    console.error('🚨 Error:', results.connection.message);
  }
  
  console.log('🔍 Endpoint tests:');
  Object.entries(results.endpoints).forEach(([name, result]) => {
    if (result.success) {
      console.log(`  ✅ ${name}: ${result.status} ${result.statusText}`);
    } else {
      console.error(`  ❌ ${name}: ${result.error || 'Failed'}`);
    }
  });
  
  console.groupEnd();
  
  return results;
};