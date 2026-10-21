"""Capture actual GPU views of all imported prototype models, with no drive-test claim."""
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import time
import unreal

GROUP=os.environ.get('ANOMALIA_ASSET_GROUP','Expansion1')
if GROUP not in ['Expansion1','Metro1','NamedVehicles1','Military1']:raise RuntimeError('Unsupported import group')
MAPS={'Expansion1':'Expansion','Metro1':'Metro','NamedVehicles1':'NamedVehicles','Military1':'Military'}
TAG='AnomaliaExpansionSHA' if GROUP=='Expansion1' else 'Anomalia'+GROUP+'SHA'
OUT=Path(os.environ['ANOMALIA_EXPANSION_VISUAL']);OUT.mkdir(parents=True,exist_ok=False)
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),screenshots=[],drivingTested=False,walkingTested=False,multiplayerTested=False)
state=dict(index=0,task=None,until=time.monotonic()+30,busy=False,started=time.monotonic())
views=[]

def finish(error=None):
    if state.get('finishing'):return
    state['finishing']=True;state['busy']=True
    if 'handle' in state:unreal.unregister_slate_post_tick_callback(state.pop('handle'))
    if error:report['error']=str(error)
    else:report['state']='REAL_GPU_CAPTURES_CREATED_NOT_VISUALLY_REVIEWED'
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    state['task']=None
    views.clear()
    for key in ('world','actors','actor','mesh'):
        globals().pop(key,None)
    gc.collect();unreal.SystemLibrary.quit_editor()


def camera():
    name,actor=views[state['index']]
    origin,extent=actor.get_actor_bounds(False);radius=max(extent.x,extent.y,extent.z,100)
    eye=unreal.Vector(origin.x+radius*1.45,origin.y-radius*1.65,origin.z+radius*.85)
    dx,dy,dz=origin.x-eye.x,origin.y-eye.y,origin.z-eye.z
    rotation=unreal.Rotator(pitch=math.degrees(math.atan2(dz,math.hypot(dx,dy))),yaw=math.degrees(math.atan2(dy,dx)),roll=0)
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(eye,rotation)


def tick(delta):
    if state['busy'] or state.get('finishing'):return
    try:
        if time.monotonic()-state['started']>600:raise RuntimeError('Capture timeout')
        if time.monotonic()<state['until']:return
        if state['task'] is None:
            state['busy']=True
            state['task']=unreal.AutomationLibrary.take_high_res_screenshot(1280,720,str(OUT/(views[state['index']][0]+'.png')),delay=1.,force_game_view=True)
            if not state['task'] or not state['task'].is_valid_task():raise RuntimeError('Missing viewport task')
            state['busy']=False;return
        if not state['task'].is_task_done():return
        path=OUT/(views[state['index']][0]+'.png')
        if not path.is_file() or path.stat().st_size<4096:raise RuntimeError('Missing screenshot: '+path.name)
        report['screenshots'].append(dict(model=views[state['index']][0],file=path.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        state['index']+=1
        if state['index']==len(views):finish();return
        state['task']=None;camera();state['until']=time.monotonic()+2
    except Exception as error:finish(error)

try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Maps/ANOMALIA_'+MAPS[GROUP]+'Review_v1'):raise RuntimeError('Missing review level')
    spec=json.loads((Path(unreal.Paths.project_dir())/'SourceAssets'/GROUP/'manifest.json').read_text())
    actors={a.get_actor_label():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
    for item in spec['models']:
        actor=actors.get('ANOMALIA_'+GROUP+'_'+item['id'])
        if not actor:raise RuntimeError('Missing review actor: '+item['id'])
        mesh=actor.get_component_by_class(unreal.StaticMeshComponent).get_editor_property('static_mesh')
        if unreal.EditorAssetLibrary.get_metadata_tag(mesh,TAG)!=item['sha256']:raise RuntimeError('Stale review mesh')
        views.append((item['id'],actor))
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for command in ['r.DynamicGlobalIlluminationMethod 0','r.ReflectionMethod 0','r.Shadow.Virtual.Enable 0','r.Nanite 0','r.AntiAliasingMethod 2','sg.ShadowQuality 1','r.ScreenPercentage 100','t.MaxFPS 20']:
        unreal.SystemLibrary.execute_console_command(world,command)
    unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
    camera();state['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception as error:finish(error)
