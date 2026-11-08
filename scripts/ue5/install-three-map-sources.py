"""Narrow, recoverable source merge into the actual existing D project."""
import hashlib,json,os,shutil,re
from pathlib import Path

repo=Path(__file__).resolve().parents[2]
root=Path('D:/ANOMALIA/unreal').resolve()
out=Path(os.environ['THREE_MAP_OUT'])
module=json.loads((root/'AnomaliaPrimeval.uproject').read_text(encoding='utf-8-sig'))['Modules'][0]['Name']
if module not in ('AnomaliaPrimeval','AnomaliaZPrigimalia'):raise RuntimeError('Unknown actual module')
def canonical(s):return re.sub(r'Anomalia(?!ZPrigimalia)', 'AnomaliaZPrigimalia', s.replace('AnomaliaPrimeval','AnomaliaZPrigimalia')).replace('ANOMALIAPRIMEVAL','ANOMALIAZPRIGIMALIA').strip()
def local(s):return s.replace('AnomaliaZPrigimalia',prefix).replace('ANOMALIAZPRIGIMALIA',module.upper())
target=root/'Source'/module
source=repo/'unreal/Source/AnomaliaZPrigimalia'
headers=list((target/'World').glob('*ExtraWorldHeights.h'))
if len(headers)!=1:raise RuntimeError('Unique installed terrain header required')
header=headers[0]
prefix=header.stem.removesuffix('ExtraWorldHeights')
current=canonical(header.read_text(encoding='utf-8-sig'))
new=(source/'World/AnomaliaZPrigimaliaExtraWorldHeights.h').read_text().strip()
if current!=new and hashlib.sha256(current.encode()).hexdigest()!='8244ae65b368448c7c46b292238bb55da723fdc15efa481a2baefd94d3458ac8':
 raise RuntimeError('Installed terrain header differs; preserve local work and defer merge')
cpp=target/'World'/(prefix+'WorldImportLibrary.cpp')
text=cpp.read_text(encoding='utf-8-sig')
anchor='  if(MapIdentifier==TEXT("DRAKHEIM"))return EWorld::Drakheim;'
extra='\n  if(MapIdentifier==TEXT("YUDINAVIA"))return EWorld::Yudinavia;\n  if(MapIdentifier==TEXT("MOSCOVIE"))return EWorld::Moscovie;\n  if(MapIdentifier==TEXT("CORSIVIA"))return EWorld::Corsivia;'
if 'EWorld::Yudinavia' not in text:
 if text.count(anchor)!=1:raise RuntimeError('Installed terrain resolver differs; no broad source replacement')
 text=text.replace(anchor,anchor+extra)
old='const int32 Expected=(Size==3025?576:256);'
updated='const int32 Expected=((Size-1)/126)*((Size-1)/126);'
if old in text:text=text.replace(old,updated)
elif updated not in text:raise RuntimeError('Installed component validator differs')
browser=target/(prefix+'ServerBrowserLibrary.cpp')
browsertext=browser.read_text(encoding='utf-8-sig')
anchor='{TEXT("deadroot-v1"), TEXT("DEADROOT"), TEXT("/Game/Maps/PRIGIMALIA_DEADROOT")}'
extra=',\n'+',\n'.join('        {TEXT("'+n.lower()+'-v1"), TEXT("'+n+'"), TEXT("/Game/Maps/PRIGIMALIA_'+n+'")}' for n in ('YUDINAVIA','MOSCOVIE','CORSIVIA'))
if 'TEXT("yudinavia-v1")' not in browsertext:
 if browsertext.count(anchor)!=1:raise RuntimeError('Installed browser differs; no broad replacement')
 browsertext=browsertext.replace(anchor,anchor+extra)
catalog=root/'Config/Anomalia/map-catalog.json'
cli=root/'Saved/MapIntegration/anomalia-editor-tools.py'
plan=[(header,local(new)+'\n'),(cpp,text),(browser,browsertext),
      (catalog,(repo/'public/config/anomalia-map-catalog.json').read_text(encoding='utf-8')),
      (cli,(repo/'scripts/ue5/anomalia-editor-tools.py').read_text(encoding='utf-8'))]
backup=out/'source-backup'
backup.mkdir(parents=True,exist_ok=False)
receipt=[]
for path,content in plan:
 rel=path.relative_to(root);prior=backup/rel
 if path.exists():
  prior.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,prior)
 receipt.append({'path':str(path),'backup':str(prior) if prior.exists() else None})
(out/'source-backups.json').write_text(json.dumps(receipt,indent=2))
for path,content in plan:
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8')
(out/'source-install.json').write_text(json.dumps({'module':module,'state':'SOURCES_INSTALLED_COMPILATION_PENDING','files':[str(p) for p,_ in plan]},indent=2))
