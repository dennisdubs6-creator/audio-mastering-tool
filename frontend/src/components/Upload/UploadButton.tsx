import React from 'react';
import Button from '@/components/common/Button';

interface UploadButtonProps {
  onFileSelected: (filePath: string) => void;
  onFilesSelected?: (filePaths: string[]) => void;
  multiple?: boolean;
}

const UploadButton: React.FC<UploadButtonProps> = ({ onFileSelected, onFilesSelected, multiple = false }) => {
  const handleClick = async () => {
    if (multiple) {
      const filePaths = await window.electron.selectFiles();
      if (filePaths && filePaths.length > 0) {
        if (onFilesSelected) {
          onFilesSelected(filePaths);
        } else {
          filePaths.forEach((fp) => onFileSelected(fp));
        }
      }
    } else {
      const filePath = await window.electron.selectFile();
      if (filePath) {
        onFileSelected(filePath);
      }
    }
  };

  return (
    <Button variant="primary" onClick={handleClick}>
      {multiple ? 'Select WAV Files' : 'Select WAV File'}
    </Button>
  );
};

export default UploadButton;
