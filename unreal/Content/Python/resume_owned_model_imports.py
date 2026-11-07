"""Resume source-family model imports in the actual existing project; preserve every existing package."""
import os,pathlib,json,hashlib,time,gc,shutil,unreal
PROJECT=pathlib.Path(r"D:\ANOMALIA\unreal")
STATE=PROJECT/"Saved/ImportReceipts/RawResume20261107"
OUT=pathlib.Path(os.environ["MISSION_RAW_OUT"])
manifest=json.loads((STATE/"raw-preparation-manifest.json").read_text(encoding="utf-8"))
root=manifest["outputNamespace"]
assert root=="/Game/Anomalia/LocalResources/B_41851208057"
assert pathlib.Path(unreal.Paths.project_file_path()).resolve()==(PROJECT/"AnomaliaPrimeval.uproject").resolve()
prior=json.loads((OUT/"prior/raw-import-report.json").read_text(encoding="utf-8"))
receipt=STATE/"raw-import-report.json"
report=json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else {"sources":prior["sources"],"errors":prior["errors"],"deferred":[],"state":"RESUMING"}
report.update(gameplayAccepted=False,mapsSaved=0,existingAssetsReplaced=False)
completed={r["sha256"]:r for r in report["sources"] if r.get("state") in {"IMPORTED_SAVED_RELOADED_NOT_GAMEPLAY_ACCEPTED","RESUMED_IMPORTED_SAVED_RELOADED_NOT_GAMEPLAY_ACCEPTED"}}
failed={r["sha256"] for r in report["errors"]}
rigs={}
for row in completed.values():
 for asset in row.get("assets",[]):
  if asset.get("class")=="SkeletalMesh" and asset.get("skeleton") and unreal.EditorAssetLibrary.does_asset_exist(asset["skeleton"]):
   rigs.setdefault(row["family"],set()).add(asset["skeleton"])
tools=unreal.AssetToolsHelpers.get_asset_tools()
started=time.monotonic();attempts=0
batch={"newSources":0,"newAssets":0,"errors":[],"skippedPriorSources":0,"deferredSkeletons":0,"freeBefore":{d:shutil.disk_usage(d+":/").free for d in ["C","D"]}}
def checkpoint():
 report["remainingSources"]=sum(r["sha256"] not in completed and r["sha256"] not in failed for r in manifest["imports"])
 report["completedSourceCount"]=len(completed);report["failedSourceCount"]=len(failed)
 tmp=receipt.with_suffix(".tmp");tmp.write_text(json.dumps(report,indent=2),encoding="utf-8");os.replace(tmp,receipt)
 batch["elapsedSeconds"]=time.monotonic()-started
 batch["completedSourcesTotal"]=len(completed);batch["remainingSources"]=report["remainingSources"]
 batch["freeNow"]={d:shutil.disk_usage(d+":/").free for d in ["C","D"]}
 (OUT/"import-batch-summary.json").write_text(json.dumps(batch,indent=2),encoding="utf-8")
 print("ACTUAL_PROJECT_IMPORT "+json.dumps(batch),flush=True)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(4*1024**2),b""):h.update(chunk)
 return h.hexdigest()
unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")
checkpoint()
for row in manifest["imports"]:
 if row["sha256"] in completed:batch["skippedPriorSources"]+=1;continue
 if row["sha256"] in failed:continue
 if attempts>=100 or time.monotonic()-started>25*60:break
 if min(shutil.disk_usage(d+":/").free for d in ["C","D"])<8*1024**3:
  batch["pausedForDiskReserve"]=True;break
 source=pathlib.Path(row["prepared"]);family=row["family"]
 animation=bool(row.get("animationOnly"))
 owned=rigs.get(family,set())
 if animation and len(owned)!=1:batch["deferredSkeletons"]+=1;continue
 attempts+=1
 entry={"source":row["source"],"sha256":row["sha256"],"family":family,"assets":[]}
 destination=root+"/G_"+family[:12]+"/S_"+row["sha256"][:16]
 try:
  if not source.is_file():raise RuntimeError("Prepared source missing; retained source path requires recovery")
  if sha(source)!=row["preparedSHA256"]:raise RuntimeError("Prepared source SHA256 differs; preserved")
  if unreal.EditorAssetLibrary.does_directory_exist(destination):
   # A prior partial import is preserved; new output has its own owned namespace.
   destination+="/Resume_"+os.environ["GITHUB_RUN_ID"]+"_"+os.environ.get("IMPORT_BATCH","0")
   if unreal.EditorAssetLibrary.does_directory_exist(destination):raise RuntimeError("Existing recovery namespace preserved")
  task=unreal.AssetImportTask()
  for key,value in {"filename":str(source),"destination_path":destination,"automated":True,"replace_existing":False,"replace_existing_settings":False,"save":True}.items():task.set_editor_property(key,value)
  if source.suffix.casefold()==".fbx":
   options=unreal.FbxImportUI()
   options.set_editor_property("automated_import_should_detect_type",not animation)
   options.set_editor_property("import_mesh",not animation)
   options.set_editor_property("import_animations",True)
   options.set_editor_property("import_materials",not animation)
   options.set_editor_property("import_textures",not animation)
   if animation:
    options.set_editor_property("mesh_type_to_import",unreal.FBXImportType.FBXIT_ANIMATION)
    options.set_editor_property("skeleton",unreal.load_asset(next(iter(owned))))
   task.set_editor_property("options",options);task.set_editor_property("factory",unreal.FbxFactory())
  tools.import_asset_tasks([task])
  paths=unreal.EditorAssetLibrary.list_assets(destination,recursive=True,include_folder=False)
  accepted=0
  for path in paths:
   obj=unreal.load_asset(path)
   if not obj:raise RuntimeError("Imported package cannot reload: "+path)
   cls=obj.get_class().get_name()
   asset={"path":obj.get_path_name(),"class":cls}
   if isinstance(obj,unreal.SkeletalMesh):
    skeleton=obj.get_editor_property("skeleton")
    if not skeleton:raise RuntimeError("Imported skeletal mesh has no rig")
    asset["skeleton"]=skeleton.get_path_name();rigs.setdefault(family,set()).add(asset["skeleton"]);accepted+=1
   elif isinstance(obj,unreal.StaticMesh):accepted+=1
   elif isinstance(obj,unreal.AnimSequence):
    skeleton=obj.get_editor_property("skeleton")
    if not skeleton or obj.get_play_length()<=0:raise RuntimeError("Animation has no valid rig or duration")
    asset.update(skeleton=skeleton.get_path_name(),lengthSeconds=obj.get_play_length())
    if animation and asset["skeleton"] not in owned:raise RuntimeError("Animation rig differs from verified source family")
    accepted+=1
   unreal.EditorAssetLibrary.set_metadata_tag(obj,"Anomalia_LocalSourceSHA256",row["sha256"])
   unreal.EditorAssetLibrary.set_metadata_tag(obj,"Anomalia_LocalSourceFamily",family)
   entry["assets"].append(asset)
  if not accepted:raise RuntimeError("Import produced no usable mesh or animation")
  if not unreal.EditorAssetLibrary.save_directory(destination,only_if_is_dirty=False,recursive=True):raise RuntimeError("Imported asset save failed")
  for asset in entry["assets"]:
   if not unreal.EditorAssetLibrary.does_asset_exist(asset["path"]):raise RuntimeError("Saved asset is missing")
  entry["state"]="RESUMED_IMPORTED_SAVED_RELOADED_NOT_GAMEPLAY_ACCEPTED"
  report["sources"].append(entry);completed[row["sha256"]]=entry
  batch["newSources"]+=1;batch["newAssets"]+=len(entry["assets"])
 except Exception as exc:
  entry.update(state="FAILED_PRESERVED_FOR_DIAGNOSIS",error=str(exc))
  report["errors"].append(entry);failed.add(row["sha256"])
  batch["errors"].append({"source":str(source),"error":str(exc)})
 checkpoint();gc.collect();unreal.collect_garbage()
report["state"]="RESUME_FINISHED_WITH_REMAINING_OR_ERRORS" if report.get("remainingSources") or failed else "IMPORTED_SAVED_RELOADED_GAMEPLAY_VALIDATION_REQUIRED"
checkpoint()
