"""Import the 29 existing Racconia reference models into isolated UE assets only."""
import hashlib, json, os, traceback
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
out=Path(os.environ["RACCONIA_MODEL_REPORT"])
report={"state":"FAILED","nativeLevelCreated":False,"placedInMap":False,"models":[]}
try:
    if str(root).replace("\\","/").lower()!="c:/anomaliaz_skarvik_stage_41188816555/unreal":
        raise RuntimeError("Unexpected native staging root")
    if (root/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("Untrusted staging marker")
    source=root/"SourceAssets/Racconia16km_20261111/Models_original_blockouts"
    files=sorted(source.glob("*.glb"))
    if len(files)!=29:raise RuntimeError("Expected exactly 29 original GLB sources")
    maps=list((root/"Content/Maps").rglob("*.umap"))
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in maps}
    lib=unreal.EditorAssetLibrary
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    for file in files:
        dest="/Game/Anomalia/Racconia/OriginalBlockouts_20261111/"+file.stem
        receipt=root/"SourceAssets/Racconia16km_20261111"/(file.stem+".import.json")
        digest=hashlib.sha256(file.read_bytes()).hexdigest()
        if lib.does_directory_exist(dest):
            if not receipt.is_file():raise RuntimeError("Existing model folder without receipt: "+dest)
            prior=json.loads(receipt.read_text())
            if prior["sourceSHA256"]!=digest:raise RuntimeError("Source changed; refuse overwrite")
            paths=prior["assets"]
        else:
            task=unreal.AssetImportTask()
            task.filename=str(file);task.destination_path=dest
            task.automated=True;task.replace_existing=False;task.save=True;task.async_=False
            tools.import_asset_tasks([task]);task.get_objects()
            paths=list(lib.list_assets(dest,recursive=True,include_folder=False))
        meshes=[p for p in paths if isinstance(lib.load_asset(p),unreal.StaticMesh)]
        if not meshes:raise RuntimeError("No native StaticMesh imported for "+file.name)
        for path in paths:
            if not lib.save_asset(path,only_if_is_dirty=False):raise RuntimeError("Failed saving "+path)
        row={"source":file.name,"sourceSHA256":digest,"assets":paths,"staticMeshes":meshes}
        receipt.write_text(json.dumps(row,indent=2),encoding="utf-8")
        report["models"].append(row)
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=v for p,v in before.items()):
        raise RuntimeError("Existing native map changed")
    report.update(state="29_RACCONIA_ORIGINAL_BLOCKOUT_SOURCES_IMPORTED_AS_NATIVE_ASSETS_NOT_PLACED",
                  existingMapsUnchanged=True,sourceCount=len(report["models"]),
                  staticMeshCount=sum(len(r["staticMeshes"]) for r in report["models"]))
except Exception as exc:
    report["error"]=str(exc);report["traceback"]=traceback.format_exc()
    unreal.log_error("RACCONIA_IMPORT_FAILED="+str(exc))
finally:
    out.write_text(json.dumps(report,indent=2),encoding="utf-8")
