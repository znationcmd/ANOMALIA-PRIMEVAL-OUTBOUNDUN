'use strict';
const { app, BrowserWindow, ipcMain } = require('electron');
const { EditorUpdates } = require('./updates.cjs');
let editorUpdates;
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
  ipcMain.handle('editor:updates:status',()=>editorUpdates.getStatus());
  ipcMain.handle('editor:updates:check',()=>editorUpdates.check());
  ipcMain.handle('editor:updates:install',()=>editorUpdates.installNow());
  createWindow();
  editorUpdates.start();
  app.on('activate',()=>{if(!BrowserWindow.getAllWindows().length)createWindow();});
});
app.on('window-all-closed',()=>{if(process.platform!=='darwin')app.quit();});

app.on('before-quit',()=>editorUpdates?.stop());
