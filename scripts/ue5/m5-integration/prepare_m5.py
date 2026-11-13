"""Verify every source before copying; retain existing vehicle tuning and originals."""
import os,json,hashlib,shutil,gzip
from pathlib import Path
root=Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal');here=Path(__file__).parent;out=Path(os.environ['SCENE_REPAIR_OUT']);out.mkdir(parents=True,exist_ok=True)
def sha(data):return hashlib.sha256(data).hexdigest()
def normalized(path):return path.read_bytes().replace(b'\r\n',b'\n')
previous=json.loads((here/'previous-native-hash.json').read_text())
sources=['AnomaliaChaosRoadVehicle.cpp','AnomaliaM5PresentationComponent.h','AnomaliaM5PresentationComponent.cpp']
for name in sources:
 target=root/'Source/AnomaliaPrimeval/Vehicles'/name;source=here/name
 if target.exists() and sha(normalized(target)) not in [previous.get(name),sha(normalized(source))]:raise RuntimeError('Modified native source preserved: '+str(target))
for name in sources:
 target=root/'Source/AnomaliaPrimeval/Vehicles'/name
 if target.exists():backup=out/'SourceBackup'/name;backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup)
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(here/name,target)
assets=here/'assets';engine=json.loads((assets/'engine-manifest.json').read_text());audio=json.loads((assets/'audio-manifest.json').read_text())
outputs=[('E39M5S62_v1','engine_bay.glb',engine['sha256'])]+[('E39M5S62Audio_v1',p['file'],p['sha256']) for p in audio['sounds']]
for folder,name,expected in outputs:
 data=gzip.decompress((assets/(name+'.gz')).read_bytes())
 if sha(data)!=expected:raise RuntimeError('Asset checksum mismatch: '+name)
 target=root/'SourceAssets'/folder/name
 if target.exists() and sha(target.read_bytes())!=expected:raise RuntimeError('Modified source asset preserved: '+str(target))
 target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():target.write_bytes(data)
for folder,data in [('E39M5S62_v1',engine),('E39M5S62Audio_v1',audio)]:
 target=root/'SourceAssets'/folder/'manifest.json'
 if target.exists() and json.loads(target.read_text(encoding='utf-8-sig'))!=data:raise RuntimeError('Modified source manifest preserved: '+str(target))
 if not target.exists():target.write_text(json.dumps(data,indent=2),encoding='utf-8')
config=root/'Config/DefaultGame.ini';backup=out/'DefaultGame.ini.before';shutil.copy2(config,backup)
text=config.read_text(encoding='utf-8-sig');add=[]
for directory in ['/Game/Anomalia/E39M5S62_v1','/Game/Anomalia/E39M5S62Audio_v1']:
 if directory not in text:add.append('+DirectoriesToAlwaysCook=(Path="'+directory+'")')
if 'DirectoriesToAlwaysStageAsNonUFS=(Path="ThirdPartyNotices")' not in text:add.append('+DirectoriesToAlwaysStageAsNonUFS=(Path="ThirdPartyNotices")')
if add:config.write_text(text+'\n[/Script/UnrealEd.ProjectPackagingSettings]\n'+'\n'.join(add)+'\n',encoding='utf-8')
notices=root/'Content/ThirdPartyNotices';notices.mkdir(parents=True,exist_ok=True);notice=notices/'BMW_E39_M5_Audio.txt'
credit='BMW M5 E39 engine and exhaust recording — AfricaAuddyTech\nSource: '+audio['originalVideo']+'\nCommons: '+audio['source']+'\nLicense: CC BY 3.0 — '+audio['licenseURL']+'\nChanges: '+audio['changes']+'\nNo endorsement by the author or BMW is implied.\n'
if notice.exists() and notice.read_text(encoding='utf-8')!=credit:raise RuntimeError('Existing attribution notice preserved')
notice.write_text(credit,encoding='utf-8')
(out/'m5-source-prepared.json').write_text(json.dumps({'state':'M5_NATIVE_AUDIO_AND_V8_PREPARED_NOT_INSTALLED','files':sources,'assetHashes':outputs,'sourceRecording':audio},indent=2))
print('M5_NATIVE_AUDIO_AND_V8_PREPARED_NOT_INSTALLED')
