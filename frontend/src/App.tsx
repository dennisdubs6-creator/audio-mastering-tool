import React, { useEffect, useState, useRef, useCallback } from 'react';
import { AudioAnalysisAPI } from '@/api/client';
import Header from '@/components/Layout/Header';
import Sidebar from '@/components/Layout/Sidebar';
import MainContent from '@/components/Layout/MainContent';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import Button from '@/components/common/Button';
import Modal from '@/components/common/Modal';
import ErrorMessage from '@/components/common/ErrorMessage';
import EmptyState from '@/components/Upload/EmptyState';
import SettingsScreen from '@/components/Settings/SettingsScreen';
import ProgressScreen from '@/components/Progress/ProgressScreen';
import DashboardView from '@/components/Dashboard/DashboardView';
import ErrorBoundary from '@/components/ErrorHandling/ErrorBoundary';
import { useAnalysis } from '@/hooks/useAnalysis';
import { useBatchAnalysis } from '@/hooks/useBatchAnalysis';
import { useAppSelector } from '@/store';
import type { AnalysisSettings, FileInfo } from '@/store/types';

type ConnectionState = 'connecting' | 'ready' | 'error';

declare global {
  interface Window {
    electron: {
      getBackendPort: () => Promise<number | null>;
      selectFile: () => Promise<string | null>;
      selectFiles: () => Promise<string[] | null>;
      readFileBytes: (filePath: string) => Promise<ArrayBuffer | null>;
      restartBackend: () => Promise<number | null>;
    };
  }
}

const App: React.FC = () => {
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [apiClient, setApiClient] = useState<AudioAnalysisAPI | null>(null);

  // Track the dropped File object for upload
  const droppedFileRef = useRef<File | null>(null);

  const { state: analysisState, selectFile, startAnalysis, cancelAnalysis, reset } =
    useAnalysis(apiClient);

  const { addFilesToBatch, processBatch, switchToFile } = useBatchAnalysis(apiClient);

  const selectedBatchFileId = useAppSelector((s) => s.analysis.selectedBatchFileId);
  const batchFiles = useAppSelector((s) => s.analysis.batchFiles);
  const isBatchProcessing = useAppSelector((s) => s.ui.batchProcessing);
  const selectedBatchFile = selectedBatchFileId
    ? batchFiles.find((file) => file.id === selectedBatchFileId) ?? null
    : null;

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

  // Switch to file when selectedBatchFileId changes
  useEffect(() => {
    if (selectedBatchFileId) {
      switchToFile(selectedBatchFileId);
    }
  }, [selectedBatchFileId, switchToFile]);

  // --- Handlers for EmptyState ---
  const handleFileAccepted = (file: File) => {
    droppedFileRef.current = file;
    const fileInfo: FileInfo = { name: file.name, path: '', size: file.size };
    selectFile(fileInfo);
  };

  const handleFilesAccepted = useCallback(
    (files: File[]) => {
      const batchEntries = files.map((file) => ({
        id: crypto.randomUUID(),
        file,
        fileName: file.name,
        filePath: '',
      }));
      addFilesToBatch(batchEntries);

      // Also select the first file for single-file flow
      if (files.length === 1) {
        droppedFileRef.current = files[0];
        const fileInfo: FileInfo = { name: files[0].name, path: '', size: files[0].size };
        selectFile(fileInfo);
      }
    },
    [addFilesToBatch, selectFile]
  );

  const handleElectronFileSelected = (filePath: string) => {
    droppedFileRef.current = null;
    const name = filePath.split(/[/\\]/).pop() || filePath;
    const fileInfo: FileInfo = { name, path: filePath, size: 0 };
    selectFile(fileInfo);
  };

  const handleElectronFilesSelected = useCallback(
    (filePaths: string[]) => {
      const batchEntries = filePaths.map((fp) => ({
        id: crypto.randomUUID(),
        file: null,
        fileName: fp.split(/[/\\]/).pop() || fp,
        filePath: fp,
      }));
      addFilesToBatch(batchEntries);

      // Also select the first file for single-file flow
      if (filePaths.length === 1) {
        droppedFileRef.current = null;
        const name = filePaths[0].split(/[/\\]/).pop() || filePaths[0];
        const fileInfo: FileInfo = { name, path: filePaths[0], size: 0 };
        selectFile(fileInfo);
      }
    },
    [addFilesToBatch, selectFile]
  );

  const handleAddFiles = useCallback(() => {
    // Trigger file selection for adding more files to batch
    window.electron.selectFiles().then((filePaths) => {
      if (filePaths && filePaths.length > 0) {
        handleElectronFilesSelected(filePaths);
      }
    });
  }, [handleElectronFilesSelected]);

  // --- Handlers for SettingsScreen ---
  const handleAnalyze = async (settings: AnalysisSettings) => {
    // If batch files exist, process them all
    if (batchFiles.length > 1) {
      await processBatch(batchFiles, settings);
      return;
    }

    const file = droppedFileRef.current;
    if (file) {
      await startAnalysis(file, settings);
    } else if (analysisState.file?.path) {
      // File was selected via Electron dialog — read bytes via IPC
      try {
        const arrayBuffer = await window.electron.readFileBytes(analysisState.file.path);
        if (!arrayBuffer) {
          throw new Error('Failed to read file from disk');
        }
        const blob = new Blob([arrayBuffer], { type: 'audio/wav' });
        const f = new File([blob], analysisState.file.name, { type: 'audio/wav' });
        await startAnalysis(f, settings);
      } catch (err) {
        console.error('[App] Failed to read file via IPC:', err);
        alert(`Could not read file: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
    }
  };

  // --- Connection screens ---
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

  // --- Main app content based on analysis status ---
  const renderContent = () => {
    if (
      isBatchProcessing &&
      selectedBatchFile &&
      (selectedBatchFile.status === 'pending' || selectedBatchFile.status === 'analyzing')
    ) {
      return (
        <ProgressScreen
          fileName={selectedBatchFile.fileName}
          percent={selectedBatchFile.progress}
          currentBand={analysisState.currentBand}
          onCancel={cancelAnalysis}
        />
      );
    }

    switch (analysisState.status) {
      case 'idle':
        return (
          <EmptyState
            onFileAccepted={handleFileAccepted}
            onFilesAccepted={handleFilesAccepted}
            onElectronFileSelected={handleElectronFileSelected}
            onElectronFilesSelected={handleElectronFilesSelected}
          />
        );

      case 'file_selected':
        return (
          <SettingsScreen
            fileName={analysisState.file?.name || 'Unknown file'}
            fileSize={analysisState.file?.size || 0}
            onAnalyze={handleAnalyze}
            onCancel={reset}
          />
        );

      case 'uploading':
      case 'analyzing':
        return (
          <ProgressScreen
            fileName={analysisState.file?.name || 'Unknown file'}
            percent={analysisState.progress}
            currentBand={analysisState.currentBand}
            onCancel={cancelAnalysis}
          />
        );

      case 'completed':
        return (
          <DashboardView
            analysisId={analysisState.analysisId}
            fileName={analysisState.results?.file_name}
            onAnalyzeAnother={reset}
            apiClient={apiClient}
            isBatchFile={batchFiles.length > 1}
          />
        );

      case 'error':
        return null; // Handled by modal below

      default:
        return null;
    }
  };

  return (
    <ErrorBoundary>
      <div className="h-screen w-screen flex flex-col bg-slate-950">
        <Header />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar onAddFiles={handleAddFiles} />
          <MainContent>{renderContent()}</MainContent>
        </div>

        <Modal open={analysisState.status === 'error'} onClose={reset}>
          <ErrorMessage
            message={analysisState.error || 'An unexpected error occurred'}
            onRetry={reset}
          />
        </Modal>
      </div>
    </ErrorBoundary>
  );
};

export default App;
