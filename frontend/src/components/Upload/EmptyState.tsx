import React, { useState, useCallback } from 'react';
import DropZone from './DropZone';
import UploadButton from './UploadButton';
import FileValidatorError, { validateFile } from './FileValidator';

interface EmptyStateProps {
  onFileAccepted: (file: File) => void;
  onFilesAccepted?: (files: File[]) => void;
  onElectronFileSelected: (filePath: string) => void;
  onElectronFilesSelected?: (filePaths: string[]) => void;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  onFileAccepted,
  onFilesAccepted,
  onElectronFileSelected,
  onElectronFilesSelected,
}) => {
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleFileDrop = useCallback(
    (file: File) => {
      const result = validateFile(file);
      if (result.valid) {
        setValidationError(null);
        onFileAccepted(file);
      } else {
        setValidationError(result.error || 'Invalid file');
      }
    },
    [onFileAccepted]
  );

  const handleFilesDrop = useCallback(
    (files: File[]) => {
      const validFiles: File[] = [];
      const errors: string[] = [];

      for (const file of files) {
        const result = validateFile(file);
        if (result.valid) {
          validFiles.push(file);
        } else {
          errors.push(`${file.name}: ${result.error}`);
        }
      }

      if (errors.length > 0) {
        setValidationError(errors.join('; '));
      } else {
        setValidationError(null);
      }

      if (validFiles.length > 0) {
        if (onFilesAccepted) {
          onFilesAccepted(validFiles);
        } else {
          onFileAccepted(validFiles[0]);
        }
      }
    },
    [onFileAccepted, onFilesAccepted]
  );

  const handleClear = () => {
    setValidationError(null);
  };

  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <DropZone onFileSelected={handleFileDrop} onFilesSelected={handleFilesDrop}>
        <div className="flex flex-col items-center gap-4 py-16 px-8">
          <svg
            className="w-16 h-16 text-slate-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
            />
          </svg>
          <h2 className="text-xl font-semibold text-slate-300">Analyze Your Track</h2>
          <p className="text-sm text-slate-500 max-w-sm">
            Drag and drop WAV files or click to browse. Multiple files supported. WAV files only, up to 500 MB each.
          </p>
          <UploadButton
            onFileSelected={onElectronFileSelected}
            onFilesSelected={onElectronFilesSelected}
            multiple={true}
          />
        </div>
      </DropZone>

      {validationError && (
        <FileValidatorError error={validationError} onClear={handleClear} />
      )}
    </div>
  );
};

export default EmptyState;
