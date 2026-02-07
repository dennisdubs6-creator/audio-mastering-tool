import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Analysis, AnalysisProgress, AnalysisState, FileState } from '../types';

const initialState: AnalysisState = {
  currentAnalysis: null,
  analysisProgress: {
    status: 'idle',
    progress: 0,
  },
  batchFiles: [],
};

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setCurrentAnalysis(state, action: PayloadAction<Analysis | null>) {
      state.currentAnalysis = action.payload;
    },
    updateProgress(state, action: PayloadAction<Partial<AnalysisProgress>>) {
      state.analysisProgress = { ...state.analysisProgress, ...action.payload };
    },
    addBatchFile(state, action: PayloadAction<FileState>) {
      state.batchFiles.push(action.payload);
    },
    removeBatchFile(state, action: PayloadAction<string>) {
      state.batchFiles = state.batchFiles.filter((f) => f.path !== action.payload);
    },
    clearAnalysis(state) {
      state.currentAnalysis = null;
      state.analysisProgress = { status: 'idle', progress: 0 };
    },
  },
});

export const {
  setCurrentAnalysis,
  updateProgress,
  addBatchFile,
  removeBatchFile,
  clearAnalysis,
} = analysisSlice.actions;

export default analysisSlice.reducer;
