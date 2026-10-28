#!/usr/bin/env python3
"""Stage legally downloadable Sketchfab glTF assets for ANOMALIA, without modifying Unreal.

Run locally on a Windows PC with its own Sketchfab API token. The API requires auth;
this does not scrape or bypass that requirement. Never commit a credential or archive.
"""
from __future__ import annotations

import argparse
import datetime as dt
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / 'unreal/Config/Anomalia/sketchfab-vehicles.json'
DEFAULT_OUT = Path.home() / 'Downloads' / 'ANOMALIA_Sketchfab_Staging'
UID_PATTERN = re.compile(r'^[a-f0-9]{32}$')
MAX_ARCHIVE = 512 * 1024 * 1024
MAX_UNPACKED = 2 * 1024 * 1024 * 1024
MAX_FILES = 2000
USER_AGENT = 'ANOMALIA-asset-staging/1.0'


def slug(value: str) -> str:
    s = re.sub(r'[^a-z0-9_]+', '_', value.lower().replace(' ', '_'))
    return s.strip('_')[:64]


def model_folder(row: dict) -> str:
    return f"{slug(row['nom'])}_{row['uid'][:8]}"


def read_catalogue(path: Path = CATALOGUE) -> list[dict]:
    data = json.loads(path.read_text(encoding='utf-8'))
    rows = data['modeles']
    assert len({r['nom'] for r in rows}) == len(rows), 'Duplicate model names'
    return rows


def license_allowed(meta: dict) -> bool:
    """Allow only CC0 and CC-BY, never NC/ND/SA by inference."""
    lic = meta.get('license') or {}
    slug_value = (lic.get('slug') or lic.get('uid') or '').lower().replace('_', '-')
    if slug_value in {'cc0', 'cc0-1.0', 'cc-by', 'cc-by-4.0', 'cc-by-3.0'}:
        return True
    label = (lic.get('label') or '').strip().lower()
    return label in {'cc attribution', 'cc0 public domain', 'creative commons attribution', 'cc zero'}


def request_json(url: str, token: str, auth_type: str) -> dict:
    req = urllib.request.Request(url, headers={
        'Authorization': f'{auth_type} {token}',
        'User-Agent': USER_AGENT, 'Accept': 'application/json'
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def download_verified_zip(url: str, to_path: Path) -> tuple[str, int]:
    """Stream bounded archive to a temp file and commit it only after ZIP validation."""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    fd, temp_name = tempfile.mkstemp(dir=to_path.parent, suffix='.part')
    os.close(fd)
    temp_path = Path(temp_name)
    sha = hashlib.sha256()
    size = 0
    try:
        with urllib.request.urlopen(req, timeout=120) as remote, temp_path.open('wb') as out:
            while True:
                chunk = remote.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_ARCHIVE:
                    raise ValueError('Archive larger than staging limit')
                out.write(chunk)
                sha.update(chunk)
        with zipfile.ZipFile(temp_path) as z:
            validate_zip(z)
        if to_path.exists():
            raise FileExistsError(f'Will not replace existing archive: {to_path}')
        temp_path.replace(to_path)
        return sha.hexdigest(), size
    finally:
        temp_path.unlink(missing_ok=True)


def validate_zip(z: zipfile.ZipFile) -> None:
    entries = z.infolist()
    if len(entries) > MAX_FILES or sum(i.file_size for i in entries) > MAX_UNPACKED:
        raise ValueError('Archive exceeds secure extraction limits')
    for entry in entries:
        parts = Path(entry.filename.replace('\\', '/')).parts
        if entry.filename.startswith(('/', '\\')) or '..' in parts or (parts and ':' in parts[0]):
            raise ValueError('Unsafe archive path')
        if (entry.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError('Archive has symbolic link')


def extract_safe(zippath: Path, dest: Path) -> None:
    """Extract to a brand-new directory; never overwrite a prior import."""
    with zipfile.ZipFile(zippath) as z:
        validate_zip(z)
        with tempfile.TemporaryDirectory(prefix='sf_extract_', dir=dest.parent) as tmp:
            root = Path(tmp).resolve()
            for entry in z.infolist():
                target = (root / entry.filename.replace('\\', '/')).resolve()
                if not target.is_relative_to(root):
                    raise ValueError('Path traversal detected')
                if entry.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(entry) as src, target.open('wb') as out:
                        shutil.copyfileobj(src, out, length=1024*1024)
            if not any(root.rglob('*.gltf')) and not any(root.rglob('*.glb')):
                raise ValueError('ZIP has no glTF/GLB model')
            if dest.exists():
                raise FileExistsError(f'Will not replace extracted directory: {dest}')
            shutil.move(str(root), str(dest))


def collect(out: Path, rows: list[dict], token: str, auth_type: str, limit: int | None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    results = []
    count = 0
    for row in rows:
        state = row['statut']
        uid = row.get('uid') or ''
        result = {'nom': row['nom'], 'uid': uid, 'source': row.get('lien'), 'etat': 'non_traite',
                  'ue_catalog_type': row.get('ue_catalog_type')}
        if row.get('distributable') is False:
            result['etat'] = 'droits_a_verifier'; results.append(result); continue
        if state != 'telechargement_confirme' or not UID_PATTERN.fullmatch(uid):
            result['etat'] = 'source_ou_licence_a_verifier'; results.append(result); continue
        if limit is not None and count >= limit:
            result['etat'] = 'limite_de_lot'; results.append(result); continue
        count += 1
        try:
            meta = request_json(f'https://api.sketchfab.com/v3/models/{uid}', token, auth_type)
            if not meta.get('isDownloadable'):
                result['etat'] = 'non_telechargeable'; results.append(result); continue
            if not license_allowed(meta):
                result['etat'] = 'licence_non_autorisee_ou_inconnue'; results.append(result); continue
            folder = out / model_folder(row)
            archive = folder / 'original_gltf.zip'
            if folder.exists():
                result['etat'] = 'deja_present_sans_ecrasement'; results.append(result); continue
            folder.mkdir(parents=True)
            try:
                signed = request_json(f'https://api.sketchfab.com/v3/models/{uid}/download', token, auth_type)
                url = (signed.get('gltf') or {}).get('url')
                if not url or not url.startswith('https://'):
                    raise ValueError('Sketchfab returned no HTTPS glTF archive')
                digest, size = download_verified_zip(url, archive)
                extract_safe(archive, folder / 'extrait')
                author = meta.get('user') or {}
                lic = meta.get('license') or {}
                provenance = {'uid': uid, 'nom': row['nom'], 'source': row.get('lien'),
                              'auteur': author.get('displayName') or author.get('username'),
                              'licence': lic, 'archive_sha256': digest, 'archive_bytes': size,
                              'telecharge_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                              'compatibilite_commerciale_et_marques': 'a_verifier_humainement'}
                (folder / 'provenance.json').write_text(json.dumps(provenance, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
                result['etat'] = 'archive_extraite_non_importee'; result['dossier'] = str(folder)
            except Exception:
                # Keep any successfully downloaded archive for recovery, never delete user files.
                raise
        except (urllib.error.URLError, ValueError, OSError) as exc:
            result['etat'] = 'erreur'; result['detail'] = str(exc)[:300]
            if isinstance(exc, urllib.error.HTTPError) and exc.code == 429:
                results.append(result)
                break  # Respect Sketchfab rate limits
        results.append(result)
        time.sleep(0.25)
    report = {'creee_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'downloaded': sum(r['etat'] == 'archive_extraite_non_importee' for r in results),
              'unreal_imported': 0, 'results': results}
    (out / 'rapport_recepisse.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, default=CATALOGUE)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--download', action='store_true', help='Explicitly use official authenticated Download API')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--auth-type', choices=['Token','Bearer'], default='Token')
    args = parser.parse_args(argv)
    rows = read_catalogue(args.catalogue)
    candidates = [r for r in rows if r['statut']=='telechargement_confirme' and r.get('uid')]
    print(f'ANOMALIA Sketchfab: {len(rows)} references; {len(candidates)} candidates; 0 imported by this command.')
    if not args.download:
        print('Preflight only. For authorized staging use --download on your PC.')
        return 0
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    token = os.environ.get('SKETCHFAB_API_TOKEN') or getpass.getpass('Jeton Sketchfab (masque, jamais enregistre): ')
    if not token:
        print('No credentials: cannot download from official API.')
        return 2
    try:
        request_json('https://api.sketchfab.com/v3/me', token, args.auth_type)
    except (urllib.error.URLError, ValueError) as exc:
        print('Authentication failed:', str(exc)[:180])
        return 2
    report = collect(args.output, rows, token, args.auth_type, args.limit)
    print('Archives extracted:', report['downloaded'], '— Unreal assets imported: 0')
    print('See:', args.output / 'rapport_recepisse.json')
    return 0 if report['downloaded'] > 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
