"""Run a real native PIE automation test; source checks never count as gameplay."""
import argparse,json,subprocess,uuid
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--engine-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[2];a.output.mkdir(parents=True,exist_ok=True)
export=(a.output/('world-pie-'+uuid.uuid4().hex)).resolve();export.mkdir()
report=dict(state='FAILED',mode='Play In Editor',headless=True,renderingValidated=False,multiplayerTested=False,automationReport=str(export))
try:
 command=[str(a.engine_root/'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'),str(root/'unreal/AnomaliaZPrigimalia.uproject'),'-unattended','-nopause','-nosound','-NullRHI','-ExecCmds=Automation RunTests Anomalia.World.ArchipelagoPIE; Quit',f'-ReportExportPath={export}',f'-abslog={export/"editor.log"}']
 with (export/'process.log').open('w',encoding='utf-8') as log:
  run=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=600,check=False)
 report['exitCode']=run.returncode
 data=json.loads((export/'index.json').read_text(encoding='utf-8-sig'))
 rows=data.get('tests',[])
 if run.returncode or len(rows)!=1 or rows[0].get('fullTestPath')!='Anomalia.World.ArchipelagoPIE' or rows[0].get('state')!='Success':raise RuntimeError('Native PIE test missing, incomplete or failed')
 report.update(state='TESTED_IN_EDITOR_HEADLESS',checks=['load_real_map','start_PIE','spawn_native_character','stand_on_landscape_collision','walk_on_terrain','inventory_add_remove','bridge_streaming_collision','continuous_roads_and_bridge_crossing_3490m','all_50_spans_in_sequence'])
except Exception as error:
 report['error']=str(error)
finally:
 (a.output/'world-pie-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report,indent=2))
raise SystemExit(0 if report['state']=='TESTED_IN_EDITOR_HEADLESS' else 1)
