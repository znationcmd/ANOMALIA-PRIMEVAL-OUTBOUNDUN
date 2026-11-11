'use strict';
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('cmdStudio', Object.freeze({
  call: (action, payload) => ipcRenderer.invoke('studio:call', action, payload),
  pick: (kind) => ipcRenderer.invoke('studio:pick', kind),
  openExternal: (url) => ipcRenderer.invoke('studio:openExternal', url)
}));
