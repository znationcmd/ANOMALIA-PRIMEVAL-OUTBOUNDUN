'use strict';
const path=require('node:path');
const {app,BrowserWindow,safeStorage}=require('electron');
const {autoUpdater}=require('electron-updater');
const {PUBLIC_KEY,INTERVAL_MS,validateFeedUrl,redactError,writeJsonAtomic,readPrivateSettings}=require('./update-policy.cjs');

class PrivateAutoUpdates{
  constructor(){
    this.file=path.join(app.getPath('userData'),'private-updates.json');
    this.settings=readPrivateSettings(this.file);
    this.state={phase:'initialisation',message:'Mises à jour privées',version:app.getVersion(),progress:0};
    this.ready=false;
    this.checking=false;
    this.timer=null;
    this.lastEvent='';
    autoUpdater.autoDownload=true;
    autoUpdater.autoInstallOnAppQuit=true;
    autoUpdater.allowPrerelease=false;
    autoUpdater.allowDowngrade=false;
    autoUpdater.updateManifestPublicKey=PUBLIC_KEY;
    autoUpdater.on('checking-for-update',()=>this.setState('verification','Recherche d’une nouvelle version…'));
    autoUpdater.on('update-available',info=>this.setState('disponible','Nouvelle version '+info.version+' : téléchargement sécurisé…',0,info.version));
    autoUpdater.on('download-progress',progress=>this.setState('telechargement',
      'Téléchargement : '+Math.round(progress.percent||0)+' %',Math.round(progress.percent||0)));
    autoUpdater.on('update-not-available',()=>this.setState('a-jour','CMD Studio est à jour.'));
    autoUpdater.on('update-downloaded',info=>this.setState('prete',
      'Version '+info.version+' téléchargée et vérifiée. Elle sera installée lorsque tu fermeras CMD Studio.',100,info.version));
    autoUpdater.on('error',error=>this.setState('erreur','Échec des mises à jour : '+redactError(error)));
  }
  setState(phase,message,progress=null,version=null){
    this.state={phase,message,version:this.state.version||app.getVersion(),
      progress:progress===null?this.state.progress:progress,
      ...(version?{nextVersion:version}:this.state.nextVersion?{nextVersion:this.state.nextVersion}:{})};
    for(const win of BrowserWindow.getAllWindows()){
      if(win.isDestroyed()||win.webContents.isDestroyed())continue;
      win.webContents.send('studio:update-status',this.status());
    }
  }
  status(){
    return {
      ...this.state,
      configured:Boolean(this.settings.url && this.settings.tokenEncrypted),
      enabled:this.settings.enabled,
      feedUrl:this.settings.url,
      hasToken:Boolean(this.settings.tokenEncrypted),
      autoInstallOnExit:true,
      intervalHours:INTERVAL_MS/3600000
    };
  }
  decryptToken(){
    if(!this.settings.tokenEncrypted)return '';
    if(!safeStorage.isEncryptionAvailable())throw Error('Chiffrement Windows indisponible : connexion de mise à jour désactivée.');
    return safeStorage.decryptString(Buffer.from(this.settings.tokenEncrypted,'base64'));
  }
  configure({url,token,enabled}={}){
    const nextUrl=url===undefined?this.settings.url:validateFeedUrl(url);
    const nextEnabled=enabled===undefined?this.settings.enabled:enabled===true;
    const isDifferentHost=this.settings.url&&new URL(nextUrl).origin!==new URL(this.settings.url).origin;
    let encrypted=this.settings.tokenEncrypted;
    if(isDifferentHost&&!token)throw Error('Un nouveau serveur nécessite sa propre clé privée.');
    if(token!==undefined&&token!==''){
      if(typeof token!=='string'||token.length>4096||token.length<12)throw Error('Clé privée invalide (12 à 4096 caractères).');
      if(!safeStorage.isEncryptionAvailable())throw Error('Windows ne permet pas encore de chiffrer la clé de connexion.');
      encrypted=safeStorage.encryptString(token).toString('base64');
    }
    if(nextEnabled&&(!nextUrl||!encrypted))
      throw Error('Indique l’adresse HTTPS privée et la clé de connexion pour activer les mises à jour.');
    const previousUrl=this.settings.url;
    this.settings={url:nextUrl,enabled:nextEnabled,tokenEncrypted:encrypted};
    writeJsonAtomic(this.file,this.settings);
    if(!nextEnabled){
      this.setState('desactivee','Mises à jour automatiques désactivées.');
      return this.status();
    }
    if(previousUrl!==nextUrl || !this.ready)this.ready=false;
    this.activate();
    return this.status();
  }
  activate(){
    if(process.platform!=='win32'||!app.isPackaged){
      this.setState('developpement','Les mises à jour s’activent dans l’application Windows installée.');
      return;
    }
    if(!this.settings.enabled||!this.settings.url||!this.settings.tokenEncrypted){
      this.setState('configuration','Configure une source de mises à jour privée pour activer les mises à jour.');
      return;
    }
    try{
      const token=this.decryptToken();
      if(!token)throw Error('Clé de connexion absente.');
      autoUpdater.setFeedURL({provider:'generic',url:validateFeedUrl(this.settings.url),channel:'latest'});
      // electron-updater 6.8+ scopes credential headers to the feed origin.
      autoUpdater.requestHeaders={Authorization:'Bearer '+token};
      autoUpdater.updateManifestPublicKey=PUBLIC_KEY;
      this.ready=true;
      this.setState('veille','Mises à jour automatiques activées. Vérification toutes les 6 heures.');
      if(this.timer)clearInterval(this.timer);
      this.timer=setInterval(()=>{this.check().catch(()=>{});},INTERVAL_MS);
      setTimeout(()=>{this.check().catch(()=>{});},12000);
    }catch(e){this.ready=false;this.setState('erreur','Configuration des mises à jour : '+redactError(e));}
  }
  async check(){
    if(!this.ready){
      if(!this.settings.enabled)throw Error('Mises à jour automatiques désactivées.');
      throw Error('Configure une source privée pour activer les mises à jour.');
    }
    if(this.state.phase==='prete')return this.status();
    if(this.checking)return this.status();
    this.checking=true;
    try{
      await autoUpdater.checkForUpdates();
      return this.status();
    }catch(e){
      this.setState('erreur','Vérification impossible : '+redactError(e));
      throw Error('La recherche de mise à jour a échoué. Vérifie ta connexion et la source privée.');
    }finally{this.checking=false;}
  }
  installNow(){
    if(this.state.phase!=='prete')throw Error('Aucune mise à jour téléchargée.');
    autoUpdater.quitAndInstall(false,true);
    return {started:true};
  }
  shutdown(){
    if(this.timer)clearInterval(this.timer);
    this.timer=null;
  }
}
module.exports={PrivateAutoUpdates};
