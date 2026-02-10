import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { UIState } from '../types';

const initialState: UIState = {
  sidebarExpanded: false,
  batchProcessing: false,
  activeModal: null,
  theme: 'dark',
  expandedCards: [],
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar(state) {
      state.sidebarExpanded = !state.sidebarExpanded;
    },
    setSidebarExpanded(state, action: PayloadAction<boolean>) {
      state.sidebarExpanded = action.payload;
    },
    setBatchProcessing(state, action: PayloadAction<boolean>) {
      state.batchProcessing = action.payload;
    },
    setActiveModal(state, action: PayloadAction<string | null>) {
      state.activeModal = action.payload;
    },
    toggleCardExpansion(state, action: PayloadAction<string>) {
      const cardId = action.payload;
      const currentlyExpanded = state.expandedCards[0];
      if (currentlyExpanded === cardId) {
        state.expandedCards = [];
      } else {
        state.expandedCards = [cardId];
      }
    },
    setTheme(state, action: PayloadAction<'dark' | 'light'>) {
      state.theme = action.payload;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarExpanded,
  setBatchProcessing,
  setActiveModal,
  toggleCardExpansion,
  setTheme,
} = uiSlice.actions;

export default uiSlice.reducer;
