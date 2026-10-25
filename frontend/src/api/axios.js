import axios from 'axios';

function resolveApiBase() {
  const configured = import.meta.env.VITE_API_URL;
  if (import.meta.env.PROD) {
    if (!configured || configured.includes('localhost')) return '/api';
    return configured;
  }
  return configured || '/api';
}

const API_BASE = resolveApiBase();

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
export const getJapaneseLevel = () => api.get('/profile/japanese-level');
export const updateJapaneseLevel = (japanese_level) =>
  api.put('/profile/japanese-level', { japanese_level });
export const getLearningSkills = () => api.get('/learning/skills');
export const getLearningResources = (skill) => api.get('/learning/resources', { params: { skill } });
export const getLearningPlans = () => api.get('/learning/plans');
export const getLearningPlan = (id) => api.get(`/learning/plans/${id}`);
export const createLearningPlan = (data) => api.post('/learning/plans', data);
export const updateLearningTask = (planId, taskId, done) =>
  api.patch(`/learning/plans/${planId}/tasks/${taskId}`, { done });

export async function openResumeFile() {
  try {
    const response = await api.get('/resume/file', { responseType: 'blob' });
    const type = response.headers['content-type'] || 'application/octet-stream';
    const blob = new Blob([response.data], { type });
    const url = URL.createObjectURL(blob);
    const opened = window.open(url, '_blank', 'noopener,noreferrer');
    if (!opened) {
      const link = document.createElement('a');
      link.href = url;
      link.download = type.includes('pdf') ? 'cv.pdf' : 'cv.docx';
      link.click();
    }
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
  } catch (err) {
    let detail = 'Could not open the original CV file.';
    const data = err.response?.data;
    if (data instanceof Blob) {
      try {
        const parsed = JSON.parse(await data.text());
        if (typeof parsed.detail === 'string') detail = parsed.detail;
      } catch {
        /* keep the fallback message */
      }
    } else if (typeof data?.detail === 'string') {
      detail = data.detail;
    }
    throw new Error(detail);
  }
}

// Jobs
export const searchJobs = (data) => api.post('/search-jobs', data);
export const getJobs = () => api.get('/jobs');
export const getJob = (id) => api.get(`/jobs/${id}`);
export const translateJobPage = (id, language) =>
  api.post(`/jobs/${id}/translate`, { language });
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
