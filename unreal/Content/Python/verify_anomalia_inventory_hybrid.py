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
        hidden=list(s['pc'].get_editor_property('hidden_actors'))
        require(hidden==s['previous_hidden'],'Inventory changed another system camera-hidden actors')
        require(not dict(s['widget'].get_editor_property('IconTextures')),'Thumbnail textures not released on close')
        require(s['widget'].get_editor_property('IconCapture') is None and s['widget'].get_editor_property('IconPreviewActor') is None,'Transient preview actors not released')
        report['checks'].append('camera-local hidden actors restored and transient thumbnail resources released')
    save()
    if s.get('handle'): unreal.unregister_slate_post_tick_callback(s.pop('handle'))
    editor.editor_request_end_play()
    s['close_at']=time.monotonic()+3
    def close(delta):
        if not editor.is_in_play_in_editor() and time.monotonic()>s['close_at']:
            unreal.unregister_slate_post_tick_callback(s.pop('close_handle'))
            unreal.SystemLibrary.quit_editor()
    s['close_handle']=unreal.register_slate_post_tick_callback(close)

def relays(): return list(s['widget'].get_editor_property('ActionRelays'))

def click_text(text):
    for relay in relays():
        button=relay.get_editor_property('Button')
        child=button.get_child_at(0)
        if isinstance(child,unreal.TextBlock) and str(child.get_text())==text:
            require(button.get_is_enabled(),'Disabled action '+text);relay.execute();return
    report['availableActionTexts']=[str(r.get_editor_property('Button').get_child_at(0).get_text()) for r in relays() if isinstance(r.get_editor_property('Button').get_child_at(0),unreal.TextBlock)]
    report['inventoryAtFailure']=[{'id':x.stack_id,'item':str(x.item_id),'count':x.count,'container':str(x.container_id)} for x in s['inv'].get_editor_property('stacks')]
    raise RuntimeError('No bound action '+text)

def select(stack_id):
    row=next(x for x in s['inv'].get_editor_property('stacks') if x.stack_id==stack_id)
    full_name={'apple':'Pomme','canned_beans':'Haricots en conserve'}[str(row.item_id)]
    expected=full_name+' ×'+str(row.count)+' ·'
    for relay in relays():
        button=relay.get_editor_property('Button')
        if str(button.get_editor_property('tool_tip_text')).startswith(expected):
            relay.execute();return
    raise RuntimeError('No matching live item tile '+expected)

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
            for item,count in [('apple',4),('water_bottle',1),('canned_beans',1),('hunting_knife',1),('eur_note_50',1)]:
                require(inv.try_add_item(item,count),'Catalog item rejected '+item)
            actor.restore_survival(60,60,100)
            pc=unreal.GameplayStatics.get_player_controller(world,0)
            prior=list(pc.get_editor_property('hidden_actors'));prior.append(gm);pc.set_editor_property('hidden_actors',prior)
            s.update(world=world,actor=actor,inv=inv,pc=pc,previous_camera=pc.get_view_target(),previous_hidden=prior)
            widget=unreal.AnomaliaInventoryWidget.create_for_player_inventory(pc)
            require(widget is not None,'Native widget creation failed');s['widget']=widget
            require(pc.get_view_target().get_class()==unreal.CameraActor.static_class(),'Live character camera not selected')
            require(actor.get_editor_property('jacket_mesh').get_editor_property('skeletal_mesh_asset') is not None,'Real equipped jacket missing')
            report['checks']+=['isolated native profile','real equipped pawn in live camera','actual storage grid widget created']
            s['shots']=[('Inventory_hybrid','inventory'),('Inventory_bank','bank'),('Inventory_crafting','craft')];s['shot_index']=0;phase('capture_prepare');return
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
            click_text('Ranger');require(str(stack('apple').container_id)!='hands','Personal storage target failed')
            click_text('Mains');click_text('Ranger');require(str(stack('apple').container_id)!='hands','Selected stow callback failed')
            require(s['inv'].request_move_stack(stack('canned_beans').stack_id,'pockets',2,2,False),'Rotation fixture placement failed')
            select(stack('canned_beans').stack_id);click_text('Tourner 90°')
            require(stack('canned_beans').rotated,'Rotate callback failed')
            select(stack('apple').stack_id);click_text('Manger')
            require(stack('apple').count==3 and s['actor'].get_editor_property('hunger')>60,'Eat callback failed')
            report['checks']+=['tile selection','split preserves total count','merge preserves total count','move to hands','stow into storage','rotate 1x2 item','consume selected apple with native survival effect']
            report['appleCountAfterUse']=stack('apple').count
            report['inventoryWeightKg']=s['inv'].get_current_weight_kg()
            require(s['inv'].get_editor_property('cash_balance_cents')==5000,'Cash does not reflect physical banknote')
            boxes={str(b.id):b for b in s['inv'].get_editor_property('compartments')}
            for name,capacity in [('worn_top',200),('worn_legs',200),('worn_back',350),('worn_gloves',2),('worn_feet',4)]:
                require(name in boxes and boxes[name].width*boxes[name].height==capacity,'Missing real garment storage '+name)
            select(stack('apple').stack_id);click_text('Ranger : Veste')
            require(str(stack('apple').container_id)=='worn_top','Jacket destination callback failed')
            require(not s['actor'].set_clothing_mesh('Jacket',None),'Occupied garment removed')
            click_text('Ranger : Sac à dos')
            require(str(stack('apple').container_id)=='worn_back','Backpack destination callback failed')
            s['jacket']=s['actor'].get_editor_property('jacket_mesh').get_editor_property('skeletal_mesh_asset')
            require(s['actor'].set_clothing_mesh('Jacket',None),'Empty jacket cannot be removed')
            require(s['actor'].set_clothing_mesh('Jacket',s['jacket']),'Compatible jacket cannot be restored')
            s['bag']=s['actor'].get_editor_property('backpack_mesh').get_editor_property('skeletal_mesh_asset')
            s['actor'].get_editor_property('backpack_mesh').set_editor_property('skeletal_mesh_asset',None)
            phase('recovery');return
        if s['phase']=='recovery' and now-s['at']>2:
            inv=s['inv'];box=next(b for b in inv.get_editor_property('compartments') if str(b.id)=='worn_back')
            require(box.recovery_only,'Missing garment storage must allow withdrawal only')
            require(not inv.request_stow_stack_in(stack('canned_beans').stack_id,'worn_back'),'Deposit into missing garment accepted')
            require(stack('apple').count==3,'Missing mesh lost cargo')
            report['recoverySaveResult']=str(inv.save_inventory_to_player_profile(SCOPE,'local-owner'))
            report['recoveryLoadResult']=str(inv.load_inventory_from_player_profile(SCOPE,'local-owner'))
            box=next(b for b in inv.get_editor_property('compartments') if str(b.id)=='worn_back')
            require(box.recovery_only and stack('apple').count==3,'Recovery-only clothing cargo did not reload')
            s['actor'].get_editor_property('backpack_mesh').set_editor_property('skeletal_mesh_asset',s['bag'])
            report['checks']+=['five real worn storage compartments','jacket and backpack bound destination callbacks','occupied garment removal rejected','empty garment removal and compatible replacement','missing garment recovery-only deposit rejected','recovery-only cargo saved and reloaded without loss','cash derived from physical 50 EUR note']
            s['recipes']=[('cloth_bandage',[('cloth',2)],'bandage','Pansement en tissu'),('rag_rope',[('rags',6)],'rope','Corde en chiffons'),('field_splint',[('wood',2),('rags',4)],'splint','Attelle de fortune'),('saddle',[('fiber',6),('cloth',4)],'saddle','Selle')]
            s['recipe_index']=0;phase('craft');return
        if s['phase']=='craft' and now-s['at']>1:
            recipe,materials,output,label=s['recipes'][s['recipe_index']]
            for item,count in materials: require(s['inv'].try_add_item(item,count),'Craft fixture rejected '+item)
            s['widget'].show_craft_tab()
            before={item:sum(x.count for x in s['inv'].get_editor_property('stacks') if str(x.item_id)==item) for item,_ in materials}
            selected=next((r for r in relays() if str(r.get_editor_property('Button').get_editor_property('tool_tip_text'))=='Fabriquer : '+label),None)
            require(selected is not None,'Missing real crafting callback '+recipe)
            require(selected.get_editor_property('Button').get_is_enabled(),'Craft button incorrectly disabled '+recipe);selected.execute()
            require(stack(output).count>=1,'Craft output missing '+recipe)
            for item,count in materials:
                total=sum(x.count for x in s['inv'].get_editor_property('stacks') if str(x.item_id)==item)
                require(total==before[item]-count,'Craft material mismatch '+recipe)
            report['checks'].append('bound craft transaction '+recipe)
            s['recipe_index']+=1
            if s['recipe_index']<len(s['recipes']): phase('craft')
            else: phase('reject_craft')
            return
        if s['phase']=='reject_craft' and now-s['at']>1:
            require(not s['inv'].request_craft_recipe('unknown_recipe'),'Unapproved recipe accepted')
            report['checks'].append('unknown crafting recipe rejected')
            require(not s['inv'].request_collect_nearby(None),'Null nearby pickup accepted')
            report['checks'].append('invalid vicinity pickup rejected')
            pickups=list(unreal.GameplayStatics.get_all_actors_of_class(s['world'],unreal.AnomaliaLootPickup))
            require(pickups,'Isolated registered loot fixture did not spawn')
            pickup=pickups[0];s['pickup']=pickup
            s['pickup_item']=str(pickup.get_editor_property('item_id'));s['pickup_count']=pickup.get_editor_property('count')
            s['pickup_before']=sum(x.count for x in s['inv'].get_editor_property('stacks') if str(x.item_id)==s['pickup_item'])
            pickup.set_actor_location(s['actor'].get_actor_location()+unreal.Vector(100,0,30),False,True)
            s['widget'].show_inventory_tab();phase('vicinity');return
        if s['phase']=='vicinity' and now-s['at']>1:
            targets=[r for r in relays() if str(r.get_editor_property('Button').get_editor_property('tool_tip_text'))=='Prendre']
            require(targets,'Nearby registered pickup absent from real vicinity column')
            targets[0].execute()
            total=sum(x.count for x in s['inv'].get_editor_property('stacks') if str(x.item_id)==s['pickup_item'])
            require(total==s['pickup_before']+s['pickup_count'],'Vicinity callback failed authoritative pickup transfer')
            report['checks'].append('registered nearby loot listed and collected through real bound vicinity button')
            report['collectedLoot']={'item':s['pickup_item'],'count':s['pickup_count']}
            finish();return
        if s['phase']=='capture_prepare':
            if not report.get('thumbnailReadback'):
                textures=dict(s['widget'].get_editor_property('IconTextures'))
                required=['worn_top','worn_legs','worn_back','worn_gloves','worn_feet','item_apple','item_canned_beans']
                available={str(k):v for k,v in textures.items()}
                require(all(k in available for k in required),'Real mesh thumbnails missing: '+str(list(available)))
                if s['widget'].get_editor_property('IconCaptureCount')<len(required): return
                report['thumbnailReadback']=[]
                for key in required:
                    target=available[key]
                    pixels=unreal.RenderingLibrary.read_render_target(s['world'],target,True)
                    colors={(c.r,c.g,c.b) for c in pixels}
                    require(len(pixels)==256*256 and len(colors)>16,'Empty/flat real-model thumbnail '+key)
                    unreal.RenderingLibrary.export_render_target(s['world'],target,str(OUT),key+'.png')
                    report['thumbnailReadback'].append({'id':key,'pixels':len(pixels),'distinctRGB':len(colors)})
                report['checks'].append('seven actual mesh thumbnails rendered and GPU readback nonempty')
            name,tab=s['shots'][s['shot_index']]
            if tab=='bank': s['widget'].show_bank_tab()
            elif tab=='craft': s['widget'].show_craft_tab()
            else: s['widget'].show_inventory_tab()
            s['shot_file']=OUT/(name+'.png');s['stat']=None;phase('capture_wait');return
        if s['phase']=='capture_wait' and now-s['at']>3:
            unreal.SystemLibrary.execute_console_command(s['world'],'Shot ShowUI nosuffix filename="'+str(s['shot_file']).replace('\\','/')+'"')
            phase('capture_file');return
        if s['phase']=='capture_file':
            require(now-s['at']<30,'UI screenshot did not save')
            p=s['shot_file']
            if not p.exists():
                matches=list(OUT.glob(p.stem+'*.png'))
                if len(matches)==1: p=matches[0]
            if not p.exists() or p.stat().st_size<4096: return
            stat=(p.stat().st_size,p.stat().st_mtime_ns)
            if stat!=s['stat']: s.update(stat=stat,stable_at=now+3);return
            if now<s['stable_at']: return
            report['screenshots'].append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
            s['shot_index']+=1
            if s['shot_index']<len(s['shots']): phase('capture_prepare')
            else:
                s['widget'].show_inventory_tab();report['checks'].append('bank and inventory tabs switch without replacing data');phase('actions')
    except Exception as error: finish(error)

try:
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    require(not (Path(unreal.Paths.project_saved_dir())/'Servers'/SCOPE).exists(),'Existing profile preserved')
    # Private new server scope only: shipped catalogue, one real registered fresh-food spawn.
    fixture=Path(unreal.Paths.project_saved_dir())/'Servers'/SCOPE;fixture.mkdir(parents=True,exist_ok=False)
    tiers=json.loads((Path(unreal.Paths.project_content_dir())/'Anomalia/Data/loot_tiers.json').read_text(encoding='utf-8-sig'))
    tiers['enabled']=True
    tier=next(t for t in tiers['tiers'] if t['tier']==1 and 'food' in t['categories'])
    tier['rarityMultiplier']=1
    (fixture/'loot_tiers.json').write_text(json.dumps(tiers),encoding='utf8')
    catalog=json.loads((Path(unreal.Paths.project_content_dir())/'Anomalia/Data/loot_items_catalog.json').read_text(encoding='utf-8-sig'))
    for item in catalog['items']:
        if item['category']=='fresh_food' and item['id']!='apple': item['enabled']=False
    (fixture/'loot_items_catalog.json').write_text(json.dumps(catalog),encoding='utf8')
    spawn={'schemaVersion':1,'spawns':[{'id':'inventory_vicinity_proof','map':'L_Survival_Playtest','buildingType':tier['buildings'][0],'categories':['fresh_food'],'anchor':'player_start','x':100,'y':0,'z':50}]}
    (fixture/'loot_spawns.json').write_text(json.dumps(spawn),encoding='utf8')
    w=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    w.get_world_settings().set_editor_property('default_game_mode',unreal.GameModeBase.static_class())
    for command in ('DisableAllScreenMessages','r.DynamicGlobalIlluminationMethod 0','r.ReflectionMethod 0','r.Shadow.Virtual.Enable 0','r.Nanite 0','sg.TextureQuality 1','t.MaxFPS 30','t.IdleWhenNotForeground 0'):
        unreal.SystemLibrary.execute_console_command(w,command)
    editor.editor_request_begin_play();s['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception as error: finish(error)


