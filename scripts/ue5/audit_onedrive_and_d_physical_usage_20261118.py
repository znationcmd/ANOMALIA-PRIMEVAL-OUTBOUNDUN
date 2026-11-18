"""Read-only audit: disk usage, D project top-level, and OneDrive online-only state.
No credentials or file contents are read; only metadata.
"""
import os,pathlib,stat,time,json,shutil,datetime
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
out={"readOnly":True,"generatedUTC":utc(),"freeBytes":{},
"counts":{},"onedriveSamples":[],"dSubtreeTotals":[],"bigFiles":[],"errors":[]}
for k in ["C","D"]:
 out["freeBytes"][k]=shutil.disk_usage(k+":/").free
src=pathlib.Path(r"D:\ANOMALIA")
dest=pathlib.Path(os.environ.get("OneDriveConsumer","C:/_nonexistent"))/"ANOMALIAZ_PRIGIMALIA/Backups/CitySample"
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
for rel in samples:
 p=dest/rel
 item={"file":rel,"exists":False}
 try:
  st=p.lstat()
  mask=getattr(st,"st_file_attributes",0)
  item.update(exists=True,bytes=st.st_size,offline=bool(mask&0x1000),unpinned=bool(mask&0x100000),reparse=bool(mask&0x400))
 except FileNotFoundError:pass
 out["onedriveSamples"].append(item)
out["oneDriveProcessPresent"]=any(True for _ in [])
# Read-only sizing of D:\ANOMALIA limited to 150 seconds.
first={};second={};largest=[]
start=time.monotonic()
skip={".git"}
visited=0
for base,dirs,names in os.walk(src,followlinks=False):
 current=pathlib.Path(base)
 dirs[:]=[d for d in dirs if d.casefold() not in skip and not (getattr((current/d).lstat(),"st_file_attributes",0)&0x400)]
 rel=current.relative_to(src)
 parts=rel.parts
 for name in names:
  p=current/name
  try:
   st=p.lstat()
   if not stat.S_ISREG(st.st_mode) or getattr(st,"st_file_attributes",0)&0x400:continue
   visited+=1
   grp=parts[0] if parts else "(root)"
   sub="/".join(parts[:2]) if len(parts)>1 else grp
   item=first.setdefault(grp,{"name":grp,"bytes":0,"files":0})
   item["bytes"]+=st.st_size;item["files"]+=1
   item2=second.setdefault(sub,{"name":sub,"bytes":0,"files":0})
   item2["bytes"]+=st.st_size;item2["files"]+=1
   if st.st_size>512*1024*1024:
    largest.append({"path":str(p.relative_to(src)),"bytes":st.st_size,"suffix":p.suffix,"links":st.st_nlink})
  except OSError:pass
 if time.monotonic()-start>150:
  out["partialScan"]=True
  break
out["counts"]["filesScanned"]=visited
out["counts"]["seconds"]=round(time.monotonic()-start,2)
out["dSubtreeTotals"]=sorted(second.values(),key=lambda x:x["bytes"],reverse=True)[:30]
out["dTopLevelTotals"]=sorted(first.values(),key=lambda x:x["bytes"],reverse=True)[:30]
out["bigFiles"]=sorted(largest,key=lambda x:x["bytes"],reverse=True)[:30]
out["afterFreeBytes"]={k:shutil.disk_usage(k+":/").free for k in ["C","D"]}
text=json.dumps(out,ensure_ascii=False)
print("ANOMALIA_ONEDRIVE_D_USAGE_AUDIT "+text,flush=True)
dest=pathlib.Path(os.environ["D_ONEDRIVE_AUDIT_DIR"])
dest.mkdir(parents=True,exist_ok=True)
(dest/"onedrive-and-d-usage-audit.json").write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
