'use strict';
const {app,BrowserWindow}=require('electron');
const {autoUpdater}=require('electron-updater');

const FEED='https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/releases/download/anomalia-tools-latest/';
const PERIOD=6*3600*1000;
class ToolsUpdater{
  constructor(){
    this.timer=null;this.checking=false;this.initialTimer=null;this.stopping=false;
    this.state={phase:'initialisation',message:'Vérification du service de mise à jour.',currentVersion:app.getVersion(),progress:0};
    autoUpdater.autoDownload=true;
    autoUpdater.autoInstallOnAppQuit=true;
    autoUpdater.allowDowngrade=false;
    autoUpdater.allowPrerelease=false;
    autoUpdater.setFeedURL({provider:'generic',url:FEED,channel:'latest'});
    autoUpdater.on('checking-for-update',()=>this.emit('verification','Recherche d’une version plus récente…'));
    autoUpdater.on('update-available',info=>this.emit('disponible','Version '+info.version+' disponible. Téléchargement en cours.',0,info.version));
    autoUpdater.on('download-progress',info=>this.emit('telechargement','Téléchargement : '+Math.round(info.percent||0)+' %',Math.round(info.percent||0)));
    autoUpdater.on('update-not-available',()=>this.emit('a-jour','ANOMALIA Tools est à jour.'));
    autoUpdater.on('update-downloaded',info=>this.emit('prete','Version '+info.version+' téléchargée. Installation lors de la fermeture de l’application.',100,info.version));
    autoUpdater.on('error',e=>this.emit('erreur',this.sanitizeError(e)));
  }
  sanitizeError(e){
    const str=String(e?.message||e||'');
    if(/404|not found|ERR_HTTP_RESPONSE_CODE_FAILURE/i.test(str))return 'Le canal officiel n’a pas encore de version publiée.';
    if(/ENOTFOUND|ETIMEDOUT|ECONNRESET|ERR_INTERNET|net::/i.test(str))return 'Connexion indisponible. Les mises à jour seront revérifiées automatiquement.';
    return 'Impossible de vérifier les mises à jour. Le logiciel installé reste inchangé.';
  }
  emit(phase,message,progress=0,nextVersion=null){
    this.state={phase,message,currentVersion:app.getVersion(),progress,...(nextVersion?{nextVersion}:{})};
    for(const win of BrowserWindow.getAllWindows()){
      if(!win.isDestroyed()&&!win.webContents.isDestroyed())win.webContents.send('tools:updates:status',this.status());
    }
  }
  status(){return {...this.state,enabled:true,checkEveryHours:6,installOnQuit:true,channel:'public-editor-independent'};}
  async check(){
    if(process.platform!=='win32'||!app.isPackaged){
      this.emit('developpement','Mises à jour disponibles uniquement dans l’application Windows installée.');
      return this.status();
    }
    if(this.checking||this.state.phase==='prete')return this.status();
    this.checking=true;
    try{await autoUpdater.checkForUpdates();return this.status();}
    catch(err){this.emit('erreur',this.sanitizeError(err));return this.status();}
    finally{this.checking=false;}
  }
  start(){
    if(process.platform!=='win32'||!app.isPackaged){
      this.emit('developpement','Les mises à jour automatiques s’activent dans la version Windows installée.');return;
    }
    this.emit('veille','Vérification au démarrage et toutes les 6 heures.');
    this.timer=setInterval(()=>this.check().catch(()=>{}),PERIOD);
    this.initialTimer=setTimeout(()=>this.check().catch(()=>{}),12000);
  }
  installNow(){
    if(this.state.phase!=='prete')throw Error('Aucune mise à jour téléchargée n’est prête.');
    autoUpdater.quitAndInstall(false,true);
    return {started:true};
  }
  stop(){
    this.stopping=true;
    if(this.timer)clearInterval(this.timer);
    if(this.initialTimer)clearTimeout(this.initialTimer);
  }
}
module.exports={ToolsUpdater,FEED,PERIOD};
