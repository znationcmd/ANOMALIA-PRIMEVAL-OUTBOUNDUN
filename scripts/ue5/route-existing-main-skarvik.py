"""Route the actual installed project to its existing, fingerprinted SKARVIK map."""
from pathlib import Path
import os,re,json,hashlib,shutil
ROOT=Path('D:/ANOMALIA/unreal')
MAP='/Game/Maps/PRIGIMALIA_SKARVIK_FINAL_v1'
KNOWN_SHA='f61ad17decfb48e7be2a5ed9001d661d8567dc4419f9b3739352006cbdf57604'
SECTION='/Script/EngineSettings.GameMapsSettings'
def set_map_settings(text):
 lines=text.splitlines(keepends=True);active=False;found=False;keys=set();output=[]
 for line in lines:
  stripped=line.strip()
  if stripped.startswith('[') and stripped.endswith(']'):
   if active:
    for key in ('GameDefaultMap','EditorStartupMap'):
     if key not in keys:output.append(key+'='+MAP+'\n')
   active=stripped=='['+SECTION+']';found=found or active
  if active and not stripped.startswith((';','#')) and '=' in stripped:
   key,value=stripped.split('=',1)
   if key.strip() in ('GameDefaultMap','EditorStartupMap'):
    keys.add(key.strip());output.append(key.strip()+'='+MAP+'\n');continue
  output.append(line)
 if not found:raise RuntimeError('Installed GameMapsSettings section missing')
 if active:
  for key in ('GameDefaultMap','EditorStartupMap'):
   if key not in keys:output.append(key+'='+MAP+'\n')
 return ''.join(output)
def main():
 out=Path(os.environ['MAIN_MAP_OUT']);out.mkdir(parents=True,exist_ok=True)
 file=ROOT/'Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap'
 if hashlib.sha256(file.read_bytes()).hexdigest()!=KNOWN_SHA:raise RuntimeError('Existing SKARVIK differs from preserved 653-map inventory; no configuration changed')
 config=ROOT/'Config/DefaultEngine.ini';raw=config.read_bytes()
 text=raw.decode('utf-8-sig');current=None;active=False
 for line in text.splitlines():
  stripped=line.strip()
  if stripped.startswith('['):active=stripped=='['+SECTION+']'
  elif active and stripped.startswith('GameDefaultMap='):current=stripped.split('=',1)[1]
 if current not in ('/Game/AnomaliaWorld.AnomaliaWorld','/Game/AnomaliaWorld',MAP):raise RuntimeError('Startup route changed externally; preserve it for review')
 replacement=set_map_settings(text);encoded=replacement.encode('utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8')
 backup=out/'DefaultEngine.ini.before'
 if backup.exists():raise RuntimeError('Routing backup already exists; preserve prior attempt')
 shutil.copy2(config,backup)
 temp=config.with_name('DefaultEngine.ini.skarvik-'+os.environ['GITHUB_RUN_ID']+'.tmp')
 with temp.open('xb') as stream:stream.write(encoded);stream.flush();os.fsync(stream.fileno())
 if config.read_bytes()!=raw:raise RuntimeError('Config changed while preparing update; original retained')
 os.replace(temp,config)
 report={'state':'EXISTING_SKARVIK_STARTUP_ROUTE_APPLIED_NOT_PLAYTESTED','project':str(ROOT),'previousDefaultMap':current,'mainMap':MAP,'mapSHA256':KNOWN_SHA,'originalMapModified':False,'configBackup':str(backup),'configSHA256':hashlib.sha256(config.read_bytes()).hexdigest(),'gameplayVerified':False}
 (out/'main-map-routing.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report),flush=True)
if __name__=='__main__':main()
