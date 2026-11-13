"""Copy only missing, regenerated parts of the pinned licensed original car."""
import hashlib,json,shutil,sys
from pathlib import Path
source=Path(sys.argv[1])/'unreal/SourceAssets/BMWE39Review_v7';target=Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal\SourceAssets\BMWE39Review_v7')
manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8-sig'))
if manifest['source']['sha256']!='984a9daab49b5a31c45bbc284c657fa5898a010f2201c003358cb6b6f411751d':raise RuntimeError('Original BMW source identity mismatch')
if len(manifest['models'])!=11:raise RuntimeError('Original car is incomplete')
existing=json.loads((target/'manifest.json').read_text(encoding='utf-8-sig')) if (target/'manifest.json').exists() else None
if existing and {p['id']:p['sha256'] for p in existing['models']}!={p['id']:p['sha256'] for p in manifest['models']}:raise RuntimeError('Existing car manifest differs; preserve source')
files=[(source/p['file'],target/p['file'],p['sha256']) for p in manifest['models']]
for src,dst,expected in files:
 if hashlib.sha256(src.read_bytes()).hexdigest()!=expected:raise RuntimeError('Generated original part integrity mismatch')
 if dst.exists() and hashlib.sha256(dst.read_bytes()).hexdigest()!=expected:raise RuntimeError('Existing original artist file preserved: '+str(dst))
target.mkdir(parents=True,exist_ok=True)
for src,dst,_ in files:
 if not dst.exists():shutil.copy2(src,dst)
for name in ['manifest.json','CREDITS.md']:
 if not (target/name).exists():shutil.copy2(source/name,target/name)
out=Path(__import__('os').environ['SCENE_REPAIR_OUT']);(out/'original-car-restored.json').write_text(json.dumps({'state':'ELEVEN_PINNED_SOURCE_CAR_PARTS_RESTORED','sourceSHA256':manifest['source']['sha256'],'target':str(target),'models':manifest['models']},indent=2));print('ELEVEN_PINNED_SOURCE_CAR_PARTS_RESTORED')
