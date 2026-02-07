import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { UIState } from '../types';

const initialState: UIState = {
  sidebarExpanded: false,
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
    setActiveModal(state, action: PayloadAction<string | null>) {
      state.activeModal = action.payload;
    },
    toggleCardExpansion(state, action: PayloadAction<string>) {
      const cardId = action.payload;
      const index = state.expandedCards.indexOf(cardId);
      if (index >= 0) {
        state.expandedCards.splice(index, 1);
      } else {
        state.expandedCards.push(cardId);
      }
    },
    setTheme(state, action: PayloadAction<'dark' | 'light'>) {
      state.theme = action.payload;
    },
  },
});

export const {
  toggleSidebar,
  setActiveModal,
  toggleCardExpansion,
  setTheme,
} = uiSlice.actions;

export default uiSlice.reducer;
