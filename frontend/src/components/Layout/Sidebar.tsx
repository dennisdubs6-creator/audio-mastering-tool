import React from 'react';
import { useAppSelector, useAppDispatch } from '@/store';
import { toggleSidebar } from '@/store/slices/uiSlice';

const Sidebar: React.FC = () => {
  const dispatch = useAppDispatch();
  const sidebarExpanded = useAppSelector((state) => state.ui.sidebarExpanded);
  const batchFiles = useAppSelector((state) => state.analysis.batchFiles);

  if (!sidebarExpanded) {
    return null;
  }

  return (
    <aside className="flex flex-col w-64 bg-slate-900 border-r border-slate-700 transition-all duration-200">
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Batch Files
        </h2>
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="p-1 rounded hover:bg-slate-700 transition-colors"
          title="Collapse sidebar"
        >
          <svg
            className="w-4 h-4 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {batchFiles.length === 0 ? (
          <p className="text-sm text-slate-500 text-center mt-8 px-4">
            No files in batch queue. Upload audio files to begin analysis.
          </p>
        ) : (
          <ul className="space-y-1">
            {batchFiles.map((file) => (
              <li
                key={file.path}
                className="flex items-center gap-2 p-2 rounded-md hover:bg-slate-800 cursor-pointer transition-colors"
              >
                <svg
                  className="w-4 h-4 text-slate-400 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
                  />
                </svg>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200 truncate">{file.name}</p>
                  <p className="text-xs text-slate-500">{file.status}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
