'use strict';
const {app,BrowserWindow}=require('electron');
const {autoUpdater}=require('electron-updater');

class EditorUpdates {
  constructor(){
    this.timer=null;this.checking=false;
    this.state={phase:'initialisation',currentVersion:app.getVersion(),message:'Initialisation des mises à jour.',progress:0};
    autoUpdater.autoDownload=true;
    autoUpdater.autoInstallOnAppQuit=true;
    autoUpdater.allowPrerelease=false;
    autoUpdater.allowDowngrade=false;
    // Seul ANOMALIA Editor est publié sous ce tag ; pas de confusion avec les autres applications.
    autoUpdater.setFeedURL({provider:'generic',
      url:'https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/releases/download/anomalia-editor-latest/',
      channel:'latest'});
    autoUpdater.on('checking-for-update',()=>this.emit('verification','Recherche d’une mise à jour…'));
    autoUpdater.on('update-available',info=>this.emit('disponible','Version '+info.version+' disponible. Téléchargement en cours.',0,info.version));
    autoUpdater.on('download-progress',p=>this.emit('telechargement','Téléchargement : '+Math.round(p.percent||0)+' %',Math.round(p.percent||0)));
    autoUpdater.on('update-not-available',()=>this.emit('a-jour','ANOMALIA Editor est à jour.'));
    autoUpdater.on('update-downloaded',info=>this.emit('prete','Version '+info.version+' prête. Installation automatique à la fermeture.',100,info.version));
    autoUpdater.on('error',err=>this.emit('erreur',this.publicError(err)));
  }
  publicError(e){
    const s=String(e?.message||e||'Erreur');
    if(/404|not found|ERR_HTTP_RESPONSE_CODE_FAILURE/i.test(s))return 'Canal de mises à jour en attente de la première publication officielle.';
    if(/net::|ENOTFOUND|ETIMEDOUT|ECONNRESET|ERR_INTERNET/i.test(s))return 'Serveur inaccessible. Vérifie la connexion Internet.';
    return 'Vérification impossible. La version actuelle reste inchangée.';
  }
  emit(phase,message,progress=0,newVersion=null){
    this.state={phase,message,progress,currentVersion:app.getVersion(),...(newVersion?{nextVersion:newVersion}:{})};
    for(const w of BrowserWindow.getAllWindows())if(!w.isDestroyed()&&!w.webContents.isDestroyed()){
      w.webContents.send('editor:update-status',this.getStatus());
    }
  }
  getStatus(){return {...this.state,automatic:true,checkEveryHours:6,installOnQuit:true};}
  async check(){
    if(!app.isPackaged||process.platform!=='win32'){
      this.emit('developpement','Les mises à jour automatiques concernent l’application Windows installée.');
      return this.getStatus();
    }
    if(this.state.phase==='prete'||this.checking)return this.getStatus();
    this.checking=true;
    try{await autoUpdater.checkForUpdates();return this.getStatus();}
    catch(e){this.emit('erreur',this.publicError(e));return this.getStatus();}
    finally{this.checking=false;}
  }
  start(){
    if(!app.isPackaged||process.platform!=='win32'){
      this.emit('developpement','Fonction disponible après installation sur Windows.');return;
    }
    this.emit('veille','Vérification automatique au démarrage et toutes les 6 heures.');
    this.timer=setInterval(()=>this.check().catch(()=>{}),6*3600*1000);
    setTimeout(()=>this.check().catch(()=>{}),12000);
  }
  installNow(){
    if(this.state.phase!=='prete')throw Error('Aucune version téléchargée à installer.');
    autoUpdater.quitAndInstall(false,true);
    return {started:true};
  }
  stop(){if(this.timer)clearInterval(this.timer);}
}
module.exports={EditorUpdates};
