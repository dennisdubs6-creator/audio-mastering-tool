import axios, { AxiosInstance, AxiosError } from 'axios';
import type { AnalysisResponse, ComparisonResponse, SimilaritySearchResponse } from './types';

export interface AnalysisSettings {
  genre?: string;
  recommendationLevel?: string;
}

export interface HealthResponse {
  status: string;
}

export interface UploadResponse {
  analysis_id: string;
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

  async uploadAndAnalyze(file: File, settings: AnalysisSettings = {}): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (settings.genre) formData.append('genre', settings.genre);
      if (settings.recommendationLevel) {
        formData.append('recommendation_level', settings.recommendationLevel);
      }

      const response = await this.client.post<UploadResponse>('/api/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });

      return response.data;
    } catch (err) {
      throw this.handleError(err);
    }
  }

  async getAnalysisResults(analysisId: string): Promise<AnalysisResponse> {
    try {
      const response = await this.client.get<AnalysisResponse>(`/api/analysis/${analysisId}`);
      return response.data;
    } catch (err) {
      throw this.handleError(err);
    }
  }

  async findSimilarTracks(
    analysisId: string,
    genre?: string,
    topK?: number,
  ): Promise<SimilaritySearchResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (genre) params.genre = genre;
      if (topK) params.top_k = topK;

      const response = await this.client.post<SimilaritySearchResponse>(
        `/api/similarity/${analysisId}`,
        null,
        { params },
      );
      return response.data;
    } catch (err) {
      throw this.handleError(err);
    }
  }

  async compareWithReference(
    analysisId: string,
    referenceId: string,
    recommendationLevel?: string,
  ): Promise<ComparisonResponse> {
    try {
      const params: Record<string, string> = {};
      if (recommendationLevel) params.recommendation_level = recommendationLevel;

      const response = await this.client.get<ComparisonResponse>(
        `/api/compare/${analysisId}/${referenceId}`,
        { params },
      );
      return response.data;
    } catch (err) {
      throw this.handleError(err);
    }
  }

  getBaseUrl(): string {
    return this.client.defaults.baseURL || '';
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
