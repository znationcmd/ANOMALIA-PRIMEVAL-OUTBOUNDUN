"""Repair only the missing City Sample AssetManager type, preserving configuration."""
import os,json,pathlib,hashlib,re
stage=pathlib.Path(r"C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal")
source=pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample\Config\DefaultGame.ini")
target=stage/"Config/DefaultGame.ini"
out=pathlib.Path(os.environ["MISSION_MAP_OUT"]);out.mkdir(parents=True,exist_ok=True)
assert (stage/".skarvik-ci-stage-marker").read_text().strip()=="41188816555"
def decode(raw):
    enc="utf-16" if raw.startswith((b"\xff\xfe",b"\xfe\xff")) else ("utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8")
    return raw.decode(enc),enc
def rules(text):
    section=""
    result=[]
    for line in text.splitlines():
        if line.strip().startswith("["):section=line.strip()
        if section=="[/Script/Engine.AssetManagerSettings]" and line.lstrip().startswith("+PrimaryAssetTypesToScan=") and 'PrimaryAssetType="GameFeatureData"' in line:
            result.append(line.strip())
    return result
source_raw=source.read_bytes();old=target.read_bytes()
golden,enc_source=decode(source_raw);text,enc=decode(old)
candidates=rules(golden)
assert len(candidates)==1 and "AssetBaseClass=/Script/GameFeatures.GameFeatureData" in candidates[0],"Expected exactly one existing City Sample GameFeatureData rule"
present=rules(text)
receipt={"source":str(source),"target":str(target),"sourceSHA256":hashlib.sha256(source_raw).hexdigest(),"targetSHA256Before":hashlib.sha256(old).hexdigest(),"rule":candidates[0],"mainDProjectModified":False,"modified":False}
if present:
    assert present==candidates,"A distinct existing rule must be reviewed and preserved"
else:
    backup=stage/"Saved/MissionConfigurationBackups"/os.environ["GITHUB_RUN_ID"]/"DefaultGame.ini"
    backup.parent.mkdir(parents=True,exist_ok=False)
    with backup.open("xb") as file:file.write(old)
    assert backup.read_bytes()==old
    updated=text.rstrip("\r\n")+"\r\n\r\n[/Script/Engine.AssetManagerSettings]\r\n"+candidates[0]+"\r\n"
    assert target.read_bytes()==old,"Configuration changed during preparation"
    temporary=target.with_name(target.name+".mission-"+os.environ["GITHUB_RUN_ID"])
    with temporary.open("xb") as file:file.write(updated.encode(enc))
    os.replace(temporary,target)
    receipt.update(modified=True,backup=str(backup),backupSHA256=hashlib.sha256(backup.read_bytes()).hexdigest())
assert source.read_bytes()==source_raw,"Original City Sample configuration changed"
receipt["targetSHA256After"]=hashlib.sha256(target.read_bytes()).hexdigest()
(out/"assetmanager-repair-receipt.json").write_text(json.dumps(receipt,indent=2),encoding="utf-8")
print("Existing City Sample GameFeatureData rule installed:",receipt["modified"])
