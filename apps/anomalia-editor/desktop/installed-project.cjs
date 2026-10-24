'use strict';
const fs=require('node:fs');
const path=require('node:path');
const MAPS=new Set(['/Game/Maps/ANOMALIA_Archipelago_v2','/Game/Maps/ANOMALIA_Inhabited_v2']);
const inside=(base,file)=>{const rel=path.relative(base,file);return rel!==''&&rel!=='..'&&!rel.startsWith('..'+path.sep)&&!path.isAbsolute(rel);};
function readJson(filename){
 const stat=fs.statSync(filename);
 if(!stat.isFile()||stat.size>1024*1024)throw Error('Métadonnées de projet invalides.');
 return JSON.parse(fs.readFileSync(filename,'utf8').replace(/^\uFEFF/,''));
}
// Re-read active.json on every scan, so an installed update changes the project
// without copying user scenes or persisting an obsolete version directory.
function discoverInstalledProject(localAppData=process.env.LOCALAPPDATA){
 if(!localAppData)return null;
 const root=path.join(localAppData,'CMD','ANOMALIA-UE5');
 if(!fs.existsSync(path.join(root,'active.json')))return null;
 const owner=readJson(path.join(root,'owner.json'));
 if(owner.product!=='ANOMALIA-UE5-EDITOR-v1')throw Error('Installation Unreal non reconnue.');
 const active=readJson(path.join(root,'active.json'));
 if(active.state!=='VALIDATED_EDITOR_PROJECT_INSTALLED'||!(/^[a-f0-9]{40}$/.test(active.commit))||
    typeof active.project!=='string'||!path.isAbsolute(active.project)||path.basename(active.project)!=='AnomaliaPrimeval.uproject')throw Error('Version Unreal active invalide.');
 const versions=fs.realpathSync(path.join(root,'versions'));
 if(!inside(fs.realpathSync(root),versions))throw Error('Le dossier de versions sort de l’installation.');
 const project=fs.realpathSync(active.project);
 if(!inside(versions,project)||path.basename(path.dirname(project))!==active.commit)throw Error('Le projet actif sort du dossier de versions.');
 const config=readJson(project);
 if(!Array.isArray(config.Modules))throw Error('Projet Unreal incomplet.');
 const projectRoot=path.dirname(project);
 const mapPackage=MAPS.has(active.mapPackage)?active.mapPackage:'/Game/Maps/ANOMALIA_Archipelago_v2';
 const mapFile=path.join(projectRoot,'Content',...mapPackage.slice('/Game/'.length).split('/'))+'.umap';
 if(!fs.statSync(mapFile).isFile())throw Error('La carte active est absente du projet installé.');
 return {project,projectRoot,commit:active.commit,mapPackage,engineRoot:active.engineRoot,
  automatic:true,source:'owned-installed-project'};
}
module.exports={discoverInstalledProject};
