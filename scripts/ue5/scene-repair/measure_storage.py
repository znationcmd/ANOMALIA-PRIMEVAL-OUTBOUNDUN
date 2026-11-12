"""Read measured cache candidates; never delete source assets or installed games."""
import os,json,stat,shutil
from pathlib import Path
out=Path(os.environ['SCENE_REPAIR_OUT'])
roots=[Path(r'C:\ANOMALIAZ_AuthenticBuild\Cooked\Windows'),Path(r'C:\ANOMALIA-Validation\c40543166274\unreal\Intermediate'),Path(r'C:\ANOMALIA-Validation\c40543166274\unreal\Saved\Cooked'),Path(r'C:\ANOMALIA-Validation\c40543166274\unreal\DerivedDataCache'),Path(r'C:\Users\utilisateur\AppData\Local\UnrealEngine\Common\DerivedDataCache'),Path(r'C:\Users\utilisateur\AppData\Local\UnrealEngine\Common\Zen\Data'),Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal\Saved\Cooked'),Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal\Saved\StagedBuilds')]
r={'free':{d:shutil.disk_usage(d).free for d in ['C:/','D:/']},'measured':[]}
for p in roots:
 size=0;files=0
 if not p.is_dir():continue
 for base,dirs,names in os.walk(p,followlinks=False):
  dirs[:]=[n for n in dirs if not getattr(Path(base,n).lstat(),'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT]
  for name in names:
   try:size+=Path(base,name).stat().st_size;files+=1
   except OSError:pass
 r['measured'].append({'path':str(p),'bytes':size,'files':files})
(out/'storage-measured.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
