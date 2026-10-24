'use strict';
const {app,BrowserWindow,dialog,shell,ipcMain}=require('electron');
const path=require('node:path');
const {AnomaliaTools}=require('./core.cjs');
const {ToolsUpdater}=require('./updates.cjs');
let toolsApp;let win;let updater;
if(process.platform==='win32')app.setAppUserModelId('fr.anomalia.tools');
const ownInstance=app.requestSingleInstanceLock();
if(!ownInstance)app.quit();
if(ownInstance&&process.platform==='win32'&&app.isPackaged)app.setAsDefaultProtocolClient('anomalia-tools');
const workshopDeepLink=argv=>argv.some(arg=>/^anomalia-tools:\/\/workshop\/?$/i.test(arg));
app.on('second-instance',(_event,argv)=>{
  if(workshopDeepLink(argv)&&win&&!win.isDestroyed()){
    if(win.isMinimized())win.restore();
    win.show();win.focus();
    win.webContents.send('tools:navigate','workshop');
  }
});

const allowed=new Set(['overview','listProjects','createProject','listFiles','readText','writeText',
  'getEconomy','saveEconomy','importAssets','previewAsset','generateTerrain','packageMod',
  'scaffoldNativeMod','getNativeModStatus','validateNativeMod','buildNativeMod',
  'listWorkshopMods','publishWorkshopMod','subscribeWorkshopMod','prepareWorkshopMod','toggleWorkshopMod','exportWorkshopHostingManifest',
   'createWorkforgeProfile','activateWorkforgeProfile','setWorkforgeProfileMod','deleteWorkforgeProfile']);
function start(){
  win=new BrowserWindow({width:1550,height:940,minWidth:1040,minHeight:710,
    title:'ANOMALIA Tools',backgroundColor:'#10101b',
    icon:path.join(__dirname,'assets','anomalia-tools.ico'),webPreferences:{
      preload:path.join(__dirname,'preload.cjs'),nodeIntegration:false,contextIsolation:true,sandbox:true,webSecurity:true
    }});
  win.setMenuBarVisibility(false);
  win.loadFile(path.join(__dirname,'dist','index.html'));
  win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  win.webContents.on('will-navigate',e=>e.preventDefault());
}
if(ownInstance)app.whenReady().then(()=>{
  toolsApp=new AnomaliaTools(path.join(app.getPath('userData'),'private-workspaces'));
  updater=new ToolsUpdater();
  ipcMain.handle('tools:updates:status',()=>updater.status());
  ipcMain.handle('tools:updates:check',()=>updater.check());
  ipcMain.handle('tools:updates:install',()=>updater.installNow());
  ipcMain.handle('tools:call',async(_,method,payload={})=>{
    if(!allowed.has(method)||typeof toolsApp[method]!=='function')throw Error('Commande interdite');
    return toolsApp[method](payload);
  });
  ipcMain.handle('tools:exportHostingManifest',async(_event,projectId)=>{
    const manifest=toolsApp.exportWorkshopHostingManifest({projectId});
    const choice=await dialog.showSaveDialog(win,{
      defaultPath:'ANOMALIA-CMD-Hosting-'+manifest.mod.id+'.json',
      filters:[{name:'ANOMALIA CMD Hosting (JSON)',extensions:['json']}]
    });
    if(choice.canceled||!choice.filePath)return {cancelled:true};
    const fs=require('node:fs');
    // The dialog destination is explicitly selected by the user.
    fs.writeFileSync(choice.filePath,JSON.stringify(manifest,null,2)+'\n',{encoding:'utf8',flag:'w'});
    return {saved:true,file:choice.filePath,mod:manifest.mod.name,
      note:'Fiche exportée, non installée sur le serveur.'};
  });
  ipcMain.handle('tools:chooseAssets',async()=>{
    const result=await dialog.showOpenDialog(win,{properties:['openFile','multiSelections'],filters:[{
      name:'Modèles, textures et fichiers audio',
      extensions:['glb','gltf','fbx','obj','usd','png','jpg','jpeg','webp','tga','wav','ogg','json','xml','ini']
    }]});
    return result.canceled?[]:result.filePaths;
  });
  ipcMain.handle('tools:openFolder',async(_,projectId)=>{
    const project=toolsApp.getProjectPath(projectId);
    return shell.openPath(project);
  });
  ipcMain.handle('tools:exportPackage',async(_,projectId)=>{
    const archive=await toolsApp.packageMod({projectId});
    const suggested=path.basename(archive.path);
    const choice=await dialog.showSaveDialog(win,{defaultPath:suggested,filters:[{name:'Mods ANOMALIA ZIP',extensions:['zip']}]});
    if(choice.canceled||!choice.filePath)return {cancelled:true,manifest:archive.manifest};
    const fs=require('node:fs');
    if(path.resolve(choice.filePath)!==path.resolve(archive.path))fs.copyFileSync(archive.path,choice.filePath);
    return {saved:true,path:choice.filePath,manifest:archive.manifest};
  });
  start();if(workshopDeepLink(process.argv)){win.webContents.once('did-finish-load',()=>win.webContents.send('tools:navigate','workshop'));}updater.start();app.on('activate',()=>{if(!BrowserWindow.getAllWindows().length)start();});
});
app.on('window-all-closed',()=>{if(process.platform!=='darwin')app.quit();});

app.on('before-quit',()=>updater?.stop());
