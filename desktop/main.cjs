/**
 * ANOMALIA PRIMEVAL OUTBOUNDUN — Windows installed game runtime.
 * Bundled 3D assets use a secure, standard local application origin, allowing
 * offline ES modules and persistent saves without file:// CORS failures.
 */
const {app,BrowserWindow,Menu,protocol,net}=require("electron");
const path=require("node:path");
const fs=require("node:fs");
const {pathToFileURL}=require("node:url");

const GAME_TITLE="ANOMALIA PRIMEVAL OUTBOUNDUN";
const SCHEME="anomalia";
protocol.registerSchemesAsPrivileged([
 {scheme:SCHEME,privileges:{standard:true,secure:true,supportFetchAPI:true,stream:true}}
]);

function createGameWindow(){
 const game=new BrowserWindow({
  title:GAME_TITLE,
  width:1440,height:900,minWidth:960,minHeight:600,
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
  if(!url.startsWith("anomalia://game/"))event.preventDefault();
 });
 game.webContents.on("will-attach-webview",event=>event.preventDefault());
 game.loadURL("anomalia://game/index.html");
 return game;
}

app.whenReady().then(()=>{
 const bundleDir=path.resolve(__dirname,"..","dist");
 const configDir=path.join(app.getPath("userData"),"config");
 fs.mkdirSync(configDir,{recursive:true});
 const configNames=["types.xml","events.xml","cfgeventspawns.xml","cfgspawnabletypes.xml","globals.xml","economy.xml","ai.xml","cfgeconomycore.xml","serverDZ.cfg","Game.ini","GameUserSettings.ini","world-settings.json","creatures.json"];
 for(const name of configNames){const from=path.join(bundleDir,"config",name),to=path.join(configDir,name);if(!fs.existsSync(to)&&fs.existsSync(from))fs.copyFileSync(from,to);}

 protocol.handle(SCHEME,async(request)=>{
  try{
   const url=new URL(request.url);
   if(url.host!=="game")return new Response("Not found",{status:404});
   const pathname=decodeURIComponent(url.pathname);
   if(pathname.includes("\0"))return new Response("Forbidden",{status:403});
   const relative=pathname==="/"?"index.html":pathname.replace(/^\/+/, "");
   if(relative==="config/location.json")return new Response(JSON.stringify({directory:configDir}),{headers:{"Content-Type":"application/json"}});
   const isConfig=relative.startsWith("config/");
   if(isConfig&&!configNames.includes(relative.slice(7)))return new Response("Not found",{status:404});
   const root=isConfig?configDir:bundleDir;
   const target=path.resolve(root,isConfig?relative.slice(7):relative);
   if(target!==root&&!target.startsWith(root+path.sep))
    return new Response("Forbidden",{status:403});
   return await net.fetch(pathToFileURL(target).href);
  }catch{return new Response("Asset not found",{status:404})}
 });
 Menu.setApplicationMenu(null);
 createGameWindow();
 app.on("activate",()=>{if(!BrowserWindow.getAllWindows().length)createGameWindow()});
});
app.on("window-all-closed",()=>{if(process.platform!=="darwin")app.quit()});
