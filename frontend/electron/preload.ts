import { contextBridge, ipcRenderer } from 'electron';

const electronAPI = {
  getBackendPort: (): Promise<number> => ipcRenderer.invoke('get-backend-port'),
  selectFile: (): Promise<string | null> => ipcRenderer.invoke('select-file'),
  restartBackend: (): Promise<number> => ipcRenderer.invoke('restart-backend'),
};

contextBridge.exposeInMainWorld('electron', electronAPI);

export type ElectronAPI = typeof electronAPI;
