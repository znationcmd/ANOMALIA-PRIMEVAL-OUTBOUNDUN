"""Capture only real Unreal viewport pixels from the existing map; no synthetic images."""
import gc,hashlib,json,math,os,time,traceback
from pathlib import Path
import unreal
OUT=Path(os.environ['ANOMALIA_VISUAL_OUTPUT']);OUT.mkdir(parents=True,exist_ok=True)
REPORT=OUT/'visual-report.json';PACKAGE='/Game/Maps/ANOMALIA_Archipelago_v2'
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),mapPackage=PACKAGE,requestedRHI='D3D11 SM5',headless=False,screenshots=[],gameplayValidated=False,performanceValidated=False)
state=dict(index=0,task=None,until=time.monotonic()+45,frames=[],started=time.monotonic(),busy=False)
# UE coordinates in centimetres; these are views of the real, unchanged archipelago.
views=[
 ('01_archipelago',(0,0,3200000),(0,0,0)),
 ('02_snow_mountains',(-800000,-1020000,250000),(-575000,-725000,160000)),
 ('03_beach',(-1690000,1020000,1800),(-1660000,985000,600)),
 ('04_desert',(1580000,1190000,11000),(1630000,1230000,4500)),
 ('05_detroit_bridge',(1450000,840000,30000),(1475000,900000,3200)),
]
def finish(error=None):
    if error:report['error']=str(error)
    else:report['state']='REAL_VIEWPORT_CAPTURES_CREATED_NOT_VISUALLY_REVIEWED'
    if state['frames']:
        report['editorSlateDeltaMeanMs']=sum(state['frames'])/len(state['frames'])*1000
        report['timingScope']='Editor Slate callback timing, not a gameplay FPS benchmark'
    REPORT.write_text(json.dumps(report,indent=2)+'\n')
    if 'handle' in state:unreal.unregister_slate_post_tick_callback(state['handle'])
    # Release automation UObject wrappers before requesting editor teardown.
    state['task']=None
    gc.collect()
    unreal.SystemLibrary.quit_editor()
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
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(PACKAGE):raise RuntimeError('Real map unavailable')
    # Load known generated geometry for aerial captures without altering streaming rules on disk.
    desc=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
    wanted=[d.guid for d in desc if 'Landscape' in str(d.native_class) or str(d.label).startswith('ANOMALIA_')]
    unreal.WorldPartitionBlueprintLibrary.load_actors(wanted)
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for command in ['r.DynamicGlobalIlluminationMethod 0','r.ReflectionMethod 0','r.Shadow.Virtual.Enable 0','r.Nanite 0','r.AntiAliasingMethod 2','sg.ViewDistanceQuality 1','sg.ShadowQuality 1','sg.EffectsQuality 1','sg.TextureQuality 1','r.ScreenPercentage 100','r.Streaming.PoolSize 256','t.MaxFPS 20']:
        unreal.SystemLibrary.execute_console_command(world,command)
    unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
    set_view();state['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception as error:
    unreal.log_error(traceback.format_exc());finish(error)
