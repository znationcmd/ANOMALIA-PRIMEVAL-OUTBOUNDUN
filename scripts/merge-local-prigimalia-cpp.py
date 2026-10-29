#!/usr/bin/env python3
"""Safely carry over local-only Unreal native source files into the renamed STAGED copy.

No file in D:\\ANOMALIA is edited. Existing migrated files are NEVER overwritten.
Source additions are audited and written only beneath the new module in staging.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

OLD="AnomaliaPrimeval"
NEW="AnomaliaZPrigimalia"
EXTS={".cpp",".h",".cs"}

def transformed(content:str)->str:
    content=content.replace("ANOMALIAPRIMEVAL_API","ANOMALIAZPRIGIMALIA_API")
    content=content.replace(OLD,"__OLD_MODULE__")
    content=re.sub(r"Anomalia(?!ZPrigimalia)",NEW,content)
    return content.replace("__OLD_MODULE__",NEW)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True,type=Path)
    p.add_argument("--staged",required=True,type=Path)
    p.add_argument("--apply",action="store_true")
    args=p.parse_args()
    original=args.original.resolve()
    stage=args.staged.resolve()
    root=stage/"unreal"
    legacy=original/"unreal/Source"/OLD
    newer=root/"Source"/NEW
    marker=root/"Saved/BrandMigration/verified-source-backup.marker"
    if original.name.lower()!="anomalia" or stage.name.lower()!="anomaliaz-prigimalia":
        raise RuntimeError("Refusing migration outside expected original and stage directories")
    if not marker.exists() or not newer.is_dir() or not legacy.is_dir():
        raise RuntimeError("Missing verified stage, original module, or renamed module")
    copied=[]
    identical=[]
    differing=[]
    local_conflicts=[]
    conflict_root=root/"Saved/BrandMigration/LocalSourceConflicts"
    for src in sorted(legacy.rglob("*")):
        if not src.is_file() or src.suffix.lower() not in EXTS:
            continue
        relative=src.relative_to(legacy).as_posix()
        target_relative=re.sub(r"Anomalia(?!ZPrigimalia)",NEW,relative)
        target=newer/target_relative
        original_text=src.read_text(encoding="utf-8-sig")
        migrated=transformed(original_text)
        if target.exists():
            current=target.read_text(encoding="utf-8-sig")
            if current==migrated:
                identical.append(relative)
            else:
                differing.append(relative)
                local_conflicts.append({
                    "relative": relative,
                    "local_sha256": hashlib.sha256(migrated.encode("utf-8")).hexdigest(),
                    "git_sha256": hashlib.sha256(current.encode("utf-8")).hexdigest(),
                    "preserved_at": "unreal/Saved/BrandMigration/LocalSourceConflicts/"+target_relative,
                })
                if args.apply:
                    conflict_path=conflict_root/target_relative
                    conflict_path.parent.mkdir(parents=True,exist_ok=True)
                    if conflict_path.exists():
                        raise RuntimeError("Refusing to overwrite an existing local source conflict: "+str(conflict_path))
                    conflict_path.write_text(migrated,encoding="utf-8")
            continue
        copied.append({"source":relative,"target":target_relative})
        if args.apply:
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                raise RuntimeError("Race: source target exists, refusing overwrite: "+str(target))
            target.write_text(migrated,encoding="utf-8")
    report={"original":str(original),"staged":str(stage),"apply":args.apply,
            "addedLocalCppFiles":len(copied),"existingIdentical":len(identical),
            "existingDifferentKept":len(differing),"added":copied,
            "differentLocalFilesNotOverwritten":differing,
            "localConflictDetails":local_conflicts,
            "conflictingLocalVersionsSavedSeparately":args.apply,
            "originalUnmodified":True}
    output=root/"Saved/BrandMigration/local-cpp-merge-report.json"
    if args.apply:
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("added","differentLocalFilesNotOverwritten")},ensure_ascii=False,indent=2))
    for f in copied:
        print("LOCAL_ONLY_CPP_ADDED="+f["target"])
    if differing:
        print("LOCAL_CODE_CONFLICTS_PRESERVED_SEPARATELY="+str(len(differing)))
        print("REVIEW_CONFLICTS_BEFORE_FINAL_MERGE=true")
    if not args.apply:
        print("DRY_RUN=true")
if __name__=="__main__":
    main()
