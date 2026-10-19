/**
 * ANOMALIA PRIMEVAL OUTBOUNDUN — dedicated Windows desktop game shell.
 * Vite bundles the 3D game; Electron runs it locally without a browser tab,
 * external web services or arbitrary Node.js access from game content.
 */
const { app, BrowserWindow, Menu, shell } = require("electron");
const path = require("node:path");

const GAME_TITLE="ANOMALIA PRIMEVAL OUTBOUNDUN";
function createGameWindow(){
 const game=new BrowserWindow({
  title:GAME_TITLE,width:1440,height:900,minWidth:960,minHeight:600,
  backgroundColor:"#111824",show:false,autoHideMenuBar:true,
  webPreferences:{
   nodeIntegration:false,
   contextIsolation:true,
   sandbox:true,
   webSecurity:true,
   allowRunningInsecureContent:false,
   devTools:!app.isPackaged
  }
 });
 game.once("ready-to-show",()=>game.show());
 game.webContents.setWindowOpenHandler(()=>({action:"deny"}));
 game.webContents.on("will-navigate",(event,url)=>{
  const current=game.webContents.getURL();
  if(url!==current)event.preventDefault();
 });
 game.webContents.on("will-attach-webview",(event)=>event.preventDefault());
 game.loadFile(path.join(__dirname,"..","dist","index.html"));
 return game;
}
app.whenReady().then(()=>{
 Menu.setApplicationMenu(null);
 createGameWindow();
 app.on("activate",()=>{if(BrowserWindow.getAllWindows().length===0)createGameWindow()});
});
app.on("window-all-closed",()=>{if(process.platform!=="darwin")app.quit()});
