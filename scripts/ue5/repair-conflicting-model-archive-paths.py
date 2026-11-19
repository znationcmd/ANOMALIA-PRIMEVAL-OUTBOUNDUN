"""Extract conflicting owned ZIP entries losslessly and repair unambiguous glTF/OBJ dependencies.

Original ZIPs are never removed. Conflicting bytes are kept under separate content hashes.
Only dependency-complete prepared models enter the native import queue.
"""
import pathlib,hashlib,json,zipfile,os,posixpath,re,stat,struct,urllib.parse,shlex,shutil,time

def file_sha(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()

def safe_member(name):
    name=name.replace('\\','/')
    p=pathlib.PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or re.match(r'^[A-Za-z]:',name) or any(ord(c)<32 for c in name):
        raise ValueError('Unsafe archive traversal or absolute path retained in original')
    return str(p)

def write_owned(path,data):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data:raise ValueError('Different owned preparation preserved: '+str(path))
    else:
        with path.open('xb') as f:f.write(data)

class Repair:
    def __init__(self,source,target,reserve=8*1024**3):
        self.source=pathlib.Path(source);self.root=pathlib.Path(target)
        self.reserve=reserve;self.rows=[];self.by_name={};self.by_fold={};self.prepared_mtls={}
    def extract(self):
        original=file_sha(self.source);before=self.source.stat()
        self.root.mkdir(parents=True,exist_ok=True)
        if getattr(self.root.lstat(),'st_file_attributes',0)&0x400:raise ValueError('Output reparse point preserved')
        write_owned(self.root/'owner.json',json.dumps({'sourceSHA256':original,'version':1}).encode())
        with zipfile.ZipFile(self.source) as z:
            infos=[i for i in z.infolist() if not i.is_dir()]
            for i in infos:
                safe_member(i.filename)
                if i.flag_bits&1 or stat.S_IFMT(i.external_attr>>16)==stat.S_IFLNK:raise ValueError('Encrypted or linked member retained')
            if shutil.disk_usage(self.root).free<sum(i.file_size for i in infos)+self.reserve:
                raise ValueError('Insufficient measured disk reserve for full lossless extraction')
            by_hash={}
            for i in infos:
                name=safe_member(i.filename);temp=self.root/('member-'+str(i.header_offset)+'.partial')
                if temp.exists():raise ValueError('Interrupted temporary member preserved for review')
                h=hashlib.sha256()
                with z.open(i) as src,temp.open('xb') as dst:
                    for block in iter(lambda:src.read(4*1024**2),b''):h.update(block);dst.write(block)
                digest=h.hexdigest()
                base='src_'+re.sub(r'[^A-Za-z0-9._-]','_',pathlib.PurePosixPath(name).name)[-100:]
                dest=by_hash.get(digest,self.root/'Files'/digest[:2]/digest/base)
                if not dest.resolve().is_relative_to(self.root.resolve()):raise ValueError('Existing content path escapes owned output')
                dest.parent.mkdir(parents=True,exist_ok=True)
                if dest.exists():
                    if file_sha(dest)!=digest:raise ValueError('Existing extracted contents differ; preserved')
                    temp.unlink()
                else:os.rename(temp,dest)
                by_hash[digest]=dest
                row={'original':name,'headerOffset':i.header_offset,'sha256':digest,'path':str(dest),'bytes':i.file_size}
                self.rows.append(row);self.by_name.setdefault(name,[]).append(row);self.by_fold.setdefault(name.casefold(),[]).append(row)
        after=self.source.stat()
        if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns) or file_sha(self.source)!=original:
            raise ValueError('Original archive changed; no import accepted')
        write_owned(self.root/'extracted-members.json',json.dumps(self.rows,indent=2).encode())
        return original
    def resolve(self,owner,uri):
        # Resolve exact author casing before falling back to one unambiguous Windows name.
        if uri.startswith('data:'):return None
        if uri.lower().startswith(('http:','https:','ftp:','file:','//')):raise ValueError('External dependency is not an owned archive member')
        decoded=urllib.parse.unquote(uri.split('#',1)[0].split('?',1)[0]).replace('\\','/')
        name=posixpath.normpath(posixpath.join(posixpath.dirname(owner),decoded))
        if name.startswith('../') or name.startswith('/'):raise ValueError('Dependency escapes archive root')
        rows=self.by_name.get(name) or self.by_fold.get(name.casefold(),[])
        if not rows:raise ValueError('Missing dependency: '+name)
        if len({r['sha256'] for r in rows})!=1:raise ValueError('Ambiguous dependency has different contents: '+name)
        return rows[0]
    def relative(self,path,dest):return pathlib.Path(os.path.relpath(path,pathlib.Path(dest).parent)).as_posix()
    def rewrite_gltf(self,row,dest):
        if not pathlib.Path(dest).resolve().is_relative_to(self.root.resolve()):raise ValueError('Prepared path escapes owned output')
        source=pathlib.Path(row['path']);blob=source.read_bytes();binary=source.suffix.casefold()=='.glb'
        chunks=[]
        if binary:
            if len(blob)<20 or struct.unpack_from('<III',blob)!=(0x46546c67,2,len(blob)):raise ValueError('Invalid GLB header')
            offset=12
            while offset<len(blob):
                size,kind=struct.unpack_from('<II',blob,offset);chunks.append((kind,blob[offset+8:offset+8+size]));offset+=8+size
            if offset!=len(blob) or not chunks or chunks[0][0]!=0x4e4f534a:raise ValueError('Invalid GLB chunks')
            data=json.loads(chunks[0][1])
        else:data=json.loads(blob.decode('utf-8-sig'))
        for key in ('images','buffers'):
            for item in data.get(key,[]):
                if 'uri' in item:
                    dep=self.resolve(row['original'],item['uri'])
                    if dep:item['uri']=urllib.parse.quote(self.relative(dep['path'],dest),safe='/._-')
        encoded=json.dumps(data,separators=(',',':'),ensure_ascii=False).encode('utf-8')
        if binary:
            encoded+=b' '*((-len(encoded))%4)
            body=b''.join(struct.pack('<II',len(v),k)+v for k,v in [(0x4e4f534a,encoded)]+chunks[1:])
            encoded=struct.pack('<III',0x46546c67,2,len(body)+12)+body
        write_owned(dest,encoded)
    def rewrite_mtl(self,row):
        if row['sha256'] in self.prepared_mtls:return self.prepared_mtls[row['sha256']]
        dest=self.root/'PreparedMaterials'/(row['sha256']+'.mtl');lines=[]
        if not dest.resolve().is_relative_to(self.root.resolve()):raise ValueError('Material path escapes owned output')
        for line in pathlib.Path(row['path']).read_text(encoding='utf-8-sig').splitlines():
            split=line.strip().split(None,1)
            if len(split)==2 and (split[0].casefold().startswith('map_') or split[0].casefold() in {'bump','disp','decal','norm','refl'}):
                tokens=shlex.split(split[1].replace('\\','/'));found=False
                for i in range(len(tokens)):
                    try:dep=self.resolve(row['original'],' '.join(tokens[i:]))
                    except ValueError:continue
                    if dep:
                        line=split[0]+' '+' '.join(tokens[:i]+[self.relative(dep['path'],dest)]);found=True;break
                if not found:raise ValueError('Unresolved OBJ material texture: '+line)
            lines.append(line)
        write_owned(dest,('\n'.join(lines)+'\n').encode());self.prepared_mtls[row['sha256']]=dest;return dest
    def rewrite_obj(self,row,dest):
        if not pathlib.Path(dest).resolve().is_relative_to(self.root.resolve()):raise ValueError('OBJ path escapes owned output')
        lines=[]
        for line in pathlib.Path(row['path']).read_text(encoding='utf-8-sig').splitlines():
            split=line.strip().split(None,1)
            if len(split)==2 and split[0].casefold()=='mtllib':
                try:deps=[self.resolve(row['original'],split[1].strip().strip('"'))]
                except ValueError:deps=[self.resolve(row['original'],s) for s in shlex.split(split[1].replace('\\','/'))]
                line='mtllib '+' '.join(self.relative(self.rewrite_mtl(d),dest) for d in deps)
            lines.append(line)
        write_owned(dest,('\n'.join(lines)+'\n').encode())
    def models(self):
        accepted=[];deferred=[];seen=set()
        for row in self.rows:
            suffix=pathlib.Path(row['path']).suffix.casefold()
            if suffix not in {'.glb','.gltf','.obj','.fbx','.blend','.dae','.stl','.usd','.usdz','.3ds','.abc','.uasset','.umap'}:continue
            if row['sha256'] in seen:continue
            seen.add(row['sha256']);dest=self.root/'PreparedModels'/(row['sha256']+suffix)
            try:
                if suffix in {'.glb','.gltf'}:self.rewrite_gltf(row,dest)
                elif suffix=='.obj':self.rewrite_obj(row,dest)
                else:raise ValueError('Extracted losslessly; format/material reference review required before native import')
                accepted.append({**row,'prepared':str(dest),'preparedSHA256':file_sha(dest)})
            except Exception as exc:deferred.append({**row,'reason':str(exc)})
        return accepted,deferred

def main():
    project=pathlib.Path(r'D:\ANOMALIA\unreal');state=project/'Saved/ImportReceipts/AllResources20261107'
    raw_path=project/'Saved/ImportReceipts/RawResume20261107/raw-preparation-manifest.json'
    out=pathlib.Path(os.environ['PATH_REPAIR_OUT']);out.mkdir(parents=True,exist_ok=True)
    prior=json.loads((state/'summary.json').read_text(encoding='utf-8'))
    sources={r['archive'] for r in prior.get('blocked',[]) if r.get('archive','').lower().endswith('.zip')}
    known=set()
    for line in (state/'archive-receipts.jsonl').open(encoding='utf-8'):
        row=json.loads(line)
        if row.get('state')=='VERIFIED_EXTRACTED':known.add(row['archiveSHA256'])
    # Recover former temporary Fab archives only from matching owned inventory paths.
    missing={s for s in sources if not pathlib.Path(s).is_file() and not pathlib.Path(s+'.extracted.json').exists()}
    plan=project/'Saved/CloudTransfer/Direct20261106/direct-source-plan.jsonl';alternates={}
    if missing and plan.is_file():
        for line in plan.open(encoding='utf-8'):
            p=pathlib.Path(json.loads(line)['path'])
            if p.suffix.casefold()!='.zip':continue
            for original in missing:
                old=pathlib.Path(original);uid=re.search(r'[0-9a-f]{8}-[0-9a-f-]{27}',original,re.I)
                if p.name.casefold()==old.name.casefold() and (not old.name.casefold().startswith('fbx') or uid and uid.group().casefold() in str(p).casefold()) and p.is_file():alternates.setdefault(original,[]).append(p)
    report={'archivesRepaired':0,'newQueuedModels':0,'losslesslyExtractedModelsAwaitingFormatReview':0,'missing':[],'errors':[],'sources':[],'originalArchivesDeleted':0,'existingAssetsReplaced':0}
    start=time.monotonic()
    def checkpoint():
        report['freeBytes']={d:shutil.disk_usage(d+':/').free for d in ['C','D']}
        (out/'path-repair-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('MODEL_PATH_REPAIR '+json.dumps({k:report[k] for k in ['archivesRepaired','newQueuedModels','losslesslyExtractedModelsAwaitingFormatReview','freeBytes']}),flush=True)
    checkpoint()
    for original in sorted(sources):
        if time.monotonic()-start>65*60:report['timeBudgetReached']=True;break
        try:
            source=pathlib.Path(original)
            if not source.is_file():
                if pathlib.Path(original+'.extracted.json').exists():continue
                replacements=alternates.get(original,[])
                if not replacements:report['missing'].append(original);continue
                source=replacements[0]
            digest=file_sha(source)
            if digest in known:continue
            recovered_roots=[project/'SourceAssets/PathRepaired',pathlib.Path(r'C:\ANOMALIA_ResourceRecovery20261108/PathRepaired')]
            already=False
            for existing_root in recovered_roots:
                marker=existing_root/digest[:20]/'path-repair-result.json'
                if marker.is_file():
                    saved=json.loads(marker.read_text(encoding='utf-8'))
                    if saved.get('sourceSHA256')==digest and all(pathlib.Path(x['prepared']).is_file() and file_sha(x['prepared'])==x['preparedSHA256'] for x in saved.get('accepted',[])):
                        report['archivesAlreadyRepaired']=report.get('archivesAlreadyRepaired',0)+1;already=True;break
            if already:continue
            with zipfile.ZipFile(source) as archive:required=sum(i.file_size for i in archive.infolist())
            roots=recovered_roots
            root=None
            for candidate in roots:
                candidate.mkdir(parents=True,exist_ok=True)
                if shutil.disk_usage(candidate).free>=required+12*1024**3:root=candidate;break
            if root is None:raise ValueError('Insufficient space on C and D with 12 GiB reserve')
            repair=Repair(source,root/digest[:20],12*1024**3);repair.extract();accepted,deferred=repair.models()
            raw=json.loads(raw_path.read_text(encoding='utf-8'));seen={r['sha256'] for r in raw['imports']};added=0
            for model in accepted:
                if model['sha256'] in seen:continue
                raw['imports'].append({'source':model['path'],'prepared':model['prepared'],'sha256':model['sha256'],'preparedSHA256':model['preparedSHA256'],'family':hashlib.sha256(digest.encode()).hexdigest(),'animationOnly':False})
                seen.add(model['sha256']);added+=1
            temporary=raw_path.with_suffix('.paths.tmp');temporary.write_text(json.dumps(raw,indent=2),encoding='utf-8');os.replace(temporary,raw_path)
            record={'archive':str(source),'originalArchive':original,'sourceSHA256':digest,'folder':str(repair.root),'accepted':accepted,'deferred':deferred,'originalModified':False}
            write_owned(repair.root/'path-repair-result.json',json.dumps(record,indent=2).encode())
            report['sources'].append(record);report['archivesRepaired']+=1;report['newQueuedModels']+=added;report['losslesslyExtractedModelsAwaitingFormatReview']+=len(deferred)
        except Exception as exc:report['errors'].append({'source':original,'reason':str(exc)})
        checkpoint()
    checkpoint()
if __name__=='__main__':main()
