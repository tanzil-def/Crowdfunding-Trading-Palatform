// API Client Configuration & Endpoint Reference
// Frontend developers: Use these exact endpoints in your API calls

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// ============================================================================
// 🔐 AUTHENTICATION ENDPOINTS
// ============================================================================
export const AUTH_ENDPOINTS = {
  REGISTER: `${API_BASE_URL}/auth/register/`,
  LOGIN: `${API_BASE_URL}/auth/login/`,
  LOGOUT: `${API_BASE_URL}/auth/logout/`,
  REFRESH: `${API_BASE_URL}/auth/refresh/`,
  VERIFY_EMAIL: `${API_BASE_URL}/auth/verify-email/`,
  PROFILE: `${API_BASE_URL}/auth/profile/`,
};

// ============================================================================
// 📁 PROJECTS ENDPOINTS
// ============================================================================
export const PROJECTS_ENDPOINTS = {
  // Developer - Project Management
  CREATE: `${API_BASE_URL}/projects/`,
  LIST: `${API_BASE_URL}/projects/`,
  MY_PROJECTS: `${API_BASE_URL}/projects/my/`,
  DETAIL: (projectId) => `${API_BASE_URL}/projects/${projectId}/`,
  UPDATE: (projectId) => `${API_BASE_URL}/projects/${projectId}/`,
  SUBMIT: (projectId) => `${API_BASE_URL}/projects/${projectId}/submit/`,

  // Developer - Media
  UPLOAD_MEDIA: (projectId) => `${API_BASE_URL}/projects/${projectId}/media/`,
  LIST_MEDIA: (projectId) => `${API_BASE_URL}/projects/${projectId}/media/list/`,

  // Admin - Project Review
  ADMIN_PENDING: `${API_BASE_URL}/projects/admin/projects/pending/`,
  ADMIN_APPROVE: (projectId) => `${API_BASE_URL}/projects/admin/projects/${projectId}/approve/`,
  ADMIN_REJECT: (projectId) => `${API_BASE_URL}/projects/admin/projects/${projectId}/reject/`,
  ADMIN_REQUEST_CHANGES: (projectId) => `${API_BASE_URL}/projects/admin/projects/${projectId}/request-changes/`,

  // Investor - Discovery
  BROWSE: `${API_BASE_URL}/projects/browse/`,
  COMPARE: `${API_BASE_URL}/projects/compare/`,
  INVESTOR_DETAIL: (projectId) => `${API_BASE_URL}/projects/${projectId}/detail/`,
};

// ============================================================================
// 💰 INVESTMENTS ENDPOINTS
// ============================================================================
export const INVESTMENTS_ENDPOINTS = {
  // Investor
  INITIATE: `${API_BASE_URL}/investments/initiate/`,
  MY_INVESTMENTS: `${API_BASE_URL}/investments/my/`,
  INVESTMENT_DETAIL: (investmentId) => `${API_BASE_URL}/investments/${investmentId}/`,
  PORTFOLIO_SUMMARY: `${API_BASE_URL}/investments/portfolio/summary/`,

  // Payment Gateway
  PAYMENT_CALLBACK: `${API_BASE_URL}/investments/payments/callback/`,

  // Admin
  ADMIN_TRANSACTIONS: `${API_BASE_URL}/investments/admin/transactions/`,
  ADMIN_TRANSACTION_DETAIL: (transactionId) => `${API_BASE_URL}/investments/admin/transactions/${transactionId}/`,
};

// ============================================================================
// 🔐 ACCESS REQUESTS ENDPOINTS
// ============================================================================
export const ACCESS_REQUESTS_ENDPOINTS = {
  CREATE: `${API_BASE_URL}/access-requests/`,
  MY_REQUESTS: `${API_BASE_URL}/access-requests/my/`,
  ADMIN_APPROVE: (requestId) => `${API_BASE_URL}/access-requests/admin/${requestId}/approve/`,
  ADMIN_REJECT: (requestId) => `${API_BASE_URL}/access-requests/admin/${requestId}/reject/`,
  ADMIN_REVOKE: (requestId) => `${API_BASE_URL}/access-requests/admin/${requestId}/revoke/`,
};

// ============================================================================
// ⭐ FAVORITES ENDPOINTS
// ============================================================================
export const FAVORITES_ENDPOINTS = {
  CREATE: `${API_BASE_URL}/favorites/`,
  LIST: `${API_BASE_URL}/favorites/`,
  DELETE: (favoriteId) => `${API_BASE_URL}/favorites/${favoriteId}/`,
};

// ============================================================================
// 📊 DASHBOARD ENDPOINTS
// ============================================================================
export const DASHBOARD_ENDPOINTS = {
  DEVELOPER: `${API_BASE_URL}/dashboard/developer/`,
  INVESTOR: `${API_BASE_URL}/dashboard/investor/`,
  ADMIN: `${API_BASE_URL}/dashboard/admin/`,
};

// ============================================================================
// 📋 AUDIT LOGS ENDPOINTS
// ============================================================================
export const AUDIT_ENDPOINTS = {
  ADMIN_LOGS: `${API_BASE_URL}/audit/admin/audit-logs/`,
};

// ============================================================================
// 🔔 NOTIFICATIONS ENDPOINTS
// ============================================================================
export const NOTIFICATIONS_ENDPOINTS = {
  LIST: `${API_BASE_URL}/notifications/`,
  MARK_READ: (notificationId) => `${API_BASE_URL}/notifications/${notificationId}/`,
  DELETE: (notificationId) => `${API_BASE_URL}/notifications/${notificationId}/`,
};

// ============================================================================
// 🛠️ API UTILITY FUNCTIONS
// ============================================================================

/**
 * Get authorization header with access token
 * @returns {Object} Headers object with Authorization
 */
export const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
};

/**
 * Generic API request wrapper
 * @param {string} url - API endpoint
 * @param {string} method - HTTP method (GET, POST, PATCH, DELETE)
 * @param {Object} data - Request body (optional)
 * @returns {Promise<Object>} Response data
 */
export const apiRequest = async (url, method = 'GET', data = null) => {
  const options = {
    method,
    headers: getAuthHeaders(),
  };

  if (data) {
    options.body = JSON.stringify(data);
  }

  const response = await fetch(url, options);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json();
};

// ============================================================================
// ❌ COMMON ERRORS & SOLUTIONS
// ============================================================================

/*
1. 405 Method Not Allowed
   ❌ WRONG: GET /investments/initiate/ (should be POST)
   ✅ CORRECT: POST /investments/initiate/
   
2. 404 Not Found
   ❌ WRONG: GET /audit-logs/ (missing path)
   ✅ CORRECT: GET /audit/admin/audit-logs/
   
   ❌ WRONG: GET /investments/portfolio/ (missing /summary/)
   ✅ CORRECT: GET /investments/portfolio/summary/
   
   ❌ WRONG: GET /projects/pending/ (missing /admin/projects/)
   ✅ CORRECT: GET /projects/admin/projects/pending/

3. 403 Forbidden
   ❌ WRONG: Missing Authorization header
   ✅ CORRECT: Include "Authorization: Bearer <token>" in headers
   
4. 400 Bad Request
   ❌ WRONG: Missing required fields in request body
   ✅ CORRECT: Include all required fields per API documentation
*/

// ============================================================================
// 📝 EXAMPLE USAGE IN REACT
// ============================================================================

/*
// Example 1: Initiate Investment
import { INVESTMENTS_ENDPOINTS, apiRequest } from './api-client';

const investmentData = {
  project_id: '71b7d9e6-f29a-46e0-9899-f0dd317403a7',
  shares_requested: 5,
  idempotency_key: 'inv-unique-key-001'
};

try {
  const response = await apiRequest(
    INVESTMENTS_ENDPOINTS.INITIATE,
    'POST',
    investmentData
  );
  console.log('Investment initiated:', response);
} catch (error) {
  console.error('Error:', error.message);
}

// Example 2: Get Portfolio Summary
try {
  const portfolio = await apiRequest(
    INVESTMENTS_ENDPOINTS.PORTFOLIO_SUMMARY,
    'GET'
  );
  console.log('Portfolio:', portfolio);
} catch (error) {
  console.error('Error:', error.message);
}

// Example 3: Get Admin Audit Logs
try {
  const logs = await apiRequest(
    AUDIT_ENDPOINTS.ADMIN_LOGS,
    'GET'
  );
  console.log('Audit logs:', logs);
} catch (error) {
  console.error('Error:', error.message);
}
*/
