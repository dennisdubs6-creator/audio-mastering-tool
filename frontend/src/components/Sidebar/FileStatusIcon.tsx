import React from 'react';
import type { BatchFileStatus } from '@/store/types';

interface FileStatusIconProps {
  status: BatchFileStatus;
}

const FileStatusIcon: React.FC<FileStatusIconProps> = ({ status }) => {
  switch (status) {
    case 'pending':
      return (
        <svg className="w-4 h-4 text-gray-500 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="8" />
        </svg>
      );
    case 'analyzing':
      return (
        <svg className="w-4 h-4 text-blue-500 flex-shrink-0 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
      );
    case 'complete':
      return (
        <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      );
    case 'error':
      return (
        <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      );
  }
};

export default FileStatusIcon;
