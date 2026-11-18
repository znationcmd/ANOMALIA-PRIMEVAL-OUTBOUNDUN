r"""Read-only investigation of real World Partition Landscape geometry after reload."""
import json,os,traceback
from pathlib import Path
import unreal
out=Path(os.environ["ANOMALIA_WORLD_TERRAIN_COMPONENT_REPORT"])
pkg=os.environ.get("ANOMALIA_WORLD_TERRAIN_PACKAGE","/Game/Maps/PRIGIMALIA_MOROEDENACHTMERR")
root=Path(unreal.Paths.project_dir()).resolve()
r={"status":"FAIL","package":pkg,"project":str(root),"readOnly":True,"landscapes":[],"sampleHeights":[]}
try:
 if root!=Path(r"D:\ANOMALIA\unreal").resolve():raise RuntimeError("Not original game project")
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 sub=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
 if not levels.load_level(pkg):raise RuntimeError("Cannot reopen real world")
 world=sub.get_editor_world()
 allactors=actors.get_all_level_actors()
 r["loadedActors"]=len(allactors)
 r["name"]=world.get_name()
 if hasattr(unreal,"WorldPartitionBlueprintLibrary"):
  try:
   descriptions=unreal.WorldPartitionBlueprintLibrary.get_actor_descs() or []
   r["savedWPDescriptions"]={"count":len(descriptions),
      "landscapes":[str(d.label) for d in descriptions if "LANDSCAPE" in str(d.label).upper()][:15]}
  except Exception as e:r["wpDescError"]=str(e)
 for a in allactors:
  if not isinstance(a,unreal.LandscapeProxy):continue
  row={"label":a.get_actor_label(),"class":str(a.get_class().get_name()),
       "location":[a.get_actor_location().x,a.get_actor_location().y,a.get_actor_location().z]}
  try:
   components=a.get_components_by_class(unreal.LandscapeComponent)
   row["landscapeComponentCount"]=len(components)
   row["landscapeComponentDetails"]=[]
   for c in components[:4]:
    row["landscapeComponentDetails"].append({"name":c.get_name(),
          "isRegistered":c.is_registered() if hasattr(c,"is_registered") else "API_UNAVAILABLE",
          "bounds":str(c.bounds)[:320] if hasattr(c,"bounds") else "NO_BOUNDS_FIELD"})
  except Exception as e:row["componentsError"]=str(e)
  try:
   colls=a.get_components_by_class(unreal.LandscapeHeightfieldCollisionComponent)
   row["collisionComponentCount"]=len(colls)
  except Exception as e:row["collisionComponentError"]=str(e)
  try:
   row["landscapeInfoValid"]=a.get_landscape_info()!=None if hasattr(a,"get_landscape_info") else "API_UNAVAILABLE"
  except Exception as e:row["landscapeInfoError"]=str(e)
  r["landscapes"].append(row)
 if hasattr(unreal,"AnomaliaPrimevalElevenWorldLibrary"):
  lib=unreal.AnomaliaPrimevalElevenWorldLibrary
  r["nativeSamplerLoaded"]=hasattr(lib,"named_world_height")
  if r["nativeSamplerLoaded"]:
   for e,n in ((0,0),(-1300,500),(3000,-3000)):
    try:r["sampleHeights"].append({"x":e,"y":n,"metres":lib.named_world_height("MOROEDENACHTMERR",float(e),float(n))})
    except Exception as ex:r["sampleHeights"].append({"error":str(ex)})
 r["status"]="READ_ONLY_LANDSCAPE_COMPONENTS_AUDITED"
except Exception as ex:
 r["error"]=str(ex);r["traceback"]=traceback.format_exc()
finally:
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(r,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
 unreal.log("ANOMALIA_AUTO30_TERRAIN_RELOAD "+json.dumps({k:v for k,v in r.items() if k!="traceback"},ensure_ascii=False,default=str))
