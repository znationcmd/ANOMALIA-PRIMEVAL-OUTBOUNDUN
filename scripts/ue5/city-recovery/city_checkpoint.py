"""Lossless actor checkpoints for original architectural extraction."""
import json,hashlib,os
from pathlib import Path
def write_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 temporary=path.with_name(path.name+'.tmp');temporary.write_text(json.dumps(value,separators=(',',':')),encoding='utf-8');os.replace(temporary,path)
def source_fingerprint(project):
 project=Path(project);world=project/'Content/Map/Big_City_LVL.umap'
 digest=hashlib.sha256(world.read_bytes())
 # Ordinary authored external-actor edits invalidate prior checkpoints.
 for relative in ['Content/__ExternalActors__/Map/Big_City_LVL','Content/__ExternalObjects__/Map/Big_City_LVL']:
  directory=project/relative
  if directory.exists():
   for p in sorted(directory.rglob('*')):
    if p.is_file():
     s=p.stat();digest.update(json.dumps([p.relative_to(project).as_posix(),s.st_size,s.st_mtime_ns]).encode())
 return digest.hexdigest()
def collapse(actors):
 rows={};count=0;output=[]
 for actor in actors.values():
  n=0
  for batch in actor['batches']:
   key=json.dumps([batch['mesh'],batch['materials'],batch['visible'],batch['collision']],separators=(',',':'))
   if key not in rows:rows[key]={k:v for k,v in batch.items() if k!='instances'};rows[key]['instances']=[]
   elif rows[key]['localMin']!=batch['localMin'] or rows[key]['localMax']!=batch['localMax']:raise ValueError('Shared mesh bounds changed during extraction')
   rows[key]['instances'].extend(batch['instances']);n+=len(batch['instances'])
  if n!=actor['instances']:raise ValueError('Incomplete architectural actor: '+actor['label'])
  count+=n;output.append({k:v for k,v in actor.items() if k!='batches'})
 return output,list(rows.values()),count
