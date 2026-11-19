r"""Import the four authentic public CC0 house GLBs as native Unreal StaticMesh assets.

Only adds assets to a new isolated /Game/Anomalia/RegionalArchitecture namespace
and never replaces any old .uasset or .umap. "Hawaiian" bungalow and Nordic
farmhouse are generic stand-ins, NOT culturally authentic Hawaiian or Norwegian
house models, and are labeled as such. No interior/gameplay proof from an import.
"""
import json,os,hashlib,traceback
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE=ROOT/"SourceAssets/RegionalArchitecture/Innerscene_CC0_20261118"
OUT=Path(os.environ["ANOMALIA_REGIONAL_HOUSE_UNREAL_REPORT"])
TARGET="/Game/Anomalia/RegionalArchitecture/Innerscene_CC0"
EXPECTED={"korean_hanok","indian_modern_3bhk","hawaiian_tropical_bungalow","rural_nordic_house_candidate"}
report={"state":"FAILED","originalGameProjectModified":False,"originalUnrealMapsModified":False,
    "existing3DMeshesReplaced":0,"newNativeStaticMeshCount":0,
    "inputGLBCount":0,"housesImported":[],
    "nativeGeometryPassed":False,
    "texturesPBRVisuallyValidated":False,
    "interiorsNavigable":False,"gameplayPlaytested":False,
    "regionalHawaiianAndNorwegianAuthenticityProven":False}
def hash_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        while True:
            chunk=f.read(1024*1024)
            if not chunk:break
            h.update(chunk)
    return h.hexdigest()
def is_native_mesh(obj):
    return isinstance(obj,unreal.StaticMesh)
try:
    if ROOT!=Path(r"D:\ANOMALIA\unreal").resolve():
        raise RuntimeError("Not original UE project")
    if not (ROOT/"Content/Maps/ANOMALIA_Archipelago_v2.umap").is_file():
        raise RuntimeError("Protected original main world absent")
    provenance=SOURCE/"INNERSCENE_CC0_HOUSE_PROVENANCE.json"
    if not provenance.is_file():raise RuntimeError("Original licensed GLBs were not staged on D")
    data=json.loads(provenance.read_text(encoding="utf-8-sig"))
    if data.get("license")!="CC0 1.0" or {m["key"] for m in data["models"]}!=EXPECTED:
        raise RuntimeError("Incorrect original CC0 house provenance")
    tools=unreal.AssetToolsHelpers.get_asset_tools()
    lib=unreal.EditorAssetLibrary
    for info in data["models"]:
        key=info["key"]
        p=SOURCE/(key+".glb")
        if not p.is_file() or p.stat().st_size!=info["bytes"]:
            raise RuntimeError("Original GLB missing or size differs "+key)
        if hash_file(p)!=info["sha256"]:raise RuntimeError("Original house source SHA256 changed "+key)
        report["inputGLBCount"]+=1
        folder=TARGET+"/"+key
        if lib.does_directory_exist(folder):
            saved=lib.list_assets(folder,recursive=True,include_folder=False)
            meshes=[]
            for asset in saved:
                try:
                    obj=lib.load_asset(asset)
                    if is_native_mesh(obj):meshes.append(str(asset))
                except Exception:pass
            if not meshes:
                raise RuntimeError("Preexisting destination contains unverified files: "+folder)
            report["housesImported"].append({"key":key,"nativeMeshPaths":meshes[:120],
                "meshCount":len(meshes),"state":"EXISTING_ORIGINAL_MESHES_PRESERVED"})
            continue
        task=unreal.AssetImportTask()
        task.set_editor_property("filename",str(p))
        task.set_editor_property("destination_path",folder)
        task.set_editor_property("automated",True)
        task.set_editor_property("replace_existing",False)
        task.set_editor_property("replace_existing_settings",False)
        task.set_editor_property("save",True)
        tools.import_asset_tasks([task])
        imported_paths=[str(v) for v in task.get_editor_property("imported_object_paths")]
        try:imported_paths+=list(map(str,lib.list_assets(folder,recursive=True,include_folder=False)))
        except Exception:pass
        assets=[]
        for path in sorted(set(imported_paths)):
            try:
                obj=lib.load_asset(path)
                if is_native_mesh(obj):assets.append(path)
            except Exception:pass
        if not assets:
            raise RuntimeError("No real native Unreal StaticMesh imported from original GLB "+key)
        report["newNativeStaticMeshCount"]+=len(assets)
        report["housesImported"].append({"key":key,"nativeMeshPaths":assets[:120],
            "meshCount":len(assets),"state":"GENUINE_NATIVE_UNREAL_MESHES_CREATED",
            "sourceLicense":"CC0 1.0",
            "verifiedReal3DGeometry":True,"realEnterableInteriorsVerified":False})
        unreal.log("ANOMALIA_REAL_CC0_CULTURAL_HOUSE_NATIVE_IMPORTED "+key+" meshes "+str(len(assets)))
    if len(report["housesImported"])!=4:
        raise RuntimeError("Not all four CC0 GLBs imported")
    report["state"]="FOUR_REGIONAL_SOURCE_HOUSES_IMPORTED_NATIVE_UNREAL_UNPLAYTESTED"
    report["nativeGeometryPassed"]=True
except Exception as e:
    report["error"]=str(e)
    report["traceback"]=traceback.format_exc()
    unreal.log_error("ANOMALIA_CC0_HOUSE_IMPORT_FAILED "+str(e))
finally:
    if OUT:
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    unreal.log("ANOMALIA_REGIONAL_CC0_HOUSES_IMPORT_REPORT "+json.dumps({k:v for k,v in report.items() if k!="traceback"},ensure_ascii=False))
