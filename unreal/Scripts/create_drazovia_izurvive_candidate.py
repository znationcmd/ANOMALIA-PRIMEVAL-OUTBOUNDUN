"""Create a NEW isolated DRAZOVIA 48x48km World Partition from the NEW user iZurvive image.

NEVER modify the existing /Game/Maps/ANOMALIA_Inhabited_v2, SKARVIK,
existing 27 towns, their saves or any original project backup.

Run in a separate approved Windows UE5.8 checkout after native C++ has
successfully compiled and the verified user-source R16 is installed.
This produces *terrain only*, not finished city roads or vegetation.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import traceback
import unreal

ROOT=Path(unreal.Paths.project_dir()).resolve()
SOURCE=ROOT/"TerrainSource/DRAZOVIA_NEW_REFERENCE/DRAZOVIA_NEW_TOPO_48KM_3025.r16"
PACKAGE="/Game/Maps/ANOMALIA_DrazoviaTopo_NewReference_Candidate"
FILE=ROOT/"Content/Maps/ANOMALIA_DrazoviaTopo_NewReference_Candidate.umap"
ORIGINALS=(
    ROOT/"Content/Maps/ANOMALIA_Inhabited_v2.umap",
    ROOT/"Content/Maps/ANOMALIA_Archipelago_v2.umap",
)
EXPECTED_SHA256="704222bd547c6ec4a417a20e7b580aaefec1db769d18a4b331adf2ac0d263e9c"
WIDTH=3025
EXPECTED_BYTES=WIDTH*WIDTH*2
REPORT=Path(os.environ.get("ANOMALIA_DRAZOVIA_TOPO_REPORT",
    str(ROOT/"Saved/DrazoviaIzurviveReferenceCandidate"/"first-import.json")))
status={"state":"FAILED","mapPackage":PACKAGE,"source":"user-izurvive-image-synthetic-R16",
        "gameplayTested":False,"renderingValidated":False,
        "roadsRebuilt":False,"oldSettlementsMoved":False,
        "originalMapsModified":False}

def sample_height(raw,ix,iy):
    v=struct.unpack_from("<H",raw,(iy*WIDTH+ix)*2)[0]
    return (v-32768.)/16.

def safe_spawn(raw):
    # Spawn in mainland terrain, away from steep slopes and water.
    for row in range(800,2200,37):
        for col in range(650,2400,37):
            heights=[sample_height(raw,col+dx,row+dy)
                     for dx,dy in ((0,0),(3,0),(-3,0),(0,3),(0,-3))]
            if 12<min(heights) and max(heights)<160 and max(heights)-min(heights)<3.5:
                east=-24000+48000*col/(WIDTH-1)
                north=24000-48000*row/(WIDTH-1)
                return (east*100,-north*100,heights[0]*100+180)
    raise RuntimeError("No surveyed shallow-slope dry candidate for spawn")

def run():
    # Reject the protected original project and all nested locations.
    root_norm=str(ROOT).replace("/","\\").lower()
    if root_norm=="d:\\anomalia" or root_norm.startswith("d:\\anomalia\\"):
        raise RuntimeError("Protected original D:\\ANOMALIA: native authoring is prohibited")
    if not SOURCE.is_file() or SOURCE.stat().st_size!=EXPECTED_BYTES:
        raise RuntimeError("Verified DRAZOVIA source RAW 3025² missing or truncated")
    raw=SOURCE.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=EXPECTED_SHA256:
        raise RuntimeError("DRAZOVIA source revision differs; refusing unapproved import")
    if FILE.exists() or unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
        raise RuntimeError("Candidate map already exists; NEVER overwrite it")
    for part in ("__ExternalActors__","__ExternalObjects__"):
        folder=ROOT/"Content"/part/"Maps/ANOMALIA_DrazoviaTopo_NewReference_Candidate"
        if folder.exists():
            raise RuntimeError("Existing candidate external actor data detected")
    # Original files are NEVER opened or saved, even if they already exist.
    native=unreal.AnomaliaZPrigimaliaWorldImportLibrary
    if not hasattr(native,"create_drazovia_izurvive_candidate_landscape"):
        raise RuntimeError("Compile native candidate importer with the new UE5 source first")
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not level or not actors:
        raise RuntimeError("Must run from an installed native Unreal Editor")
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in ORIGINALS if p.is_file()}
    if not level.new_level(PACKAGE,is_partitioned_world=True):
        raise RuntimeError("Cannot create candidate World Partition level")
    w=unreal.EditorLevelLibrary.get_editor_world()
    if w.get_outermost().get_name()!=PACKAGE:
        raise RuntimeError("Unexpected active UE map; refusing Landscape creation")
    actor=native.create_drazovia_izurvive_candidate_landscape()
    if not actor:
        raise RuntimeError("Actual native DRAZOVIA R16 Landscape import failed")
    count=len(actor.get_components_by_class(unreal.LandscapeComponent))
    if count!=576:
        raise RuntimeError("Expected 576 Landscape components; got "+str(count))
    pos=safe_spawn(raw)
    spawn=actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(*pos))
    if not spawn:
        raise RuntimeError("Failed PlayerStart placement")
    spawn.set_actor_label("DRAZOVIA_IzurviveCandidate_SafeSpawn")
    sun=actors.spawn_actor_from_class(unreal.DirectionalLight,
        unreal.Vector(0,0,80000),unreal.Rotator(-47,-25,0))
    sky=actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector(0,0,0))
    ambience=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,5000))
    if not sun or not sky or not ambience:
        raise RuntimeError("Candidate daylight environment incomplete")
    if not level.save_all_dirty_levels():
        raise RuntimeError("Candidate .umap save failed")
    if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True):
        raise RuntimeError("Candidate external actor save failed")
    if not FILE.is_file() or FILE.stat().st_size<1024:
        raise RuntimeError("No actual candidate UE .umap produced")
    after={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
           for p in ORIGINALS if p.is_file()}
    if before!=after:
        raise RuntimeError("Protected world was modified unexpectedly")
    status.update({"state":"CANDIDATE_NATIVE_TERRAIN_SAVED_NOT_PLAYTESTED",
                   "sourceSha256":digest,"landscapeComponents":count,
                   "worldPartitionRequested":True,"playerStartCm":pos,
                   "umapBytes":FILE.stat().st_size,
                   "oldWorldHashesUnchanged":True})

try:
    run()
except Exception as ex:
    status["error"]=str(ex)
    status["traceback"]=traceback.format_exc()
    raise
finally:
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    # Unique receipts should be configured for repeated runs; no overwrite.
    if REPORT.exists():
        raise FileExistsError("Refusing to overwrite existing DRAZOVIA import receipt")
    REPORT.write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    unreal.log("ANOMALIA_DRAZOVIA_TOPO_REPORT="+str(REPORT))
