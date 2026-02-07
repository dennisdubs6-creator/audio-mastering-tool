import React, { useEffect, useState } from 'react';
import { AudioAnalysisAPI } from '@/api/client';
import Header from '@/components/Layout/Header';
import Sidebar from '@/components/Layout/Sidebar';
import MainContent from '@/components/Layout/MainContent';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import Button from '@/components/common/Button';

type ConnectionState = 'connecting' | 'ready' | 'error';

declare global {
  interface Window {
    electron: {
      getBackendPort: () => Promise<number | null>;
      selectFile: () => Promise<string | null>;
      restartBackend: () => Promise<number | null>;
    };
  }
}

const App: React.FC = () => {
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [apiClient, setApiClient] = useState<AudioAnalysisAPI | null>(null);

  const connectToBackend = async () => {
    setConnectionState('connecting');
    setErrorMessage('');

    try {
      const port = await window.electron.getBackendPort();

      if (!port) {
        setConnectionState('error');
        setErrorMessage(
          'Backend failed to start. Please check that Python 3.10+ is installed and in your PATH.'
        );
        return;
      }

      const baseUrl = `http://127.0.0.1:${port}`;
      const client = new AudioAnalysisAPI(baseUrl);

      console.log(`[App] Connecting to backend at ${baseUrl}`);

      await client.healthCheck();

      setApiClient(client);
      setConnectionState('ready');
      console.log(`[App] Backend connected on port ${port}`);
    } catch (err) {
      console.error('[App] Failed to connect to backend:', err);
      setConnectionState('error');
      setErrorMessage(
        err instanceof Error ? err.message : 'Failed to connect to backend'
      );
    }
  };

  const handleRetry = async () => {
    try {
      const newPort = await window.electron.restartBackend();
      if (newPort === null) {
        setConnectionState('error');
        setErrorMessage('Backend failed to restart. No port was assigned.');
        return;
      }
      console.log(`[App] Backend restarted on port ${newPort}`);
      await connectToBackend();
    } catch (err) {
      console.error('[App] Failed to restart backend:', err);
      setConnectionState('error');
      setErrorMessage(
        err instanceof Error ? err.message : 'Failed to restart backend'
      );
    }
  };

  useEffect(() => {
    connectToBackend();
  }, []);

  if (connectionState === 'connecting') {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-950">
        <LoadingSpinner message="Starting backend..." />
      </div>
    );
  }

  if (connectionState === 'error') {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-4 max-w-md text-center">
          <svg
            className="w-12 h-12 text-red-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
          <h2 className="text-lg font-semibold text-white">Backend Connection Failed</h2>
          <p className="text-sm text-slate-400">{errorMessage}</p>
          <div className="flex gap-3 mt-2">
            <Button variant="primary" onClick={handleRetry}>
              Restart Backend
            </Button>
            <Button variant="secondary" onClick={connectToBackend}>
              Retry Connection
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-950">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <MainContent>
          <div className="flex flex-col items-center justify-center h-full text-center">
            <svg
              className="w-16 h-16 text-slate-600 mb-4"
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
            <h2 className="text-xl font-semibold text-slate-300 mb-2">
              Ready to Analyze
            </h2>
            <p className="text-sm text-slate-500 mb-6 max-w-sm">
              Upload an audio file to begin mastering analysis. Supported formats: WAV, FLAC, MP3,
              AIFF, OGG.
            </p>
            <Button
              variant="primary"
              onClick={async () => {
                const filePath = await window.electron.selectFile();
                if (filePath) {
                  console.log(`[App] Selected file: ${filePath}`);
                  // File handling will be implemented in the analysis feature
                }
              }}
            >
              Select Audio File
            </Button>
            {apiClient && (
              <p className="text-xs text-slate-600 mt-4">
                Backend connected
              </p>
            )}
          </div>
        </MainContent>
      </div>
    </div>
  );
};

export default App;
