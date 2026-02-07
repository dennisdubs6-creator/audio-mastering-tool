export interface ProgressMessage {
  type: 'progress' | 'complete' | 'error';
  progress: number;
  step?: string;
  message?: string;
  error?: string;
}

export type ProgressCallback = (message: ProgressMessage) => void;
export type ErrorCallback = (error: Event | Error) => void;
export type CloseCallback = (event: CloseEvent) => void;

export class ProgressWebSocket {
  private ws: WebSocket | null = null;
  private baseUrl: string;
  private analysisId: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectDelay = 1000;
  private onProgressCallback: ProgressCallback | null = null;
  private onErrorCallback: ErrorCallback | null = null;
  private onCloseCallback: CloseCallback | null = null;

  constructor(baseUrl: string, analysisId: string) {
    // Convert http:// to ws://
    this.baseUrl = baseUrl.replace(/^http/, 'ws');
    this.analysisId = analysisId;
  }

  connect(onProgress: ProgressCallback): void {
    this.onProgressCallback = onProgress;
    this.establishConnection();
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
    this.reconnectAttempts = 0;
  }

  onError(callback: ErrorCallback): void {
    this.onErrorCallback = callback;
  }

  onClose(callback: CloseCallback): void {
    this.onCloseCallback = callback;
  }

  private establishConnection(): void {
    const url = `${this.baseUrl}/ws/progress/${this.analysisId}`;
    console.log(`[WebSocket] Connecting to ${url}`);

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const message: ProgressMessage = JSON.parse(event.data);
          console.log(`[WebSocket] Progress: ${message.progress}% - ${message.step || ''}`);
          this.onProgressCallback?.(message);
        } catch (err) {
          console.error('[WebSocket] Failed to parse message:', err);
        }
      };

      this.ws.onerror = (event: Event) => {
        console.error('[WebSocket] Error:', event);
        this.onErrorCallback?.(event);
      };

      this.ws.onclose = (event: CloseEvent) => {
        console.log(`[WebSocket] Closed: code=${event.code}, reason=${event.reason}`);
        this.onCloseCallback?.(event);

        // Attempt reconnection if not a clean close
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.attemptReconnect();
        }
      };
    } catch (err) {
      console.error('[WebSocket] Failed to create connection:', err);
      this.onErrorCallback?.(err instanceof Error ? err : new Error(String(err)));
    }
  }

  private attemptReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    setTimeout(() => {
      this.establishConnection();
    }, delay);
  }
}
