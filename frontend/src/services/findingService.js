import api from './api';

export const findingService = {
  async listAllFindings(filters = {}) {
    const response = await api.get('/findings', { params: filters });
    return response.data;
  },
};
