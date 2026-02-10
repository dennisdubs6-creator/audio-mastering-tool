import { useEffect, useRef, useState } from 'react';
import { ProgressWebSocket, type ProgressMessage } from '@/api/websocket';

interface AnalysisProgressState {
  progress: number;
  currentBand: string | null;
  status: 'connecting' | 'listening' | 'complete' | 'error';
  error: string | null;
}

interface UseAnalysisProgressReturn extends AnalysisProgressState {
  analysisId: string | null;
}

export function useAnalysisProgress(
  baseUrl: string,
  analysisId: string | null
): UseAnalysisProgressReturn {
  const [state, setState] = useState<AnalysisProgressState>({
    progress: 0,
    currentBand: null,
    status: 'connecting',
    error: null,
  });
  const wsRef = useRef<ProgressWebSocket | null>(null);

  useEffect(() => {
    if (!analysisId || !baseUrl) return;

    const ws = new ProgressWebSocket(baseUrl, analysisId);
    wsRef.current = ws;

    ws.connect((message: ProgressMessage) => {
      if (message.type === 'band_progress') {
        setState({
          progress: message.progress ?? 0,
          currentBand: message.band || null,
          status: 'listening',
          error: null,
        });
      } else if (message.type === 'complete') {
        setState({
          progress: 100,
          currentBand: null,
          status: 'complete',
          error: null,
        });
        ws.disconnect();
      } else if (message.type === 'error') {
        setState({
          progress: 0,
          currentBand: null,
          status: 'error',
          error: message.status || message.message || 'Analysis failed',
        });
        ws.disconnect();
      }
    });

    ws.onError(() => {
      setState((prev) => ({
        ...prev,
        status: 'error',
        error: 'WebSocket connection error',
      }));
    });

    return () => {
      ws.disconnect();
      wsRef.current = null;
    };
  }, [baseUrl, analysisId]);

  return { ...state, analysisId };
}
