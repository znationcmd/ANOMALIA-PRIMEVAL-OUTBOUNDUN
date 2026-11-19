r"""Read-only UE 5.8 ground-tracing and verified real mesh survey in the original project."""
import json,os,traceback,math
from pathlib import Path
import unreal

root=Path(unreal.Paths.project_dir()).resolve()
out=Path(os.environ["ANOMALIA_30_AUTOBUILD_AUDIT_REPORT"])
package=os.environ.get("ANOMALIA_30_AUTOBUILD_AUDIT_PACKAGE","/Game/Maps/PRIGIMALIA_MOROEDENACHTMERR")
road="/Game/Road/Kit_City_Road/SM_ROAD_19_10_0_0_road"
house="/Game/Anomalia/Buildings/Expansion1/SM_townhouse"
report={"state":"ERROR","project":str(root),"package":package,"modifiedSourceAssets":False,"savedLevel":False,"samples":[]}
try:
    if root!=Path(r"D:\ANOMALIA\unreal").resolve():
        raise RuntimeError("Not the original D project")
    if not (root/"Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file():
        raise RuntimeError("Missing original SKARVIK world")
    levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    subs=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels or not subs or not actors:raise RuntimeError("Unreal editor subsystems unavailable")
    report["meshSources"]={}
    for kind,p in [("road",road),("house",house)]:
        m=unreal.EditorAssetLibrary.load_asset(p)
        if not isinstance(m,unreal.StaticMesh):raise RuntimeError("Missing genuine mesh "+p)
        b=m.get_bounds()
        report["meshSources"][kind]={"path":p,"bounds":list(map(float,(b.box_extent.x,b.box_extent.y,b.box_extent.z))),
            "origin":list(map(float,(b.origin.x,b.origin.y,b.origin.z)))}
    if not levels.load_level(package):raise RuntimeError("Cannot load existing real native target level")
    world=subs.get_editor_world()
    if not world:raise RuntimeError("World unavailable")
    report["activePackage"]=world.get_outermost().get_name()
    allactors=actors.get_all_level_actors()
    report["actorLoadedCount"]=len(allactors)
    report["landscapes"]=[]
    for a in allactors:
        if isinstance(a,unreal.LandscapeProxy):
            try:
                origin,extent=a.get_actor_bounds(False)
                report["landscapes"].append({"label":a.get_actor_label(),
                    "origin":list(map(float,(origin.x,origin.y,origin.z))),
                    "extent":list(map(float,(extent.x,extent.y,extent.z)))})
            except Exception as e:
                report["landscapes"].append({"label":a.get_actor_label(),"error":str(e)})
    for east,north in [(0,0),(-1400,1200),(2000,-2000),(3500,2500)]:
        try:
            # Unreal local X east, Y negative north, Landscape collision via Visibility.
            start=unreal.Vector(east*100,-north*100,500000)
            end=unreal.Vector(east*100,-north*100,-100000)
            result=unreal.SystemLibrary.line_trace_single(
                world,start,end,unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                True,[],unreal.DrawDebugTrace.NONE,True)
            obj=result[1] if isinstance(result,tuple) and len(result)>1 else result
            report["samples"].append({"east":east,"north":north,"hit":str(result[0]) if isinstance(result,tuple) else "UNKNOWN",
                "hitRepr":str(obj)[:1100]})
        except Exception as e:
            report["samples"].append({"east":east,"north":north,"error":str(e)[:1200]})
    report["worldPartitionPythonAvailable"]=hasattr(unreal,"WorldPartitionBlueprintLibrary")
    report["state"]="NATIVE_EDITOR_READ_ONLY_CAPABILITY_AUDIT_OK"
except Exception as exc:
    report["error"]=str(exc)
    report["traceback"]=traceback.format_exc()
    unreal.log_error("ANOMALIA_30_PROCEDURAL_EDITOR_AUDIT_ERROR "+str(exc))
finally:
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    unreal.log("ANOMALIA_30_PROCEDURAL_EDITOR_AUDIT "+json.dumps({k:v for k,v in report.items() if k!="traceback"},ensure_ascii=False))
