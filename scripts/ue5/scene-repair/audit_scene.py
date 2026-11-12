import unreal,json,os,traceback,collections,shutil
from pathlib import Path
out=Path(os.environ['SCENE_REPAIR_OUT']);root=Path(unreal.Paths.project_dir()).resolve()
r={'state':'FAILED','groups':{},'actors':[]}
def vec(v):return [float(v.x),float(v.y),float(v.z)]
def trans(t):
 q=t.rotation
 return {'translation':vec(t.translation),'scale':vec(t.scale3d),'quaternion':[q.x,q.y,q.z,q.w]}
try:
 if root!=Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal').resolve():raise RuntimeError('Wrong principal project')
 for rel in ['Source/AnomaliaPrimeval/Vehicles/AnomaliaChaosRoadVehicle.cpp','Source/AnomaliaPrimeval/Vehicles/AnomaliaChaosRoadVehicle.h','Source/AnomaliaPrimeval/Vehicles/AnomaliaVehiclePanelComponent.cpp','Source/AnomaliaPrimeval/AnomaliaVisualReviewProbe.cpp','Saved/CitySourceCache/complete-buildings-20261111.json','SourceAssets/BMWE39Review_v7/manifest.json']:
  f=root/rel
  if f.is_file():shutil.copy2(f,out/rel.replace('/','_'))
 for f in [Path(r'C:\ANOMALIA-Validation\c40543166274\unreal\SourceAssets\BMWE39Review_v7\manifest.json')]:
  if f.is_file():shutil.copy2(f,out/'original-e39-manifest.json')
 ed=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);wp=unreal.WorldPartitionBlueprintLibrary
 if not ed.load_level('/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1'):raise RuntimeError('True SKARVIK failed to load')
 desc=wp.get_actor_descs() or []
 prefixes=('SKARVIK_COMPLETE_REAL_BUILDING_','SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_','SKARVIK_FINAL_REAL_CITYSAMPLE_DISTRICT_','ANOMALIA_AUTHENTIC_')
 target=[d for d in desc if str(d.label).startswith(prefixes) or 'BIG_CITY_PLAYER_START' in str(d.label)]
 wp.load_actors([d.guid for d in target])
 region=unreal.Box(min=unreal.Vector(190000,790000,-10000),max=unreal.Vector(220000,820000,60000))
 nearby=wp.get_intersecting_actor_descs(region) or []
 wp.load_actors([d.guid for d in nearby if not d.actor_is_editor_only])
 loaded=actors.get_all_level_actors()
 for a in loaded:
  label=a.get_actor_label()
  if not label.startswith(prefixes) and not isinstance(a,unreal.PlayerStart):continue
  o,e=a.get_actor_bounds(False)
  item={'label':label,'class':a.get_class().get_path_name(),'transform':trans(a.get_actor_transform()),'boundsMin':[o.x-e.x,o.y-e.y,o.z-e.z],'boundsMax':[o.x+e.x,o.y+e.y,o.z+e.z],'components':[]}
  for c in a.get_components_by_class(unreal.StaticMeshComponent):
   mesh=c.get_editor_property('static_mesh')
   if not mesh:continue
   data={'name':c.get_name(),'mesh':mesh.get_path_name(),'transform':trans(c.get_world_transform()),'relativeTransform':trans(c.get_relative_transform())}
   if hasattr(mesh,'get_bounding_box'):
    b=mesh.get_bounding_box();data['localMin']=vec(b.min);data['localMax']=vec(b.max)
   if hasattr(c,'get_editor_property'):
    data['materials']=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())]
   item['components'].append(data)
  r['actors'].append(item)
  group=label.rsplit('_',1)[0] if label.startswith('SKARVIK_COMPLETE_REAL_BUILDING_') else next((p for p in prefixes if label.startswith(p)), 'PlayerStart')
  g=r['groups'].setdefault(group,{'count':0,'min':[float('inf')]*3,'max':[float('-inf')]*3})
  g['count']+=1
  for i in range(3):g['min'][i]=min(g['min'][i],item['boundsMin'][i]);g['max'][i]=max(g['max'][i],item['boundsMax'][i])
 r['state']='TRUE_SKARVIK_SCENE_ASSEMBLY_AUDIT';r['descriptorCount']=len(desc)
except Exception:r['error']=traceback.format_exc()
finally:
 (out/'scene-audit.json').write_text(json.dumps(r,indent=2),encoding='utf-8');unreal.SystemLibrary.quit_editor()
