import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 — redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || '';
      if (url.includes('/auth/login') || url.includes('/auth/google')) {
        return Promise.reject(error);
      }
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const register = (data) => api.post('/auth/register', data);
export const login = (data) => api.post('/auth/login', data);
export const loginGoogle = (access_token) => api.post('/auth/google', { access_token });
export const getMe = () => api.get('/auth/me');

// Resume
export const uploadResume = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post('/upload-resume', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};
export const getResume = () => api.get('/resume');

// Jobs
export const searchJobs = (data) => api.post('/search-jobs', data);
export const getJobs = () => api.get('/jobs');
export const getJob = (id) => api.get(`/jobs/${id}`);
export const toggleFavorite = (id) => api.post(`/jobs/${id}/favorite`);
export const getSearchHistory = () => api.get('/search-history');

// Analysis
export const analyzeJob = (id) => api.post(`/analyze-job/${id}`);
export const analyzeAllJobs = () => api.post('/analyze-all');
export const reanalyzeJob = (id) => api.post(`/reanalyze-job/${id}`);
export const getRankedJobs = (params) => api.get('/ranked-jobs', { params });
export const getSkillsGap = () => api.get('/skills-gap');
export const exportReport = () => api.get('/export-report');

export default api;
