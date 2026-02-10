import { useCallback, useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  addBatchFile,
  updateBatchFileStatus,
  updateBatchFileProgress,
  setBatchFileAnalysisId,
  setBatchFileError,
  setSelectedBatchFile,
  removeBatchFile,
  setCurrentAnalysis,
  setComplete,
  setFile,
  startUpload,
  setProgress,
  setAnalysisId,
  setSettings,
} from '@/store/slices/analysisSlice';
import { setBatchProcessing } from '@/store/slices/uiSlice';
import type { AudioAnalysisAPI } from '@/api/client';
import { ProgressWebSocket, type ProgressMessage } from '@/api/websocket';
import type { AnalysisResponse } from '@/api/types';
import type { AnalysisSettings, BatchFileState } from '@/store/types';

export function useBatchAnalysis(apiClient: AudioAnalysisAPI | null) {
  const dispatch = useAppDispatch();
  const batchFiles = useAppSelector((s) => s.analysis.batchFiles);
  const selectedBatchFileId = useAppSelector((s) => s.analysis.selectedBatchFileId);
  const isBatchProcessing = useAppSelector((s) => s.ui.batchProcessing);
  const batchProcessingRef = useRef(false);
  const batchFileObjectsRef = useRef<Map<string, File>>(new Map());
  const batchFilesRef = useRef<BatchFileState[]>(batchFiles);
  const selectedBatchFileIdRef = useRef<string | null>(selectedBatchFileId);
  const batchResultsRef = useRef<Map<string, AnalysisResponse>>(new Map());

  useEffect(() => {
    batchFilesRef.current = batchFiles;
  }, [batchFiles]);

  useEffect(() => {
    selectedBatchFileIdRef.current = selectedBatchFileId;
  }, [selectedBatchFileId]);

  const showFileProgressInMainPane = useCallback(
    (file: BatchFileState) => {
      dispatch(setFile({
        name: file.fileName,
        path: file.filePath,
        size: 0,
      }));
      dispatch(startUpload());
      dispatch(setProgress({ percent: file.progress }));
      if (file.analysisId) {
        dispatch(setAnalysisId(file.analysisId));
      }
    },
    [dispatch]
  );

  const applyCompletedResults = useCallback(
    (results: AnalysisResponse) => {
      dispatch(setCurrentAnalysis(results));
      dispatch(setComplete(results));
    },
    [dispatch]
  );

  const addFilesToBatch = useCallback(
    (files: Array<{ id: string; file: File | null; fileName: string; filePath: string }>) => {
      for (const f of files) {
        if (f.file) {
          batchFileObjectsRef.current.set(f.id, f.file);
        }
        dispatch(addBatchFile({
          id: f.id,
          fileName: f.fileName,
          filePath: f.filePath,
          status: 'pending',
          analysisId: null,
          progress: 0,
          error: null,
        }));
      }
    },
    [dispatch]
  );

  const processBatch = useCallback(
    async (files: BatchFileState[], settings: AnalysisSettings) => {
      if (!apiClient || batchProcessingRef.current) return;

      const firstPendingFile = files.find((f) => f.status === 'pending');
      if (!firstPendingFile) return;

      batchProcessingRef.current = true;
      dispatch(setBatchProcessing(true));
      dispatch(setSettings(settings));
      selectedBatchFileIdRef.current = firstPendingFile.id;
      dispatch(setSelectedBatchFile(firstPendingFile.id));
      showFileProgressInMainPane(firstPendingFile);

      let completedFileToSelect = files.find((f) => f.status === 'complete')?.id ?? null;

      for (const batchFile of files) {
        if (batchFile.status === 'complete') continue;

        selectedBatchFileIdRef.current = batchFile.id;
        dispatch(setSelectedBatchFile(batchFile.id));
        showFileProgressInMainPane(batchFile);
        dispatch(updateBatchFileStatus({ id: batchFile.id, status: 'analyzing' }));
        dispatch(updateBatchFileProgress({ id: batchFile.id, progress: 0 }));
        dispatch(setProgress({ percent: 0 }));

        try {
          let file: File | undefined = batchFileObjectsRef.current.get(batchFile.id) ?? undefined;

          if (!file && batchFile.filePath) {
            const arrayBuffer = await window.electron.readFileBytes(batchFile.filePath);
            if (!arrayBuffer) {
              throw new Error('Failed to read file from disk');
            }
            const blob = new Blob([arrayBuffer], { type: 'audio/wav' });
            file = new File([blob], batchFile.fileName, { type: 'audio/wav' });
          }

          if (!file) {
            throw new Error('No file data available');
          }

          const { analysis_id } = await apiClient.uploadAndAnalyze(file, {
            genre: settings.genre,
            recommendationLevel: settings.recommendationLevel,
          });

          dispatch(setBatchFileAnalysisId({ id: batchFile.id, analysisId: analysis_id }));
          if (selectedBatchFileIdRef.current === batchFile.id) {
            dispatch(setAnalysisId(analysis_id));
          }

          await new Promise<void>((resolve, reject) => {
            const ws = new ProgressWebSocket(apiClient.getBaseUrl(), analysis_id);

            ws.connect((message: ProgressMessage) => {
              if (message.type === 'band_progress') {
                const nextProgress = message.progress ?? 0;
                dispatch(updateBatchFileProgress({
                  id: batchFile.id,
                  progress: nextProgress,
                }));
                if (selectedBatchFileIdRef.current === batchFile.id) {
                  dispatch(setProgress({ percent: nextProgress, band: message.band }));
                }
              } else if (message.type === 'complete') {
                ws.disconnect();
                dispatch(updateBatchFileStatus({ id: batchFile.id, status: 'complete' }));
                dispatch(updateBatchFileProgress({ id: batchFile.id, progress: 100 }));
                if (selectedBatchFileIdRef.current === batchFile.id) {
                  dispatch(setProgress({ percent: 100 }));
                }
                resolve();
              } else if (message.type === 'error') {
                ws.disconnect();
                reject(new Error(message.status || message.message || 'Analysis failed'));
              }
            });

            ws.onError(() => {
              reject(new Error('Connection lost during analysis'));
            });
          });

          const results = await apiClient.getAnalysisResults(analysis_id);
          batchResultsRef.current.set(batchFile.id, results);
          if (!completedFileToSelect) {
            completedFileToSelect = batchFile.id;
          }
          if (selectedBatchFileIdRef.current === batchFile.id) {
            applyCompletedResults(results);
          }

          batchFileObjectsRef.current.delete(batchFile.id);
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : 'Analysis failed';
          dispatch(setBatchFileError({ id: batchFile.id, error: errorMsg }));
          continue;
        }
      }

      batchProcessingRef.current = false;
      dispatch(setBatchProcessing(false));

      if (completedFileToSelect) {
        selectedBatchFileIdRef.current = completedFileToSelect;
        dispatch(setSelectedBatchFile(completedFileToSelect));
        const cachedResults = batchResultsRef.current.get(completedFileToSelect);
        if (cachedResults) {
          applyCompletedResults(cachedResults);
        } else {
          const completedFile = batchFilesRef.current.find((f) => f.id === completedFileToSelect);
          if (completedFile?.analysisId) {
            try {
              const results = await apiClient.getAnalysisResults(completedFile.analysisId);
              batchResultsRef.current.set(completedFile.id, results);
              applyCompletedResults(results);
            } catch (err) {
              console.error('Failed to fetch analysis for default completed file:', err);
            }
          }
        }
      }
    },
    [apiClient, dispatch, applyCompletedResults, showFileProgressInMainPane]
  );

  const switchToFile = useCallback(
    async (fileId: string) => {
      if (!apiClient) return;

      const file = batchFilesRef.current.find((f) => f.id === fileId);
      if (!file) return;

      if (file?.status === 'complete' && file.analysisId) {
        const cachedResults = batchResultsRef.current.get(file.id);
        if (cachedResults) {
          applyCompletedResults(cachedResults);
          return;
        }

        try {
          const results = await apiClient.getAnalysisResults(file.analysisId);
          batchResultsRef.current.set(file.id, results);
          applyCompletedResults(results);
        } catch (err) {
          console.error('Failed to fetch analysis for file:', err);
        }
      } else if (
        (batchProcessingRef.current || isBatchProcessing) &&
        (file.status === 'pending' || file.status === 'analyzing')
      ) {
        showFileProgressInMainPane(file);
      }
    },
    [apiClient, applyCompletedResults, isBatchProcessing, showFileProgressInMainPane]
  );

  const removeFile = useCallback(
    (fileId: string) => {
      batchFileObjectsRef.current.delete(fileId);
      batchResultsRef.current.delete(fileId);
      dispatch(removeBatchFile(fileId));
    },
    [dispatch]
  );

  const batchProgress = {
    total: batchFiles.length,
    completed: batchFiles.filter((f) => f.status === 'complete').length,
    failed: batchFiles.filter((f) => f.status === 'error').length,
    processing: batchProcessingRef.current,
  };

  return {
    addFilesToBatch,
    processBatch,
    switchToFile,
    removeFile,
    batchProgress,
    batchFileObjects: batchFileObjectsRef,
  };
}
