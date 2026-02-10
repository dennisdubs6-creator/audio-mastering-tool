# Audio Mastering Tool - Frontend

Electron + React + TypeScript frontend for the Audio Mastering Tool.

## Prerequisites

- Node.js 18+
- Python 3.10+ (for the backend)

## Installation

```bash
cd frontend
npm install
```

## Development

Start both the Vite dev server and Electron simultaneously:

```bash
npm run dev
```

This runs:
- `dev:vite` - Vite dev server on port 5173 with HMR
- `dev:electron` - Electron main process connecting to the Vite dev server

## Project Structure

```
frontend/
├── electron/               # Electron main process
│   ├── main.ts             # App lifecycle, window management, IPC handlers
│   ├── preload.ts          # Context bridge for secure IPC
│   └── backend-manager.ts  # Python backend process management
├── src/                    # React renderer process
│   ├── App.tsx             # Root component with backend connection logic
│   ├── main.tsx            # React entry point
│   ├── api/
│   │   ├── client.ts       # HTTP API client (axios)
│   │   └── websocket.ts    # WebSocket client for progress updates
│   ├── store/
│   │   ├── index.ts        # Redux store configuration
│   │   ├── types.ts        # TypeScript type definitions
│   │   └── slices/         # Redux Toolkit slices
│   ├── components/
│   │   ├── Layout/         # Header, Sidebar, MainContent
│   │   ├── Upload/         # UploadButton, DropZone, EmptyState
│   │   ├── Dashboard/      # DashboardView, MetricCards
│   │   ├── Sidebar/        # FileItem, FileStatusIcon
│   │   ├── ErrorHandling/  # ErrorBoundary, ErrorMessage
│   │   └── common/         # Button, LoadingSpinner
│   ├── hooks/
│   │   ├── useAnalysis.ts       # Single file analysis hook
│   │   └── useBatchAnalysis.ts  # Batch processing hook
│   └── styles/
│       └── globals.css     # Tailwind directives and dark theme variables
├── package.json
├── tsconfig.json           # TypeScript config for renderer
├── tsconfig.node.json      # TypeScript config for Electron main process
├── vite.config.ts          # Vite bundler configuration
├── tailwind.config.js      # Tailwind CSS configuration
├── postcss.config.js       # PostCSS configuration
└── index.html              # HTML entry point
```

## Backend Communication

The frontend communicates with the Python backend through a dynamic port handshake:

1. Electron main process spawns the Python backend with `--port 0` (OS-assigned port)
2. Backend Manager parses the port from uvicorn's stdout/stderr output
3. Health check is performed (up to 3 retries with 1-second delays)
4. Port is stored and exposed to the renderer process via IPC
5. React app initializes the API client with `http://127.0.0.1:{port}`

## State Management

Redux Toolkit manages global state with two slices:

- **analysisSlice**: Current analysis, progress tracking, batch file queue with per-file status
- **uiSlice**: Sidebar state, batch processing flag, modals, theme, card expansion

Typed hooks (`useAppDispatch`, `useAppSelector`) ensure type safety throughout.

## Batch Processing

The tool supports analyzing multiple WAV files in a single session:

1. **Multi-file upload**: Drag and drop multiple files or use the file picker with multi-select
2. **Sidebar file list**: When 2+ files are loaded, the sidebar auto-expands showing all files with status indicators (pending, analyzing, complete, error)
3. **Sequential processing**: Files are analyzed one at a time to manage memory usage
4. **File switching**: Click any completed file in the sidebar to view its analysis
5. **Progress tracking**: Each file shows individual progress; overall batch progress shown at top of sidebar
6. **Error resilience**: If one file fails, processing continues with the next file

### File Status Indicators

- Gray circle: Pending (queued for analysis)
- Blue spinner: Analyzing (currently being processed)
- Green checkmark: Complete (analysis finished successfully)
- Red X: Error (analysis failed, error message shown)

## Edge Case Handling

The backend detects and handles common audio issues:

- **Silence detection**: Warns when a file is essentially silent (RMS < -120 dBFS)
- **Clipping detection**: Warns when audio exceeds -0.1 dBFS (true peak)
- **DC offset**: Automatically detected and removed; warning included in results

## Styling

Tailwind CSS with a dark theme (slate/zinc palette). CSS variables define the color system in `globals.css`. The `dark` class is applied to the root HTML element.

## Building

Build for production:

```bash
npm run build
```

Package as a distributable:

```bash
npm run package
```

## Troubleshooting

- **Backend won't start**: Ensure Python 3.10+ is installed and in your PATH
- **File upload fails**: Only WAV files (16/24-bit, 44.1/48 kHz) are supported
- **Analysis stalls**: Check backend logs; try restarting via the error screen
- **Sidebar not showing**: Sidebar auto-expands only when 2+ files are in the batch queue
```
