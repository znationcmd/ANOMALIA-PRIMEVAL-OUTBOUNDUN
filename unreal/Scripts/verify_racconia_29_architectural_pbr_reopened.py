"""Reopen the saved original RACCONIA PBR level without saving any asset."""
import hashlib,json,math,os,traceback
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
WORLD="/Game/Maps/PRIGIMALIA_RACCONIA_VARKOVIA_16KM_v1"
OUT=Path(os.environ["RACCONIA_PBR_REOPEN_REPORT"])
BUILD=Path(os.environ["RACCONIA_29_PBR_NATIVE_IMPORT_REPORT"])
report={"state":"FAILED","readOnly":True,"PIETested":False,"photorealismVisuallyVerified":False}
try:
    if ROOT.as_posix().lower()!="c:/anomaliaz_skarvik_stage_41188816555/unreal":
        raise RuntimeError("Unexpected project")
    if (ROOT/".skarvik-ci-stage-marker").read_text(encoding="utf-8-sig").strip()!="41188816555":
        raise RuntimeError("Untrusted staging marker")
    build=json.loads(BUILD.read_text(encoding="utf-8-sig"))
    if not build.get("nativeMapSaved") or build.get("originalSiteAnchorsSaved")!=29:
        raise RuntimeError("The native 29-site build did not finish")
    sources=[ROOT/"Content/Maps/PRIGIMALIA_RACCONIA_VARKOVIA_16KM_v1.umap",
             ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap",
             ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_GRADED_v2.umap",
             ROOT/"Content/Maps/PRIGIMALIA_SKARVIK_ISLANDS_v1.umap",
             ROOT/"Content/Map/Big_City_LVL.umap",
             Path("D:/ANOMALIA/unreal/Content/Maps/ANOMALIA_Archipelago_v2.umap")]
    before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(WORLD):
        raise RuntimeError("Cannot reopen saved native Racconia")
    wp=unreal.WorldPartitionBlueprintLibrary
    desc=wp.get_actor_descs() or []
    labels=[str(d.label) for d in desc]
    anchors={s for s in labels if s.startswith("RACCONIA_ORIGINAL_SITE_")}
    prefix="RACCONIA_ARCH_PBR_V2_"
    parts=[d for d in desc if str(d.label).startswith(prefix)]
    if len(anchors)!=29 or len(parts)!=build["nativePBRBuildingPartsPlaced"]:
        raise RuntimeError("Saved anchor/mesh actor counts differ after reopening")
    if len({str(d.label) for d in parts})!=len(parts):
        raise RuntimeError("Duplicate architectural actor labels")
    parts=sorted(parts,key=lambda d:str(d.label))
    indices=sorted({int(i*(len(parts)-1)/11) for i in range(12)})
    chosen=[parts[i] for i in indices]
    wp.load_actors([d.guid for d in chosen])
    loaded={a.get_actor_label():a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
    samples=[]
    for d in chosen:
        label=str(d.label);actor=loaded.get(label)
        if not isinstance(actor,unreal.StaticMeshActor):raise RuntimeError("Saved building part cannot reload")
        comp=actor.get_component_by_class(unreal.StaticMeshComponent)
        mesh=comp.get_editor_property("static_mesh") if comp else None
        if not isinstance(mesh,unreal.StaticMesh) or not mesh.get_path_name().startswith("/Game/Anomalia/Racconia/ArchitecturalPBR_V2/"):
            raise RuntimeError("Saved PBR mesh asset is missing or unrelated")
        keys=[key for key in build["sitePlacementsCm"] if label.startswith(prefix+key+"_")]
        if not keys:raise RuntimeError("Unknown original site identity")
        expected=build["sitePlacementsCm"][max(keys,key=len)]
        p=actor.get_actor_location()
        if max(abs(p.x-expected[0]),abs(p.y-expected[1]),abs(p.z-expected[2]))>1:
            raise RuntimeError("Saved placement differs from verified original raster")
        samples.append({"actor":label,"mesh":mesh.get_path_name()})
    wp.unload_actors([d.guid for d in chosen])
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=v for p,v in before.items()):
        raise RuntimeError("Read-only reopening changed a source level")
    report.update(state="RACCONIA_29_ORIGINAL_PBR_SITES_AND_MESHES_PERSIST_AFTER_REOPEN_NOT_PIE_TESTED",
                  savedSites=29,savedArchitecturalMeshActors=len(parts),samples=samples,sourceLevelsUnchanged=True)
except Exception as error:
    report["error"]=str(error);report["traceback"]=traceback.format_exc()
finally:
    OUT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    unreal.log("RACCONIA_PBR_REOPEN_STATE="+report["state"])
