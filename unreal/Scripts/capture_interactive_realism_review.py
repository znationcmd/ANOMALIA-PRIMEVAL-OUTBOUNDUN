"""Capture actual Unreal pixels of isolated licensed model assets."""
import gc,hashlib,json,math,os,time,traceback
from pathlib import Path
import unreal
OUT=Path(os.environ['ANOMALIA_VISUAL_OUTPUT']);OUT.mkdir(parents=True,exist_ok=True)
PHASE='inspect'
PACKAGE='/Game/Maps/ANOMALIA_InteractiveRealismReview_v1'
REPORT=OUT/'visual-report.json'
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA'),mapPackage=PACKAGE,
 requestedRHI='D3D11 SM5',screenshots=[],gameplayValidated=False,performanceValidated=False)
state=dict(index=0,task=None,until=time.monotonic()+45,frames=[],started=time.monotonic(),busy=False)
views=[]
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
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(PACKAGE):raise RuntimeError('Review map not found')
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for command in ['r.DynamicGlobalIlluminationMethod 0','r.ReflectionMethod 0','r.Shadow.Virtual.Enable 0','r.Nanite 0','r.AntiAliasingMethod 2','sg.ShadowQuality 2','sg.TextureQuality 2','r.ScreenPercentage 100','r.Streaming.PoolSize 512','t.MaxFPS 20']:
        unreal.SystemLibrary.execute_console_command(world,command)
    unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    wanted=['wood_house_enterable','modular_shed_interior','sports_car_930_review']
    for identifier in wanted:
        found=[a for a in actors.get_all_level_actors() if a.get_actor_label()=='Review_'+identifier]
        if len(found)!=1:raise RuntimeError('Missing unique model actor: '+identifier)
        origin,extent=found[0].get_actor_bounds(False)
        target=(origin.x,origin.y,origin.z)
        size=max(extent.x,extent.y,extent.z)*2
        for suffix,dx,dy in [('front',1,-1),('rear',-1,1)]:
            eye=(origin.x+dx*size*.85,origin.y+dy*size*.85,origin.z+size*.55)
            views.append((identifier+'_'+suffix,eye,target))
    found=None
    set_view();state['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception as error:
    unreal.log_error(traceback.format_exc());finish(error)

