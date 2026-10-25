const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('anomaliaServer',Object.freeze({host:options=>ipcRenderer.invoke('anomalia:host',options),stop:()=>ipcRenderer.invoke('anomalia:stop'),selectProfile:address=>ipcRenderer.invoke('anomalia:select-profile',address),openWorkshop:()=>ipcRenderer.invoke('anomalia:open-workshop')}));

// Read-only bridge for the Workshop embedded in the game, not for loading UE5 plugins.
contextBridge.exposeInMainWorld('anomaliaWorkshop',Object.freeze({
 list:()=>ipcRenderer.invoke('anomalia:workshop:list')
}));

contextBridge.exposeInMainWorld('anomaliaUpdates',Object.freeze({
 status:()=>ipcRenderer.invoke('anomalia:update:status'),
 check:()=>ipcRenderer.invoke('anomalia:update:check'),
 install:()=>ipcRenderer.invoke('anomalia:update:install'),
 subscribe:fn=>{
  if(typeof fn!=='function')throw Error('Invalid updater listener');
  const listener=(_event,data)=>fn(data);
  ipcRenderer.on('anomalia:update:status',listener);
  return ()=>ipcRenderer.removeListener('anomalia:update:status',listener);
 }
}));

contextBridge.exposeInMainWorld('anomaliaTransport',Object.freeze({
 connect:(token,url)=>ipcRenderer.invoke('anomalia:connect',token,url),
 send:(token,data)=>ipcRenderer.send('anomalia:send',token,data),
 close:token=>ipcRenderer.send('anomalia:disconnect',token),
 subscribe:callback=>{const listener=(_event,data)=>callback(data);ipcRenderer.on('anomalia:socket',listener);return ()=>ipcRenderer.removeListener('anomalia:socket',listener);}
}));
