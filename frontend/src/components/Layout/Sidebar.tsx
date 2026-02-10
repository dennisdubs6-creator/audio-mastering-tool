import React, { useEffect, useRef } from 'react';
import { useAppSelector, useAppDispatch } from '@/store';
import { toggleSidebar, setSidebarExpanded } from '@/store/slices/uiSlice';
import { setSelectedBatchFile, removeBatchFile } from '@/store/slices/analysisSlice';
import FileItem from '@/components/Sidebar/FileItem';

interface SidebarProps {
  onAddFiles?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onAddFiles }) => {
  const dispatch = useAppDispatch();
  const sidebarExpanded = useAppSelector((state) => state.ui.sidebarExpanded);
  const batchFiles = useAppSelector((state) => state.analysis.batchFiles) || [];
  const selectedBatchFileId = useAppSelector((state) => state.analysis.selectedBatchFileId);
  const previousFileCountRef = useRef(0);

  const completedCount = batchFiles.filter((f) => f.status === 'complete').length;
  const totalCount = batchFiles.length;

  useEffect(() => {
    const previousCount = previousFileCountRef.current;
    if (batchFiles.length >= 2 && previousCount < 2) {
      dispatch(setSidebarExpanded(false));
    } else if (batchFiles.length <= 1) {
      dispatch(setSidebarExpanded(false));
    }
    previousFileCountRef.current = batchFiles.length;
  }, [batchFiles.length, dispatch]);

  if (!sidebarExpanded) {
    return (
      <aside className="flex flex-col w-14 bg-slate-900 border-r border-slate-700 transition-all duration-200">
        <div className="flex items-center justify-center p-3 border-b border-slate-700">
          <button
            onClick={() => dispatch(toggleSidebar())}
            className="p-1 rounded hover:bg-slate-700 transition-colors"
            title="Expand sidebar"
            aria-label="Expand sidebar"
          >
            <svg
              className="w-4 h-4 text-slate-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {totalCount > 0 && (
          <div className="flex flex-col items-center gap-2 px-2 py-3 border-b border-slate-700">
            <p className="text-[10px] text-slate-400 tabular-nums">
              {completedCount}/{totalCount}
            </p>
            <div className="h-16 w-1 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="w-full bg-green-500 transition-all duration-300"
                style={{ height: `${totalCount > 0 ? (completedCount / totalCount) * 100 : 0}%` }}
              />
            </div>
          </div>
        )}
      </aside>
    );
  }

  const handleFileClick = (id: string) => {
    dispatch(setSelectedBatchFile(id));
  };

  const handleFileRemove = (id: string) => {
    dispatch(removeBatchFile(id));
  };

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

      {totalCount > 0 && (
        <div className="px-4 py-2 border-b border-slate-700">
          <p className="text-xs text-slate-400">
            {completedCount} of {totalCount} files analyzed
          </p>
          <div className="mt-1 h-1 bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 transition-all duration-300"
              style={{ width: `${totalCount > 0 ? (completedCount / totalCount) * 100 : 0}%` }}
            />
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-2">
        {batchFiles.length === 0 ? (
          <p className="text-sm text-slate-500 text-center mt-8 px-4">
            No files in batch queue. Upload audio files to begin analysis.
          </p>
        ) : (
          <ul className="space-y-1">
            {batchFiles.map((file) => (
              <FileItem
                key={file.id}
                file={file}
                isActive={file.id === selectedBatchFileId}
                onClick={handleFileClick}
                onRemove={handleFileRemove}
              />
            ))}
          </ul>
        )}
      </div>

      {onAddFiles && (
        <div className="p-3 border-t border-slate-700">
          <button
            onClick={onAddFiles}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-md transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Files
          </button>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;
