"""Resolve SKARVIK from the installed game's actual routing; never select a staging map."""
import pathlib,os,re,json,hashlib,shutil
PROJECT=pathlib.Path(r'D:\ANOMALIA\unreal')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def value(text,section,key):
 current='';result=None
 for line in text.splitlines():
  line=line.strip()
  if line.startswith('[') and line.endswith(']'):current=line[1:-1]
  elif current==section and '=' in line and not line.startswith((';','#')):
   name,v=line.split('=',1)
   if name.strip()==key:result=v.strip()
 return result
def select_main(engine,source):
 boot=value(engine,'/Script/EngineSettings.GameMapsSettings','GameDefaultMap')
 # Map IDs can change during migration; use the explicit installed SKARVIK title.
 rows=re.findall(r'TEXT\s*\(\s*"([^"]*)"\s*\)\s*,\s*TEXT\s*\(\s*"([^"]*)"\s*\)\s*,\s*TEXT\s*\(\s*"(/Game/[^"]+)"\s*\)',source)
 routes={package for ident,title,package in rows if title.strip().upper()=='SKARVIK'}
 if len(routes)>1:raise ValueError('Multiple installed SKARVIK routes; refuse an arbitrary map')
 routed=next(iter(routes),None)
 if boot and ('SKARVIK' in boot.upper() or 'ARCHIPELAGO' in boot.upper()):selected=boot;basis='INSTALLED_GAME_DEFAULT_SKARVIK_MAP'
 elif routed:selected=routed;basis='INSTALLED_NATIVE_SKARVIK_WORLD_CHOICE'
 else:raise ValueError('Installed main SKARVIK route is unresolved; do not test a replacement map')
 if not selected.startswith('/Game/') or '..' in selected:raise ValueError('Unsafe main map route')
 return {'mainMap':selected,'basis':basis,'gameDefaultMap':boot,'nativeSkarvikRoute':routed,'bootRouteMismatch':bool(boot and boot!=selected)}
def isolated_scope(code,main_map):
 scope=re.search(r'FParse::Value\(FCommandLine::Get\(\),\s*TEXT\("([^"]*AutomationServerId=)"\)',code)
 if not scope:return None,False
 guard=code[max(0,scope.start()-900):scope.start()]
 # This validator requests normal Editor PIE, not an Automation RunTests session.
 if 'GIsAutomationTesting' in guard:return scope.group(1),False
 restricted=re.findall(r'MapName\.EndsWith\(TEXT\("([^"]+)"\)\)',guard)
 if restricted and not any(main_map.endswith(name) for name in restricted):return scope.group(1),False
 return scope.group(1),True
def main():
 out=pathlib.Path(os.environ['MAIN_MAP_OUT']);out.mkdir(parents=True,exist_ok=True)
 assert (PROJECT/'AnomaliaPrimeval.uproject').is_file(),'Actual D project unavailable'
 engine_path=PROJECT/'Config/DefaultEngine.ini';engine=engine_path.read_text(encoding='utf-8-sig')
 browser=PROJECT/'Source/AnomaliaPrimeval/AnomaliaServerBrowserLibrary.cpp'
 if not browser.is_file():raise ValueError('Installed native map routing source unavailable; preserve project')
 source=browser.read_text(encoding='utf-8-sig')
 try:
  route=select_main(engine,source)
 except ValueError as exc:
  evidence={'error':str(exc),'project':str(PROJECT),'gameDefaultMap':value(engine,'/Script/EngineSettings.GameMapsSettings','GameDefaultMap'),'installedRoutingLines':[line for line in source.splitlines() if any(word in line.upper() for word in ['SKARVIK','ARCHIPELAGO','/GAME/MAPS/'])]}
  (out/'main-map-preflight.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
  raise
 file=PROJECT/'Content'/(route['mainMap'][len('/Game/'):]+'.umap')
 if not file.is_file():raise ValueError('Configured main map is absent: '+str(file))
 mode=PROJECT/'Source/AnomaliaPrimeval/AnomaliaGameMode.cpp'
 code=mode.read_text(encoding='utf-8-sig') if mode.is_file() else ''
 scope_option,scope_allowed=isolated_scope(code,route['mainMap'])
 report={**route,'project':str(PROJECT),'readOnly':True,'mapFile':str(file),'mapSHA256':sha(file),'engineConfigSHA256':sha(engine_path),'scopeOption':scope_option,'PIEAllowedWithIsolatedProfile':scope_allowed,'advancedFinalExistsWithoutBeingOpened':(PROJECT/'Content/Maps/PRIGIMALIA_SKARVIK_FINAL_v1.umap').is_file(),'persistentSM5TargetConfigured':'PCD3D_SM5' in engine,'persistentDefaultRHI':value(engine,'/Script/WindowsTargetPlatform.WindowsTargetSettings','DefaultGraphicsRHI'),'rendererSettings':{k:value(engine,'/Script/Engine.RendererSettings',k) for k in ['r.Nanite.ProjectEnabled','r.DynamicGlobalIlluminationMethod','r.ReflectionMethod','r.Shadow.Virtual.Enable']},'freeBytes':{d:shutil.disk_usage(d+':/').free for d in ['C','D']}}
 protected=[]
 for kind in ['__ExternalActors__','__ExternalObjects__']:
  directory=PROJECT/'Content'/kind/route['mainMap'][len('/Game/'):]
  if directory.is_dir():
   for f in directory.rglob('*.uasset'):protected.append({'path':str(f),'bytes':f.stat().st_size,'sha256':sha(f)})
 (out/'protected-main-map-packages.json').write_text(json.dumps(protected),encoding='utf-8')
 (out/'main-map-preflight.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report),flush=True)
if __name__=='__main__':main()
