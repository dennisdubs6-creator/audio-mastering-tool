import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ message }) => {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4">
      <div className="w-10 h-10 border-4 border-slate-600 border-t-blue-500 rounded-full animate-spin" />
      {message && <p className="text-sm text-slate-400">{message}</p>}
    </div>
  );
};

export default LoadingSpinner;
