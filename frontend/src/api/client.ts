import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// Request interceptor — attach JWT and org context
apiClient.interceptors.request.use((config) => {
  const authData = localStorage.getItem('taskforge-auth');
  if (authData) {
    try {
      const parsed = JSON.parse(authData);
      const token = parsed?.state?.accessToken;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch {}
  }

  const orgData = localStorage.getItem('taskforge-org');
  if (orgData) {
    try {
      const parsed = JSON.parse(orgData);
      const orgId = parsed?.state?.currentOrg?.id;
      if (orgId) {
        config.headers['X-Org-ID'] = orgId;
      }
    } catch {}
  }

  return config;
});

// Response interceptor — handle 401 for token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const authData = localStorage.getItem('taskforge-auth');
        if (authData) {
          const parsed = JSON.parse(authData);
          const refreshToken = parsed?.state?.refreshToken;

          if (refreshToken) {
            const response = await axios.post(`${API_BASE}/auth/refresh`, {
              refresh_token: refreshToken,
            });

            const { access_token, refresh_token } = response.data;

            // Update store
            const updatedState = {
              ...parsed,
              state: {
                ...parsed.state,
                accessToken: access_token,
                refreshToken: refresh_token,
              },
            };
            localStorage.setItem('taskforge-auth', JSON.stringify(updatedState));

            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return apiClient(originalRequest);
          }
        }
      } catch {
        // Refresh failed — clear auth and redirect
        localStorage.removeItem('taskforge-auth');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
