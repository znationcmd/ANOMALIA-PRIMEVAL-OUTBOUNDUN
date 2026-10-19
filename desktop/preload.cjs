const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('anomaliaServer',Object.freeze({host:options=>ipcRenderer.invoke('anomalia:host',options),stop:()=>ipcRenderer.invoke('anomalia:stop')}));
