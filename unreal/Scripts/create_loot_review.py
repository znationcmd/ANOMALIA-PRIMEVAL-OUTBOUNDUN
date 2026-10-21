"""Create a separate real UE map for catalogue pickups; preserve every existing map."""
import unreal

PACKAGE = '/Game/Maps/ANOMALIA_LootReview_v1'
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(PACKAGE):
    unreal.log('Existing loot review preserved: '+PACKAGE)
else:
    if not level.new_level(PACKAGE):
        raise RuntimeError('Cannot create loot review map')
    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 250, -20))
    floor.set_actor_label('ANOMALIA_LootReviewFloor')
    floor.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube'))
    floor.set_actor_scale3d(unreal.Vector(30, 30, .4))
    start = actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, 100))
    start.set_actor_label('ANOMALIA_LootReviewStart')
    actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 1000), unreal.Rotator(-45, -30, 0))
    actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 500))
    actors.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0))
    if not level.save_all_dirty_levels():
        raise RuntimeError('Cannot save loot review map')
    unreal.log('ANOMALIA loot review created. Play to spawn server-selected pickups; Interact to collect, I for inventory.')
