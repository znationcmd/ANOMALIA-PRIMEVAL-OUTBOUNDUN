"""Actual GPU viewport captures and editor physics traces; never modifies a level."""
import gc,hashlib,json,math,os,time
from pathlib import Path
import unreal
OUT=Path(os.environ['ANOMALIA_LOT1_VISUAL']);OUT.mkdir(parents=True,exist_ok=False)
report=dict(state='FAILED',sourceCommit=os.environ.get('GITHUB_SHA','manual'),screenshots=[],collisionChecks=[],drivingTested=False,walkingTested=False)
state=dict(index=0,task=None,until=time.monotonic()+30,busy=False,started=time.monotonic())
views=[('hlm',(-4700,1800,2200),(-2400,-800,1000)),('villa',(4500,4000,1500),(2500,1800,100)) ,('quad',(-350,-1100,230),(-700,-700,65)),('snowmobile',(320,-1100,210),(0,-700,70)),('jetski',(1000,-1100,240),(650,-700,55)),('zodiac',(1750,-1200,290),(1300,-700,40)),('house',(-1800,2100,850),(-750,700,160)),('garage',(1700,2000,750),(750,700,180))]
def finish(error=None):
 if state.get('finishing'):return
 state['finishing']=True;state['busy']=True
 if 'handle' in state:unreal.unregister_slate_post_tick_callback(state.pop('handle'))
 if error:report['error']=str(error)
 else:report['state']='REAL_GPU_VIEWS_AND_EDITOR_COLLISION_TRACES_PASSED'
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');state['task']=None;gc.collect();unreal.SystemLibrary.quit_editor()
def camera():
 _,eye,target=views[state['index']];dx,dy,dz=[target[i]-eye[i] for i in range(3)]
 unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(*eye),unreal.Rotator(pitch=math.degrees(math.atan2(dz,math.hypot(dx,dy))),yaw=math.degrees(math.atan2(dy,dx)),roll=0))
def tick(delta):
 if state['busy'] or state.get('finishing'):return
 try:
  if time.monotonic()-state['started']>600:raise RuntimeError('Capture timed out')
  if time.monotonic()<state['until']:return
  if state['task'] is None:
   state['busy']=True
   state['task']=unreal.AutomationLibrary.take_high_res_screenshot(1280,720,str(OUT/(views[state['index']][0]+'.png')),delay=1.,force_game_view=True)
   if not state['task'] or not state['task'].is_valid_task():raise RuntimeError('Missing viewport task')
   state['busy']=False;return
  if not state['task'].is_task_done():return
  f=OUT/(views[state['index']][0]+'.png')
  if not f.is_file() or f.stat().st_size<4096:raise RuntimeError('Empty screenshot')
  report['screenshots'].append(dict(file=f.name,bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
  state['index']+=1
  if state['index']==len(views):finish();return
  state['task']=None;camera();state['until']=time.monotonic()+8
 except Exception as exc:finish(exc)
try:
 unreal.EditorPythonScripting.set_keep_python_script_alive(True)
 if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Maps/ANOMALIA_AssetsShowcase_v1'):raise RuntimeError('Missing review level')
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
 # Entry paths must be empty at torso height; adjacent wall and interior floor must block.
 for name,x,y,depth in [('house',-750,700,800),('garage',750,700,900)]:
  checks=[('open_door',(x,y+depth/2+100,120),(x,y+depth/2-150,120),False),('solid_wall',(x+300,y+depth/2+100,120),(x+300,y+depth/2-100,120),True),('interior_floor',(x,y,100),(x,y,-50),True)]
  for kind,a,b,expected in checks:
   hit=unreal.SystemLibrary.line_trace_single(world,unreal.Vector(*a),unreal.Vector(*b),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],unreal.DrawDebugTrace.NONE)
   blocked=hit is not None and bool(hit.to_tuple()[0])
   report['collisionChecks'].append(dict(building=name,test=kind,blocked=blocked,expected=expected))
   if blocked!=expected:raise RuntimeError('Collision failed: '+name+'/'+kind)
 for cmd in ['r.DynamicGlobalIlluminationMethod 0','r.ReflectionMethod 0','r.Shadow.Virtual.Enable 0','r.Nanite 0','r.AntiAliasingMethod 2','sg.ShadowQuality 1','r.ScreenPercentage 100','t.MaxFPS 20']:
  unreal.SystemLibrary.execute_console_command(world,cmd)
 unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
 camera();state['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception as exc:finish(exc)
