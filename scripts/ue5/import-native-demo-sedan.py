"""Wait for the real Unreal import process before validating its evidence."""
import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--engine-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument("--e39",action="store_true")
    args=parser.parse_args()
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env['ANOMALIA_SEDAN_OUTPUT']=str(output)
    env['ANOMALIA_SEDAN_USE_E39']='1' if args.e39 else '0'
    editor=args.engine_root/'Engine/Binaries/Win64/UnrealEditor.exe'
    with (output/'import-process.log').open('w',encoding='utf-8') as log:
        result=subprocess.run([str(editor),str(ROOT/'unreal/AnomaliaPrimeval.uproject'),
            '-ExecutePythonScript='+str(ROOT/'unreal/Scripts/import_native_demo_sedan.py'),
            '-NullRHI','-unattended','-nopause','-nosound','-nosplash',
            '-abslog='+str(output/'import.log')],env=env,stdout=log,stderr=subprocess.STDOUT,
            timeout=900,check=False)
    if result.returncode:raise RuntimeError('Unreal sedan import process failed: '+str(result.returncode))
    report=json.loads((output/'sedan-import-report.json').read_text(encoding='utf-8-sig'))
    if (report['state']!=('E39_STATIC_PARTS_IMPORTED_NOT_DRIVEN' if args.e39 else 'CC0_SEDAN_STATIC_PARTS_IMPORTED_NOT_DRIVEN') or
        report['sourceCommit']!=env.get('GITHUB_SHA') or len(report['models'])!=(5 if args.e39 else 6)):
        raise RuntimeError('Real sedan part import not verified: '+str(report.get('error')))
    print('E39 static parts imported; doors and gameplay remain unverified.' if args.e39 else 'Six CC0 sedan parts imported, including separate driver door; gameplay remains unverified.')

if __name__=='__main__':main()
