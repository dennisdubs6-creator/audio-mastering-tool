import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { AnalysisResponse, ComparisonResponse, ReferenceTrackResponse, SimilarityMatchResponse } from '@/api/types';
import type { AnalysisSettings, AnalysisState, BatchFileState, BatchFileStatus, ComparisonMode, FileInfo } from '../types';

const initialState: AnalysisState = {
  status: 'idle',
  file: null,
  settings: null,
  analysisId: null,
  progress: 0,
  currentBand: null,
  results: null,
  currentAnalysis: null,
  batchFiles: [],
  selectedBatchFileId: null,
  error: null,
  selectedReference: null,
  comparisonMode: 'side-by-side',
  similarReferences: [],
  comparisonData: null,
};

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setFile(state, action: PayloadAction<FileInfo>) {
      state.file = action.payload;
      state.status = 'file_selected';
      state.error = null;
    },
    setSettings(state, action: PayloadAction<AnalysisSettings>) {
      state.settings = action.payload;
    },
    startUpload(state) {
      state.status = 'uploading';
      state.progress = 0;
      state.currentBand = null;
      state.error = null;
    },
    setAnalysisId(state, action: PayloadAction<string>) {
      state.analysisId = action.payload;
      state.status = 'analyzing';
    },
    setProgress(state, action: PayloadAction<{ percent: number; band?: string }>) {
      state.progress = action.payload.percent;
      if (action.payload.band) {
        state.currentBand = action.payload.band;
      }
    },
    setComplete(state, action: PayloadAction<AnalysisResponse>) {
      state.status = 'completed';
      state.analysisId = action.payload.id;
      state.results = action.payload;
      state.currentAnalysis = action.payload;
      state.progress = 100;
    },
    setError(state, action: PayloadAction<string>) {
      state.status = 'error';
      state.error = action.payload;
    },
    setCurrentAnalysis(state, action: PayloadAction<AnalysisResponse | null>) {
      state.currentAnalysis = action.payload;
    },
    addBatchFile(state, action: PayloadAction<Omit<BatchFileState, 'file'>>) {
      state.batchFiles.push({ ...action.payload, file: null });
    },
    updateBatchFileStatus(state, action: PayloadAction<{ id: string; status: BatchFileStatus }>) {
      const file = state.batchFiles.find((f) => f.id === action.payload.id);
      if (file) {
        file.status = action.payload.status;
      }
    },
    updateBatchFileProgress(state, action: PayloadAction<{ id: string; progress: number }>) {
      const file = state.batchFiles.find((f) => f.id === action.payload.id);
      if (file) {
        file.progress = action.payload.progress;
      }
    },
    setBatchFileAnalysisId(state, action: PayloadAction<{ id: string; analysisId: string }>) {
      const file = state.batchFiles.find((f) => f.id === action.payload.id);
      if (file) {
        file.analysisId = action.payload.analysisId;
      }
    },
    setBatchFileError(state, action: PayloadAction<{ id: string; error: string }>) {
      const file = state.batchFiles.find((f) => f.id === action.payload.id);
      if (file) {
        file.error = action.payload.error;
        file.status = 'error';
      }
    },
    setSelectedBatchFile(state, action: PayloadAction<string>) {
      state.selectedBatchFileId = action.payload;
    },
    removeBatchFile(state, action: PayloadAction<string>) {
      state.batchFiles = state.batchFiles.filter((f) => f.id !== action.payload);
      if (state.selectedBatchFileId === action.payload) {
        state.selectedBatchFileId = state.batchFiles.length > 0 ? state.batchFiles[0].id : null;
      }
    },
    clearBatchFiles(state) {
      state.batchFiles = [];
      state.selectedBatchFileId = null;
    },
    setSelectedReference(state, action: PayloadAction<ReferenceTrackResponse | null>) {
      state.selectedReference = action.payload;
    },
    setComparisonMode(state, action: PayloadAction<ComparisonMode>) {
      state.comparisonMode = action.payload;
    },
    setSimilarReferences(state, action: PayloadAction<SimilarityMatchResponse[]>) {
      state.similarReferences = action.payload;
    },
    setComparisonData(state, action: PayloadAction<ComparisonResponse | null>) {
      state.comparisonData = action.payload;
    },
    clearReference(state) {
      state.selectedReference = null;
      state.comparisonMode = 'side-by-side';
      state.comparisonData = null;
    },
    clearAnalysis() {
      return initialState;
    },
  },
});

export const {
  setFile,
  setSettings,
  startUpload,
  setAnalysisId,
  setProgress,
  setComplete,
  setError,
  setCurrentAnalysis,
  addBatchFile,
  updateBatchFileStatus,
  updateBatchFileProgress,
  setBatchFileAnalysisId,
  setBatchFileError,
  setSelectedBatchFile,
  removeBatchFile,
  clearBatchFiles,
  setSelectedReference,
  setComparisonMode,
  setSimilarReferences,
  setComparisonData,
  clearReference,
  clearAnalysis,
} = analysisSlice.actions;

export default analysisSlice.reducer;
