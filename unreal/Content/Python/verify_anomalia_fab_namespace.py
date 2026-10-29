"""Verify a newly copied namespace in the installed Unreal project, without changing defaults."""
import json, os, traceback
from pathlib import Path
import unreal
receipt=json.loads(Path(os.environ["FAB_SOURCE_RECEIPT"]).read_text(encoding="utf-8"))
base=receipt["namespace"]
report={"state":"FAILED","namespace":base,"objects":[],"errors":[],"gameplay":"not_run","mainMapModified":False}
try:
    for row in receipt["sources"]:
        for a in row["assets"]:
            obj=unreal.load_asset(a["path"])
            if not obj:raise RuntimeError("Cannot load "+a["path"])
            if obj.get_class().get_name()!=a["class"]:raise RuntimeError("Class mismatch "+a["path"])
            report["objects"].append({"path":obj.get_path_name(),"class":obj.get_class().get_name()})
    report["state"]="INSTALLED_NAMESPACE_LOADED_NOT_GAMEPLAY_ACCEPTED"
except Exception as e:
    report["errors"].append(str(e));unreal.log_error(traceback.format_exc())
Path(os.environ["FAB_INSTALLED_RECEIPT"]).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
