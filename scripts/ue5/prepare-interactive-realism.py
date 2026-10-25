"""Fetch exact licensed review sources without replacing artist edits or fetching whole tar shards."""
import hashlib
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    registry = json.loads((ROOT / 'docs/art/interactive-realism-sources.json').read_text())
    folder = ROOT / 'unreal/SourceAssets/InteractiveRealismSources_v1'
    folder.mkdir(parents=True, exist_ok=True)
    for item in registry['models']:
        dest = folder / item['file']
        if dest.parent != folder or item['license'] != 'CC-BY-4.0':
            raise RuntimeError('Unexpected review source')
        if not dest.exists():
            headers = {}
            url = item['url']
            start = item.get('rangeStart')
            if start is not None:
                headers['Range'] = f"bytes={start}-{start + item['bytes'] - 1}"
                url += f'?download=true&asset-range={start}'
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=180) as response:
                if start is not None:
                    match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range', ''))
                    if response.status != 206 or not match or int(match[1]) != start or int(match[2]) != start + item['bytes'] - 1:
                        raise RuntimeError('Exact byte range required; full archive download refused')
                data = response.read(item['bytes'] + 1)
            if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                raise RuntimeError('Downloaded source identity mismatch: ' + item['id'])
            with dest.open('xb') as output:
                output.write(data)
        data = dest.read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise RuntimeError('Existing source differs and was preserved: ' + item['id'])
        print(item['id'], len(data), item['sha256'], flush=True)


if __name__ == '__main__':
    main()
