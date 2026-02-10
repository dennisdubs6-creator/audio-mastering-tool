import React, { useState } from 'react';
import ProgressBar from './ProgressBar';
import StatusText from './StatusText';
import Button from '@/components/common/Button';
import ConfirmDialog from '@/components/common/ConfirmDialog';

interface ProgressScreenProps {
  fileName: string;
  percent: number;
  currentBand: string | null;
  onCancel: () => void;
}

const ProgressScreen: React.FC<ProgressScreenProps> = ({
  fileName,
  percent,
  currentBand,
  onCancel,
}) => {
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <div className="w-full max-w-md flex flex-col items-center gap-6">
        <svg
          className="w-12 h-12 text-blue-500"
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

        <div className="text-center">
          <h2 className="text-lg font-semibold text-slate-200 mb-1">Analyzing Audio</h2>
          <p className="text-sm text-slate-400 truncate max-w-sm">{fileName}</p>
        </div>

        <div className="w-full">
          <ProgressBar percent={percent} />
        </div>

        <StatusText currentBand={currentBand} percent={percent} />

        <Button variant="secondary" onClick={() => setShowCancelConfirm(true)}>
          Cancel
        </Button>
      </div>

      <ConfirmDialog
        open={showCancelConfirm}
        title="Cancel Analysis?"
        message="Canceling will stop the analysis and discard all progress. This cannot be undone."
        confirmLabel="Cancel Analysis"
        cancelLabel="Continue Analysis"
        onConfirm={() => {
          setShowCancelConfirm(false);
          onCancel();
        }}
        onCancel={() => setShowCancelConfirm(false)}
      />
    </div>
  );
};

export default ProgressScreen;
