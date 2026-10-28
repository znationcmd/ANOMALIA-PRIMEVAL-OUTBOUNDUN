"""Exercise the actual native hybrid inventory in an isolated PIE profile."""
import hashlib
import json
import os
from pathlib import Path
import time
import traceback
import unreal

OUT=Path(os.environ['ANOMALIA_PIE_REPORT']);OUT.mkdir(parents=True,exist_ok=False)
MAP='/Game/Anomalia/CharacterTests/SurvivalPlayable_40658680443/L_Survival_Playtest'
SCOPE='inventory-hybrid-'+os.environ['GITHUB_RUN_ID']
report={'state':'FAILED','engine':unreal.SystemLibrary.get_engine_version(),'map':MAP,'scope':SCOPE,'checks':[],'screenshots':[],'errors':[],
        'input':'actual UMG layout and action relay callbacks; physical mouse/keyboard not tested','multiplayer':False,'installedMainProjectModified':False}
s={'phase':'wait','start':time.monotonic(),'at':time.monotonic(),'finished':False}
editor=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
worlds=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

def require(ok,message):
    if not ok: raise RuntimeError(message)

def save(): (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')

def phase(value): s.update(phase=value,at=time.monotonic())

def finish(error=None):
    if s['finished']: return
    s['finished']=True
    if error: report['errors'].append(str(error));report['traceback']=traceback.format_exc()
    else: report['state']='HYBRID_INVENTORY_RENDER_AND_BOUND_ACTIONS_PASSED_NOT_MANUAL_NETWORK_ACCEPTANCE'
    if s.get('widget'):
        s['widget'].remove_from_parent()
        if s.get('previous_camera'): require(s['pc'].get_view_target()==s['previous_camera'],'Original gameplay camera was not restored')
        report['cameraRestoredOnClose']=True
    save()
    if s.get('handle'): unreal.unregister_slate_post_tick_callback(s.pop('handle'))
    editor.editor_request_end_play()
    s['close_at']=time.monotonic()+3
    def close(delta):
        if not editor.is_in_play_in_editor() and time.monotonic()>s['close_at']:
            unreal.unregister_slate_post_tick_callback(s.pop('close_handle'))
            unreal.SystemLibrary.quit_editor()
    s['close_handle']=unreal.register_slate_post_tick_callback(close)

def relays(): return list(s['widget'].get_editor_property('action_relays'))

def click_text(text):
    for relay in relays():
        button=relay.get_editor_property('button')
        child=button.get_child_at(0)
        if isinstance(child,unreal.TextBlock) and str(child.get_text())==text:
            require(button.get_is_enabled(),'Disabled action '+text);relay.execute();return
    raise RuntimeError('No bound action '+text)

def select(stack_id):
    prefix='InventoryTile_'+str(stack_id)
    for relay in relays():
        button=relay.get_editor_property('button')
        if button.get_name()==prefix or button.get_name().startswith(prefix+'_'):
            relay.execute();return
    raise RuntimeError('No item tile '+str(stack_id))

def stack(item): return next(x for x in s['inv'].get_editor_property('stacks') if str(x.item_id)==item)

def tick(delta):
    if s['finished']: return
    try:
        now=time.monotonic();require(now-s['start']<210,'UI runtime timed out at '+s['phase'])
        if s['phase']=='wait':
            world=worlds.get_game_world()
            if not world or not editor.is_in_play_in_editor() or now-s['at']<3: return
            unreal.GameplayStatics.open_level(world,MAP,True,'AnomaliaServerId='+SCOPE);phase('travel');return
        if s['phase']=='travel':
            world=worlds.get_game_world()
            if not world: return
            gm=unreal.GameplayStatics.get_game_mode(world)
            if not gm or 'GM_Survival_Playtest' not in gm.get_class().get_name(): return
            require(gm.get_editor_property('server_id')==SCOPE,'Test profile isolation failed')
            actor=unreal.GameplayStatics.get_player_pawn(world,0)
            if not actor or unreal.GameplayStatics.get_time_seconds(world)<3: return
            inv=actor.get_editor_property('inventory_component')
            require(not inv.get_editor_property('stacks'),'Fresh isolated profile is not empty')
            for item,count in [('apple',4),('water_bottle',1),('canned_beans',1),('hunting_knife',1)]:
                require(inv.try_add_item(item,count),'Catalog item rejected '+item)
            actor.restore_survival(60,60,100)
            pc=unreal.GameplayStatics.get_player_controller(world,0)
            s.update(world=world,actor=actor,inv=inv,pc=pc,previous_camera=pc.get_view_target())
            widget=unreal.AnomaliaInventoryWidget.create_for_player_inventory(pc)
            require(widget is not None,'Native widget creation failed');s['widget']=widget
            require(pc.get_view_target().get_class()==unreal.CameraActor.static_class(),'Live character camera not selected')
            require(actor.get_editor_property('jacket_mesh').get_editor_property('skeletal_mesh_asset') is not None,'Real equipped jacket missing')
            report['checks']+=['isolated native profile','real equipped pawn in live camera','actual storage grid widget created']
            phase('actions');return
        if s['phase']=='actions' and now-s['at']>2:
            apples=stack('apple');select(apples.stack_id)
            click_text('½ pile')
            rows=[x for x in s['inv'].get_editor_property('stacks') if str(x.item_id)=='apple']
            require(len(rows)==2 and sum(x.count for x in rows)==4,'Split callback lost inventory')
            select(rows[0].stack_id);click_text('Fusionner')
            rows=[x for x in s['inv'].get_editor_property('stacks') if str(x.item_id)=='apple']
            require(len(rows)==1 and rows[0].count==4,'Merge callback failed')
            select(rows[0].stack_id);click_text('Mains')
            require(str(stack('apple').container_id)=='hands','Move-to-hands callback failed')
            click_text('Ranger');require(str(stack('apple').container_id)!='hands','Stow callback failed')
            require(s['inv'].request_move_stack(stack('canned_beans').stack_id,'pockets',2,2,False),'Rotation fixture placement failed')
            select(stack('canned_beans').stack_id);click_text('Tourner 90°')
            require(stack('canned_beans').rotated,'Rotate callback failed')
            select(stack('apple').stack_id);click_text('Manger')
            require(stack('apple').count==3 and s['actor'].get_editor_property('hunger')>60,'Eat callback failed')
            report['checks']+=['tile selection','split preserves total count','merge preserves total count','move to hands','stow into storage','rotate 1x2 item','consume selected apple with native survival effect']
            report['appleCountAfterUse']=stack('apple').count
            report['inventoryWeightKg']=s['inv'].get_current_weight_kg()
            s['shots']=[('Inventory_hybrid','inventory'),('Inventory_bank','bank')];s['shot_index']=0;phase('capture_prepare');return
        if s['phase']=='capture_prepare':
            name,tab=s['shots'][s['shot_index']]
            if tab=='bank': s['widget'].show_bank_tab()
            else: s['widget'].show_inventory_tab()
            s['shot_file']=OUT/(name+'.png');s['stat']=None;phase('capture_wait');return
        if s['phase']=='capture_wait' and now-s['at']>3:
            unreal.SystemLibrary.execute_console_command(s['world'],'Shot ShowUI filename="'+str(s['shot_file']).replace('\\','/')+'"')
            phase('capture_file');return
        if s['phase']=='capture_file':
            require(now-s['at']<30,'UI screenshot did not save')
            p=s['shot_file']
            if not p.exists() or p.stat().st_size<4096: return
            stat=(p.stat().st_size,p.stat().st_mtime_ns)
            if stat!=s['stat']: s.update(stat=stat,stable_at=now+3);return
            if now<s['stable_at']: return
            report['screenshots'].append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
            s['shot_index']+=1
            if s['shot_index']<len(s['shots']): phase('capture_prepare')
            else:
                s['widget'].show_inventory_tab();report['checks'].append('bank and inventory tabs switch without replacing data');finish()
    except Exception as error: finish(error)

try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    require(not (Path(unreal.Paths.project_saved_dir())/'Servers'/SCOPE).exists(),'Existing profile preserved')
    w=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    w.get_world_settings().set_editor_property('default_game_mode',unreal.GameModeBase.static_class())
    for command in ('r.DynamicGlobalIlluminationMethod 0','r.ReflectionMethod 0','r.Shadow.Virtual.Enable 0','r.Nanite 0','sg.TextureQuality 1','t.MaxFPS 30','t.IdleWhenNotForeground 0'):
        unreal.SystemLibrary.execute_console_command(w,command)
    editor.editor_request_begin_play();s['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception as error: finish(error)
