# Batch Processing

## Overview

The Audio Mastering Tool supports batch analysis of multiple WAV files. Files are processed sequentially to manage memory usage, with real-time progress tracking per file.

## Workflow

1. User uploads multiple WAV files via drag-and-drop or file picker (multi-select)
2. Files appear in the sidebar with "pending" status
3. User configures analysis settings (genre, recommendation level)
4. User clicks "Analyze" to start batch processing
5. Each file is processed sequentially:
   - Status changes to "analyzing" with progress bar
   - WebSocket streams per-band progress updates
   - On completion, status changes to "complete"
   - On failure, status changes to "error" with message; processing continues
6. User can click any completed file in sidebar to view its analysis
7. Dashboard updates to show the selected file's metrics

## File Status State Machine

```
[Added] --> Pending
Pending --> Analyzing (analysis started)
Analyzing --> Complete (analysis succeeded)
Analyzing --> Error (analysis failed)
Error --> Analyzing (user retries)
Complete --> [Removed] (user removes)
Error --> [Removed] (user removes)
```

## API Endpoints

Batch processing uses the same single-file endpoints, called sequentially:

- `POST /api/analyze` - Submit a WAV file for analysis (called per file)
- `GET /api/analysis/{id}` - Retrieve completed analysis results
- `WS /ws/progress/{id}` - Real-time progress updates per analysis

## WebSocket Message Format

```json
// Progress update
{
  "type": "band_progress",
  "band": "low_mid",
  "progress": 40,
  "status": "Analyzing Low Mid..."
}

// Completion
{
  "type": "complete",
  "analysis_id": "uuid-here"
}

// Error
{
  "type": "error",
  "message": "Analysis failed: unsupported sample rate"
}
```

## Frontend State Management

### BatchFileState (per file)

```typescript
interface BatchFileState {
  id: string;           // Unique ID (crypto.randomUUID())
  file: File | null;    // File object for drag-drop uploads
  fileName: string;     // Display name
  filePath: string;     // Electron file path (empty for drag-drop)
  status: 'pending' | 'analyzing' | 'complete' | 'error';
  analysisId: string | null;  // Backend analysis UUID
  progress: number;     // 0-100 percent
  error: string | null; // Error message if failed
}
```

### Redux Actions

- `addBatchFile` - Add a file to the batch queue
- `updateBatchFileStatus` - Update file status
- `updateBatchFileProgress` - Update progress percentage
- `setBatchFileAnalysisId` - Link to backend analysis ID
- `setBatchFileError` - Set error message
- `setSelectedBatchFile` - Switch dashboard to show this file
- `removeBatchFile` - Remove file from batch

## Error Handling

- Invalid file format: Rejected at upload with error message
- Network failure: File marked as "error", retry available
- Analysis failure: File marked as "error", processing continues to next file
- Corrupted file: Backend returns error via WebSocket, file marked accordingly

## Edge Case Detection

The backend automatically detects:

- **Silence**: RMS < -120 dBFS (1e-6 linear)
- **Clipping**: True peak > -0.1 dBFS (0.99 linear)
- **DC Offset**: Mean > 0.01 (automatically removed)

Warnings are stored in the `OverallMetrics.warnings` field as JSON and returned in the analysis response.

## Performance Considerations

- Files are processed sequentially (not in parallel) to limit memory usage
- Each analysis loads one file at a time; previous file data is released
- WebSocket progress messages are sent per-band (5 messages per file)
- Sidebar uses standard list rendering; virtual scrolling available for 100+ files
- Analysis results are cached in Redux to avoid re-fetching on file switch
