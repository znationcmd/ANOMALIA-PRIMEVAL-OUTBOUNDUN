/**
 * ANOMALIA PRIMEVAL OUTBOUNDUN — Windows installed game runtime.
 * Bundled 3D assets use a secure, standard local application origin, allowing
 * offline ES modules and persistent saves without file:// CORS failures.
 */
const {app,BrowserWindow,Menu,protocol,net,ipcMain}=require("electron");
const path=require("node:path");
const fs=require("node:fs");
const {pathToFileURL}=require("node:url");
const {createHash}=require("node:crypto");
const {autoUpdater}=require("electron-updater");

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
   preload:path.join(__dirname,"preload.cjs"),
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

let multiplayerServer=null;const clientSockets=new Map();
const validSender=event=>{const url=new URL(event.senderFrame.url);if(url.protocol!=='anomalia:'||url.host!=='game')throw Error('Forbidden');};
app.whenReady().then(()=>{
 ipcMain.handle('anomalia:connect',async(event,token,address)=>{
  validSender(event);if(typeof token!=='string'||token.length>64)throw Error('Invalid socket token');const url=new URL(address);if(!['ws:','wss:'].includes(url.protocol)||url.username||url.password)throw Error('Invalid server address');
  const owner=event.sender.id,previous=clientSockets.get(owner);previous?.socket.close();
  const {WebSocket}=require('ws'),socket=new WebSocket(url.href,{maxPayload:256*1024});clientSockets.set(owner,{token,socket});
  const emit=data=>{if(!event.sender.isDestroyed())event.sender.send('anomalia:socket',{token,...data});};
  socket.on('message',data=>emit({kind:'message',data:data.toString()}));socket.on('error',()=>emit({kind:'error'}));socket.on('close',()=>{if(clientSockets.get(owner)?.token===token)clientSockets.delete(owner);emit({kind:'close'});});
  event.sender.once('destroyed',()=>{if(clientSockets.get(owner)?.token===token){socket.terminate();clientSockets.delete(owner);}});
  await new Promise((resolve,reject)=>{socket.once('open',resolve);socket.once('error',reject);});return true;
 });
 ipcMain.on('anomalia:send',(event,token,data)=>{validSender(event);const active=clientSockets.get(event.sender.id);if(active?.token===token&&active.socket.readyState===1&&typeof data==='string'&&Buffer.byteLength(data)<=256*1024)active.socket.send(data);});
 ipcMain.on('anomalia:disconnect',(event,token)=>{validSender(event);const active=clientSockets.get(event.sender.id);if(active?.token===token)active.socket.close();});
 ipcMain.handle('anomalia:host',async(event,options={})=>{
  validSender(event);const port=Number(options.port||2303),password=String(options.password||'');if(!Number.isInteger(port)||port<1024||port>65535||password.length>128)throw Error('Invalid server options');
  const gameMode=String(options.mode||'pve');if(!['rp','pvp','pve','mixed'].includes(gameMode))throw Error('Invalid game mode');
  if(multiplayerServer){await multiplayerServer.close();multiplayerServer=null;}
  const {createMultiplayerServer}=await import('../server/server.mjs');const legacyWorld=path.join(app.getPath('userData'),'world-server.json');
  const isolatedWorld=path.join(app.getPath('userData'),'servers','local-'+port,'world.json');
  if(fs.existsSync(legacyWorld)&&!fs.existsSync(isolatedWorld)){fs.mkdirSync(path.dirname(isolatedWorld),{recursive:true});fs.copyFileSync(legacyWorld,isolatedWorld);}
  const next=createMultiplayerServer({port,host:'0.0.0.0',password,maxPlayers:16,mode:gameMode,serverId:'local-'+port,dataRoot:app.getPath('userData')});
  try{await new Promise((resolve,reject)=>{next.server.once('listening',resolve);next.server.once('error',reject);});}catch(e){await next.close();throw e;}
  multiplayerServer=next;
  const addresses=Object.values(require('node:os').networkInterfaces()).flat().filter(n=>n.family==='IPv4'&&!n.internal).map(n=>`ws://${n.address}:${port}`);
  return {url:`ws://localhost:${port}`,addresses,adminKey:next.adminKey,mode:next.mode};
 });
 ipcMain.handle('anomalia:stop',async event=>{validSender(event);if(multiplayerServer){await multiplayerServer.close();multiplayerServer=null;}return true;});
 const bundleDir=path.resolve(__dirname,"..","dist");
 let activeProfile="solo";
 const configRoot=path.join(app.getPath("userData"),"profiles");
 const configDirFor=id=>path.join(configRoot,id,"config");
 const configDir=configDirFor("solo");
 fs.mkdirSync(configDir,{recursive:true});
 const configNames=["types.xml","events.xml","cfgeventspawns.xml","cfgspawnabletypes.xml","globals.xml","economy.xml","ai.xml","cfgeconomycore.xml","serverDZ.cfg","Game.ini","GameUserSettings.ini","world-settings.json","creatures.json","config.json","admin_config.json","scenarios.json","mods.json","cfggameplay.json","cfglootspawn.xml","cfgplayerspawnpoints.xml","messages.xml","vehicles.xml","AllowedCheaterSteamIDs.txt"];
 const ensureConfig=id=>{const folder=configDirFor(id);fs.mkdirSync(folder,{recursive:true});for(const name of configNames){const from=path.join(bundleDir,"config",name),to=path.join(folder,name);if(!fs.existsSync(to)&&fs.existsSync(from))fs.copyFileSync(from,to);}return folder;};
 ensureConfig("solo");
 ipcMain.handle("anomalia:select-profile",(event,address)=>{validSender(event);if(!address){activeProfile="solo";return activeProfile;}const url=new URL(address);if(!["ws:","wss:"].includes(url.protocol)||url.username||url.password)throw Error("Invalid address");activeProfile="remote-"+createHash("sha256").update(url.host.toLowerCase()+url.pathname).digest("hex").slice(0,24);ensureConfig(activeProfile);return activeProfile;});

 protocol.handle(SCHEME,async(request)=>{
  try{
   const url=new URL(request.url);
   if(url.host!=="game")return new Response("Not found",{status:404});
   const pathname=decodeURIComponent(url.pathname);
   if(pathname.includes("\0"))return new Response("Forbidden",{status:403});
   const relative=pathname==="/"?"index.html":pathname.replace(/^\/+/, "");
   if(relative==="config/location.json")return new Response(JSON.stringify({directory:ensureConfig(activeProfile),profile:activeProfile}),{headers:{"Content-Type":"application/json"}});
   const isConfig=relative.startsWith("config/");
   if(isConfig&&!configNames.includes(relative.slice(7)))return new Response("Not found",{status:404});
   const root=isConfig?ensureConfig(activeProfile):bundleDir;
   const target=path.resolve(root,isConfig?relative.slice(7):relative);
   if(target!==root&&!target.startsWith(root+path.sep))
    return new Response("Forbidden",{status:403});
   return await net.fetch(pathToFileURL(target).href);
  }catch{return new Response("Asset not found",{status:404})}
 });
 Menu.setApplicationMenu(null);
 createGameWindow();
 if(app.isPackaged){
  autoUpdater.autoDownload=true;
  autoUpdater.autoInstallOnAppQuit=true;
  autoUpdater.on("error",error=>console.warn("[ANOMALIA] Update unavailable:",error.message));
  autoUpdater.on("update-downloaded",()=>console.log("[ANOMALIA] New version downloaded; will install on quit"));
  const checkUpdates=()=>autoUpdater.checkForUpdates().catch(error=>console.warn("[ANOMALIA] Update check:",error.message));
  setTimeout(checkUpdates,15000).unref?.();
  setInterval(checkUpdates,6*60*60*1000).unref?.();
 }
 app.on("activate",()=>{if(!BrowserWindow.getAllWindows().length)createGameWindow()});
});
app.on("window-all-closed",()=>{if(multiplayerServer){multiplayerServer.close().catch(()=>{});multiplayerServer=null;}if(process.platform!=="darwin")app.quit()});
