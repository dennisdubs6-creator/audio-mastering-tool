import { contextBridge, ipcRenderer } from 'electron';

const electronAPI = {
  getBackendPort: (): Promise<number | null> => ipcRenderer.invoke('get-backend-port'),
  selectFile: (): Promise<string | null> => ipcRenderer.invoke('select-file'),
  restartBackend: (): Promise<number | null> => ipcRenderer.invoke('restart-backend'),
};

contextBridge.exposeInMainWorld('electron', electronAPI);

export type ElectronAPI = typeof electronAPI;
