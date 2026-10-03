import api, { API_BASE_URL } from './api';

export const reportService = {
  async generateReport(scanId, compareWith = null) {
    const payload = compareWith ? { compare_with: compareWith } : {};
    const response = await api.post(`/reports/${scanId}/generate`, payload);
    return response.data;
  },

  getViewReportUrl(scanId) {
    return `${API_BASE_URL}/reports/${scanId}`;
  },

  getDownloadReportUrl(scanId) {
    return `${API_BASE_URL}/reports/${scanId}/download`;
  },
};
