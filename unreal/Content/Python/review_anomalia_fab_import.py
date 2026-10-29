"""Visual review of imported Fab assets; editor-only gallery, no gameplay claim."""
import gc, hashlib, json, math, os, time
from pathlib import Path
import unreal
OUT=Path(os.environ["FAB_REVIEW_OUTPUT"]);OUT.mkdir(parents=True,exist_ok=False)
receipt=Path(r"C:\ANOMALIA\FabImports\UserSelection_40561644379\import-report.json")
source=json.loads(receipt.read_text(encoding="utf-8"))
base=source["namespace"]
report={"state":"FAILED","batch":base,"sourceCount":len(source["sources"]),"groups":[],"screenshots":[],"gameplay":"not_run","errors":[]}
state={"index":0,"task":None,"busy":False,"started":time.monotonic(),"until":time.monotonic()+40}
views=[]
def finish(error=None):
    if state.get("finishing"):return
    state["finishing"]=True
    if "handle" in state:unreal.unregister_slate_post_tick_callback(state.pop("handle"))
    if error:report["errors"].append(str(error))
    else:report["state"]="GPU_GALLERY_CAPTURED_NOT_GAMEPLAY_ACCEPTED"
    (OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    state["task"]=None;gc.collect();unreal.SystemLibrary.quit_editor()
def camera():
    _,eye,target=views[state["index"]]
    d=[target[i]-eye[i] for i in range(3)]
    rot=unreal.Rotator(pitch=math.degrees(math.atan2(d[2],math.hypot(*d[:2]))),yaw=math.degrees(math.atan2(d[1],d[0])),roll=0)
    unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(*eye),rot)
def tick(dt):
    if state["busy"] or state.get("finishing"):return
    try:
        if time.monotonic()-state["started"]>600:raise RuntimeError("GPU review timeout")
        if time.monotonic()<state["until"]:return
        name,_,_=views[state["index"]]
        if state["task"] is None:
            state["busy"]=True
            state["task"]=unreal.AutomationLibrary.take_high_res_screenshot(1280,720,str(OUT/(name+".png")),delay=1.,force_game_view=True)
            if not state["task"] or not state["task"].is_valid_task():raise RuntimeError("Screenshot unavailable")
            state["busy"]=False;return
        if not state["task"].is_task_done():return
        p=OUT/(name+".png")
        if not p.is_file() or p.stat().st_size<4096:raise RuntimeError("Missing actual screenshot "+name)
        report["screenshots"].append({"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size})
        state["index"]+=1
        if state["index"]==len(views):finish();return
        state["task"]=None;camera();state["until"]=time.monotonic()+12
    except Exception as e:finish(e)
try:
    if source["state"]!="IMPORT_FINISHED" or source["errors"]:raise RuntimeError("Source import not accepted")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for i,row in enumerate(source["sources"]):
        objects=[]
        for asset in row["assets"]:
            obj=unreal.load_asset(asset["path"])
            if not obj:raise RuntimeError("Reload failed: "+asset["path"])
            if isinstance(obj,unreal.StaticMesh):objects.append(obj)
        if not objects:raise RuntimeError("No static geometry in "+row["source"])
        low=[float("inf")]*3;high=[float("-inf")]*3
        for mesh in objects:
            b=mesh.get_bounds()
            for k,axis in enumerate(("x","y","z")):
                low[k]=min(low[k],getattr(b.origin,axis)-getattr(b.box_extent,axis))
                high[k]=max(high[k],getattr(b.origin,axis)+getattr(b.box_extent,axis))
        span=max(high[k]-low[k] for k in range(3))
        if not math.isfinite(span) or span<.001:raise RuntimeError("Invalid bounds: "+row["source"])
        scale=140/span
        center=[(low[k]+high[k])/2 for k in range(3)]
        origin=[(i%4)*280,(i//4)*280,80]
        for m,mesh in enumerate(objects):
            loc=[origin[k]-center[k]*scale for k in range(3)]
            actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc))
            comp=actor.get_editor_property("static_mesh_component");comp.set_static_mesh(mesh)
            actor.set_actor_scale3d(unreal.Vector(scale,scale,scale))
            actor.set_actor_enable_collision(False)
            actor.set_actor_label("FAB_REVIEW_"+str(i)+"_"+str(m)+"_"+mesh.get_name())
        report["groups"].append({"source":row["source"],"id":row["id"],"meshCount":len(objects),"previewOriginCm":origin,"previewOnlyScale":scale,"originalMaxDimensionCm":span,"assembly":"authored_geometry_overlay_not_attachment_configuration"})
        if row["id"].startswith(("b5b0c0ba","07cdcbaa","88074ea4")) or row["source"].endswith("VV_aidbox_001.fbx"):
            views.append(("source-"+row["id"][:8],(origin[0]+160,origin[1]-230,origin[2]+130),tuple(origin)))
    floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(420,1680,-12))
    floor.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube.Cube"))
    floor.set_actor_scale3d(unreal.Vector(20,45,.2))
    light=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,700),unreal.Rotator(-40,-40,0))
    light.light_component.set_editor_property("intensity",5.)
    sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,500))
    sky.light_component.set_editor_property("intensity",2.)
    actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector())
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for c in ("r.DynamicGlobalIlluminationMethod 0","r.ReflectionMethod 0","r.Shadow.Virtual.Enable 0","r.Nanite 0","r.AntiAliasingMethod 2","sg.ShadowQuality 1","r.ScreenPercentage 100","t.MaxFPS 20"):
        unreal.SystemLibrary.execute_console_command(world,c)
    map_path=base+"/QA/L_Fab_Imported_Review"
    if unreal.EditorAssetLibrary.does_asset_exist(map_path):raise RuntimeError("Refusing existing gallery")
    if not unreal.EditorLoadingAndSavingUtils.save_map(world,map_path):raise RuntimeError("Gallery save failed")
    report["map"]=map_path
    views.insert(0,("overview",(2200,-1200,2600),(420,1500,60)))
    unreal.AutomationLibrary.set_editor_viewport_view_mode(unreal.ViewModeIndex.VMI_LIT)
    camera();state["handle"]=unreal.register_slate_post_tick_callback(tick)
except Exception as e:finish(e)
