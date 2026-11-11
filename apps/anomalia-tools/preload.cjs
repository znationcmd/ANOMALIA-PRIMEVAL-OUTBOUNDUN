'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('anomaliaTools',Object.freeze({
  call:(method,payload)=>ipcRenderer.invoke('tools:call',method,payload),
  chooseAssets:()=>ipcRenderer.invoke('tools:chooseAssets'),
  openFolder:id=>ipcRenderer.invoke('tools:openFolder',id),
  exportPackage:id=>ipcRenderer.invoke('tools:exportPackage',id)
}));
