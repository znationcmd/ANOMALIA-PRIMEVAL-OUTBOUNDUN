"""Import verified original container keys/locks into the real project; audit existing door assets.

Does not place visual-only locks on sealed meshes or modify/save a level.
Run again in a fresh editor process with AZ68_VERIFY_ONLY=1 to verify disk packages.
"""
import hashlib,json,os,pathlib,traceback,shutil,unreal

PROJECT=pathlib.Path(r"D:\ANOMALIA\unreal")
OUT=pathlib.Path(os.environ["AZ68_OUT"])
MANIFEST=pathlib.Path(os.environ["AZ68_MANIFEST"])
VERIFY=os.environ.get("AZ68_VERIFY_ONLY")=="1"
assert pathlib.Path(unreal.Paths.project_content_dir()).resolve()==(PROJECT/"Content").resolve(),"Wrong project; preserve it"
manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
assert manifest["originalSHA256"]=="d5ff88601c149ceddbda1495da7c139468de297611ccde256a0f5659e428350b"
assert len(manifest["models"])==12
report={"mode":"FRESH_PROCESS_VERIFICATION" if VERIFY else "IMPORT","project":str(PROJECT),"models":[],"errors":[],"containerCandidates":[],"runtimeClasses":{},"mapsSaved":0,"existingAssetsReplaced":False,"runtimeIntegrationAccepted":False,"pieTested":False,"packagingTested":False}
report_path=OUT/("fresh-verification.json" if VERIFY else "import-report.json")
def checkpoint():
    report_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("AZ68_RESULT "+json.dumps({"mode":report["mode"],"models":len(report["models"]),"errors":len(report["errors"]),"runtimeIntegrationAccepted":False}),flush=True)
checkpoint()
tools=unreal.AssetToolsHelpers.get_asset_tools()
for row in manifest["models"]:
    entry={"color":row["color"],"kind":row["kind"],"itemId":row["itemId"],"expectedAsset":row["assetPath"]}
    try:
        source=pathlib.Path(row["prepared"])
        assert hashlib.sha256(source.read_bytes()).hexdigest()==row["sha256"],"Source checksum differs"
        path=row["assetPath"]
        assert path.startswith("/Game/ANOMALIAZ/Items/ContainerLocks/"),"Unexpected namespace"
        # Interchange stores the actual mesh beneath the per-source folder.
        nested=path+"/StaticMeshes/"+path.rsplit("/",1)[1]
        if not unreal.EditorAssetLibrary.does_asset_exist(path) and unreal.EditorAssetLibrary.does_asset_exist(nested):path=nested
        existing=unreal.EditorAssetLibrary.does_asset_exist(path)
        if not existing:
            assert not VERIFY,"Saved package is missing in fresh editor process"
            # Preserve partial output from interrupted prior imports for diagnosis.
            prefix=path.rsplit("/",1)[1]
            folder=path.rsplit("/",1)[0]
            partial=[p for p in unreal.EditorAssetLibrary.list_assets(folder,recursive=True,include_folder=False) if p.rsplit("/",1)[-1].split(".")[0].startswith(prefix)]
            assert not partial,"Existing partial output preserved: "+str(partial)
            task=unreal.AssetImportTask()
            for key,value in {"filename":str(source),"destination_path":folder,"destination_name":prefix,"automated":True,"replace_existing":False,"replace_existing_settings":False,"save":True}.items():task.set_editor_property(key,value)
            tools.import_asset_tasks([task])
        if not existing and unreal.EditorAssetLibrary.does_asset_exist(nested):path=nested
        obj=unreal.load_asset(path)
        assert isinstance(obj,unreal.StaticMesh),"Expected single StaticMesh was not produced"
        if existing or VERIFY:
            owned=unreal.EditorAssetLibrary.get_metadata_tag(obj,"AZ68_PreparedSHA256")==row["sha256"]
            if not owned and not VERIFY:
                data=obj.get_editor_property("asset_import_data")
                filenames=data.extract_filenames() if data else []
                # Adopt only a prior import with an unchanged, hash-proven source.
                owned=any(pathlib.Path(f).is_file() and hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()==row["sha256"] for f in filenames)
                if owned:
                    package=PROJECT/"Content"/(path[len("/Game/"):]+".uasset")
                    backup=OUT/"Backups"/(path[len("/Game/"):]+".uasset");backup.parent.mkdir(parents=True,exist_ok=True)
                    if package.is_file() and not backup.exists():shutil.copy2(package,backup)
            assert owned,"Existing asset source is not checksum-proven; preserved"
        bounds=obj.get_bounds();extent=bounds.box_extent
        dimensions=[2*float(extent.x),2*float(extent.y),2*float(extent.z)]
        assert .1<min(dimensions) and max(dimensions)<40,"Unexpected centimetre bounds: "+str(dimensions)
        slots=obj.get_editor_property("static_materials")
        assert len(slots)==row["materials"],"Material slot count differs from prepared source"
        assert all(s.get_editor_property("material_interface") is not None for s in slots),"Missing imported material"
        disk=PROJECT/"Content"/(path[len("/Game/"):]+".uasset")
        if not VERIFY:
            unreal.EditorAssetLibrary.set_metadata_tag(obj,"AZ68_PreparedSHA256",row["sha256"])
            unreal.EditorAssetLibrary.set_metadata_tag(obj,"AZ68_OriginalPackSHA256",manifest["originalSHA256"])
            unreal.EditorAssetLibrary.set_metadata_tag(obj,"AZ68_KeyId",row["itemId"])
            assert unreal.EditorAssetLibrary.save_loaded_asset(obj,only_if_is_dirty=False),"Package save failed"
        assert disk.is_file(),"Saved package file is absent"
        entry.update(asset=obj.get_path_name(),dimensionsCm=dimensions,materialSlots=len(slots),packageBytes=disk.stat().st_size,state="VERIFIED_IN_FRESH_EDITOR_PROCESS" if VERIFY else "IMPORTED_AND_SAVED_REQUIRES_FRESH_VERIFICATION")
        report["models"].append(entry)
    except Exception as exc:
        report["errors"].append({**entry,"error":str(exc),"trace":traceback.format_exc()})
    checkpoint()

# Registry inspection identifies real candidates without loading or rewriting every large world.
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(synchronous_search=True)
for data in registry.get_all_assets():
    package=str(data.package_name);name=str(data.asset_name).casefold()
    if package.startswith("/Game/") and any(word in name for word in ("container","conteneur","shipping","freight")) and "/ContainerLocks/" not in package:
        report["containerCandidates"].append({"package":package,"class":str(data.asset_class_path),"movingDoorVerified":False})
for suffix in ("AnomaliaWorldMechanism","AnomaliaWorldDefinition","AnomaliaDoorActor"):
    obj=unreal.load_class(None,"/Script/AnomaliaPrimeval."+suffix)
    report["runtimeClasses"][suffix]=bool(obj)
report["remaining"]=["Verify existing container door components and pivots in the actual world","Author lock transforms on moving doors and bind six inventory IDs","Validate server authorization, quickslots, matching/wrong/absent keys","PIE six colors; save/reload; multiplayer; packaging"]
checkpoint()
if report["errors"]:raise RuntimeError("Issue-68 asset checks failed; originals and detailed results preserved")
