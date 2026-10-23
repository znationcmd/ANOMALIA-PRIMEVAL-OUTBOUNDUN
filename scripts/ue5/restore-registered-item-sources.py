"""Restore the checked source batch from its committed receipt; no UE import."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
from urllib.request import urlopen

def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()

def main():
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', type=Path, default=repo/'unreal/Saved/ItemSourceCache')
    args = parser.parse_args()
    receipt = repo/'docs/art/item-source-download-receipt-20261023.json'
    manifest = json.loads(receipt.read_text(encoding='utf-8'))
    done = set()
    for model in manifest['models']:
        for item in model['files']:
            relative = PurePosixPath(item['path'])
            if relative.is_absolute() or '..' in relative.parts or ':' in str(relative) or '\\' in str(relative):
                raise ValueError('Unsafe relative path')
            if item['path'] in done:
                continue
            done.add(item['path'])
            url = urlparse(item['url'])
            if url.scheme != 'https' or url.hostname != 'dl.polyhaven.org':
                raise ValueError('Unexpected source URL')
            target = args.destination/'ANOMALIA_SOURCE_ASSETS'/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if target.stat().st_size != item['bytes'] or digest(target) != item['sha256']:
                    raise ValueError('Existing file differs; preserved: '+str(target))
                continue
            temporary = target.with_suffix(target.suffix+'.part')
            try:
                with urlopen(item['url'], timeout=60) as response, temporary.open('wb') as output:
                    for block in iter(lambda: response.read(1024*1024), b''):
                        output.write(block)
                if temporary.stat().st_size != item['bytes'] or digest(temporary) != item['sha256']:
                    raise ValueError('Downloaded source differs: '+item['path'])
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        print(model['modelId']+' checked', flush=True)
    (args.destination/'download-receipt.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    importer = repo/'scripts/ue5/import-polyhaven-item-sources.py'
    (args.destination/'import_sources_ue5.py').write_bytes(importer.read_bytes())
    print('Sources restored; run import_sources_ue5.py inside Unreal Editor separately.')

if __name__ == '__main__':
    main()
