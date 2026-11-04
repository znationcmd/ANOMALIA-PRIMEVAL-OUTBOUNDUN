"""Read-only bounded CitySample native actor inspection for SKARVIK Big City.

Load <= 18 select source actors within a central urban district, not 86k cells.
Never copy, save, create actors, or edit the original City Sample or D: world.
Use report to choose truthful city building meshes/road sections for future import.
"""
import hashlib,json,math,os,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
CITY="/Game/Map/Big_City_LVL"
OUT=Path(os.environ["SKARVIK_CITY_BOUNDED_MESH_AUDIT_REPORT"])
TARGET=ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap"
CITYFILE=ROOT/"Content/Map/Big_City_LVL.umap"
ORIGINAL=Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")
report={"state":"FAILED","readOnly":True,"sourceCityMap":CITY,
        "actorsCopiedToSkarvik":0,"CityFullyIntegrated":False,
        "SM5VisibleTested":False,"BigCityFileModified":False,
        "OriginalDModified":False,"NativeBigCityActorMeshSamples":[]}
try:
 if "ANOMALIAZ_SKARVIK_STAGE_41188816555" not in str(ROOT).upper() or (
    ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
  raise RuntimeError("Unsafe root or marker")
 for f in (TARGET,CITYFILE,ORIGINAL):
  if not f.is_file():raise RuntimeError("Protected world missing "+str(f))
 hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (TARGET,CITYFILE,ORIGINAL)}
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
 actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 if not levels.load_level(CITY):raise RuntimeError("Cannot open actual City Sample World source")
 wp=unreal.WorldPartitionBlueprintLibrary
 ds=wp.get_actor_descs() or []
 if len(ds)<80000:raise RuntimeError("Unexpected Big City source descriptor count")
 match={"building":[],"sidewalk":[],"street":[]}
 def pos(d):
  box=d.bounds
  return ((float(box.min.x)+float(box.max.x))/2,
          (float(box.min.y)+float(box.max.y))/2,
          (float(box.min.z)+float(box.max.z))/2)
 def dimensions(d):
  box=d.bounds
  return [round(float(getattr(box.max,ax)-getattr(box.min,ax))/100.,1) for ax in ("x","y","z")]
 for desc in ds:
  label=str(desc.label)
  if "COLL" in label or "DECAL" in label or "TRAFFIC" in label:continue
  kind=("building" if label.startswith("BLDG_") else
        "sidewalk" if label.startswith("SIDEWALK_") else
        "street" if label.startswith("STREET_") else None)
  if not kind:continue
  p=pos(desc)
  if not all(math.isfinite(v) for v in p):continue
  if abs(p[0])>110000 or abs(p[1])>110000:continue
  dims=dimensions(desc)
  if not(2<max(dims[:2])<200):continue
  dist=math.hypot(p[0],p[1])
  match[kind].append((dist,label,desc))
 report["candidatesInSourceCenter"]={name:len(seq) for name,seq in match.items()}
 chosen=[]
 for kind,maxc in (("building",10),("sidewalk",4),("street",4)):
  seq=sorted(match[kind],key=lambda x:x[0])[:maxc]
  for _,label,d in seq:
   chosen.append((kind,label,d))
 report["selectedActorCount"]=len(chosen)
 if len(chosen)<6:raise RuntimeError("Source core lacks sufficient urban building/sidewalk actors")
 wp.load_actors([d.guid for _,_,d in chosen])
 current=actors.get_all_level_actors()
 bylabel={a.get_actor_label():a for a in current}
 allmesh=0
 for kind,label,d in chosen:
  match_actor=bylabel.get(label)
  actorreport={"kind":kind,"sourceActorLabel":label,"nativeDescriptorClass":str(d.native_class),
               "sourceActorFoundAfterLoading":bool(match_actor),
               "estimatedSourceBoundsMeters":dimensions(d),
               "components":[]}
  if match_actor:
   for comp in match_actor.get_components_by_class(unreal.StaticMeshComponent)[:60]:
    mesh=comp.get_editor_property("static_mesh")
    if not mesh:continue
    # Mesh and material source references only. No asset copies, no screenshots.
    transform=comp.get_world_transform()
    location=transform.translation
    actorreport["components"].append({
      "mesh":mesh.get_path_name(),"locationCm":[round(location.x,1),round(location.y,1),round(location.z,1)],
      "scaleCm":str(transform.scale3d),"componentType":comp.get_class().get_name(),
      "componentName":comp.get_name()})
    allmesh+=1
  report["NativeBigCityActorMeshSamples"].append(actorreport)
 report["sampledNativeStaticMeshComponents"]=allmesh
 for f in (TARGET,CITYFILE,ORIGINAL):
  if hashlib.sha256(f.read_bytes()).hexdigest()!=hashes[str(f)]:
   raise RuntimeError("A supposedly read-only survey modified a protected world")
 if allmesh<1:raise RuntimeError("No native StaticMesh components on selected Big City actors")
 report["state"]="BIG_CITY_NATIVE_STATIC_MESH_COMPONENTS_DISCOVERED_FROM_SMALL_BOUNDED_SOURCE_SAMPLE"
 unreal.log("SKARVIK_BIG_CITY_REAL_SOURCE_STATIC_MESH_COMPONENTS_SAMPLED="+str(allmesh))
except Exception as e:
 report["error"]=str(e);report["traceback"]=traceback.format_exc()
 unreal.log_error("SKARVIK_BIGCITY_BOUNDED_SAMPLE_FAILED="+str(e))
finally:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
