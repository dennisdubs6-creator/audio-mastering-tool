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
│   │   └── common/         # Button, LoadingSpinner
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

- **analysisSlice**: Current analysis, progress tracking, batch file queue
- **uiSlice**: Sidebar state, modals, theme, card expansion

Typed hooks (`useAppDispatch`, `useAppSelector`) ensure type safety throughout.

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
