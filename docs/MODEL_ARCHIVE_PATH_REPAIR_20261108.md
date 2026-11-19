# Remaining archive path conflicts
Only explicitly blocked ZIP sources from the prior audit are considered. Completed extraction receipts and SHA256 source ledgers are reused. Missing former temporary Fab archives are searched in the existing owned-file inventory by matching archive filename and original Fab UUID for generic export names.

Archive members are extracted to content-addressed owned paths. Illegal Windows filename characters no longer become filesystem paths. Distinct contents sharing one name are preserved separately; identical contents within an archive share one retained file. Full original ZIPs remain unchanged.

glTF/GLB image and buffer references are resolved by exact source casing first, then an unambiguous case-insensitive match. Binary GLB chunks remain unchanged. OBJ material and texture references are rewritten only when resolved. Conflicting references with the same exact name and different contents remain deferred; no arbitrary texture is selected.

Only prepared glTF/GLB/OBJ sources with resolved dependencies are appended to the durable actual-project import manifest, deduplicated by original SHA256. FBX, other DCC formats and native packages are retained losslessly and explicitly marked for format/material or mount review. This does not claim that every model is imported or gameplay-ready.

Six local regression tests passed: filename colon and case collisions; differing duplicate-name ambiguity; identical-byte deduplication; OBJ/MTL/texture rewriting; unchanged GLB binary payload; traversal and external network dependency rejection. Workflow runs the same tests before Windows extraction, then two resumable native import batches. Per-archive missing files, errors and deferred formats remain in durable receipts.
