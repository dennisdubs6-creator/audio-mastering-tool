import React from 'react';
import type { BatchFileState } from '@/store/types';
import FileStatusIcon from './FileStatusIcon';

interface FileItemProps {
  file: BatchFileState;
  isActive: boolean;
  onClick: (id: string) => void;
  onRemove: (id: string) => void;
}

const FileItem: React.FC<FileItemProps> = ({ file, isActive, onClick, onRemove }) => {
  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRemove(file.id);
  };

  return (
    <li
      onClick={() => onClick(file.id)}
      className={`group flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors ${
        isActive ? 'bg-blue-600/20 border border-blue-500/30' : 'hover:bg-slate-800'
      }`}
    >
      <FileStatusIcon status={file.status} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-200 truncate">{file.fileName}</p>
        <div className="flex items-center gap-2">
          {file.status === 'analyzing' && (
            <div className="flex-1 h-1 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all duration-300"
                style={{ width: `${file.progress}%` }}
              />
            </div>
          )}
          {file.status === 'analyzing' && (
            <span className="text-xs text-blue-400">{file.progress}%</span>
          )}
          {file.status === 'error' && (
            <span className="text-xs text-red-400 truncate">{file.error || 'Failed'}</span>
          )}
        </div>
      </div>
      <button
        onClick={handleRemove}
        className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-slate-700 transition-all"
        title="Remove file"
      >
        <svg className="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </li>
  );
};

export default FileItem;
