r"""Import verified CC0 PBR-realistic FBX architecture to actual ANOMALIA UE5.

Uses only model files previously SHA-256 provenance-staged in
SourceAssets/RegionalArchitecture/PolyHaven_CC0_20261118.
Never overwrites existing .uasset, old .umap or other player data. Do not claim
these modular FACADES constitute culturally authentic, enterable full houses.
"""
import json,os,traceback,re,hashlib
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE=ROOT/"SourceAssets/RegionalArchitecture/PolyHaven_CC0_20261118"
OUT=Path(os.environ["ANOMALIA_CC0_UNREAL_IMPORT_REPORT"])
ALLOW={
 "modular_urban_apartments_facade",
 "modular_factory_facade",
 "modular_fort_01",
 "chinese_cabinet",
 "carved_wooden_elephant",
}
TARGET="/Game/Anomalia/RegionalArchitecture/PolyHaven_CC0"
report={"state":"FAILED","originalWorldsModified":False,"otherUserAssetsOverwritten":False,
        "importedNewStaticMeshes":0,"importedNativeAssets":[],"sourcePackageCount":0,
        "culturesWithVerifiedFullHouseModels":[],"moduleMeshesNotCompleteHouses":True,
        "completeInteriorsOrDoorsTested":False,"actualGameplayVerified":False}
try:
    if ROOT!=Path(r"D:\ANOMALIA\unreal").resolve():
        raise RuntimeError("Not the original UE5 project")
    if not (ROOT/"Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file():
        raise RuntimeError("Original SKARVIK game map unavailable")
    manifest_path=SOURCE/"CC0_SOURCE_PROVENANCE.json"
    if not manifest_path.is_file():
        raise RuntimeError("CC0 source manifest not yet staged onto D")
    data=json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if data.get("license")!="CC0 1.0":
        raise RuntimeError("License not verified")
    models=data.get("models",[])
    if len(models)!=5 or {x["id"] for x in models}!=ALLOW:
        raise RuntimeError("Unexpected Poly Haven models list")
    report["sourcePackageCount"]=len(models)
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    if not tools:raise RuntimeError("Unreal native asset import service not available")
    assetlib=unreal.EditorAssetLibrary
    for item in models:
        slug=item["id"]
        relative=slug+"/model/"+slug+".fbx"
        fbx=(SOURCE/relative).resolve()
        if not fbx.is_file() or SOURCE.resolve() not in fbx.parents:
            raise RuntimeError("Source official FBX missing "+relative)
        matched=[f for f in item.get("files",[]) if f.get("relativePath")==relative]
        if len(matched)!=1:raise RuntimeError("Original FBX file not listed in source manifest")
        official=matched[0]
        if fbx.stat().st_size!=official["bytes"]:
            raise RuntimeError("Official FBX byte count differs for "+slug)
        h=hashlib.md5()
        with fbx.open("rb") as f:
            while True:
                chunk=f.read(4*1024*1024)
                if not chunk:break
                h.update(chunk)
        if h.hexdigest()!=official["md5"]:
            raise RuntimeError("Official FBX content checksum changed "+slug)
        folder=TARGET+"/"+slug
        already=assetlib.does_directory_exist(folder)
        if already:
            saved=assetlib.list_assets(folder,recursive=True,include_folder=False)
            meshes=[]
            for asset in saved:
                try:
                    obj=assetlib.load_asset(asset)
                    if isinstance(obj,unreal.StaticMesh):meshes.append(str(asset))
                except Exception:pass
            if meshes:
                report["importedNativeAssets"].append({"id":slug,"status":"EXISTING_UNREAL_MESHES_PRESERVED",
                    "staticMeshCount":len(meshes),"nativePaths":meshes[:60]})
                continue
            raise RuntimeError("Target package exists but lacks verified original StaticMesh "+folder)
        options=unreal.FbxImportUI()
        options.set_editor_property("import_mesh",True)
        options.set_editor_property("import_as_skeletal",False)
        options.set_editor_property("import_materials",True)
        options.set_editor_property("import_textures",True)
        options.set_editor_property("import_animations",False)
        imp=options.get_editor_property("static_mesh_import_data")
        if imp:
            imp.set_editor_property("combine_meshes",False)
            imp.set_editor_property("generate_lightmap_u_vs",True)
        task=unreal.AssetImportTask()
        task.set_editor_property("filename",str(fbx))
        task.set_editor_property("destination_path",folder)
        task.set_editor_property("automated",True)
        task.set_editor_property("replace_existing",False)
        task.set_editor_property("replace_existing_settings",False)
        task.set_editor_property("save",True)
        task.set_editor_property("options",options)
        tools.import_asset_tasks([task])
        paths=[str(x) for x in task.get_editor_property("imported_object_paths")]
        meshes=[]
        for pkg in paths:
            try:
                obj=assetlib.load_asset(pkg)
                if isinstance(obj,unreal.StaticMesh):meshes.append(pkg)
            except Exception:pass
        if not meshes:
            try:
                paths=list(assetlib.list_assets(folder,recursive=True,include_folder=False))
                meshes=[str(p) for p in paths if isinstance(assetlib.load_asset(p),unreal.StaticMesh)]
            except Exception:pass
        if not meshes:
            raise RuntimeError("FBX import did not produce a genuine native StaticMesh for "+slug)
        report["importedNewStaticMeshes"]+=len(meshes)
        report["importedNativeAssets"].append({
            "id":slug,"status":"NEW_NATIVE_STATIC_MESHES_IMPORTED",
            "staticMeshCount":len(meshes),"nativePaths":meshes[:60],
            "materialImportRequested":True,"PBRMaterialVisualTestPassed":False,
            "isCulturallyAuthenticHouse":False,
            "isCompleteHouse":False,
        })
        unreal.log("ANOMALIA_REGIONAL_ARCHITECTURE_UNREAL_FBX_IMPORTED "+slug+" count "+str(len(meshes)))
    report["state"]="LICENSED_REAL_ARCHITECTURAL_MESHES_IMPORTED_NOT_FULL_REGIONAL_HOUSES"
except Exception as e:
    report["error"]=str(e);report["traceback"]=traceback.format_exc()
    unreal.log_error("ANOMALIA_CC0_ARCHITECTURE_IMPORT_ERROR "+str(e))
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    unreal.log("ANOMALIA_CC0_REAL_ARCHITECTURE_IMPORT "+json.dumps({k:v for k,v in report.items() if k!="traceback"},ensure_ascii=False))
