'use strict';
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('anomaliaDesktop',Object.freeze({
  isDesktop:true,
  unreal:Object.freeze({
    status:()=>ipcRenderer.invoke('editor:unreal:status'),
    link:()=>ipcRenderer.invoke('editor:unreal:link'),
    open:map=>ipcRenderer.invoke('editor:unreal:open',map)
  }),
  gameLibrary:Object.freeze({
    status:()=>ipcRenderer.invoke('editor:library:status'),
    choose:()=>ipcRenderer.invoke('editor:library:choose'),
    importPack:()=>ipcRenderer.invoke('editor:library:import-pack'),
    scan:()=>ipcRenderer.invoke('editor:library:scan'),
    read:id=>ipcRenderer.invoke('editor:library:read',id),
    subscribe:fn=>{
      if(typeof fn!=='function')throw Error('Abonnement invalide');
      const onChange=(_event,status)=>fn({type:'changed',...status});
      const onError=(_event,message)=>fn({type:'error',message});
      ipcRenderer.on('editor:library:changed',onChange);
      ipcRenderer.on('editor:library:error',onError);
      return ()=>{ipcRenderer.removeListener('editor:library:changed',onChange);ipcRenderer.removeListener('editor:library:error',onError);};
    }
  }),
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
