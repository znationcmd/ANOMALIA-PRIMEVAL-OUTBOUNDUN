"""Import a bounded batch of CHERNASKALUXRIA's full 20x20 Landscape tile grid.

Operate strictly on an existing, owned World Partition level in the isolated
Windows staging project. Each tile is saved separately, checksum-verified, and
receipted only after real native Landscape components and packages exist.
Repeated launches resume after completed tiles and reject orphaned actors.
Terrain is procedural/reference fusion preview; NOT final photo scan or tested
gameplay. Never modify D:\ANOMALIA or any other preexisting World.
"""
import hashlib
import json
import os
import traceback
from pathlib import Path
from datetime import datetime, timezone
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
EXPECTED=r"d:\anomaliaz-prigimalia\unreal"
PACKAGE="/Game/Maps/PRIGIMALIA_CHERNASKALUXRIA"
MAP=ROOT/"Content/Maps/PRIGIMALIA_CHERNASKALUXRIA.umap"
SRC=ROOT/"TerrainSource/CHERNASKALUXRIA"
LEDGER=ROOT/"Saved/CHERNASKALUXRIA"
OWNER=LEDGER/"created-owner.json"
BATCH_START=int(os.environ["CH_ALL_TILES_START"])
BATCH_COUNT=int(os.environ.get("CH_ALL_TILES_BATCH_COUNT","8"))
OUT=Path(os.environ["CH_ALL_TILES_BATCH_RECEIPT"])
EXPECTED_TILE_BYTES=253*253*2
FIRST=(10,10)
status={"schema":1,"start":BATCH_START,"count":BATCH_COUNT,"map":PACKAGE,
        "status":"FAILED","saved":[],"previouslySaved":[],
        "gameplayTested":False,"worldPartitionStreamingTested":False,
        "finalUserImageTopography":False,"timestampUtc":datetime.now(timezone.utc).isoformat()}

def verify_identity():
    if str(ROOT).replace("/","\\").rstrip("\\").lower()!=EXPECTED:
        raise RuntimeError("Wrong project; refusing to alter original D: ANOMALIA")
    if not(0<=BATCH_START<400 and 1<=BATCH_COUNT<=12 and BATCH_START+BATCH_COUNT<=400):
        raise RuntimeError("Unsafe tile batch range; must be <=12 tiles")
    if not MAP.is_file() or MAP.stat().st_size<1024:
        raise RuntimeError("Native CHERNASKALUXRIA world has not been initialized")
    if not OWNER.is_file():
        raise RuntimeError("No original CHERNASKALUXRIA ownership receipt")
    owner=json.loads(OWNER.read_text(encoding="utf-8-sig"))
    if (owner.get("mapPackage")!=PACKAGE or owner.get("owner")!="PRIGIMALIA_CHERNASKALUXRIA"
        or owner.get("firstTile")!="CHERNASKALUXRIA_x10_y10"
        or owner.get("tilesExpected")!=400):
        raise RuntimeError("Unexpected world ownership manifest")
    first=LEDGER/"CHERNASKALUXRIA_x10_y10.json"
    if not first.is_file():
        raise RuntimeError("First native tile provenance/receipt missing")
    proof=json.loads(first.read_text(encoding="utf-8-sig"))
    if proof.get("state")!="NATIVE_LANDSCAPE_TILE_SAVED_NOT_PLAYTESTED":
        raise RuntimeError("First tile has no native save proof")
    data=SRC/"CHERNASKALUXRIA_x10_y10.r16"
    if not data.is_file() or hashlib.sha256(data.read_bytes()).hexdigest()!=proof.get("sourceSha256"):
        raise RuntimeError("First tile heightfield hash differs from installed native source")
    # Verify critical other Worlds were not removed.
    for name in ("ANOMALIA_Archipelago_v2",
                 "ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate",
                 "PRIGIMALIA_KOLCHIEM_ORIGINS_FULL"):
        if not (ROOT/"Content/Maps"/(name+".umap")).is_file():
            raise RuntimeError("Protected original World not present: "+name)

def build():
    verify_identity()
    native=unreal.AnomaliaZPrigimaliaWorldImportLibrary
    if not hasattr(native,"create_chernaskaluxria_landscape_tile") or not hasattr(native,"inspect_chernaskaluxria_tile_components"):
        raise RuntimeError("Native UE 5.8 tile importer and verifier missing")
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not level or not actors:
        raise RuntimeError("Unreal editor subsystems unavailable")
    if not level.load_level(PACKAGE):
        raise RuntimeError("Existing CHERNASKALUXRIA World could not be opened")
    world=unreal.EditorLevelLibrary.get_editor_world()
    if not world or world.get_outermost().get_name()!=PACKAGE:
        raise RuntimeError("Loaded World doesn't match owned CHERNASKALUXRIA package")

    for index in range(BATCH_START,BATCH_START+BATCH_COUNT):
        col,row=index%20,index//20
        tile=f"CHERNASKALUXRIA_x{col:02}_y{row:02}"
        raw=SRC/(tile+".r16")
        receipt=LEDGER/(tile+".json")
        if not raw.is_file() or raw.stat().st_size!=EXPECTED_TILE_BYTES:
            raise RuntimeError("Full 400-tile heightfield source missing/invalid: "+tile)
        digest=hashlib.sha256(raw.read_bytes()).hexdigest()
        if receipt.is_file():
            recorded=json.loads(receipt.read_text(encoding="utf-8-sig"))
            if recorded.get("state")!="NATIVE_LANDSCAPE_TILE_SAVED_NOT_PLAYTESTED" or recorded.get("sourceSha256")!=digest:
                raise RuntimeError("Prior native tile receipt mismatches source: "+tile)
            status["previouslySaved"].append(tile)
            unreal.log("CHERNASKALUXRIA_ALREADY_NATIVE_SAVED="+tile)
            continue
        labels={actor.get_actor_label() for actor in actors.get_all_level_actors()}
        if tile in labels:
            raise RuntimeError("Orphan/unsaved tile already exists; refuse duplicate: "+tile)
        landscape=native.create_chernaskaluxria_landscape_tile(col,row)
        if not landscape or native.inspect_chernaskaluxria_tile_components(landscape)!=4:
            raise RuntimeError("UE5 native Landscape failed four-component validation: "+tile)
        if not level.save_all_dirty_levels():
            raise RuntimeError("UE5 native CH World .umap save failed after "+tile)
        if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
            raise RuntimeError("UE5 external actor save failed after "+tile)
        if not MAP.is_file() or MAP.stat().st_size<1024:
            raise RuntimeError("UE5 native .umap missing after tile "+tile)
        with receipt.open("x",encoding="utf-8") as file:
            json.dump({"mapPackage":PACKAGE,"tile":tile,"col":col,"row":row,
                       "sourceSha256":digest,"worldFileBytes":MAP.stat().st_size,
                       "state":"NATIVE_LANDSCAPE_TILE_SAVED_NOT_PLAYTESTED",
                       "writtenBy":"full-grid-resumable-importer"},
                      file,ensure_ascii=False,indent=2)
        status["saved"].append(tile)
        unreal.log("CHERNASKALUXRIA_GRID_TILE_NATIVE_SAVED="+tile+
                   " INDEX="+str(index)+" / 399")
    status["status"]="BOUNDED_NATIVE_TILE_BATCH_SAVED_NOT_PLAYTESTED"
    status["nativeTilesVerifiedThisBatch"]=len(status["saved"])+len(status["previouslySaved"])
    unreal.log("CHERNASKALUXRIA_NATIVE_TILE_BATCH_COMPLETE="+str(status["nativeTilesVerifiedThisBatch"]))

try:
    build()
except Exception as exc:
    status["error"]=str(exc)
    status["traceback"]=traceback.format_exc()
    raise
finally:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if OUT.exists():
        raise RuntimeError("Never overwrite batch evidence")
    OUT.write_text(json.dumps(status,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
