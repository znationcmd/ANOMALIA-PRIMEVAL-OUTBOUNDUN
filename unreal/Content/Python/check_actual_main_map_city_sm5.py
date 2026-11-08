"""Inspect installed main SKARVIK only, then attempt isolated-profile rendered PIE. Never save a map."""
import pathlib,os,json,time,hashlib,re,traceback,unreal
ROOT=pathlib.Path(r'D:\ANOMALIA\unreal');OUT=pathlib.Path(os.environ['MAIN_MAP_OUT'])
P=json.loads((OUT/'main-map-preflight.json').read_text(encoding='utf-8'))
assert pathlib.Path(unreal.Paths.project_content_dir()).resolve()==(ROOT/'Content').resolve(),'Wrong project'
MAP=P['mainMap'];levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);meshes=unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
report={'map':MAP,'project':str(ROOT),'state':'STARTED','mapsSaved':0,'newMapsCreated':0,'actorsCreated':0,'otherMapsOpened':[],'cityCandidates':0,'cityActorsInspected':0,'components':[],'errors':[],'allCitySampleBuildingsInstalled':False,'allCitySampleBuildingsSM5Validated':False,'PIEPassed':False,'fullCityRendered':False,'runtimeProfileIsolated':False,'materialProblems':[],'levelInstances':[]}
started=time.monotonic();state={'phase':'INIT','index':0,'phaseTime':time.monotonic(),'loaded':[]};handle=None;cache={};screens=[]
def save():
 report['elapsedSeconds']=time.monotonic()-started
 (OUT/'main-map-city-sm5.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print('ACTUAL_MAIN_MAP_SM5 '+json.dumps({k:report[k] for k in ['map','state','cityCandidates','cityActorsInspected','PIEPassed','allCitySampleBuildingsInstalled']}),flush=True)
def package(world):return re.sub(r'UEDPIE_\d+_','',world.get_path_name().split('.')[0]) if world else ''
def city_label(label):
 upper=label.upper()
 return upper.startswith('BLDG_') or ('CITYSAMPLE' in upper and ('SOURCE' in upper or 'DISTRICT' in upper))
def finish(error=None):
 global handle
 if error:report['errors'].append(str(error))
 try:
  if levels.is_in_play_in_editor():levels.editor_request_end_play()
 except Exception:pass
 if state.get('loaded'):
  try:unreal.WorldPartitionBlueprintLibrary.unload_actors(state['loaded'])
  except Exception as exc:report['errors'].append('Unload: '+str(exc))
 report['screenshots']=[str(p) for p in screens if p.is_file()]
 report['state']='CHECK_FINISHED_WITH_REMAINING_VALIDATION' if not report['errors'] else 'CHECK_FAILED_WITH_EVIDENCE'
 save()
 if handle is not None:unreal.unregister_slate_post_tick_callback(handle);handle=None
 unreal.SystemLibrary.quit_editor()
def inspect(actor):
 label=actor.get_actor_label();report['cityActorsInspected']+=1
 for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
  mesh=comp.get_editor_property('static_mesh')
  if not mesh:report['errors'].append('Missing mesh on '+label);continue
  path=mesh.get_path_name()
  if path not in cache:
   slots=list(mesh.get_editor_property('static_materials'));materials=[]
   for index,slot in enumerate(slots):
    material=slot.get_editor_property('material_interface')
    materials.append(material.get_path_name() if material else None)
    if not material:report['materialProblems'].append({'mesh':path,'slot':index,'reason':'NULL_MATERIAL'})
   lods=meshes.get_lod_count(mesh);verts=meshes.get_number_verts(mesh,0) if lods else 0
   cache[path]={'mesh':path,'lodCount':lods,'lod0Vertices':verts,'fallbackGeometryPresent':lods>0 and verts>0,'materials':materials,'naniteAssetEnabled':bool(mesh.get_editor_property('nanite_settings').enabled)}
  report['components'].append({'actor':label,'component':comp.get_name(),'collision':str(comp.get_collision_enabled()),**cache[path]})
def screenshot(name):
 path=OUT/(name+'.png');screens.append(path)
 task=unreal.AutomationLibrary.take_high_res_screenshot(1280,720,str(path),delay=1.0)
 state.setdefault('screenshotTasks',[]).append(task)
def tick(delta):
 try:
  now=time.monotonic()
  if now-started>35*60:finish('Main-map validation time budget reached; results are partial');return
  phase=state['phase']
  if phase=='INIT':
   world=editor.get_editor_world()
   if package(world)!=MAP:
    if not levels.load_level(MAP):raise RuntimeError('Configured main map cannot be loaded')
    world=editor.get_editor_world()
   if package(world)!=MAP:raise RuntimeError('Actual editor world differs from installed main route')
   report['actualEditorWorld']=world.get_path_name()
   browser=getattr(unreal,'AnomaliaServerBrowserLibrary',None)
   if browser and hasattr(browser,'get_world_choices'):
    route=[x for x in browser.get_world_choices() if str(x.map_id)=='archipelago-v2']
    report['loadedNativeSkarvikRoute']=str(route[0].world_package) if route else None
    if route and P['basis']=='INSTALLED_NATIVE_SKARVIK_WORLD_CHOICE' and str(route[0].world_package)!=MAP:raise RuntimeError('Compiled map route differs from installed source; do not validate the wrong world')
   elif P['basis']=='INSTALLED_NATIVE_SKARVIK_WORLD_CHOICE':
    raise RuntimeError('Installed native browser route cannot be compared; preserve main-map identity guard')
   else:report['loadedNativeBrowserUnavailable']=True
   for var in ['r.Nanite','r.DynamicGlobalIlluminationMethod','r.ReflectionMethod','r.Shadow.Virtual.Enable']:
    unreal.SystemLibrary.execute_console_command(world,var+' 0')
   report['testRenderingOverrides']={v:unreal.SystemLibrary.get_console_variable_int_value(v) for v in ['r.Nanite','r.DynamicGlobalIlluminationMethod','r.ReflectionMethod','r.Shadow.Virtual.Enable']}
   descs=list(unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or [])
   state['candidates']=[d for d in descs if city_label(str(d.label))]
   report['mainMapActorDescriptors']=len(descs);report['cityCandidates']=len(state['candidates'])
   report['cityActorDescriptorLabels']=[str(d.label) for d in state['candidates']]
   for actor in actors.get_all_level_actors():
    if 'LevelInstance' in actor.get_class().get_name():
     record={'actor':actor.get_actor_label(),'class':actor.get_class().get_name()}
     try:record['worldAsset']=str(actor.get_editor_property('world_asset'))
     except Exception as exc:record['worldAssetReadError']=str(exc)
     report['levelInstances'].append(record)
   state['baselineActors']={a.get_path_name() for a in actors.get_all_level_actors()}
   if not descs:
    for actor in actors.get_all_level_actors():
     if city_label(actor.get_actor_label()):inspect(actor)
   state['phase']='BATCH';save();return
  if phase=='BATCH':
   if state['loaded']:
    unreal.WorldPartitionBlueprintLibrary.unload_actors(state['loaded']);state['loaded']=[];unreal.collect_garbage()
   candidates=state['candidates'];i=state['index']
   if i>=len(candidates):
    if not report['cityActorsInspected']:report['errors'].append('No City Sample building actors verified on the actual main map')
    if not P['PIEAllowedWithIsolatedProfile']:
     state['finalError']='Installed GameMode cannot prove an isolated automation profile on this map; PIE not started'
     screenshot('main-map-editor-profile-blocked');state['phase']='SAFE_RENDER_ONLY';state['phaseTime']=now;return
    levels.editor_request_begin_play();state['phase']='WAIT_PIE';state['phaseTime']=now;save();return
   batch=candidates[i:i+6];state['index']+=len(batch)
   unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in batch]);state['loaded']=[d.guid for d in batch]
   by_label={}
   for actor in actors.get_all_level_actors():by_label.setdefault(actor.get_actor_label(),[]).append(actor)
   for desc in batch:
    found=by_label.get(str(desc.label),[])
    if len(found)!=1:report['errors'].append('Missing or ambiguous loaded actor: '+str(desc.label));continue
    inspect(found[0])
   if i==0:
    found=by_label.get(str(batch[0].label),[])
    if found:
     p=found[0].get_actor_location();unreal.EditorLevelLibrary.set_level_viewport_camera_info(p+unreal.Vector(-2500,-2500,1500),unreal.Rotator(-15,45,0))
     screenshot('main-map-city-first-group');state['phase']='WAIT_SHOT';state['phaseTime']=now
   save();return
  if phase=='SAFE_RENDER_ONLY':
   if now-state['phaseTime']>8:finish(state['finalError'])
   return
  if phase=='WAIT_SHOT':
   if now-state['phaseTime']>8:state['phase']='BATCH'
   return
  if phase=='WAIT_PIE':
   world=editor.get_game_world()
   if not world:
    if now-state['phaseTime']>90:finish('PIE did not produce a game world')
    return
   if package(world)!=MAP:raise RuntimeError('PIE opened a different map: '+package(world))
   mode=unreal.GameplayStatics.get_game_mode(world);actual=str(mode.get_editor_property('server_id')) if mode else ''
   report['PIEWorld']=world.get_path_name();report['PIEServerId']=actual
   if actual!=os.environ['MAIN_MAP_TEST_PROFILE']:raise RuntimeError('PIE save profile is not isolated')
   report['runtimeProfileIsolated']=True;state['phase']='PIE_SAMPLE';state['phaseTime']=now;state['frames']=[];screenshot('main-map-pie');return
  if phase=='PIE_SAMPLE':
   if package(editor.get_game_world())!=MAP:raise RuntimeError('Unexpected world travel during main-map PIE')
   state['frames'].append(float(delta)*1000)
   if now-state['phaseTime']>20:
    samples=state['frames'];report['PIEEditorTickSamples']=len(samples);report['PIEMeanEditorTickMs']=sum(samples)/len(samples) if samples else None
    report['PIEPassed']=bool(samples and report['runtimeProfileIsolated']);levels.editor_request_end_play();state['phase']='END';state['phaseTime']=now
   return
  if phase=='END' and now-state['phaseTime']>5:finish()
 except Exception as exc:
  report['traceback']=traceback.format_exc();finish(exc)
save();handle=unreal.register_slate_post_tick_callback(tick)
