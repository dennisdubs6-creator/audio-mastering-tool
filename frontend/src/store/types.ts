export type AnalysisStatus = 'idle' | 'uploading' | 'analyzing' | 'completed' | 'error';

export type RecommendationLevel = 'critical' | 'suggested' | 'optional';

export type ComparisonMode = 'overlay' | 'side-by-side' | 'difference';

export interface AnalysisProgress {
  status: AnalysisStatus;
  progress: number;
  currentStep?: string;
  error?: string;
}

export interface FrequencyData {
  frequencies: number[];
  magnitudes: number[];
}

export interface DynamicsData {
  rms: number;
  peak: number;
  crestFactor: number;
  lufs: number;
  dynamicRange: number;
}

export interface StereoData {
  correlation: number;
  width: number;
  balance: number;
}

export interface Recommendation {
  id: string;
  category: string;
  level: RecommendationLevel;
  message: string;
  detail?: string;
}

export interface Analysis {
  id: string;
  fileName: string;
  filePath: string;
  createdAt: string;
  frequency?: FrequencyData;
  dynamics?: DynamicsData;
  stereo?: StereoData;
  recommendations: Recommendation[];
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

export interface Comparison {
  analysisId: string;
  referenceId: string;
  frequencyDelta: FrequencyData;
  dynamicsDelta: DynamicsData;
  stereoDelta: StereoData;
  overallScore: number;
}

export interface FileState {
  path: string;
  name: string;
  size: number;
  status: AnalysisStatus;
  analysisId?: string;
}

export interface AnalysisState {
  currentAnalysis: Analysis | null;
  analysisProgress: AnalysisProgress;
  batchFiles: FileState[];
}

export interface UIState {
  sidebarExpanded: boolean;
  activeModal: string | null;
  theme: 'dark' | 'light';
  expandedCards: string[];
}

export interface AppState {
  analysis: AnalysisState;
  ui: UIState;
}
