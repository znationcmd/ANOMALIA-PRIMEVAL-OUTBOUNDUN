'use strict';
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { GameLibrary } = require('./game-library.cjs');
const { EditorUpdates } = require('./updates.cjs');
let editorUpdates;
let gameLibrary;
let gameLibraryTimer;
const path=require('node:path');
app.setName('ANOMALIA Editor');
if(process.platform==='win32')app.setAppUserModelId('fr.anomalia.editor');
function createWindow(){
  const window=new BrowserWindow({
    width:1600,height:940,minWidth:1120,minHeight:720,
    title:'ANOMALIA Editor',backgroundColor:'#0e1420',
    icon:path.join(__dirname,'..','assets','anomalia-editor.ico'),
    webPreferences:{
      contextIsolation:true,nodeIntegration:false,sandbox:true,
      preload:path.join(__dirname,'preload.cjs'),
      webSecurity:true,devTools:false
    }
  });
  window.removeMenu();
  window.loadFile(path.join(__dirname,'..','dist','index.html'));
  window.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  window.webContents.on('will-navigate',event=>event.preventDefault());
}
app.whenReady().then(()=>{
  editorUpdates=new EditorUpdates();
  gameLibrary=new GameLibrary(app.getPath('userData'));
  ipcMain.handle('editor:library:status',()=>gameLibrary.getStatus());
  ipcMain.handle('editor:library:scan',()=>gameLibrary.scan());
  ipcMain.handle('editor:library:read',(_event,id)=>gameLibrary.read(id));
  ipcMain.handle('editor:library:import-pack',async()=>{
    const current=BrowserWindow.getFocusedWindow()||BrowserWindow.getAllWindows()[0];
    const choice=await dialog.showOpenDialog(current,{title:'Importer un pack 3D ANOMALIA ZIP',properties:['openFile'],filters:[{name:'Archives de modèles 3D',extensions:['zip']}]});
    if(choice.canceled||!choice.filePaths.length)return {cancelled:true};
    const result=await gameLibrary.importPack(choice.filePaths[0]);
    for(const w of BrowserWindow.getAllWindows())if(!w.isDestroyed())w.webContents.send('editor:library:changed',result.library);
    return result;
  });
  ipcMain.handle('editor:library:choose',async()=>{
    const current=BrowserWindow.getFocusedWindow()||BrowserWindow.getAllWindows()[0];
    const result=await dialog.showOpenDialog(current,{title:'Choisir le dossier des ressources ANOMALIA',properties:['openDirectory'],buttonLabel:'Synchroniser ce dossier'});
    if(result.canceled||!result.filePaths.length)return {cancelled:true};
    gameLibrary.setFolder(result.filePaths[0]);
    return gameLibrary.scan();
  });
  ipcMain.handle('editor:updates:status',()=>editorUpdates.getStatus());
  ipcMain.handle('editor:updates:check',()=>editorUpdates.check());
  ipcMain.handle('editor:updates:install',()=>editorUpdates.installNow());
  createWindow();
  editorUpdates.start();
  const sync=async()=>{
    try{
      const result=await gameLibrary.scan();
      if(result.changed)for(const w of BrowserWindow.getAllWindows()){
        if(!w.isDestroyed()&&!w.webContents.isDestroyed())w.webContents.send('editor:library:changed',result);
      }
    }catch(err){for(const w of BrowserWindow.getAllWindows())if(!w.isDestroyed())w.webContents.send('editor:library:error','Dossier de ressources ANOMALIA indisponible.');}
  };
  setTimeout(()=>sync(),2500);
  gameLibraryTimer=setInterval(sync,45000);
  app.on('activate',()=>{if(!BrowserWindow.getAllWindows().length)createWindow();});
});
app.on('window-all-closed',()=>{if(process.platform!=='darwin')app.quit();});

app.on('before-quit',()=>{editorUpdates?.stop();if(gameLibraryTimer)clearInterval(gameLibraryTimer);});
