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
if current!=new and hashlib.sha256(current.encode()).hexdigest() not in ('8244ae65b368448c7c46b292238bb55da723fdc15efa481a2baefd94d3458ac8','ece51bd51f55bc015e804b53b0915321bcc4189559bd2751e704f6b936efd73d'):
 raise RuntimeError('Installed terrain header differs; preserve local work and defer merge')
cpp=target/'World'/(prefix+'WorldImportLibrary.cpp')
text=cpp.read_text(encoding='utf-8-sig')
anchor='  if(MapIdentifier==TEXT("DRAKHEIM"))return EWorld::Drakheim;'
for ident,kind in [('YUDINAVIA','Yudinavia'),('MOSCOVIE','Moscovie'),('CORSIVIA','Corsivia'),('BOT_SEVER','BotSever')]:
 if ('EWorld::'+kind) not in text:
  if text.count(anchor)!=1:raise RuntimeError('Installed terrain resolver differs')
  text=text.replace(anchor,anchor+'\n  if(MapIdentifier==TEXT("'+ident+'"))return EWorld::'+kind+';')

old='const int32 Expected=(Size==3025?576:256);'
updated='const int32 Expected=((Size-1)/126)*((Size-1)/126);'
if old in text:text=text.replace(old,updated)
elif updated not in text:raise RuntimeError('Installed component validator differs')
browser=target/(prefix+'ServerBrowserLibrary.cpp')
browsertext=browser.read_text(encoding='utf-8-sig')
anchor='{TEXT("deadroot-v1"), TEXT("DEADROOT"), TEXT("/Game/Maps/PRIGIMALIA_DEADROOT")}'
for ident,title,mid in [('YUDINAVIA','YUDINAVIA','yudinavia-v1'),('MOSCOVIE','MOSCOVIE','moscovie-v1'),('CORSIVIA','CORSIVIA','corsivia-v1'),('BOT_SEVER','БОТ СЕВЕР','bot-sever-v1')]:
 if ('TEXT("'+mid+'")') not in browsertext:
  if browsertext.count(anchor)!=1:raise RuntimeError('Installed browser differs')
  browsertext=browsertext.replace(anchor,anchor+',\n        {TEXT("'+mid+'"), TEXT("'+title+'"), TEXT("/Game/Maps/PRIGIMALIA_'+ident+'")}')

catalog=root/'Config/Anomalia/map-catalog.json'
cli=root/'Saved/MapIntegration/anomalia-editor-tools.py'
plan=[(header,local(new)+'\n'),(cpp,text),(browser,browsertext),
      (root/'Config/Anomalia/locality-names.json',(repo/'public/config/anomalia-locality-names.json').read_text(encoding='utf-8')),
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
