import React, { useState, useCallback } from 'react';

interface DropZoneProps {
  onFileSelected: (file: File) => void;
  onFilesSelected?: (files: File[]) => void;
  children: React.ReactNode;
}

const DropZone: React.FC<DropZoneProps> = ({ onFileSelected, onFilesSelected, children }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [dropError, setDropError] = useState<string | null>(null);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      setDropError(null);

      const droppedFiles = Array.from(e.dataTransfer.files);
      if (droppedFiles.length === 0) return;

      const validFiles: File[] = [];
      const invalidFiles: string[] = [];

      for (const file of droppedFiles) {
        if (file.name.toLowerCase().endsWith('.wav')) {
          validFiles.push(file);
        } else {
          invalidFiles.push(file.name);
        }
      }

      if (invalidFiles.length > 0) {
        setDropError(`Only .wav files are accepted. Rejected: ${invalidFiles.join(', ')}`);
      }

      if (validFiles.length === 0) return;

      if (onFilesSelected && validFiles.length > 0) {
        onFilesSelected(validFiles);
      } else if (validFiles.length > 0) {
        onFileSelected(validFiles[0]);
      }
    },
    [onFileSelected, onFilesSelected]
  );

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`flex flex-col items-center justify-center h-full w-full rounded-xl border-2 border-dashed transition-colors ${
        isDragOver
          ? 'border-blue-500 bg-blue-500/10'
          : 'border-slate-700 hover:border-slate-500'
      }`}
    >
      {children}
      {dropError && (
        <p className="mt-2 text-xs text-red-400">{dropError}</p>
      )}
    </div>
  );
};

export default DropZone;
