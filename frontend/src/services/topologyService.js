import api from './api';

export const topologyService = {
  async getTopology(targetId = null) {
    const url = targetId ? `/topology?target_id=${targetId}` : '/topology';
    const response = await api.get(url);
    return response.data;
  },
};
