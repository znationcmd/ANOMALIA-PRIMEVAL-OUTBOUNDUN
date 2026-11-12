"""Back up verified principal source, then install optional E39 presentation and city batching."""
import hashlib,json,os,shutil,gzip
from pathlib import Path
root=Path(r'D:\ANOMALIAZ\01_Projet_Principal\unreal');out=Path(os.environ['SCENE_REPAIR_OUT']);here=Path(__file__).parent
r={'state':'FAILED','source':[]}
for stem,folder in [('AnomaliaChaosRoadVehicle','Vehicles'),('AnomaliaCityBlock','World'),('AnomaliaAuthenticGameProbe','')]:
 for suffix in ['.h','.cpp']:
  rel=Path('Source/AnomaliaPrimeval')/folder/(stem+suffix);p=root/rel
  if p.exists():
   dest=out/'SourceBackup'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
   if stem!='AnomaliaCityBlock':
    expected=json.loads((here/'source-base-hashes.json').read_text())[stem+suffix]
    current=hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    target=hashlib.sha256((here/(stem+suffix)).read_bytes()).hexdigest()
    if current not in [expected,target]:raise RuntimeError('Principal source changed since audit: '+str(p))
  p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(here/(stem+suffix),p);r['source'].append(str(rel))
asset=root/'SourceAssets/E39EngineBay_v1';asset.mkdir(parents=True,exist_ok=True)
manifest=json.loads((here/'assets/engine-bay-manifest.json').read_text());data=gzip.decompress((here/'assets/engine_bay.glb.gz').read_bytes())
if hashlib.sha256(data).hexdigest()!=manifest['sha256']:raise RuntimeError('Engine asset integrity mismatch')
(asset/'engine_bay.glb').write_bytes(data);(asset/'manifest.json').write_text(json.dumps(manifest,indent=2))
r['state']='NATIVE_SOURCE_PREPARED_NOT_VISUALLY_ACCEPTED';(out/'native-source.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
