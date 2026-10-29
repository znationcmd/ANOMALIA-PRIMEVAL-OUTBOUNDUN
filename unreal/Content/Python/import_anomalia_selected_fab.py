"""Import only hash-verified local Fab sources into a fresh validation namespace."""
import gc, hashlib, json, os, traceback
from pathlib import Path
import unreal
manifest=Path(os.environ["ANOMALIA_FAB_STAGE_MANIFEST"])
data=json.loads(manifest.read_text(encoding="utf-8"))
out=Path(os.environ["ANOMALIA_FAB_IMPORT_REPORT"])
base="/Game/Anomalia/ImportedFab/Batch_"+os.environ["GITHUB_RUN_ID"]
report={"state":"IN_PROGRESS","namespace":base,"project":unreal.Paths.get_project_file_path(),"sources":[],"errors":[],"gameplay":"not_implemented_or_tested","multiplayer":"not_run","oldAssetsReplaced":False}
def checkpoint():
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
if unreal.EditorAssetLibrary.does_directory_exist(base):
    raise RuntimeError("Refusing existing namespace "+base)
unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")
for index,row in enumerate(data["imports"]):
    entry={"id":row["id"],"source":row["relative"],"sha256":row["sha256"],"assets":[]}
    report["sources"].append(entry)
    try:
        src=Path(row["staged"])
        if hashlib.sha256(src.read_bytes()).hexdigest()!=row["sha256"]:
            raise RuntimeError("Staged source checksum changed")
        dest=base+"/"+row["id"].replace("-","_")+"/Source_"+str(index)
        task=unreal.AssetImportTask()
        for key,value in {"filename":str(src),"destination_path":dest,"automated":True,"replace_existing":False,"replace_existing_settings":False,"save":True,"async_":False}.items():
            if key!="async_":
                task.set_editor_property(key,value)
        if src.suffix.lower()==".fbx":
            opts=unreal.FbxImportUI()
            opts.set_editor_property("automated_import_should_detect_type",True)
            opts.set_editor_property("import_materials",True)
            opts.set_editor_property("import_textures",True)
            opts.set_editor_property("import_animations",True)
            opts.set_editor_property("import_mesh",True)
            opts.static_mesh_import_data.set_editor_property("combine_meshes",False)
            task.set_editor_property("options",opts)
            task.set_editor_property("factory",unreal.FbxFactory())
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        objects=list(task.get_objects())
        if not objects:
            paths=list(task.get_editor_property("imported_object_paths"))
            objects=[unreal.load_asset(p) for p in paths]
        meshes=0
        for obj in objects:
            if not obj:
                raise RuntimeError("Imported object could not be loaded")
            p=obj.get_path_name()
            if not p.startswith(base+"/"):
                raise RuntimeError("Importer returned object outside isolated namespace: "+p)
            entry["assets"].append({"path":p,"class":obj.get_class().get_name()})
        # Include dependent materials/textures which task results may omit.
        for p in unreal.EditorAssetLibrary.list_assets(dest,recursive=True,include_folder=False):
            obj=unreal.load_asset(p)
            if not obj:
                entry.setdefault("unloadable",[]).append(p)
                continue
            record=next((r for r in entry["assets"] if r["path"]==obj.get_path_name()),None)
            if record is None:
                record={"path":obj.get_path_name(),"class":obj.get_class().get_name()}
                entry["assets"].append(record)
            if isinstance(obj,(unreal.StaticMesh,unreal.SkeletalMesh)):
                meshes+=1
                if isinstance(obj,unreal.SkeletalMesh):
                    sk=obj.get_editor_property("skeleton")
                    record["skeleton"]=sk.get_path_name() if sk else None
                    materials=obj.get_editor_property("materials")
                else:
                    materials=obj.get_editor_property("static_materials")
                record["materialSlots"]=len(materials)
                record["emptyMaterialSlots"]=sum(1 for m in materials if not m.material_interface)
            if isinstance(obj,unreal.Blueprint):
                record["compiled"]=bool(unreal.BlueprintEditorLibrary.compile_blueprint(obj))
        if meshes<1:
            raise RuntimeError("No mesh imported from model source")
        if entry.get("unloadable"):
            raise RuntimeError("Some imported dependencies did not load")
        if not unreal.EditorAssetLibrary.save_directory(dest,only_if_is_dirty=False,recursive=True):
            raise RuntimeError("Failed to save imported directory")
        entry["status"]="IMPORTED_SAVED_LOADED_NOT_GAMEPLAY_ACCEPTED"
        entry["meshCount"]=meshes
    except Exception as exc:
        entry["status"]="FAILED"
        entry["error"]=str(exc)
        report["errors"].append({"source":row["relative"],"error":str(exc)})
        unreal.log_error(traceback.format_exc())
    checkpoint()
    gc.collect()
report["state"]="IMPORT_FINISHED_WITH_ERRORS" if report["errors"] else "IMPORT_FINISHED"
checkpoint()
