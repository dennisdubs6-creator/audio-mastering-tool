import axios, { AxiosInstance, AxiosError } from 'axios';

// Request/Response types matching backend schemas
export interface AnalysisSettings {
  genre?: string;
  targetLoudness?: number;
  referenceId?: string;
}

export interface AnalysisResult {
  id: string;
  fileName: string;
  status: string;
  frequency?: {
    frequencies: number[];
    magnitudes: number[];
  };
  dynamics?: {
    rms: number;
    peak: number;
    crestFactor: number;
    lufs: number;
    dynamicRange: number;
  };
  stereo?: {
    correlation: number;
    width: number;
    balance: number;
  };
  recommendations: Array<{
    id: string;
    category: string;
    level: 'critical' | 'suggested' | 'optional';
    message: string;
    detail?: string;
  }>;
}

export interface ReferenceMatch {
  referenceId: string;
  name: string;
  genre: string;
  similarity: number;
}

export interface Reference {
  id: string;
  name: string;
  genre: string;
  artist?: string;
}

export interface ComparisonResult {
  analysisId: string;
  referenceId: string;
  frequencyDelta: {
    frequencies: number[];
    magnitudes: number[];
  };
  dynamicsDelta: {
    rms: number;
    peak: number;
    crestFactor: number;
    lufs: number;
    dynamicRange: number;
  };
  stereoDelta: {
    correlation: number;
    width: number;
    balance: number;
  };
  overallScore: number;
}

export interface HealthResponse {
  status: string;
}

export class AudioAnalysisAPI {
  private client: AxiosInstance;

  constructor(baseUrl: string) {
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log(`[API Client] Initialized with base URL: ${baseUrl}`);
  }

  async healthCheck(): Promise<HealthResponse> {
    try {
      const response = await this.client.get<HealthResponse>('/health');
      return response.data;
    } catch (err) {
      throw this.handleError(err);
    }
  }

  async uploadAndAnalyze(file: File, settings: AnalysisSettings = {}): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (settings.genre) formData.append('genre', settings.genre);
      if (settings.targetLoudness !== undefined) {
        formData.append('target_loudness', String(settings.targetLoudness));
      }
      if (settings.referenceId) formData.append('reference_id', settings.referenceId);

      const response = await this.client.post<{ id: string }>('/api/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });

      return response.data.id;
    } catch (err) {
      throw this.handleError(err);
    }
  }

  async getAnalysisResults(analysisId: string): Promise<AnalysisResult> {
    try {
      const response = await this.client.get<AnalysisResult>(`/api/analysis/${analysisId}`);
      return response.data;
    } catch (err) {
      throw this.handleError(err);
    }
  }

  async findSimilarTracks(analysisId: string): Promise<ReferenceMatch[]> {
    try {
      const response = await this.client.post<ReferenceMatch[]>(`/api/similarity/${analysisId}`);
      return response.data;
    } catch (err) {
      throw this.handleError(err);
    }
  }

  async compareWithReference(analysisId: string, referenceId: string): Promise<ComparisonResult> {
    try {
      const response = await this.client.get<ComparisonResult>(
        `/api/compare/${analysisId}/${referenceId}`
      );
      return response.data;
    } catch (err) {
      throw this.handleError(err);
    }
  }

  async getReferences(genre?: string): Promise<Reference[]> {
    try {
      const params = genre ? { genre } : {};
      const response = await this.client.get<Reference[]>('/api/references', { params });
      return response.data;
    } catch (err) {
      throw this.handleError(err);
    }
  }

  private handleError(err: unknown): Error {
    if (err instanceof AxiosError) {
      if (err.response) {
        const status = err.response.status;
        const detail = err.response.data?.detail || err.response.statusText;

        if (status === 422) {
          return new Error(`Validation error: ${detail}`);
        }
        if (status === 404) {
          return new Error(`Not found: ${detail}`);
        }
        if (status >= 500) {
          return new Error(`Server error (${status}): ${detail}`);
        }
        return new Error(`Request failed (${status}): ${detail}`);
      }

      if (err.code === 'ECONNREFUSED') {
        return new Error('Cannot connect to backend. Please check that the server is running.');
      }
      if (err.code === 'ETIMEDOUT' || err.code === 'ECONNABORTED') {
        return new Error('Request timed out. Please try again.');
      }

      return new Error(`Network error: ${err.message}`);
    }

    return err instanceof Error ? err : new Error(String(err));
  }
}
