"""Import verified local model/animation sources; never overwrite an existing asset."""
import os,json,pathlib,hashlib,time,gc,unreal
out=pathlib.Path(os.environ["MISSION_RAW_OUT"])
manifest=json.loads(pathlib.Path(os.environ["MISSION_RAW_MANIFEST"]).read_text(encoding="utf-8"))
root=manifest["outputNamespace"]
assert root.startswith("/Game/Anomalia/LocalResources/B_")
tools=unreal.AssetToolsHelpers.get_asset_tools()
report={"state":"IMPORTING","sources":[],"errors":[],"deferred":[],"mapsSaved":0,"existingAssetsReplaced":False,"gameplayAccepted":False}
owned_rigs={}
def checkpoint():
    (out/"raw-import-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("RAW_IMPORT saved="+str(len(report["sources"]))+" deferred="+str(len(report["deferred"]))+" failed="+str(len(report["errors"])),flush=True)
def classify(path):
    obj=unreal.load_asset(path)
    if not obj:return None
    return {"path":obj.get_path_name(),"class":obj.get_class().get_name()}
unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")
checkpoint()
pending=list(manifest["imports"])
for second_pass in [False,True]:
    again=[]
    for row in pending:
        entry={"source":row["source"],"sha256":row["sha256"],"family":row["family"],"assets":[]}
        source=pathlib.Path(row["prepared"])
        destination=root+"/G_"+row["family"][:12]+"/S_"+row["sha256"][:16]
        try:
            if hashlib.sha256(source.read_bytes()).hexdigest()!=row["preparedSHA256"]:
                raise RuntimeError("Prepared input hash differs")
            if unreal.EditorAssetLibrary.does_directory_exist(destination):
                entry["state"]="EXISTING_NAMESPACE_PRESERVED"
                report["sources"].append(entry);checkpoint();continue
            rigs=owned_rigs.get(row["family"],set())
            animation_only=bool(row.get("animationOnly")) or second_pass
            if animation_only and len(rigs)!=1:
                if not second_pass:again.append(row);continue
                entry.update(state="DEFERRED_SOURCE_SKELETON_REQUIRED",reason="No unique verified skeleton from this same source family")
                report["deferred"].append(entry);checkpoint();continue
            disk=pathlib.Path(unreal.Paths.project_content_dir())/"Anomalia/LocalResources"
            if __import__("shutil").disk_usage(disk.resolve()).free<6*1024**3:
                entry["state"]="DEFERRED_IMPORT_DISK_RESERVE";report["deferred"].append(entry);checkpoint();continue
            task=unreal.AssetImportTask()
            for key,value in {"filename":str(source),"destination_path":destination,"automated":True,"replace_existing":False,"replace_existing_settings":False,"save":True}.items():
                task.set_editor_property(key,value)
            if source.suffix.casefold()==".fbx":
                options=unreal.FbxImportUI()
                options.set_editor_property("automated_import_should_detect_type",not animation_only)
                options.set_editor_property("import_mesh",not animation_only)
                options.set_editor_property("import_animations",True)
                options.set_editor_property("import_materials",not animation_only)
                options.set_editor_property("import_textures",not animation_only)
                if animation_only:
                    options.set_editor_property("mesh_type_to_import",unreal.FBXImportType.FBXIT_ANIMATION)
                    options.set_editor_property("skeleton",unreal.load_asset(next(iter(rigs))))
                task.set_editor_property("options",options)
                task.set_editor_property("factory",unreal.FbxFactory())
            tools.import_asset_tasks([task]);objects=list(task.get_objects())
            assets=unreal.EditorAssetLibrary.list_assets(destination,recursive=True,include_folder=False)
            accepted=0
            for path in assets:
                obj=unreal.load_asset(path)
                if not obj:raise RuntimeError("Imported asset failed to reload: "+path)
                record={"path":obj.get_path_name(),"class":obj.get_class().get_name()}
                if isinstance(obj,unreal.SkeletalMesh):
                    skeleton=obj.get_editor_property("skeleton")
                    record["skeleton"]=skeleton.get_path_name() if skeleton else None
                    if not skeleton:raise RuntimeError("Imported skeletal mesh has no skeleton")
                    owned_rigs.setdefault(row["family"],set()).add(skeleton.get_path_name())
                    accepted+=1
                elif isinstance(obj,unreal.StaticMesh):
                    accepted+=1
                elif isinstance(obj,unreal.AnimSequence):
                    skeleton=obj.get_editor_property("skeleton")
                    record["skeleton"]=skeleton.get_path_name() if skeleton else None
                    record["lengthSeconds"]=obj.get_play_length()
                    if not skeleton or record["lengthSeconds"]<=0:raise RuntimeError("Animation has no skeleton or playable duration")
                    if animation_only and skeleton.get_path_name() not in rigs:raise RuntimeError("Animation skeleton differs from the verified source-family rig")
                    accepted+=1
                unreal.EditorAssetLibrary.set_metadata_tag(obj,"Anomalia_LocalSourceSHA256",row["sha256"])
                unreal.EditorAssetLibrary.set_metadata_tag(obj,"Anomalia_LocalSourceFamily",row["family"])
                entry["assets"].append(record)
            if not accepted:
                if source.suffix.casefold()==".fbx" and not second_pass:
                    again.append(row);continue
                raise RuntimeError("No mesh or animation asset was produced")
            if not unreal.EditorAssetLibrary.save_directory(destination,only_if_is_dirty=False,recursive=True):
                raise RuntimeError("Imported asset directory was not saved")
            entry["state"]="IMPORTED_SAVED_RELOADED_NOT_GAMEPLAY_ACCEPTED"
            report["sources"].append(entry)
        except Exception as exc:
            entry.update(state="FAILED_PRESERVED_FOR_DIAGNOSIS",error=str(exc))
            report["errors"].append(entry)
        checkpoint();gc.collect();unreal.collect_garbage()
    pending=again
report["state"]="RAW_IMPORT_FINISHED_WITH_DEFERRED_OR_ERRORS" if report["deferred"] or report["errors"] else "RAW_IMPORT_FINISHED_NOT_GAMEPLAY_ACCEPTED"
checkpoint()
