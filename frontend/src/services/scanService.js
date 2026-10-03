import api, { API_BASE_URL } from './api';

export const scanService = {
  async listScans(targetId = null) {
    const params = targetId ? { target_id: targetId } : {};
    const response = await api.get('/scans', { params });
    return response.data;
  },

  async getScan(id) {
    const response = await api.get(`/scans/${id}`);
    return response.data;
  },

  async getScanStatus(id) {
    const response = await api.get(`/scans/${id}/status`);
    return response.data;
  },

  async createScan(targetId, profile = 'standard') {
    const response = await api.post('/scans', {
      target_id: targetId,
      profile,
    });
    return response.data;
  },

  async cancelScan(id) {
    const response = await api.post(`/scans/${id}/cancel`);
    return response.data;
  },

  async getScanHosts(id) {
    const response = await api.get(`/scans/${id}/hosts`);
    return response.data;
  },

  async getScanPorts(id) {
    const response = await api.get(`/scans/${id}/ports`);
    return response.data;
  },

  async getScanServices(id) {
    const response = await api.get(`/scans/${id}/services`);
    return response.data;
  },

  async getScanDNS(id) {
    const response = await api.get(`/scans/${id}/dns`);
    return response.data;
  },

  async getScanRecon(id) {
    const response = await api.get(`/scans/${id}/recon`);
    return response.data;
  },

  async getScanFindings(id, filters = {}) {
    const response = await api.get(`/scans/${id}/findings`, { params: filters });
    return response.data;
  },

  getRawXmlUrl(id) {
    return `${API_BASE_URL}/scans/${id}/raw`;
  },

  async compareScans(scan1Id, scan2Id) {
    const response = await api.get(`/scans/compare/${scan1Id}/${scan2Id}`);
    return response.data;
  },
};
