'use strict';
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('cmdStudio', Object.freeze({
  call: (action, payload) => ipcRenderer.invoke('studio:call', action, payload),
  pick: (kind) => ipcRenderer.invoke('studio:pick', kind),
  openExternal: (url) => ipcRenderer.invoke('studio:openExternal', url),
  updates: Object.freeze({
    status: () => ipcRenderer.invoke('studio:updates:status'),
    configure: options => ipcRenderer.invoke('studio:updates:configure',options),
    check: () => ipcRenderer.invoke('studio:updates:check'),
    install: () => ipcRenderer.invoke('studio:updates:install'),
    subscribe: fn => {
      if(typeof fn!=='function')throw Error('Fonction de notification invalide');
      const listener=(_event,status)=>fn(status);
      ipcRenderer.on('studio:update-status',listener);
      return ()=>ipcRenderer.removeListener('studio:update-status',listener);
    }
  })
}));
