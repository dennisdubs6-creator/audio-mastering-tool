import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import path from 'path';
import { BackendManager } from './backend-manager';

let mainWindow: BrowserWindow | null = null;
const backendManager = new BackendManager();
let backendPort: number | null = null;

const isDev = !!process.env.VITE_DEV_SERVER_URL;

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    resizable: true,
    backgroundColor: '#020617',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL!);
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../../dist-renderer/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  console.log(`[Main] Window created, backend running on port ${backendPort}`);
}

// IPC Handlers
ipcMain.handle('get-backend-port', () => {
  return backendPort;
});

ipcMain.handle('select-file', async () => {
  if (!mainWindow) return null;

  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'Audio Files', extensions: ['wav', 'flac', 'mp3', 'aiff', 'ogg'] },
      { name: 'WAV Files', extensions: ['wav'] },
      { name: 'All Files', extensions: ['*'] },
    ],
  });

  if (result.canceled || result.filePaths.length === 0) {
    return null;
  }

  return result.filePaths[0];
});

ipcMain.handle('restart-backend', async () => {
  try {
    backendPort = await backendManager.restart();
    console.log(`[Main] Backend restarted on port ${backendPort}`);
    return backendPort;
  } catch (err) {
    console.error('[Main] Failed to restart backend:', err);
    throw err;
  }
});

// App lifecycle
app.whenReady().then(async () => {
  try {
    console.log('[Main] Starting backend...');
    backendPort = await backendManager.start();
    console.log(`[Main] Backend started on port ${backendPort}`);
  } catch (err) {
    console.error('[Main] Failed to start backend:', err);
    // Still create window to show error state
  }

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', async () => {
  console.log('[Main] All windows closed, stopping backend...');
  await backendManager.stop();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', async () => {
  await backendManager.stop();
});
