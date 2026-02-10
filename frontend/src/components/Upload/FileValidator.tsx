import React from 'react';
import Button from '@/components/common/Button';

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500 MB

export function validateFile(file: File): ValidationResult {
  const ext = file.name.split('.').pop()?.toLowerCase();
  if (ext !== 'wav') {
    return { valid: false, error: `Unsupported format ".${ext}". Only WAV files are accepted.` };
  }
  if (file.size > MAX_FILE_SIZE) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
    return { valid: false, error: `File is too large (${sizeMB} MB). Maximum size is 500 MB.` };
  }
  return { valid: true };
}

interface FileValidatorErrorProps {
  error: string;
  onClear: () => void;
}

const FileValidatorError: React.FC<FileValidatorErrorProps> = ({ error, onClear }) => {
  return (
    <div className="flex flex-col items-center gap-3 mt-4">
      <div className="flex items-center gap-2 text-red-400">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span className="text-sm">{error}</span>
      </div>
      <Button variant="secondary" onClick={onClear}>
        Try Again
      </Button>
    </div>
  );
};

export default FileValidatorError;
