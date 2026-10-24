import copy,importlib.util,unittest
from pathlib import Path
from types import SimpleNamespace

path=Path(__file__).resolve().parents[1]/'unreal/Scripts/residential_audit.py'
spec=importlib.util.spec_from_file_location('audit',path);audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.items={str(i):dict(id=str(i),east=0,north=0,z=10,yaw=0) for i in range(4001)}
        self.models={'scan':dict(objectPath='/Game/Scan',sha256='scan')}
        self.original=dict(objectPath='/Game/Old',sha256='old')
        self.native=dict(state='NATIVE_RESIDENTIAL_VALUES_COPIED',packagesSaved=False,terrainModified=False,houseCount=4001,
            meshes=[dict(path='/Game/Scan.Scan',sourceSha='scan',materialsReady=True,origin=[0,0,0],extent=[1,1,1]),dict(path='/Game/Old.Old',originalSha='old'),dict(path='/Game/Unused.Unused')],
            actors=[dict(label=str(i),tags=['ANOMALIA_Inhabited_v1','ANOMALIA_ResidentialUpgrade_v1'],materialOverrides=False,mesh='/Game/Scan.Scan',location=[0,0,1000],scale=[1,1,1],yaw=0) for i in range(4001)])
        self.layout=SimpleNamespace(model_for=lambda _: 'scan',placement=lambda *args:dict(locationCm=[0,0,1000],scale=1,yaw=0))
    def verify(self):return audit.verify(self.native,self.items,self.models,self.original,self.layout,None,None)
    def test_all_saved_values_must_match(self):
        self.assertEqual(self.verify(),dict(upgraded=4001,originalsRetained=0))
        self.native['actors'][4]['location'][2]=1002
        with self.assertRaisesRegex(ValueError,'transform mismatch'):self.verify()
    def test_duplicate_actor_cannot_hide_missing_house(self):
        self.native['actors'][-1]=copy.deepcopy(self.native['actors'][0])
        with self.assertRaisesRegex(ValueError,'identities'):self.verify()
    def test_authorship_and_material_changes_refused(self):
        self.native['actors'][0]['materialOverrides']=True
        with self.assertRaisesRegex(ValueError,'Ownership or material'):self.verify()
    def test_modified_source_sha_refused(self):
        self.native['meshes'][0]['sourceSha']='wrong'
        with self.assertRaisesRegex(ValueError,'metadata'):self.verify()
    def test_saved_flag_and_nonfinite_values_cannot_pass(self):
        self.native['packagesSaved']=True
        with self.assertRaisesRegex(ValueError,'author'):self.verify()
        self.native['packagesSaved']=False;self.native['actors'][0]['scale'][0]=float('nan')
        with self.assertRaisesRegex(ValueError,'transform'):self.verify()

if __name__=='__main__':unittest.main()
