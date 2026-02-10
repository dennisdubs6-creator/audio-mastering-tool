import { useState, useCallback } from 'react';
import { validateFile } from '@/components/Upload/FileValidator';
import type { FileInfo } from '@/store/types';

interface UseFileUploadReturn {
  file: FileInfo | null;
  error: string | null;
  handleDrop: (droppedFile: File) => void;
  handleFileSelect: (filePath: string) => void;
  clearFile: () => void;
}

export function useFileUpload(): UseFileUploadReturn {
  const [file, setFile] = useState<FileInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDrop = useCallback((droppedFile: File) => {
    const result = validateFile(droppedFile);
    if (result.valid) {
      setFile({
        name: droppedFile.name,
        path: '',
        size: droppedFile.size,
      });
      setError(null);
    } else {
      setError(result.error || 'Invalid file');
    }
  }, []);

  const handleFileSelect = useCallback((filePath: string) => {
    const name = filePath.split(/[/\\]/).pop() || filePath;
    setFile({ name, path: filePath, size: 0 });
    setError(null);
  }, []);

  const clearFile = useCallback(() => {
    setFile(null);
    setError(null);
  }, []);

  return { file, error, handleDrop, handleFileSelect, clearFile };
}
