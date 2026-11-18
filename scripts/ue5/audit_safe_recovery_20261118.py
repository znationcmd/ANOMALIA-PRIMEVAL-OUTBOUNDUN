"""Read-only inventory of regenerable Unreal caches and OneDrive client sync.
No file content reads, mutations, deletion, or secret collection.
"""
import os, pathlib, json, time, shutil, datetime, stat
C=pathlib.Path("C:/")
D=pathlib.Path("D:/")
USER=pathlib.Path(os.environ["LOCALAPPDATA"])
TARGETS=[
 ("C Unreal legacy DDC", USER/"UnrealEngine/Common/DerivedDataCache"),
 ("C Unreal Zen data (audit only)", USER/"UnrealEngine/Common/Zen/Data"),
 ("C old mission DDC", pathlib.Path(r"C:\ANOMALIA_MISSION_41801391717\unreal\DerivedDataCache")),
 ("C old staging DDC", pathlib.Path(r"C:\ANOMALIAZ_SKARVIK_STAGE_41188816555\unreal\DerivedDataCache")),
 ("C Epic City Sample VaultCache", pathlib.Path(r"C:\ProgramData\Epic\EpicGamesLauncher\VaultCache\CitySample_5.8\data")),
 ("D game DDC", pathlib.Path(r"D:\ANOMALIA\unreal\DerivedDataCache")),
 ("D game Intermediate", pathlib.Path(r"D:\ANOMALIA\unreal\Intermediate")),
 ("D CitySample Intermediate", pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample\Intermediate")),
 ("D game Saved (do NOT delete)", pathlib.Path(r"D:\ANOMALIA\unreal\Saved")),
 ("D CitySample source (do NOT delete)", pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample"))
]
def scan(name,root):
  entry={"name":name,"exists":False,"bytes":0,"files":0,"reparseSkipped":0,"partial":False,"elapsedSeconds":0}
  if not root.exists():return entry
  entry["exists"]=True
  if root.is_symlink() or (getattr(root.lstat(),"st_file_attributes",0)&0x400):
    entry["rootIsReparse"]=True
    return entry
  since=time.monotonic()
  for base,dirs,names in os.walk(root,followlinks=False):
    dirs[:]=[d for d in dirs if not (getattr((pathlib.Path(base)/d).lstat(),"st_file_attributes",0)&0x400)]
    for n in names:
      p=pathlib.Path(base)/n
      try:
        s=p.lstat()
        if (getattr(s,"st_file_attributes",0)&0x400) or not stat.S_ISREG(s.st_mode):
          entry["reparseSkipped"]+=1
          continue
        entry["bytes"]+=s.st_size
        entry["files"]+=1
      except OSError:pass
    if time.monotonic()-since>100:
      entry["partial"]=True
      break
  entry["elapsedSeconds"]=round(time.monotonic()-since,1)
  return entry
source=pathlib.Path(r"D:\ANOMALIA\FabImports\CitySample")
root=os.environ.get("OneDriveConsumer","")
dest=pathlib.Path(root)/"ANOMALIAZ_PRIGIMALIA"/"Backups"/"CitySample" if root else None
samples=[
r"Content\Effect\Texture\Flipbooks\Pyro_1_Flipbook_Pyro_1_rop_comp1_0001.uasset",
r"Content\Megascans\Surfaces\Tile_Sidewalk_ug4kbdus\ug4kbdus_8K_Albedo.uasset",
r"Content\Megascans\Surfaces\Cast_In_Situ_Concrete_Wall_vcfice0\Asphalt_Road_2x2_M_05\tiggcjdo_8K_Normal.uasset",
r"Content\Building\Lighting\HDRI_SFCorner.uasset",
r"Content\Building\Texture\Concrete\T_Concrete_N.uasset",
r"Content\Prop\Kit_Border_B\Texture\T_BorderB_N_Oasis.uasset",
r"Content\Megascans\Surfaces\Cast_In_Situ_Concrete_Wall_vcfice0\Asphalt_Road_2x2_M_03\th5kfebew_8K_Normal.uasset",
r"Content\Vehicle\vehTruck_trailer01\Texture\T_vehTruck_trailer01_Grime.uasset",
r"Content\Road\Textures\Sidewalks\T_sidewalk_largeSquareTile_pebble_Color.uasset",
r"Content\Megascans\3D_Assets\Modular_Building_5th_Floor_Kit_00\Normal_8K_LOD0_vb3hbjjdw.uasset"]
observations=[]
for rel in samples:
 p=dest/rel if dest else None
 rec={"relative":rel,"exists":bool(p and p.exists())}
 if rec["exists"]:
  s=p.lstat()
  a=getattr(s,"st_file_attributes",0)
  rec.update(bytes=s.st_size,offline=bool(a&0x1000),unpinned=bool(a&0x100000),reparse=bool(a&0x400))
 observations.append(rec)
audit={"readOnly":True,"sourceFilesDeleted":0,"gameFilesModified":0,
"reportedAtUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),
"freeBytes":{"C":shutil.disk_usage(C).free,"D":shutil.disk_usage(D).free},
"onedriveBatch3Samples":observations,"targets":[]}
for n,p in TARGETS:
  r=scan(n,p);audit["targets"].append(r)
  print("RECOVERY_AUDIT_FOLDER "+json.dumps(r),flush=True)
audit["freeBytesAfterScan"]={"C":shutil.disk_usage(C).free,"D":shutil.disk_usage(D).free}
audit["reportedAtUTC"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
print("RECOVERY_READONLY_AUDIT "+json.dumps(audit),flush=True)
out=pathlib.Path(os.environ["RECOVERY_AUDIT_OUT"]);out.mkdir(parents=True,exist_ok=True)
(out/"recovery-audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
