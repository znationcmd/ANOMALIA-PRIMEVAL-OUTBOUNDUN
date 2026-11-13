"""Extract complete original lots and streets with per-actor, source-bound checkpoints."""
import unreal,os,json,traceback,gc,re,collections
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent))
from city_checkpoint import write_json,source_fingerprint,collapse
root=Path(unreal.Paths.project_dir()).resolve();out=Path(os.environ['SCENE_REPAIR_OUT']);out.mkdir(parents=True,exist_ok=True)
state={'state':'FAILED','sourceWorld':'/Game/Map/Big_City_LVL','scope':'Three complete original lots N465000/N465001/N465002 and surrounding authored streets. This is not the whole 48 km map.'}
def progress(stage,**extra):write_json(out/'city-progress.json',{'stage':stage,**extra});unreal.log('ANOMALIA_CITY_PROGRESS '+stage+' '+json.dumps(extra))
def key(g):return ':'.join(str(int(g.get_editor_property(k))&0xffffffff) for k in ['a','b','c','d'])
def vec(v):return [float(v.x),float(v.y),float(v.z)]
def trans(t):return {'translation':vec(t.translation),'scale':vec(t.scale3d),'quaternion':[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w]}
try:
 if root!=Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal').resolve():raise RuntimeError('Unexpected principal project')
 progress('fingerprinting_original_city')
 fingerprint=source_fingerprint(root);state['sourceFingerprint']=fingerprint
 cache=Path(r'C:\ANOMALIA-Repair\CitySourceCache')/(fingerprint+'.json')
 saved=json.loads(cache.read_text()) if cache.exists() else {'fingerprint':fingerprint,'actors':{}}
 if saved['fingerprint']!=fingerprint:raise RuntimeError('Source checkpoint identity mismatch')
 actors_saved=saved['actors'];progress('asset_inventory',resumedActors=len(actors_saved))
 reg=unreal.AssetRegistryHelpers.get_asset_registry();reg.wait_for_completion()
 architectural=[];categories=collections.Counter()
 for ad in reg.get_all_assets():
  package=str(ad.package_name)
  if str(ad.asset_class_path.asset_name) not in ['StaticMesh','World','Blueprint']:continue
  if any(word in package.lower() for word in ['building','village','house','cottage','barn','town','settlement','farm']):
   architectural.append({'package':package,'class':str(ad.asset_class_path.asset_name)});categories[package.split('/')[2] if package.startswith('/Game/') else 'Other']+=1
 write_json(out/'available-real-building-assets.json',{'assets':architectural,'categories':dict(categories),'note':'Asset inventory does not prove these models are placed, playable or visible in the installed game.'})
 editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);wp=unreal.WorldPartitionBlueprintLibrary
 progress('opening_actual_skarvik_inventory')
 if not editor.load_level('/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1'):raise RuntimeError('Actual SKARVIK cannot open')
 all_descriptors=wp.get_actor_descs() or []
 settlement=[{'label':str(d.label),'guid':key(d.guid),'class':str(d.native_class)} for d in all_descriptors if any(s in str(d.label).lower() for s in ['city','village','town','settlement','house','building','skarvik_final'])]
 write_json(out/'actual-skarvik-architecture-before.json',{'map':'/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1','descriptors':len(all_descriptors),'architecturalDescriptors':settlement,'note':'Read-only inventory; source map not saved or changed.'})
 progress('opening_original_city',resumedActors=len(actors_saved))
 if not editor.load_level('/Game/Map/Big_City_LVL'):raise RuntimeError('Original City Sample world cannot open')
 box=unreal.Box(min=unreal.Vector(-4000,-14000,-50000),max=unreal.Vector(18000,6000,100000))
 desc=[d for d in wp.get_intersecting_actor_descs(box) or [] if not d.actor_is_editor_only]
 desc=[d for d in desc if str(d.label).startswith(('BLDG_','GROUND_C_','GROUND_NC_','GROUND_COLLISION_'))]
 desc=[d for d in desc if str(d.label).startswith('GROUND_') or re.search(r'(?:^|_)N46500[012](?:_|$)',str(d.label))]
 unique={key(d.guid):d for d in desc};desc=list(unique.values())
 # Streets are required geometry, so process them before decorative high-poly props.
 def priority(d):
  label=str(d.label)
  return (0 if label.startswith('GROUND_') else 1 if label.startswith('BLDG_N') else 2 if label.startswith('BLDG_L1_') else 3 if label.startswith('BLDG_ROOFGEO') else 4 if label.startswith('BLDG_COLL_') else 5,label)
 desc.sort(key=priority)
 expected=set(unique)
 if not expected or not set(actors_saved).issubset(expected):raise RuntimeError('Checkpoint actors do not belong to the selected original district')
 for d in desc:
  identity=key(d.guid);label=str(d.label)
  if identity in actors_saved:
   if actors_saved[identity]['label']!=label:raise RuntimeError('Checkpoint actor label changed')
   continue
  progress('loading_original_actor',actor=label,completed=len(actors_saved),selected=len(desc))
  wp.load_actors([d.guid]);loaded=[a for a in actors.get_all_level_actors() if key(a.get_editor_property('actor_guid'))==identity]
  if len(loaded)!=1:raise RuntimeError('Original architectural actor unavailable: '+label)
  actor=loaded[0];batches=[];count=0
  for component in actor.get_components_by_class(unreal.StaticMeshComponent):
   mesh=component.get_editor_property('static_mesh')
   if not mesh:continue
   path=mesh.get_path_name()
   if path.startswith(('/Game/Vehicle/','/Game/Crowd/','/Engine/Editor')):continue
   transforms=[component.get_instance_transform(i,world_space=True) for i in range(component.get_instance_count())] if isinstance(component,unreal.InstancedStaticMeshComponent) else [component.get_world_transform()]
   bounds=mesh.get_bounding_box()
   row={'mesh':path,'materials':[component.get_material(i).get_path_name() if component.get_material(i) else None for i in range(component.get_num_materials())],'visible':bool(component.get_editor_property('visible')) and not bool(component.get_editor_property('hidden_in_game')) and not bool(actor.get_editor_property('hidden')),'collision':component.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION and actor.get_actor_enable_collision(),'localMin':vec(bounds.min),'localMax':vec(bounds.max),'instances':[trans(t) for t in transforms]}
   batches.append(row);count+=len(transforms)
  actors_saved[identity]={'label':label,'sourceGuid':[int(d.guid.get_editor_property(k))&0xffffffff for k in ['a','b','c','d']],'class':actor.get_class().get_path_name(),'instances':count,'root':trans(actor.get_actor_transform()),'batches':batches}
  saved['actors']=actors_saved;write_json(cache,saved)
  actor=None;loaded=[];component=None;mesh=None;transforms=[];batches=[]
  wp.unload_actors([d.guid]);gc.collect();unreal.SystemLibrary.collect_garbage()
  progress('actor_checkpoint_saved',actor=label,completed=len(actors_saved),selected=len(desc),persistentCheckpoint=str(cache))
 if source_fingerprint(root)!=fingerprint:raise RuntimeError('Original architectural source changed during extraction')
 if set(actors_saved)!=expected:raise RuntimeError('Incomplete district extraction')
 actor_rows,batches,count=collapse(actors_saved)
 roads=[{'mesh':b['mesh'],'instances':len(b['instances']),'zMin':min(t['translation'][2] for t in b['instances']),'zMax':max(t['translation'][2] for t in b['instances'])} for b in batches if b['instances'] and any(s in b['mesh'].lower() for s in ['road','sidewalk','street','curb'])]
 floors=sum(len(b['instances']) for b in batches if '_L1_' in b['mesh'] or 'Ground' in b['mesh'] or 'ground' in b['mesh'])
 if count<1000 or floors<100 or not roads or not any('_L1_' in b['mesh'] and b['visible'] for b in batches):raise RuntimeError('Original district lacks complete visible ground floors or streets')
 state.update(state='ORIGINAL_CITY_BLOCK_EXPORTED_WITH_AUTHORED_TRANSFORMS',actors=actor_rows,batches=batches,instances=count,groundFloorInstances=floors,roadMeshes=roads,missing=[],selectedArchitecturalDescriptors=[str(d.label) for d in desc])
 target=root/'Saved/CitySourceCache/original-city-block-repair-v1.json'
 if target.exists():
  previous=json.loads(target.read_text(encoding='utf-8-sig'))
  if previous.get('state')=='ORIGINAL_CITY_BLOCK_EXPORTED_WITH_AUTHORED_TRANSFORMS' and previous.get('sourceFingerprint')!=fingerprint:raise RuntimeError('Existing completed extraction preserved for review')
 write_json(target,state);progress('complete_original_district_exported',instances=count,actors=len(actor_rows),streets=len(roads),groundFloors=floors)
except Exception:state['error']=traceback.format_exc()
finally:write_json(out/'original-city-block.json',state);unreal.SystemLibrary.quit_editor()
