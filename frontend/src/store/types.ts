import type {
  AnalysisResponse,
  ComparisonResponse,
  ReferenceTrackResponse,
  SimilarityMatchResponse,
} from '@/api/types';

export type AnalysisStatus =
  | 'idle'
  | 'file_selected'
  | 'uploading'
  | 'analyzing'
  | 'completed'
  | 'error';

export type RecommendationLevelOption = 'analytical' | 'suggestive' | 'prescriptive';

export type ComparisonMode = 'overlay' | 'side-by-side' | 'difference';

export interface AnalysisSettings {
  genre: string;
  recommendationLevel: RecommendationLevelOption;
}

export interface AnalysisProgress {
  status: AnalysisStatus;
  progress: number;
  currentBand?: string;
  error?: string;
}

export interface FileInfo {
  name: string;
  path: string;
  size: number;
}

export type BatchFileStatus = 'pending' | 'analyzing' | 'complete' | 'error';

export interface BatchFileState {
  id: string;
  file: File | null;
  fileName: string;
  filePath: string;
  status: BatchFileStatus;
  analysisId: string | null;
  progress: number;
  error: string | null;
}

export interface AnalysisState {
  status: AnalysisStatus;
  file: FileInfo | null;
  settings: AnalysisSettings | null;
  analysisId: string | null;
  progress: number;
  currentBand: string | null;
  results: AnalysisResponse | null;
  currentAnalysis: AnalysisResponse | null;
  batchFiles: BatchFileState[];
  selectedBatchFileId: string | null;
  error: string | null;
  selectedReference: ReferenceTrackResponse | null;
  comparisonMode: ComparisonMode;
  similarReferences: SimilarityMatchResponse[];
  comparisonData: ComparisonResponse | null;
}

export interface UIState {
  sidebarExpanded: boolean;
  batchProcessing: boolean;
  activeModal: string | null;
  theme: 'dark' | 'light';
  expandedCards: string[];
}

export interface AppState {
  analysis: AnalysisState;
  ui: UIState;
}
