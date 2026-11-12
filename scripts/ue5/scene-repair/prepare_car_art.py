"""Derive corrected E39 parts without replacing any original asset."""
import os,json,hashlib,shutil
from pathlib import Path
from move_hood_liner import GLB,repair
root=Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal');out=Path(os.environ['SCENE_REPAIR_OUT'])
source=next((p for p in [root/'SourceAssets/BMWE39Review_v7',Path(r'C:\ANOMALIA-Validation\c40543166274\unreal\SourceAssets\BMWE39Review_v7')] if (p/'body.glb').is_file() and (p/'hood.glb').is_file()),None)
if not source:raise RuntimeError('Original complete E39 source parts missing')
manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8-sig'))
for part in manifest['models']:
 p=source/part['file']
 if hashlib.sha256(p.read_bytes()).hexdigest()!=part['sha256']:raise RuntimeError('Original E39 part changed: '+part['id'])
target=root/'SourceAssets/BMWE39RoadPresentation_v8';target.mkdir(parents=True,exist_ok=True)
liner=repair(source,target);changes=[]
for part in manifest['models']:
 name=part['id'];p=target/part['file'];glb=GLB(p if name in ['body','hood'] else source/part['file'])
 for m in glb.j['materials']:
  key=m.get('name','').lower();pbr=m.setdefault('pbrMetallicRoughness',{})
  if key=='body':pbr.update(roughnessFactor=.30,metallicFactor=.35)
  if key in ['window','glass']:
   rgba=pbr.get('baseColorFactor',[1,1,1,1]);rgba[:3]=[.72,.78,.82];rgba[3]=.14 if key=='window' else .22
   pbr.update(baseColorFactor=rgba,metallicFactor=0,roughnessFactor=.075);m['alphaMode']='BLEND';m['doubleSided']=True
  if any(x in key for x in ['leather','fabric','mottled','plastic']):pbr.update(metallicFactor=0,roughnessFactor=.68)
 glb.save(p);part['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();part['bytes']=p.stat().st_size;part['objectPath']='/Game/Anomalia/BMWE39RoadPresentation_v8/'+name+'/SM_'+name
manifest['presentationRepair']={'hoodLiner':liner,'paintRoughness':.30,'windowOpacity':.14,'originalSourceRetained':str(source),'nativeVisualAcceptance':False}
(target/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
credits=source/'CREDITS.md'
if credits.exists():shutil.copy2(credits,target/'CREDITS.md')
(out/'car-art-prepared.json').write_text(json.dumps(manifest['presentationRepair'],indent=2),encoding='utf-8');print(json.dumps(manifest['presentationRepair']))
