import importlib.util,unittest
from pathlib import Path

path=Path(__file__).resolve().parents[1]/'unreal/Scripts/urban_greenery.py'
spec=importlib.util.spec_from_file_location('green',path);G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)

class PlantingTests(unittest.TestCase):
    def setUp(self):
        self.site=dict(id='settlement_0_0',east=0,north=0)
        self.population=dict(mapPackage='/Game/Maps/ANOMALIA_Inhabited_v2',settlements=[self.site],buildings=[dict(id=f'settlement_0_0_house_{x}_{y}',east=x*50+25,north=y*50+25) for x in range(-4,4) for y in range(-4,4)])
        self.desc=[dict(label='house_'+str(i),nativeClass='/Script/Engine.StaticMeshActor',boundsValid=True,boundsMinCm=[(h['east']-11)*100,(-h['north']-11)*100,0],boundsMaxCm=[(h['east']+11)*100,(-h['north']+11)*100,900]) for i,h in enumerate(self.population['buildings'])]
        self.models={key:dict(origin=[0,0,400],extent=[250,250,400]) for key in ('island_tree_02','grass_medium_01')}
    def plan(self,**kw):
        return G.plan_greenery(self.population,kw.get('desc',self.desc),self.models,lambda e,n:(10,0),kw.get('envelope',lambda *args:(10,10)))
    def test_deterministic_full_crown_clears_buildings_and_streets(self):
        first=self.plan();self.assertEqual(first,self.plan());self.assertGreater(first['counts']['island_tree_02'],5)
        boxes=G.boxes_from_descriptors(self.desc)
        for cluster in first['clusters']:
            for i in cluster['instances']:
                self.assertTrue(G.clear_circle(i['east'],i['north'],i['crownRadiusMeters'],boxes))
                self.assertTrue(G.street_clear(i['east'],i['north'],i['crownRadiusMeters'],self.site))
                self.assertAlmostEqual(i['locationCm'][2],996,places=6)
    def test_water_and_steep_ground_are_not_hidden_by_placement(self):
        self.assertFalse(self.plan(envelope=lambda *args:(-1,0))['clusters'])
        self.assertFalse(self.plan(envelope=lambda *args:(10,12))['clusters'])
    def test_unknown_user_structure_is_reserved(self):
        extra=dict(label='MyBuilding',nativeClass='/Script/MyProject.CustomBuilding',boundsValid=True,boundsMinCm=[-50000,-50000,0],boundsMaxCm=[50000,50000,1000])
        self.assertFalse(self.plan(desc=self.desc+[extra])['clusters'])
    def test_bad_structure_bounds_refused_and_landscape_ignored(self):
        bad=dict(self.desc[0],boundsValid=False)
        with self.assertRaisesRegex(ValueError,'structure bounds'):self.plan(desc=[bad])
        landscape=dict(label='Land',nativeClass='/Script/Landscape.Landscape',boundsValid=False)
        self.assertEqual(self.plan(),self.plan(desc=self.desc+[landscape]))

if __name__=='__main__':unittest.main()
