"""Reuse the successful actual-project build and reclaim only its regenerable compiler intermediates."""
from pathlib import Path
import os,json,hashlib,shutil
ROOT=Path('D:/ANOMALIA/unreal').resolve()
PRIOR=ROOT/'Saved/ThreeRequestedMaps/42487952988'
OUT=Path(os.environ['THREE_MAP_OUT'])
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run():
 if not (PRIOR/'compiled.marker').is_file():raise RuntimeError('Successful prior compile marker missing')
 receipt=json.loads((PRIOR/'source-install.json').read_text(encoding='utf-8-sig'))
 module=receipt['module']
 if module not in ('AnomaliaPrimeval','AnomaliaZPrigimalia'):raise RuntimeError('Unexpected module')
 rows=json.loads((PRIOR/'source-backups.json').read_text(encoding='utf-8-sig'))
 for row in rows:
  p=Path(row['path'])
  if not p.resolve().is_relative_to(ROOT):raise RuntimeError('Receipt outside actual project')
  if not row.get('sha256'):raise RuntimeError('Missing additive source fingerprint')
  content=p.read_text(encoding='utf-8-sig')
  if hashlib.sha256(content.encode('utf-8')).hexdigest()!=row['sha256']:raise RuntimeError('Installed source changed since successful compile: '+str(p))
 dll=ROOT/'Binaries/Win64'/('UnrealEditor-'+module+'.dll')
 if not dll.is_file():raise RuntimeError('Compiled module missing')
 result={'state':'SUCCESSFUL_BUILD_REUSED_NOT_GAMEPLAY_ACCEPTANCE','module':module,'binary':str(dll),'binarySHA256':digest(dll),'priorRun':42487952988,'removedFiles':[],'logicalBytesRemoved':0,'freeBefore':shutil.disk_usage(ROOT).free}
 intermediate=ROOT/'Intermediate/Build'
 if intermediate.exists() and (intermediate.is_symlink() or not intermediate.resolve().is_relative_to(ROOT)):raise RuntimeError('Intermediate path is redirected')
 if intermediate.is_dir():
  for p in intermediate.rglob('*'):
   if p.suffix.lower() not in ('.pch','.obj','.ipch') or not p.is_file() or p.is_symlink():continue
   if not p.resolve().is_relative_to(intermediate.resolve()):continue
   size=p.stat().st_size
   # Journal the exact regenerable file before deleting; no Content/Source/Binaries/saves.
   (OUT/'intermediate-cleanup-journal.jsonl').open('a',encoding='utf-8').write(json.dumps({'path':str(p),'bytes':size})+'\n')
   p.unlink();result['removedFiles'].append(str(p));result['logicalBytesRemoved']+=size
 result['freeAfter']=shutil.disk_usage(ROOT).free
 result['actualFreeDelta']=result['freeAfter']-result['freeBefore']
 (OUT/'compiled-build-reuse.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 if result['freeAfter']<10*1024**3:raise RuntimeError('Still below landscape disk reserve; originals preserved')
 print(json.dumps(result),flush=True)
if __name__=='__main__':run()
