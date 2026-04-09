import axios from 'axios';

// Use hostname from window to handle localhost/127.0.0.1/IP mismatches
const BASE_HOST = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
export const BASE_URL = import.meta.env.VITE_API_URL || `http://${BASE_HOST}:8001`;
const BASE = BASE_URL;

const api = axios.create({ baseURL: BASE });

// Attach JWT on every request
api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// ------------------------------------------------------------------
// Auth
// ------------------------------------------------------------------
export const authApi = {
  register: (email: string, password: string, role = 'viewer') =>
    api.post('/api/auth/register', { email, password, role }),
  login: (email: string, password: string) =>
    api.post<{ access_token: string; role: string; email: string }>(
      '/api/auth/login', { email, password }
    ),
  sendOtp: (email: string) => api.post('/api/auth/otp/send', { email }),
  verifyOtp: (email: string, otp: string) =>
    api.post<{ access_token: string; role: string; email: string }>(
      '/api/auth/otp/verify', { email, otp }
    ),
  me: () => api.get('/api/auth/me'),
};

// ------------------------------------------------------------------
// Stats
// ------------------------------------------------------------------
export const statsApi = {
  get: () => api.get('/api/stats'),
  cameras: () => api.get('/api/stats/cameras'),
};

// ------------------------------------------------------------------
// Violations
// ------------------------------------------------------------------
export const violationsApi = {
  list: (params: Record<string, unknown> = {}) =>
    api.get('/api/violations', { params }),
  get: (id: number) => api.get(`/api/violations/${id}`),
  delete: (id: number) => api.delete(`/api/violations/${id}`),
};

// ------------------------------------------------------------------
// Cameras
// ------------------------------------------------------------------
export const camerasApi = {
  list: () => api.get('/api/cameras'),
  add: (camera_id: string, source: string) =>
    api.post('/api/cameras', { camera_id, source }),
  remove: (id: string) => api.delete(`/api/cameras/${id}`),
};

// ------------------------------------------------------------------
// Alerts
// ------------------------------------------------------------------
export const alertsApi = {
  recent: () => api.get('/api/alerts/recent'),
};

export default api;
