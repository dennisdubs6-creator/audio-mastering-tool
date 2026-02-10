import { contextBridge, ipcRenderer } from 'electron';

const electronAPI = {
  getBackendPort: (): Promise<number | null> => ipcRenderer.invoke('get-backend-port'),
  selectFile: (): Promise<string | null> => ipcRenderer.invoke('select-file'),
  selectFiles: (): Promise<string[] | null> => ipcRenderer.invoke('select-files'),
  readFileBytes: (filePath: string): Promise<ArrayBuffer | null> => ipcRenderer.invoke('read-file-bytes', filePath),
  restartBackend: (): Promise<number | null> => ipcRenderer.invoke('restart-backend'),
};

contextBridge.exposeInMainWorld('electron', electronAPI);

export type ElectronAPI = typeof electronAPI;
