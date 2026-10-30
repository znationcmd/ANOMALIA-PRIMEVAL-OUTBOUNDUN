"""Capture only real Unreal viewport pixels from the existing map; no synthetic images."""
import gc,hashlib,json,math,os,re,time,traceback
from pathlib import Path
import unreal
OUT=Path(os.environ['ANOMALIA_VISUAL_OUTPUT']);OUT.mkdir(parents=True,exist_ok=True)
PHASE=os.environ.get('ANOMALIA_RENDER_PHASE','inspect')
REPORT=OUT/'visual-report.json';PACKAGE=os.environ.get('ANOMALIA_CAPTURE_MAP','/Game/Maps/ANOMALIA_Archipelago_v2')
if PACKAGE not in ('/Game/Maps/ANOMALIA_Archipelago_v2','/Game/Maps/ANOMALIA_Inhabited_v2'):raise RuntimeError('Capture map is not an owned review target')
WORLD_NAME=PACKAGE.rsplit('/',1)[1]
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),mapPackage=PACKAGE,requestedRHI='D3D11 SM5',headless=False,screenshots=[],gameplayValidated=False,performanceValidated=False,renderPhase=PHASE)
state=dict(index=0,task=None,until=time.monotonic()+45,frames=[],started=time.monotonic(),busy=False)
# UE coordinates in centimetres; these are views of the real, unchanged archipelago.
views=[
 ('01_archipelago',(0,0,3200000),(0,0,0)),
 ('02_snow_mountains',(-800000,-1020000,250000),(-575000,-725000,160000)),
 ('03_beach',(-1690000,1020000,1800),(-1660000,985000,600)),
 ('04_desert',(1580000,1190000,11000),(1630000,1230000,4500)),
 ('05_detroit_bridge',(1450000,840000,30000),(1475000,900000,3200)),
]
def street_review_view(east,north,height_metres):
    if not all(math.isfinite(v) for v in (east,north,height_metres)):raise ValueError('Finite street camera position required')
    z=height_metres*100
    return ('05_town_street',(east*100,-(north+100)*100,z+180),(east*100,-(north-30)*100,z+180))
def finish(error=None):
    if state.get("finishing"):return
    state["finishing"]=True;state["busy"]=True
    if "handle" in state:unreal.unregister_slate_post_tick_callback(state.pop("handle"))
    if not error and PHASE=='repair':
        try:
            # Wrapper must first create and verify an immutable backup archive.
            backup=Path(os.environ['ANOMALIA_RENDER_BACKUP'])
            if not backup.is_file():raise RuntimeError('No pre-repair backup exists')
            packages={}
            for obj in [world]+landscapes+terrain_components:
                package=obj.get_outermost();name=package.get_name()
                allowed=name==PACKAGE or name.startswith('/Game/__ExternalActors__/Maps/'+WORLD_NAME+'/') or name.startswith('/Game/__ExternalObjects__/Maps/'+WORLD_NAME+'/')
                if not allowed:raise RuntimeError('Refusing to save unrelated package '+name)
                packages[name]=package
            if not unreal.EditorLoadingAndSavingUtils.save_packages(list(packages.values()),False):raise RuntimeError('Scoped Landscape package save failed')
            report['savedPackages']=sorted(packages)
        except Exception as exc:error=exc
    if error:report['error']=str(error)
    else:report['state']='REAL_VIEWPORT_CAPTURES_CREATED_NOT_VISUALLY_REVIEWED'
    if state['frames']:
        report['editorSlateDeltaMeanMs']=sum(state['frames'])/len(state['frames'])*1000
        report['timingScope']='Editor Slate callback timing, not a gameplay FPS benchmark'
    REPORT.write_text(json.dumps(report,indent=2)+'\n')
    if 'handle' in state:unreal.unregister_slate_post_tick_callback(state['handle'])
    # Release automation UObject wrappers before requesting editor teardown.
    state['task']=None
    # Release retained Python wrappers while their editor objects are still alive.
    # In particular, Landscape components must not outlive native World teardown.
    for key in ('world','landscapes','terrain_components','actors','desc','wanted','a','c','streamable_desc','wp','sites'):
        globals().pop(key,None)
    if 'packages' in locals():packages.clear()
    obj=package=None
    gc.collect()
    # Unload the large scene while editor/render systems still exist, after this
    # capture callback has returned. Never save the temporary blank world.
    state['exit_phase']='unload';state['exit_until']=time.monotonic()+1
    state['exit_handle']=unreal.register_slate_post_tick_callback(exit_tick)

def exit_tick(delta):
    if time.monotonic()<state['exit_until']:return
    handle=state.pop('exit_handle',None)
    if handle is not None:unreal.unregister_slate_post_tick_callback(handle)
    if state['exit_phase']=='unload':
        try:
            blank=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
            if not blank:raise RuntimeError('Cannot release capture world before shutdown')
            blank=None
            gc.collect()
            report['teardown']={'worldReleasedBeforeEditorExit':True,'temporaryWorldSaved':False}
        except Exception as exc:
            report['state']='FAILED';report['error']='Capture world cleanup failed: '+str(exc)
        REPORT.write_text(json.dumps(report,indent=2)+'\n')
        state['exit_phase']='quit';state['exit_until']=time.monotonic()+2
        state['exit_handle']=unreal.register_slate_post_tick_callback(exit_tick)
        return
    gc.collect()
    # Let the command-line Python executor finish on its own next tick, after
    # this callback returns, instead of issuing QUIT_EDITOR from Python/Slate.
    report.setdefault('teardown',{})['pythonExecutorReleased']=True
    REPORT.write_text(json.dumps(report,indent=2)+'\n')
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)

def set_view():
    _,eye,target=views[state['index']];dx,dy,dz=[target[i]-eye[i] for i in range(3)]
    if WORLD_NAME=='ANOMALIA_Inhabited_v2':
        # Stream just the inspected town and nearby foliage. Loading every HISM
        # across 48km simultaneously hung the integrated D3D11 device on reopen.
        previous=state.pop('dynamic_guids',[])
        if previous and not wp.set_archipelago_actors_loaded(previous,False):raise RuntimeError('Prior view unload refused')
        east,north=target[0]/100,-target[1]/100
        nearest=min(sites,key=lambda p:math.hypot(p.x-east,p.y-north))
        prefix=None
        if math.hypot(nearest.x-east,nearest.y-north)<1200:
            prefix=f'ANOMALIA_Inhabited1_settlement_{int((nearest.y+24000)//8000)}_{int((nearest.x+24000)//8000)}_house_'
        selected=[]
        for entry in streamable_desc:
            label=entry['label']
            if prefix and label.startswith(prefix):selected.append(entry['guid']);continue
            if entry['nativeClass']=='/Script/AnomaliaZPrigimalia.AnomaliaZPrigimaliaSceneryCluster':
                cell=re.search(r'_(-?\d+)_(-?\d+)$',label)
                if cell and abs(int(cell[1])*1000+500-east)<1600 and abs(int(cell[2])*1000+500-north)<1600:selected.append(entry['guid'])
        if selected and not wp.set_archipelago_actors_loaded(selected,True):raise RuntimeError('Nearby view load refused')
        state['dynamic_guids']=selected
        report.setdefault('streamedViewActors',[]).append(dict(view=views[state['index']][0],nearbyActors=len(selected),fullWorldForcedLoaded=False))
    rotation=unreal.Rotator(pitch=math.degrees(math.atan2(dz,math.hypot(dx,dy))),yaw=math.degrees(math.atan2(dy,dx)),roll=0)
    editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    editor.set_level_viewport_camera_info(unreal.Vector(*eye),rotation)
    actual_eye,actual_rotation=editor.get_level_viewport_camera_info()
    forward=actual_rotation.get_forward_vector()
    length=math.sqrt(dx*dx+dy*dy+dz*dz)
    alignment=(forward.x*dx+forward.y*dy+forward.z*dz)/length
    if alignment<.999:raise RuntimeError('Viewport camera does not face requested target')
    report.setdefault('cameraChecks',[]).append(dict(view=views[state['index']][0],alignment=alignment,eyeCm=[actual_eye.x,actual_eye.y,actual_eye.z],pitch=actual_rotation.pitch,yaw=actual_rotation.yaw,roll=actual_rotation.roll))
def tick(delta):
    # These native APIs may pump Slate; re-entry must never schedule nested captures.
    if state['busy']:return
    try:
        if time.monotonic()-state['started']>780:raise RuntimeError('Visual capture timed out')
        if time.monotonic()<state['until']:return
        state['frames'].append(float(delta))
        if state['task'] is None:
            state['busy']=True
            name,eye,target=views[state['index']]
            task=unreal.AutomationLibrary.take_high_res_screenshot(1280,720,str(OUT/(name+'.png')),delay=1.,force_game_view=True)
            if not task or not task.is_valid_task():raise RuntimeError('Unreal viewport screenshot task unavailable')
            state['task']=task;state['busy']=False;return
        if not state['task'].is_task_done():return
        name,eye,target=views[state['index']];file=OUT/(name+'.png')
        if not file.is_file() or file.stat().st_size<4096:raise RuntimeError('Missing/empty real screenshot '+name)
        report['screenshots'].append(dict(file=file.name,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),bytes=file.stat().st_size,cameraCm=eye,targetCm=target))
        state['index']+=1
        if state['index']==len(views):finish();return
        state['task']=None;set_view();state['until']=time.monotonic()+15
    except Exception as error:state['busy']=False;unreal.log_error(traceback.format_exc());finish(error)
try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(PACKAGE):raise RuntimeError('Real map unavailable')
    # Load known generated geometry for aerial captures without altering streaming rules on disk.
    wp=unreal.AnomaliaZPrigimaliaWorldImportLibrary
    descriptor_snapshot=json.loads(wp.get_archipelago_actor_descriptors())
    if descriptor_snapshot.get('state')!='COPIED_DESCRIPTOR_VALUES':raise RuntimeError('Owned descriptor snapshot unavailable')
    desc=descriptor_snapshot['actors']
    streamable_desc=[d for d in desc if d['owned'] and ('_house_' in d['label'] or d['nativeClass']=='/Script/AnomaliaZPrigimalia.AnomaliaZPrigimaliaSceneryCluster')] if WORLD_NAME=='ANOMALIA_Inhabited_v2' else []
    dynamic_labels={d['label'] for d in streamable_desc}
    if streamable_desc and not wp.set_archipelago_actors_loaded([d['guid'] for d in streamable_desc],False):raise RuntimeError('Initial local-view unload refused')
    wanted=[d['guid'] for d in desc if d['owned'] and d['label'] not in dynamic_labels]
    report['partitionDescriptors']=dict(total=len(desc),requested=len(wanted),classes=sorted(set(d['nativeClass'] for d in desc)),nativeDescriptorWrappersRetained=False)
    if not wp.set_archipelago_actors_loaded(wanted,True):raise RuntimeError('Landscape and owned view load refused')
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    landscapes=[a for a in actors.get_all_level_actors() if isinstance(a,unreal.LandscapeProxy)]
    terrain_components=[c for a in landscapes for c in a.get_components_by_class(unreal.LandscapeComponent)]
    report['landscapeDiagnostics']=dict(proxies=len(landscapes),components=len(terrain_components),actors=[dict(label=a.get_actor_label(),hiddenInEditor=a.is_temporarily_hidden_in_editor(),hiddenInGame=a.get_editor_property('hidden')) for a in landscapes])
    if len(terrain_components)!=576:raise RuntimeError('Graphical editor did not load all 576 Landscape components')
    # Visibility override only in this unsaved inspection session. Preserve map files.
    for a in landscapes:
        a.set_is_temporarily_hidden_in_editor(False)
    for c in terrain_components:
        c.set_visibility(True,True)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for command in ['ShowFlag.Landscape 1','r.DynamicGlobalIlluminationMethod 0','r.ReflectionMethod 0','r.Shadow.Virtual.Enable 0','r.Nanite 0','r.AntiAliasingMethod 2','sg.ViewDistanceQuality 1','sg.ShadowQuality 1','sg.EffectsQuality 1','sg.TextureQuality 1','r.ScreenPercentage 100','r.Streaming.PoolSize 256','t.MaxFPS 20']:
        unreal.SystemLibrary.execute_console_command(world,command)
    report['renderResourceRefresh']=json.loads(unreal.AnomaliaZPrigimaliaWorldImportLibrary.refresh_archipelago_render_resources(PHASE=='repair'))
    expected='REFRESHED_IN_MEMORY_NOT_VISUALLY_VALIDATED' if PHASE=='repair' else 'INSPECTED_WITHOUT_FORCED_REBUILD'
    if report['renderResourceRefresh'].get('state')!=expected:raise RuntimeError('Landscape inspection/refresh refused')
    entries=report['renderResourceRefresh']['components']
    min_z=min(c['boundsMinZCm'] for c in entries);max_z=max(c['boundsMaxZCm'] for c in entries)
    report['heightBoundsCheck']=dict(minCm=min_z,maxCm=max_z,flatSentinelComponents=sum(abs(c['boundsCenterZCm']+204800)<1 for c in entries))
    if min_z>=-10000 or max_z<=100000 or report['heightBoundsCheck']['flatSentinelComponents']:raise RuntimeError('Persisted Landscape render bounds do not contain archipelago relief')
    if report['renderResourceRefresh']['missingHeightmaps']:raise RuntimeError('Landscape heightmap data is missing')
    unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
    if WORLD_NAME=='ANOMALIA_Inhabited_v2':
        sites=unreal.AnomaliaZPrigimaliaWorldImportLibrary.inhabited_settlement_sites()
        if len(sites)!=27:raise RuntimeError('Expected all 27 inhabited settlements')
        for index,site_index in enumerate((0,13,26),start=1):
            site=sites[site_index];e,n=site.x,site.y
            z=unreal.AnomaliaZPrigimaliaWorldImportLibrary.inhabited_archipelago_height(e,n)*100
            views[index]=(f'0{index+1}_settlement_{site_index}',(e*100-18000,-n*100-18000,z+12000),(e*100,-n*100,z+200))
        report['reviewScope']='Populated archipelago overview, three settlements and a street-height view; interiors and full-map gameplay not certified'
        e,n=sites[13].x,sites[13].y
        views[4]=street_review_view(e,n,unreal.AnomaliaZPrigimaliaWorldImportLibrary.inhabited_archipelago_height(e,n))
    set_view();state['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception as error:
    unreal.log_error(traceback.format_exc());finish(error)
