"""Compile separately, then require native rig import and observable actual Chaos driving."""
import argparse,json,os,subprocess,uuid,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--record-driving',action='store_true',help='Opt-in continuous viewport recording; can significantly slow rendering')
    p.add_argument('--sedan',action='store_true',help='Use the separately imported original sedan art and authored wheel hubs')
    p.add_argument('--force-suspension',action='store_true',help='Isolated diagnostic: compare native force-based suspension without changing project configuration')
    p.add_argument("--e39",action="store_true",help="Same E39 variant with real driver leaf and required native door checks")
    args=p.parse_args()
    if args.e39 and args.sedan:p.error("Select a single art variant")
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env['ANOMALIA_CHAOS_OUTPUT']=str(out)
    env['ANOMALIA_CHAOS_USE_SEDAN']='1' if args.sedan else '0'
    env['ANOMALIA_CHAOS_USE_E39']='1' if args.e39 else '0'
    project=ROOT/'unreal/AnomaliaZPrigimalia.uproject'
    exe=args.engine_root/'Engine/Binaries/Win64/UnrealEditor.exe'
    def run(name,arguments,timeout):
        with (out/(name+'-process.log')).open('w',encoding='utf-8') as log:
            result=subprocess.run([str(exe),str(project),*arguments,'-unattended','-nopause','-nosound','-nosplash',
                '-abslog='+str(out/(name+'.log'))],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,check=False)
        if result.returncode:raise RuntimeError(name+' Unreal process failed: '+str(result.returncode))
    run('rig-import',['-ExecutePythonScript='+str(ROOT/'unreal/Scripts/create_chaos_road_review.py'),'-NullRHI'],900)
    report=json.loads((out/'rig-import-report.json').read_text(encoding='utf-8-sig'))
    if report['state']!='REAL_SKELETAL_CHAOS_REVIEW_MAP_SAVED_NOT_DRIVEN' or report['sourceCommit']!=env.get('GITHUB_SHA'):
        raise RuntimeError('Native real rig import not verified: '+str(report.get('error')))
    scope='chaos-smoke-'+uuid.uuid4().hex
    # Continuous GPU readback + PNG compression stalls this validation host.
    # Run the unchanged physical acceptance gates without that observer overhead.
    # Phase/final screenshots are still captured by the probe. Recording is an
    # explicit additional run, not a condition for proving actual wheel physics.
    capture=['-AnomaliaRecordDriving'] if args.record_driving else []
    suspension=(['-ini:Engine:[ConsoleVariables]:p.Vehicle.DisableConstraintSuspension=1',
        '-AnomaliaForceSuspensionReview'] if args.force_suspension else [])
    run('drive',[report['map']+'?AnomaliaServerId='+scope,'-game','-d3d11','-sm5','-windowed','-ResX=1280','-ResY=720',
        '-AnomaliaChaosProbe='+str(out/'drive-report.json'),*capture,*suspension],900)
    drive=json.loads((out/'drive-report.json').read_text(encoding='utf-8-sig'))
    if drive['state']!='CHAOS_ROAD_PHYSICS_DRIVE_PASSED' or len(drive['physicsSamples'])<30:
        raise RuntimeError('Actual Chaos driving failed: '+str(drive.get('error')))
    required={
        'unoccupied_chassis_stable_for_20_seconds_with_fixed_async_physics',
        'settled_spring_forces_balance_actual_chassis_weight',
        'rear_wheel_drive_observed_in_actual_wheel_torques',
        'measured_dry_braking_from_50_kmh',
        'measured_dry_braking_from_80_kmh',
        'lower_grip_increases_actual_80_kmh_stopping_distance',
        'engine_off_blocks_full_accelerator_without_fuel_consumption',
        'current_driver_can_start_engine_on_server',
        'current_driver_can_switch_engine_off',
        'refuel_requires_explicit_driver_restart_after_stall',
        'high_speed_exit_restores_original_survivor_with_vehicle_momentum',
        'manual_first_gear_drives_physical_vehicle',
        'manual_upshift_changes_actual_Chaos_gear',
        'rear_wheel_handbrake_stops_physical_vehicle',
        'driver_activates_real_headlight_components',
        'hazard_light_components_flash_on_and_off',
        'server_fuel_consumption_reaches_zero_and_cuts_Chaos_throttle',
        'empty_tank_cannot_accelerate_under_full_driver_input',
        'server_refuel_rejects_invalid_amounts_and_restores_fuel',
        'refuel_restores_physical_acceleration_and_fuel_consumption',
        'safe_exit_restores_same_survivor',
    }
    if drive.get('buildCommit')!=env.get('GITHUB_SHA') or not required.issubset(drive.get('checks',[])):
        raise RuntimeError('Current native build must pass depletion/refuel and driver safety checks')
    if len(drive.get('brakingMeasurements',[]))!=3:
        raise RuntimeError('Three measured physical braking runs are required')
    if args.sedan or args.e39:
        panels={'separate_licensed_driver_door_mesh_installed','closed_driver_door_has_actual_collision',
            'closed_driver_door_recomposes_original_body_bounds','current_driver_opens_and_closes_real_door_from_seat',
            'locked_driver_door_rejects_server_interaction','driver_door_rotates_at_hinge_and_collision_leaves_aperture',
            'driver_door_closes_and_restores_actual_collision'}
        if not drive.get('driverDoorReviewed') or not panels.issubset(drive.get('checks',[])):
            raise RuntimeError('Selected sedan requires a real animated driver door and moving collision')
    if args.e39:
        survival={'hood_open_inventory_radiator_and_spark_plug_removal_blocks_real_ignition','trunk_open_inventory_battery_and_journaled_cargo_exchange_verified','matching_physical_key_locks_actual_panels_and_closed_boot_blocks_cargo'}
        if not survival.issubset(drive.get('checks',[])):raise RuntimeError('Real E39 key, removable parts and cargo exchanges must pass')
        if 'survivor_walks_into_closed_trunk_without_launching_chassis' not in drive.get('checks',[]):
            raise RuntimeError('Real character walking must remain blocked without launching the chassis')
        expected={'door_front_right','door_rear_left','door_rear_right','hood','trunk'}
        placements={'panel_'+panel+'_fixture_settled_with_character_collision_before_opening' for panel in expected}
        placements.add('driver_fixture_settled_with_character_collision_before_opening')
        if not placements.issubset(drive.get('checks',[])):
            raise RuntimeError('Every panel fixture must settle with character collision active before opening')
        if set(drive.get('validatedAdditionalPanelIds',[]))!=expected:
            raise RuntimeError('All five additional E39 panels must pass real moving-collision checks')
    if not drive.get('stationaryReviewed') or not drive.get('asyncPhysics') or abs(drive.get('asyncFixedTimeStepSize',0)-1/120)>1e-6:
        raise RuntimeError('Stationary acceptance requires real fixed-cadence asynchronous physics')
    if drive.get('constraintSuspensionDisabled')!=1:
        raise RuntimeError('Calibrated force-based suspension was not active in the actual game')
    video=None;video_error=None
    encoder=shutil.which('ffmpeg')
    if encoder and drive.get('recordedViewportFrames',0)>=10:
        result=subprocess.run([encoder,'-y','-framerate','5','-i',str(out/'frames/frame-%05d.png'),
            '-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'actual-chaos-driving.mp4')],
            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=120,check=False)
        if result.returncode==0:video=str(out/'actual-chaos-driving.mp4')
        else:video_error='Installed video encoder failed; actual viewport frames retained'
    else:video_error=('Continuous recording disabled for physics acceptance; actual phase screenshots retained' if not args.record_driving
        else 'No installed ffmpeg encoder or insufficient actual viewport frames')
    (out/'review-report.json').write_text(json.dumps(dict(state='CHAOS_EDITOR_GAME_PHYSICAL_DRIVE_VERIFIED',
        diagnosticOnly=args.force_suspension,
        constraintSuspensionDisabled=drive.get('constraintSuspensionDisabled'),
        video=video,videoError=video_error,
        sourceCommit=env.get('GITHUB_SHA'),profileScope=scope,packagedGameTested=False,
        installed=False,multiplayerTested=False,productionMapModified=False,
        originalSedanArt=args.sedan,e39Candidate=args.e39,entryAnimationTested=False,openingDoorsTested=drive.get('driverDoorReviewed',False)),indent=2)+'\n')

if __name__=='__main__':main()
