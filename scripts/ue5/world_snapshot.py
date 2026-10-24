"""Immutable snapshots of this world's packages only. Never includes player saves."""
import hashlib,json,uuid,zipfile
from pathlib import Path

WORLD_PATHS=('Content/Maps/ANOMALIA_Archipelago_v2.umap',
 'Content/__ExternalActors__/Maps/ANOMALIA_Archipelago_v2',
 'Content/__ExternalObjects__/Maps/ANOMALIA_Archipelago_v2',
 'Content/Anomalia/World/Archipelago_v2')

def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
 return h.hexdigest()

INHABITED_PATHS=('Content/Maps/ANOMALIA_Inhabited_v2.umap',
 'Content/__ExternalActors__/Maps/ANOMALIA_Inhabited_v2',
 'Content/__ExternalObjects__/Maps/ANOMALIA_Inhabited_v2',
 'Content/Anomalia/Inhabited_v2')

def snapshot(project,output,world_paths=WORLD_PATHS):
 project=Path(project).resolve();output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
 if world_paths not in (WORLD_PATHS,INHABITED_PATHS):raise ValueError('Only known world packages may be backed up')
 if not (project/world_paths[0]).is_file():raise RuntimeError('Existing map required; no replacement or generation')
 files=[]
 for name in world_paths:
  p=project/name
  candidates=[p] if p.is_file() else sorted(p.rglob('*')) if p.is_dir() else []
  for f in candidates:
   if f.is_symlink():raise RuntimeError('Symlink in world packages: '+str(f))
   if f.is_file():files.append(f)
 records=[dict(path=f.relative_to(project).as_posix(),bytes=f.stat().st_size,sha256=sha256(f)) for f in files]
 archive=output/('world-before-render-'+uuid.uuid4().hex+'.zip')
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,allowZip64=True) as z:
  for f,record in zip(files,records):z.write(f,record['path'])
  z.writestr('snapshot-manifest.json',json.dumps(records,indent=2))
 with zipfile.ZipFile(archive) as z:
  if z.testzip():raise RuntimeError('Snapshot archive CRC verification failed')
  for record in records:
   if hashlib.sha256(z.read(record['path'])).hexdigest()!=record['sha256']:raise RuntimeError('Snapshot content checksum mismatch')
 return dict(archive=str(archive),sha256=sha256(archive),fileCount=len(records),files=records)
