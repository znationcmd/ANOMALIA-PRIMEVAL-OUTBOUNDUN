import concurrent.futures, hashlib, json, pathlib, urllib.request, zipfile, sys
ROOT=pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else pathlib.Path(__file__).resolve().parent
pin=ROOT/'pinned-source-receipt.json'
pinned={s['id']:s for s in json.loads(pin.read_text())['sources']} if pin.exists() else {}
packs=['shirts01','pants01','gloves01','shoes01','hats01','hats02','masks01','underwear04','suits01','dress01']
sources=[dict(id='mh_'+p,title=p,category='clothing',license='CC0-1.0',source='https://static.makehumancommunity.org/assets/assetpacks/'+p+'.html',url='https://files.makehumancommunity.org/asset_packs/'+p+'/'+p+'_cc0.zip',filename=p+'_cc0.zip') for p in packs]
sources += [
dict(id='oga_pills_mxc2',title='Pills 3D Models',category='medicine',author='mxc2 / Marcus Indrek Simmer',license='CC0-1.0',source='https://opengameart.org/content/pills-3d-models',url='https://opengameart.org/sites/default/files/pills-2022-marcus-indrek-simmer_4.zip',filename='pills.zip'),
dict(id='oga_money_yughues',title='Money',category='money',author='Yughues',license='CC0-1.0',source='https://opengameart.org/content/money',url='https://opengameart.org/sites/default/files/money.7z',filename='money.7z'),
dict(id='oga_cannabis_yughues',title='Cannabis plants',category='fictional_drug_prop',author='Yughues',license='CC0-1.0',source='https://opengameart.org/content/cannabis-plants',url='https://opengameart.org/sites/default/files/Cannabis.7z',filename='Cannabis.7z'),
dict(id='oga_syringe_arido',title='Syringe',category='medicine',author='Arido',license='CC0-1.0',source='https://opengameart.org/content/syringe',url='https://opengameart.org/sites/default/files/Syringe.blend',filename='Syringe.blend'),
dict(id='grab3d_pill_bottle',title='Pill Bottle',category='medicine',license='CC0-1.0',source='https://grab3d.com/models/props/pill-bottle/',url='https://grab3d.com/dl/pill-bottle/pill-bottle.glb',filename='pill-bottle.glb',quality='Lightweight; visual review required')]

def fetch(s):
    path=ROOT/'sources'/s['id']/s['filename'];path.parent.mkdir(parents=True,exist_ok=True)
    try:
        if not path.exists():
            with urllib.request.urlopen(s['url'],timeout=40) as r,path.with_suffix(path.suffix+'.part').open('wb') as out:
                for block in iter(lambda:r.read(1024*1024),b''):out.write(block)
            path.with_suffix(path.suffix+'.part').replace(path)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        expected=pinned.get(s['id'])
        if expected and expected.get('status')=='DOWNLOADED' and (digest!=expected['sha256'] or path.stat().st_size!=expected['bytes']):
            raise ValueError('Source differs from pinned receipt; file preserved')
        if path.suffix=='.zip':
            with zipfile.ZipFile(path) as z:
                assert z.testzip() is None
                for member in z.infolist():
                    p=pathlib.PurePosixPath(member.filename)
                    if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe archive')
                z.extractall(ROOT/'extracted'/s['id'])
        elif path.suffix=='.7z':
            import py7zr
            with py7zr.SevenZipFile(path) as z:
                for name in z.getnames():
                    member=pathlib.PurePosixPath(name)
                    if member.is_absolute() or '..' in member.parts or '\\' in name:raise ValueError('Unsafe archive')
                z.extractall(ROOT/'extracted'/s['id'])
        result=dict(s,status='DOWNLOADED',path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=digest,unrealImported=False)
    except Exception as e:result=dict(s,status='FAILED',error=str(e),unrealImported=False)
    print(json.dumps({k:result[k] for k in ['id','status','bytes','error'] if k in result}),flush=True)
    return result

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as p:results=list(p.map(fetch,sources))
    (ROOT/'batch-receipt.json').write_text(json.dumps(dict(schemaVersion=1,date='2026-10-23',sources=results),indent=2))
