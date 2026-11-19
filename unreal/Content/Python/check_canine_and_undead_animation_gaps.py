"""Find genuine canine/undead rigs and existing compatible animation clips in actual project."""
import unreal,pathlib,os,json,re,collections,gc
assert pathlib.Path(unreal.Paths.get_project_file_path()).resolve()==pathlib.Path(r"D:\ANOMALIA\unreal\AnomaliaPrimeval.uproject").resolve()
out=pathlib.Path(os.environ["MISSION_REGISTERED_OUT"]);out.mkdir(parents=True,exist_ok=True)
reg=unreal.AssetRegistryHelpers.get_asset_registry();reg.search_all_assets(True);reg.wait_for_completion()
assets=reg.get_assets_by_path("/Game",True,True) or []
names=re.compile(r"dog|canine|shepherd|sheperd|berger|zombi|undead|infected|wolf",re.I)
actions={"idle":["idle","rest","stand"],"walk":["walk"],"run":["run","sprint"],"attack":["attack","bite","punch"],"hurt":["hurt","hitreact","hit_react","damage"],"death":["death","die","dead"]}
anims=collections.defaultdict(list);blueprints=collections.defaultdict(list)
def skeleton_package(value):
 m=re.search(r"(/Game/[^']+)",str(value or ""))
 return m.group(1).split(".")[0] if m else None
for data in assets:
 kind=str(data.asset_class_path.asset_name)
 if kind not in {"AnimSequence","AnimBlueprint"}:continue
 sk=skeleton_package(data.get_tag_value("Skeleton") or data.get_tag_value("TargetSkeleton"))
 if not sk:continue
 item={"package":str(data.package_name),"name":str(data.asset_name)}
 (anims if kind=="AnimSequence" else blueprints)[sk].append(item)
report={"project":str(unreal.Paths.get_project_file_path()),"state":"IN_PROGRESS","models":[],"mapsSaved":0,"existingAssetsModified":0,"animationPlaybackAccepted":False,"notes":["Filename candidates are not confirmed species. Exact skeleton match does not establish good foot placement or gameplay transitions."]}
for data in assets:
 kind=str(data.asset_class_path.asset_name);package=str(data.package_name)
 if kind not in {"SkeletalMesh","StaticMesh"} or not names.search(package):continue
 row={"package":package,"class":kind,"gameplayAccepted":False};report["models"].append(row)
 if kind=="StaticMesh":
  row["state"]="RIG_REQUIRED_BEFORE_SKELETAL_ANIMATION";continue
 try:
  mesh=unreal.EditorAssetLibrary.load_asset(package)
  if not mesh:raise RuntimeError("Mesh failed to load")
  skeleton=mesh.get_editor_property("skeleton")
  if not skeleton:raise RuntimeError("No skeleton on canine/undead mesh")
  sk=skeleton.get_path_name().split(".")[0];row["skeleton"]=sk
  valid=[]
  for item in anims.get(sk,[]):
   clip=unreal.EditorAssetLibrary.load_asset(item["package"])
   if not clip:continue
   if clip.get_editor_property("skeleton")!=skeleton:continue
   length=float(clip.get_play_length())
   if length<=0:continue
   valid.append({**item,"seconds":length})
  row["compatibleClips"]=valid;row["animationBlueprints"]=blueprints.get(sk,[])
  row["actionCoverage"]={action:[x["package"] for x in valid if any(word in x["name"].lower() for word in words)] for action,words in actions.items()}
  row["missingActionCandidates"]=[k for k,v in row["actionCoverage"].items() if not v]
  row["state"]="EXISTING_COMPATIBLE_CLIPS_FOUND_BINDING_AND_PIE_REQUIRED" if valid else "MISSING_CLIPS_OR_RETARGET_REQUIRED"
  print(json.dumps({"model":package,"skeleton":sk,"clips":len(valid),"missing":row["missingActionCandidates"]}),flush=True)
 except Exception as e:row["state"]="BLOCKED";row["error"]=str(e)
 (out/"canine-undead-animation-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 mesh=None;gc.collect();unreal.collect_garbage()
report["state"]="RIG_AND_CLIP_AUDIT_COMPLETE_NOT_GAMEPLAY_ACCEPTED"
(out/"canine-undead-animation-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"models":len(report["models"]),"state":report["state"]}),flush=True)
