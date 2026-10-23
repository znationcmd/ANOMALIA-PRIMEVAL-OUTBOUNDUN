"""CMD Studio — conversion de ressources locales avec Blender installé."""
import os
import sys
import bpy

def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 2:
        raise ValueError("Usage: -- source.fbx destination.glb")
    source, destination = map(os.path.abspath, args)
    extension = os.path.splitext(source)[1].lower()
    if extension != ".blend":
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        if extension == ".fbx":
            bpy.ops.import_scene.fbx(filepath=source)
        elif extension == ".obj":
            bpy.ops.wm.obj_import(filepath=source)
        elif extension in (".glb", ".gltf"):
            bpy.ops.import_scene.gltf(filepath=source)
        elif extension in (".usd", ".usdz"):
            bpy.ops.wm.usd_import(filepath=source)
        else:
            raise ValueError("Format incompatible : " + extension)
    if not bpy.data.objects:
        raise RuntimeError("La scène ne contient aucun objet à exporter.")
    bpy.ops.export_scene.gltf(filepath=destination, export_format="GLB",
                              export_apply=True, use_selection=False)
    if not os.path.exists(destination) or os.path.getsize(destination) == 0:
        raise RuntimeError("Échec de la création du fichier GLB.")
    print("CMD_STUDIO_OK " + destination)

if __name__ == "__main__":
    main()
