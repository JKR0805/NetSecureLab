import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMsg =
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred while contacting backend API';
    console.error(`[API Error] ${error.config?.url}:`, errorMsg);
    return Promise.reject(error);
  }
);

export default api;
export { API_BASE_URL };
