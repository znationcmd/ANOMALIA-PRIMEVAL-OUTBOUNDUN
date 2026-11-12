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
 material_rows={}
 for ad in reg.get_assets_by_path('/Game/Anomalia/BMWE39Review_v7',recursive=True):
  if str(ad.asset_class_path.asset_name)!='MaterialInstanceConstant':continue
  material=unreal.load_asset(str(ad.package_name))
  material_rows[material.get_path_name()]={'parent':material.get_editor_property('parent').get_path_name(),'scalars':[{'name':str(v.get_editor_property('parameter_info').get_editor_property('name')),'value':v.get_editor_property('parameter_value')} for v in material.get_editor_property('scalar_parameter_values')]}
 (out/'car-material-settings.json').write_text(json.dumps(material_rows,indent=2),encoding='utf-8')
 material=None
 assets=reg.get_all_assets()
 ground=[{'package':str(a.package_name),'class':str(a.asset_class_path.asset_name)} for a in assets if ('forest_ground_04' in str(a.package_name).lower() or str(a.package_name).startswith('/Game/Advanced_Auto_Material/') or str(a.package_name).startswith('/Game/Anomalia/Inhabited_v2/Ground/'))]
 (out/'ground-assets.json').write_text(json.dumps(ground,indent=2),encoding='utf-8')
 assets=[]

 mesh=None;settings=None;ns=None;ad=None;gc.collect()
 if not editor.load_level('/Game/Map/Big_City_LVL'):raise RuntimeError('Original City Sample world did not open')
 box=unreal.Box(min=unreal.Vector(-4000,-14000,-50000),max=unreal.Vector(18000,6000,100000))
 desc=wp.get_intersecting_actor_descs(box) or []
 desc=[d for d in desc if not d.actor_is_editor_only]
 r['descriptors']=[{'label':str(d.label),'class':str(d.native_class)} for d in desc]
 banned=('crowd','masstraffic','vehicle','camera','worldpartition')
 desc=[d for d in desc if str(d.label).startswith(('BLDG_','GROUND_C_','GROUND_NC_','GROUND_COLLISION_'))]
 desc.sort(key=lambda d:(0 if str(d.label).startswith('GROUND_') else 1, str(d.label)))
 r['selectedArchitecturalDescriptors']=[str(d.label) for d in desc]
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
    visible=bool(c.get_editor_property('visible')) and not bool(c.get_editor_property('hidden_in_game')) and not bool(a.get_editor_property('hidden'))
    collision=c.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION and a.get_actor_enable_collision()
    key=json.dumps([path,mats,visible,collision]);row=r['batches'].setdefault(key,{'mesh':path,'materials':mats,'visible':visible,'collision':collision,'instances':[]})
    if 'localMin' not in row:
     bounds=mesh.get_bounding_box();row['localMin']=vec(bounds.min);row['localMax']=vec(bounds.max)
    for t in transforms:
     p=t.translation
     # Keep whole source actors. Clipping individual instances cuts buildings apart.
     row['instances'].append(trans(t));n+=1;count+=1
   r['actors'].append({'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'instances':n,'root':trans(a.get_actor_transform())})
  loaded={};a=None;c=None;mesh=None;transforms=[];t=None
  wp.unload_actors([d.guid for d in batch]);gc.collect()
  if first%48==0:unreal.SystemLibrary.collect_garbage()
  (out/'original-city-block.json').write_text(json.dumps(r),encoding='utf-8')
  if count>80000:raise RuntimeError('Original block exceeds safe instance budget')
 r['batches']=list(r['batches'].values());r['instances']=count
 r['meshCategories']=dict(collections.Counter(x['mesh'].split('/')[2] for x in r['batches'] if x['mesh'].startswith('/Game/')))
 r['groundFloorInstances']=sum(len(x['instances']) for x in r['batches'] if '_L1_' in x['mesh'] or 'Ground' in x['mesh'] or 'ground' in x['mesh'])
 r['roadMeshes']=[{'mesh':x['mesh'],'instances':len(x['instances']),'zMin':min(t['translation'][2] for t in x['instances']),'zMax':max(t['translation'][2] for t in x['instances'])} for x in r['batches'] if x['instances'] and any(s in x['mesh'].lower() for s in ['road','sidewalk','street','curb'])]
 r['state']='ORIGINAL_CITY_BLOCK_EXPORTED_WITH_AUTHORED_TRANSFORMS'
except Exception:r['error']=traceback.format_exc()
finally:
 (out/'original-city-block.json').write_text(json.dumps(r),encoding='utf-8');unreal.SystemLibrary.quit_editor()
