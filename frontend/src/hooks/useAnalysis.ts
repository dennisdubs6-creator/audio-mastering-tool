import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store';
import {
  setFile,
  setSettings,
  startUpload,
  setAnalysisId,
  setProgress,
  setComplete,
  setError,
  clearAnalysis,
} from '@/store/slices/analysisSlice';
import type { AudioAnalysisAPI } from '@/api/client';
import { ProgressWebSocket, type ProgressMessage } from '@/api/websocket';
import type { AnalysisSettings, FileInfo } from '@/store/types';

let activeWs: ProgressWebSocket | null = null;

export function useAnalysis(apiClient: AudioAnalysisAPI | null) {
  const dispatch = useAppDispatch();
  const state = useAppSelector((s) => s.analysis);

  const autoSaveCurrentAnalysis = useCallback(() => {
    if (state.currentAnalysis && state.analysisId) {
      console.log(`[useAnalysis] Auto-saving current analysis ${state.analysisId} before new analysis`);
    }
  }, [state.currentAnalysis, state.analysisId]);

  const selectFile = useCallback(
    (fileInfo: FileInfo) => {
      dispatch(setFile(fileInfo));
    },
    [dispatch]
  );

  const startAnalysis = useCallback(
    async (file: File, settings: AnalysisSettings) => {
      if (!apiClient) return;

      autoSaveCurrentAnalysis();

      dispatch(setSettings(settings));
      dispatch(startUpload());

      try {
        const { analysis_id } = await apiClient.uploadAndAnalyze(file, {
          genre: settings.genre,
          recommendationLevel: settings.recommendationLevel,
        });

        dispatch(setAnalysisId(analysis_id));

        // Connect WebSocket for progress
        const ws = new ProgressWebSocket(apiClient.getBaseUrl(), analysis_id);
        activeWs = ws;

        ws.connect((message: ProgressMessage) => {
          if (message.type === 'band_progress') {
            dispatch(setProgress({ percent: message.progress ?? 0, band: message.band }));
          } else if (message.type === 'complete') {
            ws.disconnect();
            activeWs = null;
            // Fetch full results
            apiClient
              .getAnalysisResults(analysis_id)
              .then((results) => dispatch(setComplete(results)))
              .catch((err) =>
                dispatch(setError(err instanceof Error ? err.message : 'Failed to fetch results'))
              );
          } else if (message.type === 'error') {
            ws.disconnect();
            activeWs = null;
            dispatch(setError(message.status || message.message || 'Analysis failed'));
          }
        });

        ws.onError(() => {
          dispatch(setError('Connection lost during analysis'));
        });
      } catch (err) {
        dispatch(setError(err instanceof Error ? err.message : 'Upload failed'));
      }
    },
    [apiClient, dispatch, autoSaveCurrentAnalysis]
  );

  const cancelAnalysis = useCallback(() => {
    if (activeWs) {
      activeWs.disconnect();
      activeWs = null;
    }
    dispatch(clearAnalysis());
  }, [dispatch]);

  const reset = useCallback(() => {
    autoSaveCurrentAnalysis();
    if (activeWs) {
      activeWs.disconnect();
      activeWs = null;
    }
    dispatch(clearAnalysis());
  }, [dispatch, autoSaveCurrentAnalysis]);

  return {
    state,
    selectFile,
    startAnalysis,
    cancelAnalysis,
    reset,
    autoSaveCurrentAnalysis,
  };
}
