import unreal,json,os,traceback,gc,collections
from pathlib import Path
out=Path(os.environ['SCENE_REPAIR_OUT']);r={'state':'FAILED','actors':[],'batches':{},'missing':[],'roadSamples':[]}
def vec(v):return [float(v.x),float(v.y),float(v.z)]
def trans(t):
 q=t.rotation
 return {'translation':vec(t.translation),'scale':vec(t.scale3d),'quaternion':[q.x,q.y,q.z,q.w]}
try:
 editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);wp=unreal.WorldPartitionBlueprintLibrary
 meshes=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem);reg=unreal.AssetRegistryHelpers.get_asset_registry();reg.wait_for_completion()
 car=[]
 for ad in reg.get_assets_by_path('/Game/Anomalia/BMWE39Review_v7',recursive=True):
  if str(ad.asset_class_path.asset_name)!='StaticMesh':continue
  mesh=unreal.load_asset(str(ad.package_name));settings=meshes.get_lod_build_settings(mesh,0);ns=meshes.get_nanite_settings(mesh)
  car.append({'path':mesh.get_path_name(),'verts':meshes.get_number_verts(mesh,0),'nanite':ns.enabled,'fallbackPercent':ns.fallback_percent_triangles,'fallbackError':ns.fallback_relative_error,'settings':{k:str(settings.get_editor_property(k)) for k in ['recompute_normals','recompute_tangents','compute_weighted_normals','use_high_precision_tangent_basis','build_scale3d']}})
 (out/'car-mesh-settings.json').write_text(json.dumps(car,indent=2),encoding='utf-8')
 mesh=None;settings=None;ns=None;ad=None;gc.collect()
 if not editor.load_level('/Game/Map/Big_City_LVL'):raise RuntimeError('Original City Sample world did not open')
 box=unreal.Box(min=unreal.Vector(-4000,-14000,-50000),max=unreal.Vector(18000,6000,100000))
 desc=wp.get_intersecting_actor_descs(box) or []
 desc=[d for d in desc if not d.actor_is_editor_only]
 r['descriptors']=[{'label':str(d.label),'class':str(d.native_class)} for d in desc]
 banned=('crowd','masstraffic','vehicle','camera','worldpartition')
 desc=[d for d in desc if not any(s in (str(d.native_class)+' '+str(d.label)).lower() for s in banned)]
 count=0
 for first in range(0,len(desc),12):
  batch=desc[first:first+12];wp.load_actors([d.guid for d in batch]);loaded={a.get_actor_label():a for a in actors.get_all_level_actors()}
  for d in batch:
   a=loaded.get(str(d.label))
   if not a:r['missing'].append(str(d.label));continue
   n=0
   for c in a.get_components_by_class(unreal.StaticMeshComponent):
    mesh=c.get_editor_property('static_mesh')
    if not mesh:continue
    path=mesh.get_path_name()
    if path.startswith(('/Game/Vehicle/','/Game/Crowd/','/Engine/Editor')):continue
    transforms=([c.get_instance_transform(i,world_space=True) for i in range(c.get_instance_count())] if isinstance(c,unreal.InstancedStaticMeshComponent) else [c.get_world_transform()])
    mats=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())]
    key=json.dumps([path,mats]);row=r['batches'].setdefault(key,{'mesh':path,'materials':mats,'instances':[]})
    for t in transforms:
     p=t.translation
     if not (-5000<=p.x<=19000 and -15000<=p.y<=7000):continue
     row['instances'].append(trans(t));n+=1;count+=1
   r['actors'].append({'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'instances':n,'root':trans(a.get_actor_transform())})
  loaded={};a=None;c=None;mesh=None;transforms=[];t=None
  wp.unload_actors([d.guid for d in batch]);gc.collect()
  if first%48==0:unreal.SystemLibrary.collect_garbage()
  (out/'original-city-block.json').write_text(json.dumps(r),encoding='utf-8')
  if count>40000:raise RuntimeError('Original block exceeds safe instance budget')
 r['batches']=list(r['batches'].values());r['instances']=count
 r['meshCategories']=dict(collections.Counter(x['mesh'].split('/')[2] for x in r['batches'] if x['mesh'].startswith('/Game/')))
 r['groundFloorInstances']=sum(len(x['instances']) for x in r['batches'] if '_L1_' in x['mesh'] or 'Ground' in x['mesh'] or 'ground' in x['mesh'])
 r['roadMeshes']=[{'mesh':x['mesh'],'instances':len(x['instances']),'zMin':min(t['translation'][2] for t in x['instances']),'zMax':max(t['translation'][2] for t in x['instances'])} for x in r['batches'] if x['instances'] and any(s in x['mesh'].lower() for s in ['road','sidewalk','street','curb'])]
 r['state']='ORIGINAL_CITY_BLOCK_EXPORTED_WITH_AUTHORED_TRANSFORMS'
except Exception:r['error']=traceback.format_exc()
finally:
 (out/'original-city-block.json').write_text(json.dumps(r),encoding='utf-8');unreal.SystemLibrary.quit_editor()
