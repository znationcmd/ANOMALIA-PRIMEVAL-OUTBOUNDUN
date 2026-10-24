"""Fetch one credited skeletal candidate for isolated UE import; never approve gameplay."""
import hashlib
import json
import struct
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UID = '38007d947ae74dea83988cb0b08ee053'
SHA256 = 'ffc3f83767d0f4c92fab0a4eeb7ec3b48917fbda98638d4bf9c6e43268eb64c2'
URL = 'https://huggingface.co/datasets/allenai/objaverse/resolve/main/glbs/000-104/' + UID + '.glb'
SOURCE = 'https://sketchfab.com/3d-models/animated-tyrannosaurus-rex-dinosaur-running-loop-' + UID


def main():
    folder = ROOT / 'unreal/SourceAssets/CreatureReview/TRexLasquetiSpice'
    folder.mkdir(parents=True, exist_ok=True)
    model = folder / 'TRex.glb'
    if not model.exists():
        # Verify bytes before committing a source file; preserve any existing file.
        with urllib.request.urlopen(URL, timeout=120) as response:
            data = response.read(32 * 1024 * 1024 + 1)
        if hashlib.sha256(data).hexdigest() != SHA256:
            raise RuntimeError('Creature download hash mismatch')
        with model.open('xb') as out:
            out.write(data)
    data = model.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise RuntimeError('Existing creature source differs; preserved without overwrite')
    magic, version, length, chunk_length, chunk_type = struct.unpack_from('<5I', data)
    if (magic, version, length, chunk_type) != (0x46546C67, 2, len(data), 0x4E4F534A):
        raise RuntimeError('Invalid GLB structure')
    doc = json.loads(data[20:20 + chunk_length])
    clips = sorted(a['name'] for a in doc.get('animations', []))
    joints = [len(s['joints']) for s in doc.get('skins', [])]
    if clips != ['attack_tail', 'bite', 'idle', 'roar', 'run'] or joints != [72]:
        raise RuntimeError('Expected skeletal rig or animation clips missing')
    report = dict(state='SOURCE_VERIFIED_NOT_NATIVE_IMPORTED', uid=UID, source=SOURCE,
                  author='LasquetiSpice', license='CC-BY-4.0',
                  licenseUrl='https://creativecommons.org/licenses/by/4.0/',
                  distributionUrl=URL, sha256=SHA256, bytes=len(data), joints=joints,
                  animations=clips, nativeImported=False, playable=False,
                  productionApproved=False,
                  limitations=['Candidate visual quality is not final photorealism approval.',
                               'Missing walk, sleep, injury, death and mount animation coverage.',
                               'Source dimensions require species-scale authoring.'])
    (folder / 'source-review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (folder / 'CREDITS.md').write_text(
        '# Skeletal creature review candidate\n\n'
        'Animated Tyrannosaurus Rex Dinosaur Running Loop by LasquetiSpice.\n\n'
        + SOURCE + '\n\nCC BY 4.0: https://creativecommons.org/licenses/by/4.0/\n\n'
        'Distributed GLB obtained from AllenAI Objaverse. Source bytes unchanged. '
        'UE import may convert coordinates, materials, mesh and animation formats. '
        'Not approved as a completed ANOMALIA gameplay creature.\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
