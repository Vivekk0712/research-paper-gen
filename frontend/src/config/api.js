import axios from 'axios';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout for file uploads
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  // Papers
  createPaper: '/api/papers',
  getPaper: (id) => `/api/papers/${id}`,
  
  // File uploads
  uploadFiles: (paperId) => `/api/papers/${paperId}/upload`,
  
  // Sections
  createSection: (paperId) => `/api/papers/${paperId}/sections`,
  getSections: (paperId) => `/api/papers/${paperId}/sections`,
  
  // Generation
  generateContent: '/api/generate',
  generateCompletePaper: (paperId) => `/api/papers/${paperId}/generate-complete`,
  
  // Metrics
  getPaperMetrics: (paperId) => `/api/papers/${paperId}/metrics`,
  
  // Export
  exportPaper: (paperId) => `/api/papers/${paperId}/export`,
  exportPaperLatex: (paperId) => `/api/papers/${paperId}/export/latex`,
  exportPaperPdf: (paperId) => `/api/papers/${paperId}/export/pdf`,
  
  // LaTeX status
  latexStatus: '/api/latex/status',
};

// API service functions
export const apiService = {
  // Papers
  async createPaper(paperData) {
    const response = await api.post(endpoints.createPaper, paperData);
    return response.data;
  },

  async getPaper(paperId) {
    const response = await api.get(endpoints.getPaper(paperId));
    return response.data;
  },

  // File uploads
  async uploadFiles(paperId, files) {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await api.post(endpoints.uploadFiles(paperId), formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Sections
  async createSection(paperId, sectionData) {
    const response = await api.post(endpoints.createSection(paperId), sectionData);
    return response.data;
  },

  async getSections(paperId) {
    const response = await api.get(endpoints.getSections(paperId));
    return response.data;
  },

  // Generation
  async generateContent(generationRequest) {
    const response = await api.post(endpoints.generateContent, generationRequest);
    return response.data;
  },

  async generateCompletePaper(paperId) {
    const response = await api.post(endpoints.generateCompletePaper(paperId));
    return response.data;
  },

  async getPaperMetrics(paperId) {
    const response = await api.get(endpoints.getPaperMetrics(paperId));
    return response.data;
  },

  // Export
  async exportPaper(paperId) {
    const response = await api.get(endpoints.exportPaper(paperId));
    return response.data;
  },

  async exportPaperLatex(paperId) {
    const response = await api.get(endpoints.exportPaperLatex(paperId));
    return response.data;
  },

  async exportPaperPdf(paperId) {
    const response = await api.get(endpoints.exportPaperPdf(paperId), {
      responseType: 'blob'
    });
    return response.data;
  },

  async getLatexStatus() {
    const response = await api.get(endpoints.latexStatus);
    return response.data;
  },
};

export default api;