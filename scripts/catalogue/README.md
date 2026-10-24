# ANOMALIA reference catalogue

Python 3 standard library + Git. The extractor collects exact class-name facts with pinned source locations. It never imports third-party models, executes DayZ scripts or marks gameplay as implemented.

From the extracted delivery root, reproduce the core export:

```sh
python outils/refresh_sources.py --manifest sources.json --cache source-cache --input categories-et-mods --out refreshed-output
```

Add `--latest` to refresh remote default-branch revisions. This deliberately changes source versions and must be reviewed. The resulting `resolved_sources.json` records actual revisions. Failures stop execution rather than silently dropping repositories. The script is ready to invoke from a scheduler; no recurring task has been activated on the user's PC.

The supplemental report script currently expects the original working directory layout (`catalogue-output`, `catalogue-input`, `workshop-metadata`, `dayz-official`). It is retained for reproducibility, but is not yet a fully automated Workshop refresh pipeline. Its aliases are provisional and require author-identity review. Workshop metadata alone never supplies the missing complete class registries.

Verify the delivered snapshot:

```sh
python outils/verify_reference_exports.py catalogue
```

Run extraction tests in the project repository:

```sh
python -m unittest discover -s tests -p test_reference_catalogue.py -v
```

CSV delimiter: semicolon, UTF-8 BOM. JSON records carry `sourceObservationIds` resolved by `observations_sources.jsonl`. IDs are case-sensitive hashes of source context plus exact class name. Observations retain file hash, Git revision, location and evidence kind. Repository SHA and evidence type must be retained when building consumers.

`complete=false`, `referenceOnly=true`, `classificationVerified=false` and all UE import/function/test flags remain false until evidence is explicitly added by a separate verified integration process. Do not convert references into gameplay definitions automatically. No direct Unreal DataTable import contract is claimed.
