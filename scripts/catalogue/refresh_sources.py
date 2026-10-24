"""Fetch reference metadata into an isolated cache; never touch a game installation.

Pinned revisions by default. --latest explicitly follows each remote default branch.
Only text source patterns are checked out; no PBO or artistic asset extraction.
"""
import argparse,json,subprocess,sys
from pathlib import Path

def run(*args,cwd=None):
    return subprocess.check_output(args,cwd=cwd,text=True).strip()

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--cache',type=Path,required=True);p.add_argument('--input',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--latest',action='store_true')
    a=p.parse_args();manifest=json.loads(a.manifest.read_text());a.cache.mkdir(parents=True,exist_ok=True)
    for repo in manifest['repositories']:
        target=a.cache.resolve()/repo['id']
        if not (target/'.git').exists():
            if target.exists():raise RuntimeError('Refusing to overwrite non-repository '+str(target))
            run('git','clone','--filter=blob:none','--no-checkout',repo['url'],str(target))
        if run('git','remote','get-url','origin',cwd=target)!=repo['url']:
            raise RuntimeError('Cache origin mismatch: '+repo['id'])
        if run('git','status','--porcelain',cwd=target):raise RuntimeError('Dirty cache: '+repo['id'])
        revision=repo['revision']
        if a.latest:
            remote=run('git','ls-remote','--symref','origin','HEAD',cwd=target)
            revision=next(line.split()[0] for line in remote.splitlines() if line.endswith('\tHEAD') and not line.startswith('ref:'))
        run('git','fetch','--depth=1','origin',revision,cwd=target)
        run('git','sparse-checkout','set','--no-cone','*.cpp','*.hpp','*.h','*.xml','*.json','*.c','*.map','*.md','*LICENSE*',cwd=target)
        run('git','checkout','--detach',revision,cwd=target)
        repo.update(directory=str(target),revision=run('git','rev-parse','HEAD',cwd=target))
    a.out.mkdir(parents=True,exist_ok=True)
    resolved=a.out/'resolved_sources.json';resolved.write_text(json.dumps(manifest,indent=2))
    subprocess.run([sys.executable,str(Path(__file__).with_name('build_reference_catalogue.py')),'--manifest',str(resolved),'--input',str(a.input),'--out',str(a.out)],check=True)
    print('Core extraction done. Run supplemental coverage reports and integrity verification before distribution.')

if __name__=='__main__':main()
