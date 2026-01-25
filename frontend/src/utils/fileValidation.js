import { FILE_VALIDATION } from '../config/constants';

/**
 * Validate uploaded files
 * @param {FileList} files - Files to validate
 * @returns {Object} - Validation result with valid files and errors
 */
export const validateFiles = (files) => {
  const validFiles = [];
  const errors = [];

  // Check if files exist
  if (!files || files.length === 0) {
    errors.push('No files selected');
    return { validFiles, errors };
  }

  // Check file count
  if (files.length > FILE_VALIDATION.maxFiles) {
    errors.push(`Maximum ${FILE_VALIDATION.maxFiles} files allowed`);
    return { validFiles, errors };
  }

  // Validate each file
  Array.from(files).forEach((file, index) => {
    const fileErrors = [];

    // Check file size
    if (file.size > FILE_VALIDATION.maxSize) {
      fileErrors.push(`File "${file.name}" is too large (max ${formatFileSize(FILE_VALIDATION.maxSize)})`);
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    if (!FILE_VALIDATION.allowedTypes.includes(fileExtension)) {
      fileErrors.push(`File "${file.name}" has unsupported format. Allowed: ${FILE_VALIDATION.allowedTypes.join(', ')}`);
    }

    // Check file name
    if (file.name.length > 255) {
      fileErrors.push(`File "${file.name}" name is too long`);
    }

    if (fileErrors.length === 0) {
      validFiles.push(file);
    } else {
      errors.push(...fileErrors);
    }
  });

  return { validFiles, errors };
};

/**
 * Format file size in human readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} - Formatted file size
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Get file type icon based on extension
 * @param {string} filename - File name
 * @returns {string} - Icon name
 */
export const getFileIcon = (filename) => {
  const extension = filename.split('.').pop().toLowerCase();
  
  switch (extension) {
    case 'pdf':
      return 'file-text';
    case 'docx':
    case 'doc':
      return 'file-text';
    default:
      return 'file';
  }
};