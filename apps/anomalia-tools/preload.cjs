'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('anomaliaTools',Object.freeze({
  call:(method,payload)=>ipcRenderer.invoke('tools:call',method,payload),
  chooseAssets:()=>ipcRenderer.invoke('tools:chooseAssets'),
  openFolder:id=>ipcRenderer.invoke('tools:openFolder',id),
  onNavigate:fn=>{
    if(typeof fn!=='function')throw Error('Invalid listener');
    const listener=(_event,tab)=>fn(tab);
    ipcRenderer.on('tools:navigate',listener);
    return ()=>ipcRenderer.removeListener('tools:navigate',listener);
  },
  exportPackage:id=>ipcRenderer.invoke('tools:exportPackage',id),
  updates:Object.freeze({
    status:()=>ipcRenderer.invoke('tools:updates:status'),
    check:()=>ipcRenderer.invoke('tools:updates:check'),
    install:()=>ipcRenderer.invoke('tools:updates:install'),
    subscribe:fn=>{
      if(typeof fn!=='function')throw Error('Abonnement invalide');
      const listener=(_event,data)=>fn(data);
      ipcRenderer.on('tools:updates:status',listener);
      return ()=>ipcRenderer.removeListener('tools:updates:status',listener);
    }
  })
}));
