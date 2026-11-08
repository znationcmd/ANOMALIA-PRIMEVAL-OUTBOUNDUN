"""Run only the installed main map in rendered DX11/SM5 and protect existing save/map packages."""
import pathlib,json,os,sys,time,subprocess,hashlib,shutil,re
ROOT=pathlib.Path(r'D:\ANOMALIA\unreal')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 return h.hexdigest()
def main():
 out=pathlib.Path(os.environ['MAIN_MAP_OUT']);pre=json.loads((out/'main-map-preflight.json').read_text(encoding='utf-8'))
 assert pre['project']==str(ROOT)
 profile='mainmap-'+os.environ['GITHUB_RUN_ID'];os.environ['MAIN_MAP_TEST_PROFILE']=profile
 backups=out/'SaveBackups';old={}
 save_bytes=sum(p.stat().st_size for name in ['Servers','SaveGames'] for p in (ROOT/'Saved'/name).rglob('*') if p.is_file())
 if shutil.disk_usage(out).free<save_bytes+8*1024**3:raise RuntimeError('Insufficient measured space for save protection and disk reserve')
 for name in ['Servers','SaveGames']:
  folder=ROOT/'Saved'/name
  if folder.is_dir():
   for p in folder.rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(ROOT/'Saved');target=backups/rel;target.parent.mkdir(parents=True,exist_ok=True)
    old[str(rel)]=sha(p);shutil.copy2(p,target)
 (out/'protected-save-files.json').write_text(json.dumps(old,indent=2),encoding='utf-8')
 editor=pathlib.Path(r'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe')
 script=pathlib.Path(sys.argv[1]);assert script.is_file() and editor.is_file()
 command=[str(editor),str(ROOT/'AnomaliaPrimeval.uproject'),pre['mainMap'],'-dx11','-sm5','-windowed','-resx=1280','-resy=720','-unattended','-nosound','-nosplash','-ExecutePythonScript='+str(script),'-abslog='+str(out/'main-map-sm5-engine.log')]
 if pre.get('scopeOption'):command.append('-'+pre['scopeOption']+profile)
 result={'mainMap':pre['mainMap'],'otherMapsTested':False,'requestedRHI':'D3D11','requestedShaderModel':'SM5','nullRHI':False,'saveChanges':[],'mapChanges':[],'SM5RendererObserved':False,'allCityBuildingsValidated':False}
 with (out/'main-map-sm5-process.log').open('wb') as log:
  child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
  try:child.wait(timeout=65*60)
  except subprocess.TimeoutExpired:
   subprocess.run(['taskkill.exe','/PID',str(child.pid),'/T','/F'],capture_output=True);child.wait(timeout=60);result['timeout']=True
 result['editorExitCode']=child.returncode
 native=out/'main-map-city-sm5.json';doc=json.loads(native.read_text(encoding='utf-8')) if native.is_file() else {'errors':['Native main-map report absent']}
 result['native']=doc
 # The original saves and main map must survive testing. Keep unexpected test writes as evidence.
 for relative,expected in old.items():
  p=ROOT/'Saved'/relative
  if not p.is_file() or sha(p)!=expected:
   result['saveChanges'].append(relative)
   if p.is_file():
    retained=out/'UnexpectedSaveWrites'/relative;retained.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,retained)
   p.parent.mkdir(parents=True,exist_ok=True);temp=p.with_suffix(p.suffix+'.validation-restore');shutil.copy2(backups/relative,temp);os.replace(temp,p)
 result['unexpectedNewSaveFiles']=[]
 for name in ['Servers','SaveGames']:
  folder=ROOT/'Saved'/name
  for p in list(folder.rglob('*')):
   if not p.is_file():continue
   relative=p.relative_to(ROOT/'Saved')
   if str(relative) in old or relative.parts[:2]==('Servers',profile):continue
   retained=out/'UnexpectedNewSaveFiles'/relative;retained.parent.mkdir(parents=True,exist_ok=True)
   if retained.exists():raise RuntimeError('Existing unexpected-save evidence preserved')
   os.rename(p,retained);result['unexpectedNewSaveFiles'].append(str(relative))
 for row in json.loads((out/'protected-main-map-packages.json').read_text(encoding='utf-8'))+[{'path':pre['mapFile'],'sha256':pre['mapSHA256']},{'path':str(ROOT/'Config/DefaultEngine.ini'),'sha256':pre['engineConfigSHA256']}]:
  p=pathlib.Path(row['path'])
  if not p.is_file() or sha(p)!=row['sha256']:result['mapChanges'].append(str(p))
 log=(out/'main-map-sm5-engine.log').read_text(encoding='utf-8',errors='replace') if (out/'main-map-sm5-engine.log').is_file() else ''
 result['SM5RendererObserved']=bool(re.search(r'LogD3D11RHI:|RHI Selected:\s*D3D11|Using.*RHI.*D3D11',log,re.I)) and '-sm5' in command
 result['shaderAndMaterialErrors']=[l for l in log.splitlines() if re.search(r'(failed to compile.*material|shader.*fatal|LogShaderCompilers:\s*Error|LogMaterial:\s*Error)',l,re.I)][:300]
 result['missingPackageErrors']=[l for l in log.splitlines() if re.search(r'(can.t find file|failed to load.*package|failed to find object)',l,re.I)][:300]
 result['allMainMapPackagesUnchanged']=not result['mapChanges'];result['existingSavesUnchanged']=not result['saveChanges'] and not result['unexpectedNewSaveFiles']
 result['PIEScreenshotPresent']=(out/'main-map-pie.png').is_file()
 result['installedCityStructurePassed']=bool(doc.get('cityCandidates') and doc.get('cityActorsInspected')==doc.get('cityCandidates') and doc.get('components') and all(c.get('fallbackGeometryPresent') for c in doc.get('components',[])) and not doc.get('materialProblems'))
 result['mainMapPIESmokePassed']=bool(child.returncode==0 and doc.get('PIEPassed') and result['PIEScreenshotPresent'] and result['SM5RendererObserved'] and not result['shaderAndMaterialErrors'] and not result['missingPackageErrors'] and result['existingSavesUnchanged'] and not result['mapChanges'])
 (out/'main-map-sm5-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps({k:result[k] for k in ['mainMap','editorExitCode','SM5RendererObserved','mainMapPIESmokePassed','existingSavesUnchanged','allMainMapPackagesUnchanged']}),flush=True)
 if child.returncode or doc.get('errors') or not result['mainMapPIESmokePassed'] or not result['installedCityStructurePassed']:return 1
 return 0
if __name__=='__main__':sys.exit(main())
