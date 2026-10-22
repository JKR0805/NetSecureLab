import api from './api';

const TOKEN_KEY = 'netsecurelab_token';
const USER_KEY = 'netsecurelab_user';

export const authService = {
  async login(username, password) {
    const res = await api.post('/auth/login', { username, password });
    if (res.data?.access_token) {
      localStorage.setItem(TOKEN_KEY, res.data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(res.data.user));
    }
    return res.data;
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },

  getUser() {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  },

  async fetchMe() {
    const res = await api.get('/auth/me');
    if (res.data) {
      localStorage.setItem(USER_KEY, JSON.stringify(res.data));
    }
    return res.data;
  },
};
