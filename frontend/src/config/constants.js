// Application constants
export const APP_CONFIG = {
  name: import.meta.env.VITE_APP_NAME || 'IEEE Paper Generator',
  maxFileSize: parseInt(import.meta.env.VITE_MAX_FILE_SIZE) || 10 * 1024 * 1024, // 10MB
  allowedFileTypes: import.meta.env.VITE_ALLOWED_FILE_TYPES?.split(',') || ['.pdf', '.docx'],
};

// IEEE Paper sections
export const IEEE_SECTIONS = [
  'Abstract',
  'Introduction',
  'Literature Review',
  'Methodology',
  'Results',
  'Discussion',
  'Conclusion',
  'References',
];

// File validation
export const FILE_VALIDATION = {
  maxSize: APP_CONFIG.maxFileSize,
  allowedTypes: APP_CONFIG.allowedFileTypes,
  maxFiles: 10,
};

// API status codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
};

// UI constants
export const UI_CONSTANTS = {
  debounceDelay: 300,
  toastDuration: 3000,
  loadingTimeout: 30000,
};