"""Reassemble authored City Sample streets in the actual SKARVIK, with recoverable backups."""
import unreal,json,os,traceback,shutil,hashlib,gc,math
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve();out=Path(os.environ['SCENE_REPAIR_OUT']);r={'state':'FAILED','map':'/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1','quarantined':[],'meshCompatibility':[]}
def v(a):return [a.x,a.y,a.z]
def backup_asset(asset):
 package=asset.get_path_name().split('.')[0]
 if not package.startswith('/Game/'):raise RuntimeError('Cannot alter engine asset')
 relative=Path('Content')/(package[len('/Game/'):]+'.uasset');source=root/relative;dest=out/'AssetBackup'/relative
 if not source.is_file():raise RuntimeError('Source asset file missing '+str(source))
 if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
def transform(row):
 t=unreal.Transform();t.translation=unreal.Vector(*row['translation']);t.rotation=unreal.Quat(*row['quaternion']);t.scale3d=unreal.Vector(*row['scale']);return t
try:
 if root!=Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal').resolve():raise RuntimeError('Unexpected principal source')
 source=root/'Saved/SceneRepair/43277880597/original-city-block.json';data=json.loads(source.read_text(encoding='utf-8-sig'))
 if data.get('state')!='ORIGINAL_CITY_BLOCK_EXPORTED_WITH_AUTHORED_TRANSFORMS' or data.get('missing'):raise RuntimeError('Complete original-source architectural extraction is required')
 if data['instances']<1000 or data['groundFloorInstances']<100 or not data['roadMeshes']:raise RuntimeError('Source lacks ground floors or roads')
 if not any('_L1_' in b['mesh'] and b['visible'] for b in data['batches']):raise RuntimeError('Original visible ground-floor geometry missing')
 r['sourceExtraction']={'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'instances':data['instances'],'actors':len(data['actors']),'groundFloors':data['groundFloorInstances']}
 # Back up the real world and its external actor packages before any change.
 for rel in ['Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap','Content/__ExternalActors__/Maps/PRIGIMALIA_SKARVIK_FINAL_v1','Content/__ExternalObjects__/Maps/PRIGIMALIA_SKARVIK_FINAL_v1']:
  src=root/rel;dest=out/'WorldBackup'/rel
  if src.is_dir():shutil.copytree(src,dest,dirs_exist_ok=True)
  elif src.is_file():dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
  elif rel.endswith('.umap'):raise RuntimeError('Actual SKARVIK is missing')
 reg=unreal.AssetRegistryHelpers.get_asset_registry();reg.wait_for_completion();editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);wp=unreal.WorldPartitionBlueprintLibrary;meshes=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
 ground=next((unreal.load_asset(p) for p in ['/Game/Anomalia/Inhabited_v2/M_PBRGround','/Game/AnomaliaZPrigimalia/Inhabited_v2/M_PBRGround'] if unreal.EditorAssetLibrary.does_asset_exist(p)),None)
 if not ground:raise RuntimeError('Existing source-verified PBR terrain material missing')
 if not editor.load_level(r['map']):raise RuntimeError('Actual SKARVIK did not open')
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 descriptors=wp.get_actor_descs() or []
 bad_prefixes=('SKARVIK_FINAL_CITYSAMPLE_3D_SOURCE_','SKARVIK_COMPLETE_REAL_BUILDING_BLDG_N465001_SFJ_')
 selected=[d for d in descriptors if str(d.label).startswith(bad_prefixes+('ANOMALIA_AUTHENTIC_',)) or str(d.native_class).endswith('Landscape')]
 wp.load_actors([d.guid for d in selected])
 nearby=wp.get_intersecting_actor_descs(unreal.Box(min=unreal.Vector(180000,775000,-10000),max=unreal.Vector(230000,825000,60000))) or []
 wp.load_actors([d.guid for d in nearby if not d.actor_is_editor_only])
 loaded=actors.get_all_level_actors();cars=[a for a in loaded if a.actor_has_tag('ANOMALIA_AUTHENTIC_E39')];starts=[a for a in loaded if a.actor_has_tag('ANOMALIA_AUTHENTIC_START')]
 if len(cars)!=1 or len(starts)!=1:raise RuntimeError('Expected one native E39 and original authored start')
 car=cars[0];start=starts[0];original_start=start.get_actor_location()
 def trace(x,y,z):
  h=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(x,y,z+400),unreal.Vector(x,y,z-2000),unreal.TraceTypeQuery.ECC_VISIBILITY,True,[car,start],unreal.DrawDebugTrace.NONE)
  if h and h.to_tuple()[0] and h.to_tuple()[6].z>.85:return h.to_tuple()[5]
  return None
 terrain=trace(200100,800000,original_start.z)
 if not terrain:raise RuntimeError('Actual terrain surface not found')
 offset=unreal.Vector(200000,800000,terrain.z)
 batches=[];seen_meshes={};road_choices=[]
 for row in data['batches']:
  mesh=unreal.load_asset(row['mesh'])
  if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError('Missing original City Sample mesh '+row['mesh'])
  if row['mesh'] not in seen_meshes:
   ns=meshes.get_nanite_settings(mesh)
   # This PC uses the real DX11/SM5 launch profile. Preserve the original
   # source mesh before enabling full conventional geometry for that profile.
   if ns.enabled:
    backup_asset(mesh);ns.enabled=False;meshes.set_nanite_settings(mesh,ns,apply_changes=True)
    if not unreal.EditorAssetLibrary.save_loaded_asset(mesh,False):raise RuntimeError('SM5 mesh compatibility save failed')
   vertices=meshes.get_number_verts(mesh,0)
   if vertices<3:raise RuntimeError('Source mesh has no conventional render geometry '+row['mesh'])
   r['meshCompatibility'].append({'mesh':row['mesh'],'verts':vertices,'naniteDisabledForActualSM5PC':True});seen_meshes[row['mesh']]=mesh
  batch=unreal.AnomaliaCityMeshBatch();batch.set_editor_property('mesh',mesh);batch.set_editor_property('materials',[unreal.load_asset(p) if p else None for p in row['materials']]);batch.set_editor_property('visible',row['visible']);batch.set_editor_property('collision',row['collision']);batch.set_editor_property('instances',[transform(t) for t in row['instances']]);batches.append(batch)
  if row['visible'] and '/Road/' in row['mesh'] and 'SM_ROAD_' in row['mesh'] and 'sidewalk' not in row['mesh'].lower():
   for t in row['instances']:
    center=unreal.Vector(*[(a+b)/2 for a,b in zip(row['localMin'],row['localMax'])]);tr=transform(t);point=unreal.MathLibrary.transform_location(tr,center)
    if abs(point.z)<150 and -2000<point.x<16000 and -12000<point.y<4000:road_choices.append((point.x**2+point.y**2,point,tr))
 if not road_choices:raise RuntimeError('No original street surface available for a real spawn')
 existing=[a for a in loaded if a.actor_has_tag('ANOMALIA_ORIGINAL_CITY_BLOCK_V1')]
 if existing:raise RuntimeError('A source city block already exists; inspect it before replacing it')
 block=actors.spawn_actor_from_class(unreal.AnomaliaCityBlock,offset);block.set_actor_label('ANOMALIA_ORIGINAL_CITYSAMPLE_STREETS_V1');block.tags=[unreal.Name('ANOMALIA_ORIGINAL_CITY_BLOCK_V1')];block.set_editor_property('is_spatially_loaded',False);block.set_editor_property('source_world','/Game/Map/Big_City_LVL');block.set_editor_property('batches',batches);block.rebuild_city()
 if block.get_original_instance_count()!=data['instances']:raise RuntimeError('Original component instances not preserved')
 # Retire the known gallery fragments and the incomplete floating upper tower.
 # Packages are backed up; actors remain available for inspection in the editor.
 for a in loaded:
  if a.get_actor_label().startswith(bad_prefixes):
   r['quarantined'].append(a.get_actor_label());a.set_editor_property('is_editor_only_actor',True);a.set_actor_hidden_in_game(True);a.set_actor_enable_collision(False)
   for c in a.get_components_by_class(unreal.PrimitiveComponent):c.set_visibility(False);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
 if len(r['quarantined'])!=1280:raise RuntimeError('Expected exactly the 720 gallery pieces and 560 incomplete tower pieces')
 # Use the existing scanned ground material, preserving all landscape height data.
 proxies=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
 for a in proxies:a.set_editor_property('landscape_material',ground)
 if not proxies:raise RuntimeError('Actual landscape proxies not loaded')
 r['terrain']={'material':ground.get_path_name(),'loadedProxies':len(proxies),'heightmapModified':False}
 # Keep the actual native E39, its physical rig and its interaction identities.
 manifest=json.loads((root/'SourceAssets/BMWE39RoadPresentation_v8/manifest.json').read_text());parts={p['id']:unreal.load_asset(p['objectPath']) for p in manifest['models']}
 if any(a is None for a in parts.values()):raise RuntimeError('Corrected car parts are missing')
 car.set_editor_property('road_body_mesh',parts['body']);car.set_editor_property('driver_door_mesh',parts['door_driver']);car.set_editor_property('road_wheel_mesh',parts['wheel_fl']);car.set_editor_property('road_wheel_meshes',[parts[n] for n in ['wheel_fl','wheel_fr','wheel_rl','wheel_rr']]);car.set_editor_property('engine_bay_mesh',unreal.load_asset('/Game/Anomalia/E39EngineBay_v1/SM_engine_bay'));car.set_editor_property('use_authored_road_cameras',True)
 definitions=car.get_editor_property('additional_panel_definitions')
 for d in definitions:d.set_editor_property('mesh',parts[str(d.get_editor_property('panel_id'))])
 car.set_editor_property('additional_panel_definitions',definitions)
 parking=None
 for _,point,tr in sorted(road_choices,key=lambda x:x[0]):
  q=point+offset;surface=trace(q.x,q.y,q.z+200)
  if not surface or abs(surface.z-q.z)>80:continue
  floors=[trace(q.x+x,q.y+y,surface.z) for x,y in [(150,-76),(150,75),(-131,-76),(-131,75)]]
  if all(floors) and max(f.z for f in floors)-min(f.z for f in floors)<20:parking=surface;break
 if parking is None:raise RuntimeError('Actual street could not support all four wheels')
 car.set_actor_location(parking+unreal.Vector(0,0,100),False,True);car.set_actor_rotation(unreal.Rotator(),False)
 spawn=trace(parking.x-600,parking.y-100,parking.z)
 if not spawn:raise RuntimeError('No real pedestrian support beside the car')
 start.set_actor_location(spawn+unreal.Vector(0,0,120),False,True);start.set_actor_rotation(unreal.Rotator(),False)
 if not car.has_valid_road_rig():raise RuntimeError('Native rig rejected corrected art')
 if not editor.save_all_dirty_levels() or not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):raise RuntimeError('Actual scene did not save')
 r.update(state='REAL_SKARVIK_SCENE_SAVED_NOT_YET_NATIVE_VISUALLY_ACCEPTED',originalSourceMap='/Game/Map/Big_City_LVL',carPosition=v(car.get_actor_location()),startPosition=v(start.get_actor_location()),cityOffset=v(offset),instances=block.get_original_instance_count())
except Exception:r['error']=traceback.format_exc()
finally:(out/'authored-real-scene.json').write_text(json.dumps(r,indent=2),encoding='utf-8');unreal.SystemLibrary.quit_editor()
