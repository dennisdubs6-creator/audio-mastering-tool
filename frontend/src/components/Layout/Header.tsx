import React from 'react';
import { useAppSelector, useAppDispatch } from '@/store';
import { toggleSidebar } from '@/store/slices/uiSlice';

const Header: React.FC = () => {
  const dispatch = useAppDispatch();
  const currentAnalysis = useAppSelector((state) => state.analysis.currentAnalysis);
  const sidebarExpanded = useAppSelector((state) => state.ui.sidebarExpanded);

  return (
    <header className="flex items-center justify-between h-14 px-4 bg-slate-800 border-b border-slate-700 select-none">
      <div className="flex items-center gap-3">
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="p-2 rounded-md hover:bg-slate-700 transition-colors"
          title={sidebarExpanded ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          <svg
            className="w-5 h-5 text-slate-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
        <h1 className="text-lg font-semibold text-white">Audio Mastering Tool</h1>
      </div>

      <div className="flex items-center gap-4">
        {currentAnalysis && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-400">Current:</span>
            <span className="text-slate-200 font-medium">{currentAnalysis.fileName}</span>
          </div>
        )}
        <button
          className="p-2 rounded-md hover:bg-slate-700 transition-colors"
          title="Settings"
        >
          <svg
            className="w-5 h-5 text-slate-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </button>
      </div>
    </header>
  );
};

export default Header;
