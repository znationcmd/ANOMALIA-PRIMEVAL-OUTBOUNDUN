"""Rename native Unreal assets inside the Editor, never by moving .uasset files.

Run through Unreal Editor Python Scripting. Default is audit only.
For an actual migration, on a BACKUP COPY, set environment variable
PRIGIMALIA_APPLY_RENAME=YES and run this script in Unreal Editor (not PIE).
Do not run while anybody edits the map. Full World Partition levels must
be separately reviewed in the editor.
"""
import os
import json
from pathlib import Path
import unreal

OLD="/Game/Anomalia"
NEW="/Game/AnomaliaZPrigimalia"
MODE=os.environ.get("PRIGIMALIA_APPLY_RENAME","NO")
ROOT=Path(unreal.Paths.project_dir()).resolve()
OUTPUT=ROOT/"Saved"/"BrandMigration"/"asset-rename-report.json"
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
api=unreal.EditorAssetLibrary

def audit():
    if not api.does_directory_exist(OLD):
        return []
    return sorted(set(api.list_assets(OLD,recursive=True,include_folder=False)))

def execute():
    names=audit()
    report={"newTitle":"ANOMALIA’Z PRIGIMALIA","source":OLD,"destination":NEW,
        "applyRequested":MODE=="YES","found":len(names),
        "renamed":False,"verified":False,"errors":[],"before":names}
    try:
        if MODE!="YES":
            unreal.log_warning("DRY RUN: pass PRIGIMALIA_APPLY_RENAME=YES only on a backup copy.")
        elif api.does_directory_exist(NEW) and api.does_directory_have_assets(NEW,recursive=True):
            raise RuntimeError("Destination already contains assets; refuse to overwrite.")
        elif not names:
            unreal.log("No legacy assets: migration may have already completed.")
        else:
            # Asset Tools updates UE object references and creates redirectors.
            # Direct OS moves / git mv of binary packages are deliberately forbidden.
            if not api.rename_directory(OLD, NEW):
                raise RuntimeError("Unreal Editor rejected directory rename")
            report["renamed"]=True
            report["verified"]=api.does_directory_exist(NEW) and all(
                api.does_asset_exist(name.replace(OLD+"/",NEW+"/",1))
                for name in names
            )
            if not report["verified"]:
                raise RuntimeError("Post-rename reference verification incomplete")
            if not api.save_directory(NEW,only_if_is_dirty=False,recursive=True):
                raise RuntimeError("One or more migrated assets could not be saved")
            unreal.log("Assets moved; review redirectors & World Partition levels in Content Browser.")
    except Exception as exc:
        report["errors"].append(str(exc))
        unreal.log_error("ANOMALIA’Z PRIGIMALIA asset rename: "+str(exc))
    finally:
        report["remainingOld"]=audit()
        OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        unreal.log("Brand migration report: "+str(OUTPUT))
    if report["errors"]:
        raise RuntimeError("Asset rename failed; original backup must be retained.")
    return report

execute()
