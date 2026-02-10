import React from 'react';

interface ErrorMessageProps {
  message: string;
  errorType?: 'validation' | 'network' | 'analysis' | 'unknown';
  onRetry?: () => void;
}

const errorTypeMessages: Record<string, string> = {
  validation: 'The file could not be validated.',
  network: 'A network error occurred. Please check your connection.',
  analysis: 'The analysis encountered an error.',
  unknown: 'An unexpected error occurred.',
};

const ErrorMessageComponent: React.FC<ErrorMessageProps> = ({
  message,
  errorType = 'unknown',
  onRetry,
}) => {
  return (
    <div className="flex flex-col items-center gap-3 p-4">
      <svg
        className="w-8 h-8 text-red-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p className="text-sm text-slate-300">{message}</p>
      <p className="text-xs text-slate-500">{errorTypeMessages[errorType]}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded-md transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  );
};

export default ErrorMessageComponent;
