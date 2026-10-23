"""Release task Python/UObject globals before the editor interpreter shuts down."""
import gc
import os
from pathlib import Path
import runpy
import unreal

def run_task():
    project = Path(unreal.Paths.project_dir()).resolve()
    task = Path(os.environ['ANOMALIA_EDITOR_TASK']).resolve()
    permitted = [project / 'Scripts', project.parent / 'scripts/world-features']
    if not any(task.is_relative_to(root.resolve()) for root in permitted):
        raise RuntimeError('Editor task must belong to the project')
    namespace = None
    try:
        namespace = runpy.run_path(str(task), run_name='__main__')
    finally:
        if namespace is not None:
            namespace.clear()
        gc.collect()
        unreal.log('ANOMALIA editor task globals released before interpreter shutdown')

run_task()
