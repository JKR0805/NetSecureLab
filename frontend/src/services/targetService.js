import api from './api';

export const targetService = {
  async listTargets() {
    const response = await api.get('/targets');
    return response.data;
  },

  async getTarget(id) {
    const response = await api.get(`/targets/${id}`);
    return response.data;
  },

  async createTarget(payload) {
    const response = await api.post('/targets', payload);
    return response.data;
  },

  async deleteTarget(id) {
    const response = await api.delete(`/targets/${id}`);
    return response.data;
  },

  async updateSchedule(id, payload) {
    const response = await api.patch(`/targets/${id}/schedule`, payload);
    return response.data;
  },
};
