"""Import a real skeletal candidate into an isolated review folder, not the game map."""
import json
import os
from pathlib import Path
import unreal


def main():
    project = Path(unreal.Paths.project_dir()).resolve()
    source = project / 'SourceAssets/CreatureReview/TRexLasquetiSpice'
    review = json.loads((source / 'source-review.json').read_text(encoding='utf-8'))
    destination = '/Game/Anomalia/CreatureReview/TRexLasquetiSpice'
    # Preserve any prior artist work. Reuse only when its actual assets satisfy checks.
    existing = unreal.EditorAssetLibrary.list_assets(destination, recursive=True, include_folder=False)
    if not existing:
        task = unreal.AssetImportTask()
        task.set_editor_property('filename', str(source / 'TRex.glb'))
        task.set_editor_property('destination_path', destination)
        task.set_editor_property('automated', True)
        task.set_editor_property('replace_existing', False)
        task.set_editor_property('save', True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes, animations = [], []
    for path in unreal.EditorAssetLibrary.list_assets(destination, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset, unreal.SkeletalMesh):
            skeleton = asset.get_editor_property('skeleton')
            if skeleton:
                meshes.append(dict(path=path, skeleton=skeleton.get_path_name()))
        elif isinstance(asset, unreal.AnimSequence):
            animations.append(dict(path=path, name=asset.get_name(), seconds=asset.get_play_length()))
    if not meshes or len(animations) < 5:
        raise RuntimeError('Skeletal mesh / five animation sequences were not imported: ' +
                           json.dumps(dict(meshes=meshes, animations=animations)))
    # Require every advertised clip, rather than accepting five unrelated sequences.
    for clip in review['animations']:
        if not any(clip.lower() in a['name'].lower() and a['seconds'] > 0 for a in animations):
            raise RuntimeError('Missing nonempty native animation: ' + clip)
    notices = project / 'Content/ThirdPartyNotices'
    notices.mkdir(parents=True, exist_ok=True)
    (notices / 'TRexLasquetiSpice-CREDITS.md').write_text(
        (source / 'CREDITS.md').read_text(encoding='utf-8'), encoding='utf-8')
    report = dict(state='SKELETAL_CREATURE_IMPORTED_NOT_PLAYTESTED',
                  sourceCommit=os.environ.get('GITHUB_SHA'), source=review,
                  skeletalMeshes=meshes, animations=animations,
                  actorIntegrated=False, mounted=False, gameplayTested=False,
                  productionApproved=False)
    output = Path(os.environ['ANOMALIA_CREATURE_IMPORT_REPORT'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    unreal.log('ANOMALIA_CREATURE_REVIEW_IMPORTED')


main()
