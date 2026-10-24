"""Verify cross-file reference integrity, preserving case and provisional UE status."""
import csv,json,re
from pathlib import Path

def verify(root):
    payload=json.loads((root/'catalogue_ANOMALIA.json').read_text())
    records=payload['records']; ids=[r['id'] for r in records]
    assert len(ids)==len(set(ids)), 'duplicate record IDs'
    categories={c['code'] for c in payload['categories']}
    assert len(categories)==29
    observations={}
    with (root/'observations_sources.jsonl').open() as stream:
        for line in stream:
            row=json.loads(line);key=row['observationId']
            assert key not in observations, 'duplicate observation ID'
            assert re.fullmatch('[0-9a-f]{64}',row['sourceSha256'])
            assert row['sourceRevision'] and row['sourceUrl']
            observations[key]=row
    for row in records:
        assert row['categoryCode'] in categories
        assert row['sourceObservationIds'] and row['sourceUrls']
        for key in row['sourceObservationIds']:
            assert observations[key]['classname']==row['classname'], 'case or provenance mismatch'
        assert row['ue5']['referenced'] is True
        assert not any(row['ue5'][k] for k in ('imported','visibleInEditor','functional','testedPC','testedMultiplayer'))
        assert row['originalAsset']['approved'] is False
    with (root/'catalogue_UE5_ANOMALIA.csv').open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.DictReader(stream,delimiter=';'))
    assert len(rows)==len(records)
    # The machine CSV and normalized JSON must retain exactly the same class identities.
    assert {(r['id_anomalia'],r['classe_dayz_reference']) for r in rows}=={(r['id'],r['classname']) for r in records}
    mods=json.loads((root/'inventaire_mods_prioritaires.json').read_text())
    assert len(mods)==54 and all(r['metadata_api_obtenue'] for r in mods)
    maps=json.loads((root/'verification_quatre_cartes.json').read_text())
    assert maps['unionExactClassnames']==2460
    assert not payload['complete'] and payload['referenceOnly']
    result=dict(status='PASS',records=len(records),observations=len(observations),categories=len(categories),priorityMods=len(mods),ue5Imported=0,complete=False)
    (root/'verification_integrite_exports.json').write_text(json.dumps(result,indent=2))
    print(result)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path)
    verify(parser.parse_args().directory)
