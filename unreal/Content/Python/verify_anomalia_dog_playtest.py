"""Exercise the real native dog, player, proximity callbacks and locomotion in an isolated PIE map."""
import os,json,time,hashlib,traceback
from pathlib import Path
import unreal
OUT=Path(os.environ['ANOMALIA_PIE_REPORT']);OUT.mkdir(parents=True,exist_ok=False)
RUN=os.environ['GITHUB_RUN_ID'];SCOPE='dog-playtest-'+RUN
SOURCE='/Game/Anomalia/CharacterTests/SurvivalPlayable_40658680443/L_Survival_Playtest'
FOLDER='/Game/Anomalia/CompanionTests/GermanShepherd_'+RUN
MAP=FOLDER+'/L_Dog_Playtest'
editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
worlds=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
assets=unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
s={'start':time.monotonic(),'phase':'wait','at':time.monotonic(),'finished':False}
r={'state':'FAILED','scope':SCOPE,'map':MAP,'checks':[],'errors':[],'screenshots':[],
   'engine':unreal.SystemLibrary.get_engine_version(),'physicalKeyboardMouseTested':False,'multiplayerTested':False,
   'mainProjectModified':False,'dogEquipmentImplemented':False,'breedsAvailable':['german_shepherd'],
   'unavailableCommands':['sit','lie_down','attack'],'appearancePersistenceTested':False}
def require(ok,message):
    if not ok:raise RuntimeError(message)
def check(ok,message):
    require(ok,message);r['checks'].append(message)
def phase(p):s.update(phase=p,at=time.monotonic())
def rows():return list(s['inv'].get_editor_property('stacks'))
def stack(item):return next(x for x in rows() if str(x.item_id)==item)
def click(text):
    for relay in s['widget'].get_editor_property('ActionRelays'):
        button=relay.get_editor_property('Button');child=button.get_child_at(0)
        if isinstance(child,unreal.TextBlock) and str(child.get_text())==text:
            require(button.get_is_enabled(),'Disabled bound action '+text);relay.execute();return
    raise RuntimeError('Actual bound action missing: '+text)
def finish(error=None):
    if s['finished']:return
    s['finished']=True
    if error:r['errors'].append(str(error));r['traceback']=traceback.format_exc()
    else:r['state']='NATIVE_DOG_AND_ATTACHMENTS_PIE_PASSED_NOT_MULTIPLAYER_ACCEPTANCE'
    try:
        if s.get('widget'):s['widget'].call_method('CloseInventory');s.pop('widget',None)
        if s.get('actor'):s['actor'].get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    except Exception as e:r['errors'].append('cleanup '+str(e));r['state']='FAILED'
    (OUT/'report.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8')
    if s.get('handle'):unreal.unregister_slate_post_tick_callback(s.pop('handle'))
    editor.editor_request_end_play();s['close_at']=time.monotonic()+8
    def close(delta):
        if not editor.is_in_play_in_editor() and time.monotonic()>s['close_at']:
            unreal.unregister_slate_post_tick_callback(s.pop('close_handle'))
            for key in ('actor','dog','mesh','inv','pc','world','pose'):s.pop(key,None)
            import gc
            gc.collect();unreal.SystemLibrary.collect_garbage();unreal.SystemLibrary.quit_editor()
    s['close_handle']=unreal.register_slate_post_tick_callback(close)
def poses(mesh):
    names=[mesh.get_bone_name(i) for i in range(1,min(mesh.get_num_bones(),24))]
    return [mesh.get_socket_transform(n,unreal.RelativeTransformSpace.RTS_COMPONENT).translation for n in names]
def tick(delta):
    if s['finished']:return
    try:
        now=time.monotonic();require(now-s['start']<180,'Dog PIE timeout at '+s['phase'])
        if s['phase']=='wait':
            world=worlds.get_game_world()
            if not world or not editor.is_in_play_in_editor() or now-s['at']<2:return
            unreal.GameplayStatics.open_level(world,MAP,True,'AnomaliaServerId='+SCOPE);phase('travel');return
        if s['phase']=='travel':
            require(now-s['at']<25,'Travel or ownership did not settle: '+str(r.get('travelObserved')))
            world=worlds.get_game_world()
            if not world:return
            gm=unreal.GameplayStatics.get_game_mode(world)
            if not gm or 'GM_Survival_Playtest' not in gm.get_class().get_name():return
            require(gm.get_editor_property('server_id')==SCOPE,'Private server scope not applied')
            actor=unreal.GameplayStatics.get_player_pawn(world,0)
            if not actor or unreal.GameplayStatics.get_time_seconds(world)<3:return
            dogs=list(unreal.GameplayStatics.get_all_actors_of_class(world,unreal.AnomaliaDogCompanion))
            require(len(dogs)==1,'Expected exactly one real companion')
            dog=dogs[0]
            r['travelObserved']={'gameMode':gm.get_class().get_name(),'player':actor.get_path_name(),'playerLocation':str(actor.get_actor_location()),
                'dogLocation':str(dog.get_actor_location()),'autoAssignEnabled':dog.get_editor_property('auto_assign_nearest_survivor'),
                'tickEnabled':dog.is_actor_tick_enabled(),'owner':str(dog.get_editor_property('survivor_owner')),'simulationSeconds':unreal.GameplayStatics.get_time_seconds(world)}
            if dog.get_editor_property('survivor_owner')!=actor:
                require(now-s['at']<20,'Dog automatic ownership failed: '+str(r['travelObserved']))
                return
            mesh=dog.get_component_by_class(unreal.SkeletalMeshComponent)
            check(mesh.get_editor_property('skeletal_mesh_asset') is not None,'native dog loads actual German Shepherd mesh')
            check(mesh.has_valid_animation_instance(),'dog has a real animation instance')
            pc=unreal.GameplayStatics.get_player_controller(world,0);inv=actor.get_editor_property('inventory_component')
            s.update(world=world,actor=actor,dog=dog,mesh=mesh,pc=pc,inv=inv,pose=poses(mesh))
            inv.set_editor_property('weight_capacity_kg',100.0)
            require(not rows(),'Fresh private profile already has contents')
            require(inv.try_add_item('tactical_belt',1),'Belt rejected')
            require(inv.request_move_stack(stack('tactical_belt').stack_id,'mount_belt',0,0,False),'Belt equip failed')
            for item,slot in [('medical_pouch','mount_belt_medical'),('handcuffs','mount_belt_cuffs'),('rifle','mount_back_weapon'),('sleeping_bag','mount_back_sleep'),('water_bottle','mount_back_water')]:
                require(inv.try_add_item(item,1),'Actual inventory item rejected '+item)
                require(inv.request_move_stack(stack(item).stack_id,slot,0,0,False),'Attachment rejected '+slot)
            require(inv.try_add_item('stanag_magazine',2),'Magazine acquisition failed')
            first=stack('stanag_magazine').stack_id
            result=inv.try_split_stack(first,1)
            second=next(x.stack_id for x in rows() if str(x.item_id)=='stanag_magazine' and x.stack_id!=first)
            require(inv.request_move_stack(first,'mount_belt_mag1',0,0,False),'First magazine failed')
            require(inv.request_move_stack(second,'mount_belt_mag2',0,0,False),'Second magazine failed')
            require(inv.try_add_item('bandage',1),'Bandage acquisition failed')
            require(inv.request_move_stack(stack('bandage').stack_id,'mount_belt_medical_cargo',0,0,False),'Medical cargo failed')
            check(not inv.request_move_stack(stack('medical_pouch').stack_id,'hands',0,0,False),'full medical pouch cannot be removed')
            check(not actor.set_clothing_mesh('Backpack',None),'backpack with mounted weapon cannot be removed')
            before=[(x.stack_id,str(x.item_id),x.count,str(x.container_id)) for x in rows()]
            saved=inv.save_inventory_to_player_profile(SCOPE,'local-owner');r['profileSaveReturn']=str(saved);require((saved=='' if isinstance(saved,str) else bool(saved[0] if isinstance(saved,tuple) else saved)),'Profile save failed: '+str(saved))
            loaded=inv.load_inventory_from_player_profile(SCOPE,'local-owner');r['profileLoadReturn']=str(loaded);require((loaded=='' if isinstance(loaded,str) else bool(loaded[0] if isinstance(loaded,tuple) else loaded)),'Profile load failed: '+str(loaded))
            check(before==[(x.stack_id,str(x.item_id),x.count,str(x.container_id)) for x in rows()],'equipped belt accessories and medical contents survive disk save and reload')
            s['widget']=unreal.AnomaliaInventoryWidget.create_for_player_inventory(pc);require(s['widget'],'Native inventory widget missing')
            s['dog_origin']=dog.get_actor_location();phase('idle');return
        if s['phase']=='idle' and now-s['at']>2:
            current=poses(s['mesh']);motion=max((a-b).length() for a,b in zip(current,s['pose']))
            check(motion>.01,'real dog animation changes component-space bone positions');r['idleBoneMotionCm']=motion
            click('Suivre');check(s['dog'].get_editor_property('command')==unreal.AnomaliaDogCommand.FOLLOW,'actual proximity Follow callback reaches native dog')
            check(not s['dog'].request_command(unreal.AnomaliaDogCommand.SIT),'missing sitting animation is rejected honestly')
            s['widget'].call_method('CloseInventory');s.pop('widget',None)
            s['move_start']=s['actor'].get_actor_location();phase('move');return
        if s['phase']=='move':
            if now-s['at']<3:
                s['actor'].add_movement_input(unreal.Vector(1,0,0),1,True);return
            s['actor'].get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately();phase('catch_up');return
        if s['phase']=='catch_up' and now-s['at']>4:
            player_distance=(s['actor'].get_actor_location()-s['move_start']).length()
            dog_distance=(s['dog'].get_actor_location()-s['dog_origin']).length()
            gap=s['dog'].get_distance_to(s['actor'])
            r['follow']={'playerMovedCm':player_distance,'dogMovedCm':dog_distance,'gapCm':gap}
            check(player_distance>300,'real CharacterMovement moves the player')
            check(dog_distance>200 and gap<350,'dog follows actual moving player without teleporting')
            s['widget']=unreal.AnomaliaInventoryWidget.create_for_player_inventory(s['pc']);phase('stay');return
        if s['phase']=='stay' and now-s['at']>1:
            click('Pas bouger');check(s['dog'].get_editor_property('command')==unreal.AnomaliaDogCommand.STAY,'actual proximity Stay callback reaches native dog')
            s['stay_position']=s['dog'].get_actor_location();phase('stay_check');return
        if s['phase']=='stay_check' and now-s['at']>2:
            check((s['dog'].get_actor_location()-s['stay_position']).length()<5,'dog remains stopped')
            unreal.GameplayStatics.apply_damage(s['dog'],10000.0,s['pc'],s['actor'],unreal.DamageType)
            check(s['dog'].get_editor_property('health')==1 and s['dog'].get_editor_property('injured'),'lethal hit injures dog without destroying it')
            require(s['dog'].treat_injury(100),'Trusted recovery hook failed')
            s['widget'].show_inventory_tab();s['shot_file']=OUT/'Dog_inventory.png';phase('capture');return
        if s['phase']=='capture' and now-s['at']>3:
            visuals=dict(s['inv'].get_editor_property('AttachmentVisuals'))
            check(len(visuals)==1,'actual Quantum rifle component attached to backpack')
            r['mountedWeapon']=[{'mesh':v.get_editor_property('static_mesh').get_path_name(),'socket':str(v.get_attach_socket_name())} for v in visuals.values()]
            r['dogBones']=[str(s['mesh'].get_bone_name(i)) for i in range(s['mesh'].get_num_bones())]
            unreal.SystemLibrary.execute_console_command(s['world'],'Shot ShowUI nosuffix filename="'+str(s['shot_file']).replace('\\','/')+'"');phase('capture_file');return
        if s['phase']=='capture_file':
            candidates=list(OUT.glob('Dog_inventory*.png'))
            if not candidates:return
            p=candidates[0]
            if p.stat().st_size<4096 or now-s['at']<4:return
            r['screenshots'].append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
            r['dogStateAtEnd']={'health':s['dog'].get_editor_property('health'),'position':str(s['dog'].get_actor_location())}
            finish()
    except Exception as e:finish(e)
try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    require(not assets.does_asset_exist(MAP),'Existing dog map preserved')
    require(not (Path(unreal.Paths.project_saved_dir())/'Servers'/SCOPE).exists(),'Existing player profile preserved')
    assets.make_directory(FOLDER)
    factory=unreal.BlueprintFactory();factory.set_editor_property('parent_class',unreal.AnomaliaDogCompanion)
    bp=unreal.AssetToolsHelpers.get_asset_tools().create_asset('BP_Anomalia_GermanShepherd',FOLDER,unreal.Blueprint,factory)
    require(bp is not None,'Native companion BP creation failed')
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    dog_class=unreal.EditorAssetLibrary.load_blueprint_class(FOLDER+'/BP_Anomalia_GermanShepherd')
    default=unreal.get_default_object(dog_class)
    default.get_editor_property('mesh').set_editor_property('skeletal_mesh_asset',assets.load_asset('/Game/German_Shepherd_3D_Model/Models/SK_GermanShepherd_01'))
    require(assets.save_loaded_asset(bp,False),'Dog BP not saved')
    require(editor.new_level_from_template(MAP,SOURCE),'Source test map could not be copied through LevelEditorSubsystem')
    world=worlds.get_editor_world()
    starts=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.PlayerStart);require(starts,'No player start')
    location=starts[0].get_actor_location()+unreal.Vector(0,200,30)
    dog=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(dog_class,location)
    require(dog is not None,'Dog actor placement failed');dog.modify();dog.set_editor_property('auto_assign_nearest_survivor',True)
    r['savedOwnershipConfiguration']={'classDefault':default.get_editor_property('auto_assign_nearest_survivor'),'placedInstance':dog.get_editor_property('auto_assign_nearest_survivor')}
    require(not r['savedOwnershipConfiguration']['classDefault'] and r['savedOwnershipConfiguration']['placedInstance'],'Test ownership must serialize as an instance override')
    require(editor.save_current_level(),'Dog test map save failed')
    r['savedBlueprint']=FOLDER+'/BP_Anomalia_GermanShepherd';r['savedMap']=MAP
    del world,starts,dog
    blank=unreal.EditorLoadingAndSavingUtils.new_blank_map(False);blank.get_world_settings().set_editor_property('default_game_mode',unreal.GameModeBase)
    for c in ('DisableAllScreenMessages','r.DynamicGlobalIlluminationMethod 0','r.ReflectionMethod 0','r.Shadow.Virtual.Enable 0','r.Nanite 0','sg.TextureQuality 1','t.MaxFPS 30','t.IdleWhenNotForeground 0'):
        unreal.SystemLibrary.execute_console_command(blank,c)
    editor.editor_request_begin_play();s['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception as e:finish(e)
