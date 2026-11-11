"""Install additive requested-world code when the old project has no extra-world helper."""
import hashlib,json,os,re,shutil
from pathlib import Path
repo=Path(__file__).resolve().parents[2]
root=Path('D:/ANOMALIA/unreal').resolve()
out=Path(os.environ['THREE_MAP_OUT'])
module=json.loads((root/'AnomaliaPrimeval.uproject').read_text(encoding='utf-8-sig'))['Modules'][0]['Name']
if module not in ('AnomaliaPrimeval','AnomaliaZPrigimalia'):raise RuntimeError('Unknown actual module')
target=root/'Source'/module
source=repo/'unreal/Source/AnomaliaZPrigimalia'
def translate(s):return s.replace('AnomaliaZPrigimalia',module).replace('ANOMALIAZPRIGIMALIA',module.upper())
plan=[]
for suffix in ('h','cpp'):
 p=target/'World'/(module+'RequestedWorldLibrary.'+suffix)
 content=translate((source/'World'/('AnomaliaZPrigimaliaRequestedWorldLibrary.'+suffix)).read_text(encoding='utf-8'))
 if p.exists() and p.read_text(encoding='utf-8-sig').strip()!=content.strip():raise RuntimeError('Existing requested-world source differs: '+str(p))
 plan.append((p,content))
p=target/'World'/(module+'RequestedWorldHeights.h')
content=translate((source/'World/AnomaliaZPrigimaliaExtraWorldHeights.h').read_text(encoding='utf-8'))
if p.exists() and p.read_text(encoding='utf-8-sig').strip()!=content.strip():raise RuntimeError('Existing requested-world height source differs')
plan.append((p,content))
build=target/(module+'.Build.cs')
code=build.read_text(encoding='utf-8-sig')
missing=[name for name in ('UnrealEd','Landscape') if ('"'+name+'"') not in code]
if missing:
 # Edit only a conventional ModuleRules constructor footer; preserve all original statements.
 match=re.search(r'(?P<footer>\n[ \t]*}\s*\n}\s*)$',code)
 if not match:raise RuntimeError('Build.cs constructor footer requires review')
 addition='\n        if (Target.bBuildEditor) { PrivateDependencyModuleNames.AddRange(new string[] { '+', '.join('"'+x+'"' for x in missing)+' }); }'
 code=code[:match.start()]+addition+code[match.start():]
 plan.append((build,code))
for name in ('map-catalog','locality-names'):
 filename='anomalia-'+('map-catalog' if name=='map-catalog' else 'locality-names')+'.json'
 plan.append((root/'Config/Anomalia'/(name+'.json'),(repo/'public/config'/filename).read_text(encoding='utf-8')))
backup=out/'source-backup'
backup.mkdir(parents=True,exist_ok=False)
rows=[]
for path,content in plan:
 prior=backup/path.relative_to(root)
 if path.exists():
  prior.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,prior)
 rows.append({'path':str(path),'backup':str(prior) if prior.exists() else None,'sha256':hashlib.sha256(content.encode('utf-8')).hexdigest()})
(out/'source-backups.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
for path,content in plan:
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8')
(out/'source-install.json').write_text(json.dumps({'module':module,'state':'ADDITIVE_SOURCES_INSTALLED_COMPILATION_PENDING','existingMapOrCharacterSourcesModified':False,'nativeBrowserIntegrationPending':True,'files':[str(p) for p,_ in plan]},indent=2),encoding='utf-8')

