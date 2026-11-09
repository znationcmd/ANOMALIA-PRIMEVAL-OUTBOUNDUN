"""UE5.8 Editor-only SAFE staging entrypoint for SKJÆRØYÅS.

Run from UE Python console in a COPY of the project (not the original):
  import sys
  sys.path.insert(0, r"C:\ANOMALIA-UE5-SOURCE\unreal\EditorPython")
  import stage_skjaeroyaas_world
  stage_skjaeroyaas_world.create_new_partitioned_staging_level(
      r"C:\SKJAEROYAAS_STAGING\skjaeroyaas-layout.json",
      confirm_create=True)

Creates a *new* World Partition level and village/road endpoint TargetPoints.
Does NOT import Landscape, forests, water meshes or existing 3D assets.
Never writes to an existing level package. No UE execution on GitHub CI.
"""
from __future__ import annotations
import json
from pathlib import Path

ASSET = "/Game/Maps/SKJAEROYAAS_15KM_STAGE"


def check_layout(path: str | Path) -> dict:
    """Schema/coordinate validation works even outside Unreal."""
    layout=json.loads(Path(path).read_text(encoding="utf-8"))
    if (layout.get("schemaVersion") != 1 or layout.get("worldId") != "skjaeroyaas"
            or layout.get("dimensionsKm") != [15,15]):
        raise ValueError("This is not the SKJÆRØYÅS staging layout")
    sites=layout.get("villages")
    edges=layout.get("roadCandidates")
    if not isinstance(sites,list) or len(sites) != 6 or not isinstance(edges,list):
        raise ValueError("Missing six village markers or proposed roads")
    seen=set()
    for site in sites:
        if site["id"] in seen:
            raise ValueError("Duplicated settlement IDs")
        seen.add(site["id"])
        for coord in ("xMeters","yMeters","zMeters"):
            if not isinstance(site.get(coord),(int,float)):
                raise ValueError("Invalid site coordinates")
        if max(abs(site["xMeters"]),abs(site["yMeters"])) > 7500:
            raise ValueError("Site outside landscape bounds")
    for edge in edges:
        if edge["from"] not in seen or edge["to"] not in seen:
            raise ValueError("Road refers to missing village")
    return layout


def create_new_partitioned_staging_level(layout_path: str | Path,
                                         confirm_create: bool=False) -> dict:
    """One-way new-level creation; do not run on original project or twice."""
    layout=check_layout(layout_path)
    if not confirm_create:
        return {"dryRun":True,"level":ASSET,"markers":len(layout["villages"]),
                "message":"Set confirm_create=True only inside backed-up staging project"}
    try:
        import unreal  # available only in native Unreal Editor with Python plugin
    except ImportError as ex:
        raise RuntimeError("Requires UE5 editor's PythonScriptPlugin, not regular Python") from ex
    # The physical and registry checks are BOTH needed, because a level asset can
    # be absent from registry when an editor scan has not yet completed.
    content=Path(unreal.Paths.project_content_dir()).resolve()
    filename=content/"Maps"/"SKJAEROYAAS_15KM_STAGE.umap"
    if filename.exists() or unreal.EditorAssetLibrary.does_asset_exist(ASSET):
        raise FileExistsError("Refusing to overwrite an existing SKJÆRØYÅS level")
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if level.is_in_play_in_editor():
        raise RuntimeError("Cannot create a level during Play In Editor")
    if not level.new_level(ASSET,is_partitioned_world=True):
        raise RuntimeError("UE failed to create a new World Partition level")
    count=0
    for site in layout["villages"]:
        pos=unreal.Vector(float(site["xMeters"])*100,
                          float(site["yMeters"])*100,
                          (float(site["zMeters"])+8)*100)
        actor=actors.spawn_actor_from_class(unreal.TargetPoint,pos,unreal.Rotator())
        if not actor:
            raise RuntimeError("Could not place settlement marker: "+site["id"])
        actor.set_actor_label("AZ_SKJAEROYAAS_"+site["id"]+"_"+site["name"])
        actor.set_editor_property("tags",[unreal.Name("AZ_SKJAEROYAAS"),
                                           unreal.Name("VILLAGE_STAGING")])
        count+=1
    # Road endpoints are markers only; road splines and bridges require authoring.
    if not level.save_current_level():
        raise RuntimeError("Unable to save new World Partition staging level")
    return {"dryRun":False, "level":ASSET, "villageTargetPoints":count,
            "landscapeImported":False, "roadsBuilt":False, "forestsPlaced":False,
            "verifyOrientationBeforeUsingLocations":True}


if __name__=="__main__":
    print("Import module in UE5's Python console; call check_layout or create_new_partitioned_staging_level.")
