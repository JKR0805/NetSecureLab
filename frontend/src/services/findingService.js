import api from './api';

export const findingService = {
  async listAllFindings(filters = {}) {
    const response = await api.get('/findings', { params: filters });
    return response.data;
  },

  async updateFinding(id, payload) {
    const response = await api.patch(`/findings/${id}`, payload);
    return response.data;
  },

  async exportCsv(filters = {}) {
    const response = await api.get('/findings/export/csv', {
      params: filters,
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'netsecurelab_findings.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async exportJson(filters = {}) {
    const response = await api.get('/findings/export/json', {
      params: filters,
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'netsecurelab_findings.json');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
