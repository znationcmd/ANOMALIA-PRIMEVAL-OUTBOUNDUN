'use strict';
// A native Unreal plugin is NOT the same thing as a source ZIP, or a cooked game mod.
const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const {spawn}=require('node:child_process');

function pluginNameFor(projectId){
  if(typeof projectId!=='string'||!/^[a-z0-9][a-z0-9-]{1,100}$/.test(projectId))
    throw Error('Identifiant de projet incorrect');
  const name=projectId.split('-').filter(Boolean).map(x=>x[0].toUpperCase()+x.slice(1)).join('').slice(0,30);
  return 'ANM'+name+crypto.createHash('sha256').update(projectId).digest('hex').slice(0,8);
}
function checkedPath(root,relative){
  const base=path.resolve(root),file=path.resolve(base,relative);
  if(!file.startsWith(base+path.sep))throw Error('Chemin extérieur au projet');
  let cursor=base;
  for(const segment of path.relative(base,file).split(path.sep)){
    cursor=path.join(cursor,segment);
    if(fs.existsSync(cursor)&&fs.lstatSync(cursor).isSymbolicLink())throw Error('Lien symbolique interdit');
  }
  return file;
}
function filesFor(root,projectId){
  const name=pluginNameFor(projectId),folder='Plugins/'+name;
  return {
    name,folder:checkedPath(root,folder),
    descriptor:checkedPath(root,folder+'/'+name+'.uplugin'),
    rules:checkedPath(root,folder+'/Source/'+name+'/'+name+'.Build.cs'),
    module:checkedPath(root,folder+'/Source/'+name+'/Private/'+name+'Module.cpp'),
    readme:checkedPath(root,folder+'/Content/README.txt'),
    output:checkedPath(root,'Dist/Native/'+name)
  };
}
function newFile(file,contents){
  fs.mkdirSync(path.dirname(file),{recursive:true});
  try{fs.writeFileSync(file,contents,{encoding:'utf8',flag:'wx'});return true;}
  catch(err){if(err.code==='EEXIST')return false;throw err;}
}
function scaffoldNativeMod(root,projectId,projectName='ANOMALIA Mod'){
  const p=filesFor(root,projectId);
  const descriptor={
    FileVersion:3,Version:1,VersionName:'0.1.0',FriendlyName:String(projectName).slice(0,80),
    Description:'ANOMALIA Unreal Engine plugin source',Category:'ANOMALIA Mods',
    CreatedBy:'ANOMALIA Tools',CanContainContent:true,IsBetaVersion:true,
    Modules:[{Name:p.name,Type:'Runtime',LoadingPhase:'Default'}]
  };
  const rules=[
    'using UnrealBuildTool;',
    'public class '+p.name+' : ModuleRules',
    '{',
    '    public '+p.name+'(ReadOnlyTargetRules Target) : base(Target)',
    '    {',
    '        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;',
    '        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });',
    '    }',
    '}',''
  ].join('\n');
  const cpp=[
    '#include "Modules/ModuleManager.h"',
    'class F'+p.name+'Module final : public IModuleInterface',
    '{','public:',
    '    virtual void StartupModule() override {}',
    '    virtual void ShutdownModule() override {}',
    '};','IMPLEMENT_MODULE(F'+p.name+'Module, '+p.name+')',''
  ].join('\n');
  const created=[];
  for(const [file,text] of [
    [p.descriptor,JSON.stringify(descriptor,null,2)+'\n'],
    [p.rules,rules],[p.module,cpp],
    [p.readme,'Importe les ressources GLB/FBX dans Unreal Editor pour obtenir des .uasset. Cette compilation ne cuit pas les assets du jeu.\n']
  ])if(newFile(file,text))created.push(path.relative(root,file).replaceAll('\\','/'));
  return {plugin:p.name,descriptor:path.relative(root,p.descriptor).replaceAll('\\','/'),created,
    note:'Le plugin UE5 généré reste une source. Compilation, cuisson et chargement dans ANOMALIA sont des étapes distinctes.'};
}
function validateNativeMod(root,projectId){
  const p=filesFor(root,projectId);
  for(const file of [p.descriptor,p.rules,p.module]){
    if(!fs.existsSync(file)||!fs.statSync(file).isFile()||fs.lstatSync(file).isSymbolicLink())
      throw Error('Fichier plugin manquant : '+path.relative(root,file));
  }
  if(fs.statSync(p.descriptor).size>1024*1024)throw Error('Descripteur trop volumineux');
  let d;
  try{d=JSON.parse(fs.readFileSync(p.descriptor,'utf8'));}
  catch{throw Error('Descripteur .uplugin invalide');}
  if(d.FileVersion!==3||d.CanContainContent!==true||!Array.isArray(d.Modules)||
     !d.Modules.some(x=>x.Name===p.name&&x.Type==='Runtime'))
    throw Error('Descripteur .uplugin incompatible');
  return {valid:true,plugin:p.name,version:d.VersionName||'unknown',descriptor:p.descriptor};
}
function buildStatus(root,projectId,engineRoot=''){
  const p=filesFor(root,projectId);
  let error=null;
  try{validateNativeMod(root,projectId);}catch(e){error=e.message;}
  const candidate=engineRoot||process.env.UE_ROOT||'';
  let uat=null;
  if(candidate&&path.isAbsolute(candidate)){
    const script=path.join(path.resolve(candidate),'Engine','Build','BatchFiles','RunUAT.bat');
    if(fs.existsSync(script)&&fs.statSync(script).isFile()&&!fs.lstatSync(script).isSymbolicLink())
      uat=script;
  }
  return {plugin:p.name,valid:!error,validationError:error,engineFound:!!uat,
    engineRoot:candidate,supportedHost:process.platform==='win32',
    nativeBuildAvailable:!error&&!!uat&&process.platform==='win32',
    output:path.relative(root,p.output).replaceAll('\\','/'),
    note:'Compilation UE5 ≠ mod cuit ni chargé dans ANOMALIA'};
}
function buildNativeMod(root,projectId,engineRoot=''){
  const source=validateNativeMod(root,projectId);
  const state=buildStatus(root,projectId,engineRoot);
  if(!state.supportedHost)throw Error('Compiler des plugins Unreal nécessite Windows, Unreal Engine et Visual Studio.');
  if(!state.engineFound)throw Error('RunUAT.bat introuvable dans le dossier racine de Unreal Engine.');
  const p=filesFor(root,projectId);
  const uat=path.join(path.resolve(state.engineRoot),'Engine','Build','BatchFiles','RunUAT.bat');
  fs.mkdirSync(path.dirname(p.output),{recursive:true});
  return new Promise((resolve,reject)=>{
    // Untrusted paths are environment values, never interpolated into PowerShell source.
    const command="& $env:ANOMALIA_UAT BuildPlugin ('-Plugin=' + $env:ANOMALIA_PLUGIN) ('-Package=' + $env:ANOMALIA_OUTPUT) '-TargetPlatforms=Win64' '-Rocket'; exit $LASTEXITCODE";
    const child=spawn('powershell.exe',['-NoProfile','-NonInteractive','-Command',command],{
      cwd:root,windowsHide:true,
      env:{...process.env,ANOMALIA_UAT:uat,ANOMALIA_PLUGIN:p.descriptor,ANOMALIA_OUTPUT:p.output}
    });
    let tail='',settled=false,timedOut=false;
    const log=chunk=>{tail=(tail+String(chunk)).slice(-120000);};
    child.stdout.on('data',log);child.stderr.on('data',log);
    const timer=setTimeout(()=>{timedOut=true;child.kill();},30*60*1000);
    child.on('error',err=>{clearTimeout(timer);if(!settled){settled=true;reject(err);}});
    child.on('close',code=>{
      clearTimeout(timer);if(settled)return;settled=true;
      if(timedOut)return reject(Error('Temps limite de compilation (30 minutes) dépassé.\n'+tail.slice(-4000)));
      if(code!==0)return reject(Error('RunUAT BuildPlugin a échoué (code '+code+').\n'+tail.slice(-5000)));
      const built=path.join(p.output,p.name+'.uplugin');
      if(!fs.existsSync(built)||!fs.statSync(built).isFile())
        return reject(Error('RunUAT terminé mais aucun descripteur de plugin compilé trouvé.'));
      const record={schema:'anomalia-native-build',version:1,projectId,
        plugin:source.plugin,platform:'Win64',createdAt:new Date().toISOString(),
        descriptorSha256:crypto.createHash('sha256').update(fs.readFileSync(p.descriptor)).digest('hex'),
        note:'Un plugin a été construit. Sa cuisson et son chargement dans ANOMALIA ne sont pas encore validés.'};
      const recordFile=checkedPath(root,'Dist/'+p.name+'-native-build.json');
      fs.writeFileSync(recordFile,JSON.stringify(record,null,2));
      resolve({built:true,plugin:p.name,output:p.output,record:recordFile,log:tail.slice(-5000),
        requiresGameModLoader:true});
    });
  });
}
module.exports={pluginNameFor,filesFor,scaffoldNativeMod,validateNativeMod,buildStatus,buildNativeMod};
