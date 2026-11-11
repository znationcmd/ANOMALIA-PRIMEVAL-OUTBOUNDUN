"""Camera regression: test real capture angles using UE Python's roll/pitch/yaw ABI.
This exercises direction math without claiming a native GPU/editor test.
"""
import ast
import math
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Rotator:
    def __init__(self, roll=0, pitch=0, yaw=0):
        self.roll, self.pitch, self.yaw = roll, pitch, yaw
    def get_forward_vector(self):
        p, y = math.radians(self.pitch), math.radians(self.yaw)
        return SimpleNamespace(x=math.cos(p)*math.cos(y), y=math.cos(p)*math.sin(y), z=math.sin(p))

class CameraTests(unittest.TestCase):
    def test_all_capture_targets_are_on_camera_axis(self):
        source = ast.parse((ROOT/'unreal/Scripts/capture_real_world.py').read_text())
        views = ast.literal_eval(next(n.value for n in source.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id=='views' for t in n.targets)))
        fn = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name=='set_view')
        class Editor:
            def set_level_viewport_camera_info(self, eye, rotation):
                self.eye, self.rotation = eye, rotation
            def get_level_viewport_camera_info(self):
                return self.eye, self.rotation
        editor = Editor()
        unreal = SimpleNamespace(Rotator=Rotator, Vector=lambda x,y,z:SimpleNamespace(x=x,y=y,z=z), get_editor_subsystem=lambda _:editor, UnrealEditorSubsystem=None)
        env = dict(math=math, unreal=unreal, views=views, state={'index':0}, report={})
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<capture-camera>', 'exec'), env)
        for i, (name, eye, target) in enumerate(views):
            with self.subTest(view=name):
                env['state']['index']=i
                env['set_view']()
                self.assertEqual(editor.rotation.roll, 0)
                forward=editor.rotation.get_forward_vector()
                distance=math.dist(eye,target)
                projected=[eye[j]+distance*v for j,v in enumerate((forward.x,forward.y,forward.z))]
                self.assertLess(math.dist(projected,target), 1e-6)

if __name__ == '__main__':
    unittest.main()
