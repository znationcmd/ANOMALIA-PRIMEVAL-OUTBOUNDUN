"""Derive corrected E39 parts without replacing any original asset."""
import os,json,hashlib,shutil
from pathlib import Path
from move_hood_liner import GLB,repair
root=Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal');out=Path(os.environ['SCENE_REPAIR_OUT'])
def resolve_source(candidates):
 failures=[]
 for candidate in candidates:
  candidate=Path(candidate)
  if not (candidate/'manifest.json').is_file():continue
  try:
   manifest=json.loads((candidate/'manifest.json').read_text(encoding='utf-8-sig'))
   models=manifest['models']
   names=[p['id'] for p in models]
   required={'body','hood','trunk','door_driver','door_front_right','door_rear_left','door_rear_right','wheel_fl','wheel_fr','wheel_rl','wheel_rr'}
   if len(names)!=len(set(names)) or set(names)!=required:raise ValueError('Expected complete eleven-part E39 v7 manifest')
   for part in models:
    path=(candidate/part['file']).resolve()
    if candidate.resolve() not in path.parents:raise ValueError('Part path outside source directory')
    if hashlib.sha256(path.read_bytes()).hexdigest().lower()!=part['sha256'].lower():raise ValueError('Part checksum mismatch: '+part['id'])
   return candidate,manifest,failures
  except (OSError,ValueError,KeyError,TypeError) as error:
   failures.append({'path':str(candidate),'error':str(error)})
 raise RuntimeError('No complete checksum-verified E39 v7 source: '+json.dumps(failures))

candidates=[root/'SourceAssets/BMWE39Review_v7',Path(r'C:\ANOMALIA-Validation\c40543166274\unreal\SourceAssets\BMWE39Review_v7')]
# Check known project copies; never recurse through unrelated user files.
for project in [Path(r'D:\ANOMALIA\unreal'),Path(r'D:\ANOMALIAZ-PRIGIMALIA\unreal'),Path(r'C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal'),Path(os.environ.get('GITHUB_WORKSPACE',str(root)))/'unreal']:
 candidates.append(project/'SourceAssets/BMWE39Review_v7')
validation=Path(r'C:\ANOMALIA-Validation')
if validation.is_dir():
 for project in sorted(validation.iterdir()):
  if project.is_dir():candidates.append(project/'unreal/SourceAssets/BMWE39Review_v7')
source,manifest,rejected=resolve_source(dict.fromkeys(candidates))
out.mkdir(parents=True,exist_ok=True)
(out/'car-source-resolution.json').write_text(json.dumps({'source':str(source),'parts':len(manifest['models']),'allChecksumsVerified':True,'rejected':rejected},indent=2),encoding='utf-8')
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
