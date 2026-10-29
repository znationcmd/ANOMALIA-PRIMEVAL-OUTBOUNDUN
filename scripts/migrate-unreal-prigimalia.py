#!/usr/bin/env python3
"""ANOMALIA’Z PRIGIMALIA -- migration of owned Unreal C++ source and project references.

Run on a clean, dedicated branch, never on the live Windows installation.
Dry-run by default. '--apply' moves tracked game-source paths and fixes textual
references; existing .uasset/.umap assets are intentionally NEVER moved here:
their package name changes require Unreal Editor and redirector fixup.

The application/runtime IDs and existing saved-game folder names stay as legacy
aliases, to prevent loss of user data. This is a technical compatibility constraint.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_MODULE = "AnomaliaPrimeval"
NEW_MODULE = "AnomaliaZPrigimalia"
NEW_TITLE = "ANOMALIA’Z PRIGIMALIA"
EXTS = {".cpp",".h",".cs",".uproject",".ini",".json",".py",".ps1",".vbs",
        ".cmd",".mjs",".js",".cjs",".html",".css",".md",".txt",".cfg",
        ".yml",".yaml",".xml"}
IGNORE = {".git",".github","node_modules","Saved","Intermediate","Binaries",
          "DerivedDataCache","dist","release",".venv","__pycache__","Content"}
LEGACY_SAVE_NAMES = ("anomalia-primeval-outboundun-save-v1",
                     "com.cmd.anomalia.primevaloutboundun",
                     "anomalia://", "anomalia:connect", "anomalia:socket")
# Saved keys, IPC messages and RPC field IDs remain as wire-compatible aliases.

def changes_in_source(src: str) -> str:
    src = src.replace("ANOMALIAPRIMEVAL_API", "ANOMALIAZPRIGIMALIA_API")
    src = src.replace("ANOMALIAPRIMEVAL", "ANOMALIAZPRIGIMALIA")
    src = src.replace(OLD_MODULE, "__MIGRATED_MODULE__")
    src = re.sub(r"Anomalia(?!ZPrigimalia)", NEW_MODULE, src)
    src = src.replace("__MIGRATED_MODULE__", NEW_MODULE)
    # UE macro name is based on the module, not a class.
    return src

def change_general(src: str, path: Path) -> str:
    # DefaultEngine.ini has legacy redirect keys: they must NEVER be rewritten as normal text.
    if path.resolve() == (ROOT / "unreal/Config/DefaultEngine.ini").resolve():
        return src
    src = src.replace(OLD_MODULE, NEW_MODULE)
    src = src.replace("ANOMALIA PRIMEVAL OUTBOUNDUN", NEW_TITLE)
    src = src.replace("ANOMALIA_PRIMEVAL_OUTBOUNDUN", "ANOMALIAZ_PRIGIMALIA")
    src = src.replace("Config/Anomalia/", "Config/AnomaliaZPrigimalia/")
    src = src.replace("AnomaliaSourceCommit", "AnomaliaZPrigimaliaSourceCommit")
    # Rename C++ symbols mentioned in validation scripts and tests, without
    # renaming serialized /Game/Anomalia packages or legacy transport IDs.
    src = re.sub(r"Anomalia(?!ZPrigimalia)(?=[A-Z][A-Za-z0-9_]+)",NEW_MODULE,src)
    # Correct all file references to C++ module and headers in scripts/tests/docs.
    if path.suffix in {".py",".ps1",".vbs",".cmd",".mjs",".js",".cjs",".md",".txt",".ini",".json",".yml",".yaml",".xml",".cfg",".html",".cs"}:
        src = re.sub(r"(?<=/)(Anomalia)(?=[A-Z][A-Za-z0-9]*\\.(?:h|cpp|generated\\.h))",
                     NEW_MODULE, src)
        src = re.sub(r"(?<=\\\\)(Anomalia)(?=[A-Z][A-Za-z0-9]*\\.(?:h|cpp))",
                     NEW_MODULE, src)
    return src

def collect_reflected_types(root: Path) -> dict[str,list[str]]:
    # Reflected type redirects make old Blueprint and serialized C++ class names loadable.
    types: dict[str,set[str]] = {"Class":set(),"Struct":set(),"Enum":set()}
    for p in (root/"unreal"/"Source").rglob("*.h"):
        if OLD_MODULE not in str(p) and NEW_MODULE not in str(p):
            continue
        text = p.read_text(encoding="utf-8",errors="replace")
        for prefix,kind in (("A","Class"),("U","Class"),("F","Struct"),("E","Enum")):
            for match in re.findall(r"\b"+prefix+r"(?:AnomaliaZPrigimalia|Anomalia)[A-Za-z0-9_]+\b",text):
                if prefix=="F" and "USTRUCT" not in text:
                    continue
                if prefix=="E" and "UENUM" not in text:
                    continue
                types[kind].add(match[1:].replace(NEW_MODULE,"Anomalia",1))
    return {kind:sorted(values) for kind,values in types.items()}

def redirects(types: dict[str,list[str]]) -> str:
    records = []
    mapping={"Class":"ClassRedirects","Struct":"StructRedirects","Enum":"EnumRedirects"}
    for kind,names in types.items():
        for name in names:
            records.append(
                f'+{mapping[kind]}=(OldName="/Script/{OLD_MODULE}.{name}",'
                f'NewName="/Script/{NEW_MODULE}.{name.replace("Anomalia",NEW_MODULE,1)}")'
            )
    return "\n".join(records)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()

    # Calculate before renaming source files.
    ue=root_ue=ROOT/"unreal"
    types=collect_reflected_types(ROOT)
    file_changes=[]
    moves=[]
    for p in list(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel=p.relative_to(ROOT)
        if any(part in IGNORE for part in rel.parts):
            continue
        if p.suffix.lower() not in EXTS:
            continue
        if p.stat().st_size>2_000_000:
            continue
        if p.resolve()==Path(__file__).resolve():
            continue
        try:
            original=p.read_text(encoding="utf-8")
        except (OSError,UnicodeDecodeError):
            continue
        source=rel.parts[:2]==("unreal","Source")
        changed=changes_in_source(original) if source else change_general(original,p)
        new_rel=rel
        if source:
            new_rel=Path(re.sub(r"Anomalia(?!ZPrigimalia)",NEW_MODULE,str(rel).replace(OLD_MODULE,"__MIGRATED_MODULE__")).replace("__MIGRATED_MODULE__",NEW_MODULE))
        elif rel==Path("unreal")/(OLD_MODULE+".uproject"):
            new_rel=Path("unreal")/(NEW_MODULE+".uproject")
        elif rel.parts[:3]==("unreal","Config","Anomalia"):
            new_rel=Path(str(rel).replace("unreal/Config/Anomalia/","unreal/Config/AnomaliaZPrigimalia/"))
        if changed!=original or new_rel!=rel:
            file_changes.append((str(rel),str(new_rel)))
            if args.apply:
                target=ROOT/new_rel
                target.parent.mkdir(parents=True,exist_ok=True)
                if new_rel!=rel and target.exists():
                    raise RuntimeError("Refusing overwrite: "+str(target))
                target.write_text(changed,encoding="utf-8")
                if new_rel!=rel:
                    p.unlink()
                    moves.append((str(rel),str(new_rel)))
    config=ue/"Config"/"DefaultEngine.ini"
    if config.exists():
        content=config.read_text(encoding="utf-8")
        section="[CoreRedirects]"
        legacy=redirects(types)
        if section not in content:
            content+="\n"+section+"\n"
        # Repair redirects wrongly rewritten by an older migration iteration.
        # OldName always identifies an actual OLD module/class, never the new one.
        updated=[]
        for line in content.splitlines():
            if line.startswith('+ActiveGameNameRedirects=') and 'OldGameName="/Script/'+NEW_MODULE+'"' in line:
                continue
            for kind in ('Class','Struct','Enum'):
                prefix=f'+{kind}Redirects=(OldName="/Script/{NEW_MODULE}.{NEW_MODULE}'
                if line.startswith(prefix):
                    line=(f'+{kind}Redirects=(OldName="/Script/{OLD_MODULE}.Anomalia'
                          +line[len(prefix):])
            updated.append(line)
        content="\n".join(updated).rstrip()+"\n"
        # Active game-name redirects belong to [/Script/Engine.Engine].
        redirect=f'+ActiveGameNameRedirects=(OldGameName="/Script/{OLD_MODULE}",NewGameName="/Script/{NEW_MODULE}")'
        engine_header='[/Script/Engine.Engine]\n'
        if redirect not in content:
            if engine_header not in content:
                raise RuntimeError("Missing Engine.Engine section")
            content=content.replace(engine_header,engine_header+redirect+"\n",1)
        # Append only missing class/struct/enum redirects to CoreRedirects.
        records=legacy.splitlines()
        for record in records:
            if record not in content:
                content+="\n"+record
        content=content.replace('GlobalDefaultGameMode=/Script/'+NEW_MODULE+'.AnomaliaGameMode',
                                'GlobalDefaultGameMode=/Script/'+NEW_MODULE+'.'+NEW_MODULE+'GameMode')
        if args.apply:
            config.write_text(content,encoding="utf-8")
    # Build a readable audit proof for the CI job; no generated assets deleted.
    report={"title":NEW_TITLE,"newModule":NEW_MODULE,
            "editedFiles":len(file_changes),"renamedFiles":len(moves),
            "redirectTypes":{k:len(v) for k,v in types.items()},
            "binaryAssetsRenamed":False,"windowsUEBuildTested":False,
            "historicalSaveIdsPreserved":list(LEGACY_SAVE_NAMES),
            "remainingNativeAssetMigration":"Run UE5.8 Editor rename + Fix Up Redirectors on Windows",
            "fileChanges":file_changes}
    if args.apply:
        proof=ROOT/"docs"/"rebrand-unreal-source-receipt.json"
        proof.parent.mkdir(parents=True,exist_ok=True)
        proof.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="fileChanges"},ensure_ascii=False,indent=2))
    for old,new in file_changes[:10]:
        print(old+" -> "+new)
    if not args.apply:
        print("DRY RUN ONLY. Use --apply on a separate branch.")
if __name__=="__main__":
    main()
