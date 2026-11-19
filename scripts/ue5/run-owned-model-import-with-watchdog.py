"""Bound one owned Editor-Cmd import process; preserve completed sources and original assets."""
import pathlib,os,json,sys,time,subprocess,hashlib

ACCEPTED={'IMPORTED_SAVED_RELOADED_NOT_GAMEPLAY_ACCEPTED','RESUMED_IMPORTED_SAVED_RELOADED_NOT_GAMEPLAY_ACCEPTED'}
def pending_status(manifest,report):
    complete={r['sha256'] for r in report.get('sources',[]) if r.get('state') in ACCEPTED}
    failed={r['sha256'] for r in report.get('errors',[]) if r.get('sha256')}
    pending={r['sha256'] for r in manifest['imports']}-complete-failed
    return complete,failed,pending
def retain_timeout(manifest,report,active):
    if not active or active.get('state')!='IMPORTING_SOURCE' or not active.get('sha256'):
        raise ValueError('No identified source; never mark an unknown model failed')
    candidates={r['sha256']:r for r in manifest['imports']}
    row=candidates.get(active['sha256'])
    if not row or row.get('preparedSHA256')!=active.get('preparedSHA256'):
        raise ValueError('Active source identity differs from durable manifest')
    complete,failed,pending=pending_status(manifest,report)
    if row['sha256'] in complete:return report
    if row['sha256'] not in failed:
        report.setdefault('errors',[]).append({'source':row['source'],'sha256':row['sha256'],'family':row['family'],'preparedSHA256':row['preparedSHA256'],'assets':[], 'state':'IMPORT_TIME_LIMIT_OR_DISK_PRESSURE_ORIGINAL_PRESERVED','error':'Owned importer stopped at its measured resource/time limit; source requires review','partialDestination':active.get('destination'),'originalDeleted':False})
    complete,failed,pending=pending_status(manifest,report)
    report.update(state='PAUSED_SOURCE_PRESERVED_OTHER_IMPORTS_MAY_CONTINUE',completedSourceCount=len(complete),failedSourceCount=len(failed),remainingSources=len(pending),gameplayAccepted=False)
    return report
def write_atomic(path,value):
    temp=path.with_suffix('.watchdog.tmp');temp.write_text(json.dumps(value,indent=2),encoding='utf-8');os.replace(temp,path)
def main():
    if os.name!='nt':raise RuntimeError('Actual Windows runner required')
    project=pathlib.Path(r'D:\ANOMALIA\unreal');state=project/'Saved/ImportReceipts/RawResume20261107'
    out=pathlib.Path(os.environ['MISSION_RAW_OUT']);out.mkdir(parents=True,exist_ok=True)
    receipt=state/'raw-import-report.json';manifest_path=state/'raw-preparation-manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'));report=json.loads(receipt.read_text(encoding='utf-8'))
    complete,failed,pending=pending_status(manifest,report)
    if not pending:
        summary={'newSources':0,'newAssets':0,'errors':[],'completedSourcesTotal':len(complete),'failedSourceCount':len(failed),'remainingSources':0,'state':'NO_PENDING_SOURCES_EDITOR_NOT_STARTED','gameplayAccepted':False}
        write_atomic(out/'import-batch-summary.json',summary);print(json.dumps(summary),flush=True);return 0
    editor=pathlib.Path(r'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe')
    script=pathlib.Path(sys.argv[1]);assert script.is_file() and editor.is_file()
    command=[str(editor),str(project/'AnomaliaPrimeval.uproject'),'-run=pythonscript','-script='+str(script),'-unattended','-nopause','-nosound','-NullRHI','-abslog='+str(out/'engine.log')]
    marker=out/'active-source.json';started=time.monotonic();reason=None;identified=None
    with (out/'native-process.log').open('wb') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
        while child.poll() is None:
            active=None
            if marker.is_file():
                try:active=json.loads(marker.read_text(encoding='utf-8'))
                except (ValueError,OSError):pass
            if active and active.get('state')=='IMPORTING_SOURCE' and time.time()-active.get('startedUTC',time.time())>20*60:
                reason='SOURCE_EXCEEDED_20_MINUTES';identified=active
            elif time.monotonic()-started>55*60:
                reason='OWNED_EDITOR_PROCESS_TOTAL_TIME_LIMIT';identified=active if active and active.get('state')=='IMPORTING_SOURCE' else None
            if reason:
                if reason=='SOURCE_EXCEEDED_20_MINUTES':
                    try:confirmed=json.loads(marker.read_text(encoding='utf-8'))
                    except (ValueError,OSError):confirmed=None
                    if not confirmed or confirmed.get('state')!='IMPORTING_SOURCE' or confirmed.get('sha256')!=identified.get('sha256'):
                        reason=None;identified=None;continue
                # Kill only the process tree created here, never a user editor or another job.
                subprocess.run(['taskkill.exe','/PID',str(child.pid),'/T','/F'],capture_output=True,check=False)
                child.wait(timeout=60);break
            time.sleep(5)
    result={'ownedEditorPID':child.pid,'exitCode':child.returncode,'stopReason':reason,'originalAssetsDeleted':False}
    if reason and identified:
        # The child has exited: it cannot race this durable receipt update.
        latest=json.loads(receipt.read_text(encoding='utf-8'))
        latest=retain_timeout(json.loads(manifest_path.read_text(encoding='utf-8')),latest,identified)
        write_atomic(receipt,latest)
        summary_path=out/'import-batch-summary.json'
        summary=json.loads(summary_path.read_text(encoding='utf-8')) if summary_path.is_file() else {'newSources':0,'newAssets':0,'errors':[]}
        completed_now,_,_=pending_status(json.loads(manifest_path.read_text(encoding='utf-8')),latest)
        if identified['sha256'] not in completed_now:summary.setdefault('errors',[]).append({'source':identified.get('source'),'reason':reason,'state':'PRESERVED_FOR_REVIEW'})
        summary.update(completedSourcesTotal=latest['completedSourceCount'],failedSourceCount=latest['failedSourceCount'],remainingSources=latest['remainingSources'],watchdogStoppedOwnedProcess=True,gameplayAccepted=False)
        write_atomic(summary_path,summary)
        result['sourceRecordedForReview']=True
    write_atomic(out/'owned-import-process.json',result);print('OWNED_IMPORT_PROCESS '+json.dumps(result),flush=True)
    return 0 if reason and identified else (child.returncode or 0)
if __name__=='__main__':sys.exit(main())
