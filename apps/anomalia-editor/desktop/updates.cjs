'use strict';
const {app,BrowserWindow}=require('electron');
const {autoUpdater}=require('electron-updater');

// The installed NSIS app checks GitHub Releases directly. Never require another
// installer download or replace userData when applying a newer version.
class EditorUpdates {
  constructor({prepareForRestart}={}){
    this.timer=null;
    this.startTimer=null;
    this.checking=false;
    this.installing=false;
    this.restartTimer=null;
    this.prepareForRestart=typeof prepareForRestart==='function'?prepareForRestart:null;
    this.state={phase:'initialisation',currentVersion:app.getVersion(),message:'Initialisation des mises à jour.',progress:0};
    autoUpdater.autoDownload=true;
    autoUpdater.autoInstallOnAppQuit=true;
    autoUpdater.allowPrerelease=false;
    autoUpdater.allowDowngrade=false;
    // NSIS update channel exclusively dedicated to ANOMALIA Editor.
    autoUpdater.setFeedURL({provider:'generic',
      url:'https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/releases/download/anomalia-editor-latest/',
      channel:'latest'});
    autoUpdater.on('checking-for-update',()=>this.emit('verification','Recherche d’une mise à jour…'));
    autoUpdater.on('update-available',info=>this.emit('disponible','Version '+info.version+' disponible. Téléchargement automatique en cours.',0,info.version));
    autoUpdater.on('download-progress',p=>this.emit('telechargement','Téléchargement automatique : '+Math.round(p.percent||0)+' %',Math.round(p.percent||0)));
    autoUpdater.on('update-not-available',()=>this.emit('a-jour','ANOMALIA Editor est à jour.'));
    autoUpdater.on('update-downloaded',info=>{
      this.emit('prete','Version '+info.version+' téléchargée. Sauvegarde avant application automatique…',100,info.version);
      // No mouse click and no manually downloaded setup are necessary.
      // The old version stays untouched if a save cannot be confirmed.
      void this.installPreparedUpdate();
    });
    autoUpdater.on('error',err=>this.emit('erreur',this.publicError(err)));
  }
  publicError(e){
    const s=String(e?.message||e||'Erreur');
    if(/404|not found|ERR_HTTP_RESPONSE_CODE_FAILURE/i.test(s))
      return 'Le canal public de mise à jour est inaccessible (404). La version installée reste inchangée.';
    if(/net::|ENOTFOUND|ETIMEDOUT|ECONNRESET|ERR_INTERNET/i.test(s))
      return 'Serveur inaccessible. Vérifie la connexion Internet, puis relance l’application.';
    if(/sha512|signature|checksum|hash|verify/i.test(s))
      return 'Contrôle de sécurité du téléchargement invalide. Aucune installation n’a été effectuée.';
    return 'Mise à jour indisponible. La version actuelle est conservée.';
  }
  emit(phase,message,progress=0,newVersion=null){
    const nextVersion=newVersion||this.state.nextVersion;
    this.state={phase,message,progress,currentVersion:app.getVersion(),...(nextVersion?{nextVersion}:{})};
    for(const win of BrowserWindow.getAllWindows()){
      if(!win.isDestroyed()&&!win.webContents.isDestroyed()){
        win.webContents.send('editor:update-status',this.getStatus());
      }
    }
  }
  getStatus(){
    return {...this.state,automatic:true,checkEveryHours:6,installOnQuit:true,
      applyWhenSaved:true,restartAutomatically:true};
  }
  async check(){
    if(!app.isPackaged||process.platform!=='win32'){
      this.emit('developpement','Mises à jour automatiques uniquement pour l’application Windows installée.');
      return this.getStatus();
    }
    if(this.installing||this.state.phase==='prete'||this.checking)return this.getStatus();
    this.checking=true;
    try{await autoUpdater.checkForUpdates();return this.getStatus();}
    catch(err){this.emit('erreur',this.publicError(err));return this.getStatus();}
    finally{this.checking=false;}
  }
  async installPreparedUpdate(){
    if(this.installing||this.state.phase!=='prete')return {started:false};
    if(!app.isPackaged||process.platform!=='win32')return {started:false};
    this.installing=true;
    const version=this.state.nextVersion;
    try{
      this.emit('sauvegarde','Version '+version+' prête. Sauvegarde automatique de toutes les cartes ouvertes…',100,version);
      // Strict safety interlock: the renderer must acknowledge an IndexedDB
      // commit BEFORE Electron is allowed to replace the installed binaries.
      const safe=this.prepareForRestart?await this.prepareForRestart():false;
      if(!safe){
        this.installing=false;
        this.emit('prete','Carte non confirmée comme sauvegardée. Mise à jour conservée pour la fermeture de l’application.',100,version);
        return {started:false,safe:false};
      }
      this.emit('installation','Cartes sauvegardées. Mise à jour automatique et redémarrage d’ANOMALIA Editor…',100,version);
      this.restartTimer=setTimeout(()=>{
        try{autoUpdater.quitAndInstall(false,true);}
        catch(err){
          this.installing=false;
          this.emit('erreur','Installation impossible : '+this.publicError(err),100,version);
        }
      },1500);
      return {started:true,safe:true};
    }catch(err){
      this.installing=false;
      this.emit('prete','Sauvegarde impossible : mise à jour différée pour protéger ton travail.',100,version);
      return {started:false,safe:false};
    }
  }
  async installNow(){
    if(this.state.phase!=='prete')throw Error('Aucune mise à jour téléchargée à installer.');
    return this.installPreparedUpdate();
  }
  start(){
    if(!app.isPackaged||process.platform!=='win32'){
      this.emit('developpement','Les mises à jour automatiques concernent l’application Windows installée.');
      return;
    }
    this.emit('veille','Vérification au démarrage, puis toutes les 6 heures. Aucune réinstallation manuelle.');
    this.timer=setInterval(()=>this.check().catch(()=>{}),6*3600*1000);
    this.startTimer=setTimeout(()=>this.check().catch(()=>{}),4000);
  }
  stop(){
    if(this.timer)clearInterval(this.timer);
    if(this.startTimer)clearTimeout(this.startTimer);
    if(this.restartTimer)clearTimeout(this.restartTimer);
  }
}
module.exports={EditorUpdates};
