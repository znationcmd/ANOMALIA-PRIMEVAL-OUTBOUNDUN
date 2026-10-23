'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('anomaliaDesktop',Object.freeze({
  isDesktop:true,
  updates:Object.freeze({
    status:()=>ipcRenderer.invoke('editor:updates:status'),
    check:()=>ipcRenderer.invoke('editor:updates:check'),
    install:()=>ipcRenderer.invoke('editor:updates:install'),
    subscribe:listener=>{
      if(typeof listener!=='function')throw Error('Invalid listener');
      const handler=(_event,s)=>listener(s);
      ipcRenderer.on('editor:update-status',handler);
      return ()=>ipcRenderer.removeListener('editor:update-status',handler);
    }
  })
}));
