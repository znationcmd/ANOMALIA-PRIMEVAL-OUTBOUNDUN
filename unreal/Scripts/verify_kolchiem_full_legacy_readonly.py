"""Read-only certification of KOLCHIEM ORIGINS FULL legacy actor candidate.
Checks actual Unreal UWorld identity and 7500+ external actor files in the
isolated stage; no saves, edits, or gameplay readiness claims.
"""
import json,os
from pathlib import Path
import unreal
root=Path(unreal.Paths.project_dir()).resolve()
if str(root).replace("/","\\").rstrip("\\").lower()!=r"d:\anomaliaz-prigimalia\unreal":
    raise RuntimeError("Reject wrong UE project")
target="/Game/Maps/PRIGIMALIA_KOLCHIEM_ORIGINS_FULL"
old="/Game/Maps/PRIGIMALIA_Inhabited_v2"
v3="/Game/Maps/ANOMALIA_DrazoviaTopo_NewReferenceV3_Candidate"
out=Path(os.environ["ANOMALIA_KOLCHIEM_FULL_NATIVE_REPORT"])
entries=[]
for package in (target,old,v3):
    a=unreal.load_asset(package)
    valid=bool(a and isinstance(a,unreal.World) and a.get_outermost().get_name()==package)
    entries.append({"package":package,"worldLoaded":valid,"actual":a.get_outermost().get_name() if a else ""})
    if not valid:
        raise RuntimeError("Native World cannot load with distinct identity: "+package)
external=root/"Content/__ExternalActors__/Maps/PRIGIMALIA_KOLCHIEM_ORIGINS_FULL"
count=sum(1 for _ in external.rglob("*.uasset")) if external.is_dir() else 0
if count<7500:
    raise RuntimeError(f"Full legacy actor set not present: {count} external actor files")
result={
 "status":"FULL_LEGACY_NATIVE_WORLD_RELOADED_EXTERNAL_ACTORS_PRESENT_NOT_PLAYTESTED",
 "worlds":entries,"externalActorFiles":count,"streamingVerified":False,
 "landscapeAndBuildingsRendered":False,"gameplayTested":False,"originalMapsModified":False}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
unreal.log("KOLCHIEM_FULL_WORLD_NATIVE_RELOADED_ACTORS="+str(count))
