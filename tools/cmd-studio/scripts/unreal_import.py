"""Import réel vers UE5.8. Activer Python Editor Script Plugin dans le .uproject."""
import json
import os
import unreal

manifest_path = os.environ.get("CMD_STUDIO_IMPORT_MANIFEST")
if not manifest_path or not os.path.isfile(manifest_path):
    raise RuntimeError("Manifeste CMD Studio introuvable.")
with open(manifest_path, "r", encoding="utf-8") as file:
    request = json.load(file)
source = request["source"]
destination = request["destination"]
if not os.path.isfile(source):
    raise RuntimeError("Fichier 3D source introuvable : " + source)
if not destination.startswith("/Game/CMDStudio/"):
    raise RuntimeError("Dossier de destination non autorisé.")
task = unreal.AssetImportTask()
task.set_editor_property("filename", source)
task.set_editor_property("destination_path", destination)
task.set_editor_property("automated", True)
task.set_editor_property("replace_existing", False)
task.set_editor_property("save", True)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
imported = task.get_editor_property("imported_object_paths")
if not imported:
    raise RuntimeError("Unreal n'a importé aucun objet ; consulter les journaux de l'éditeur.")
print("CMD_STUDIO_IMPORTED", list(imported))
