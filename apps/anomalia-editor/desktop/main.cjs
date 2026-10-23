'use strict';
const { app, BrowserWindow } = require('electron');
const path=require('node:path');
app.setName('ANOMALIA Editor');
function createWindow(){
  const window=new BrowserWindow({
    width:1600,height:940,minWidth:1120,minHeight:720,
    title:'ANOMALIA Editor',backgroundColor:'#0e1420',
    webPreferences:{
      contextIsolation:true,nodeIntegration:false,sandbox:true,
      webSecurity:true,devTools:false
    }
  });
  window.removeMenu();
  window.loadFile(path.join(__dirname,'..','dist','index.html'));
  window.webContents.setWindowOpenHandler(()=>({action:'deny'}));
  window.webContents.on('will-navigate',event=>event.preventDefault());
}
app.whenReady().then(()=>{
  createWindow();
  app.on('activate',()=>{if(!BrowserWindow.getAllWindows().length)createWindow();});
});
app.on('window-all-closed',()=>{if(process.platform!=='darwin')app.quit();});
