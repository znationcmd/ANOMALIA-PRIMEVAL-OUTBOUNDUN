#!/usr/bin/env python3
"""Finish textual UE package/map references after a VERIFIED native asset migration.

Requires a staged, backed up copy. This script does not edit uasset/umap files,
the original D:\\ANOMALIA directory, legacy saved-game IDs or network protocols.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SUFFIXES={".cpp",".h",".ini",".cfg",".py",".ps1",".json",".js",".mjs",".cjs",".html",".md",
          ".txt",".xml",".yaml",".yml",".cs",".uproject",".vbs"}
DIRECTORIES=("unreal/Config","unreal/Scripts","unreal/Source","unreal/Content/Python",
             "scripts","src","server","public","distribution","tests","docs")
REPLACEMENTS=(
    ("/Game/Anomalia/","/Game/AnomaliaZPrigimalia/"),
    ("unreal/Content/Anomalia/","unreal/Content/AnomaliaZPrigimalia/"),
    ("Content/Anomalia/","Content/AnomaliaZPrigimalia/"),
    ("ANOMALIA_","PRIGIMALIA_"),
    ("AnomaliaWorld","PrigimaliaWorld"),
)
# This path-mapping step deliberately never renames the old backup root
# D:\\ANOMALIA, historic IPC keys, or old game class redirect source entries.

def migrate(root:Path,apply:bool):
    root=root.resolve()
    if root.name.lower()!="anomaliaz-prigimalia" or str(root).lower().startswith("d:\\anomalia\\"):
        raise RuntimeError("Expected isolated ANOMALIAZ-PRIGIMALIA stage, never original project")
    marker=root/"unreal/Saved/BrandMigration/verified-source-backup.marker"
    assetreport=root/"unreal/Saved/BrandMigration/asset-rename-report.json"
    if not marker.exists() or not assetreport.exists():
        raise RuntimeError("Required clone and asset migration proofs are missing")
    proof=json.loads(assetreport.read_text(encoding="utf-8-sig"))
    if proof.get("verified") is not True or proof.get("errors"):
        raise RuntimeError("Assets were not successfully migrated in Unreal Editor")
    updates=[]
    for folder in DIRECTORIES:
        base=root/folder
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SUFFIXES:
                continue
            if path.stat().st_size>2_000_000:
                continue
            relative=path.relative_to(root).as_posix()
            if relative.endswith("migrate_prigimalia_assets.py") or relative.endswith("migrate-prigimalia-package-references.py"):
                continue
            if "rebrand-unreal-source-receipt.json" in relative or relative.startswith("docs/REBRAND_"):
                continue
            try:
                original=path.read_text(encoding="utf-8")
            except (OSError,UnicodeError):
                continue
            changed=original
            for old,new in REPLACEMENTS:
                changed=changed.replace(old,new)
            if changed!=original:
                updates.append(relative)
                if apply:
                    path.write_text(changed,encoding="utf-8")
    report={"newTitle":"ANOMALIA’Z PRIGIMALIA","root":str(root),"changedFiles":len(updates),
            "files":updates,"applied":apply,"nativeAssetsVerified":True,
            "historicDataPreserved":True}
    if apply:
        out=root/"unreal/Saved/BrandMigration/package-ref-update-report.json"
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="files"},indent=2,ensure_ascii=False))
    for path in updates[:20]:
        print("UPDATED: "+path)
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    migrate(args.root,args.apply)
