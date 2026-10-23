"""Validate actual native geography against the placement planner; no Unreal claims."""
import ctypes
import importlib.util
import math
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('population',ROOT/'unreal/Scripts/archipelago_population.py')
population=importlib.util.module_from_spec(spec);spec.loader.exec_module(population)

class PopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        base=Path(cls.tmp.name);source=base/'terrain.cpp';library=base/'terrain.so'
        source.write_text('''#include "World/AnomaliaInhabitedHeight.h"
extern "C" double height(double e,double n){return AnomaliaInhabited::Height(e,n);}
extern "C" double original(double e,double n){return AnomaliaArchipelago::Height(e,n);}
extern "C" int site_count(){return sizeof(AnomaliaInhabited::Sites)/sizeof(AnomaliaInhabited::Sites[0]);}
extern "C" double site(int i,int axis){return AnomaliaInhabited::Sites[i][axis];}
''')
        subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-fPIC','-shared','-I',str(ROOT/'unreal/Source/AnomaliaPrimeval'),str(source),'-o',str(library)],check=True,capture_output=True)
        cls.dll=ctypes.CDLL(str(library))
        for name in ('height','original'):
            fn=getattr(cls.dll,name);fn.argtypes=[ctypes.c_double,ctypes.c_double];fn.restype=ctypes.c_double
        cls.dll.site.argtypes=[ctypes.c_int,ctypes.c_int];cls.dll.site.restype=ctypes.c_double
        cls.sites=[(cls.dll.site(i,0),cls.dll.site(i,1)) for i in range(cls.dll.site_count())]
        cls.plan=population.build_plan(cls.dll.height,[11.056,9.146751,14.67],sites=cls.sites)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_coastline_and_seabed_remain_original(self):
        for n in range(-24000,24001,500):
            for e in range(-24000,24001,500):
                original=self.dll.original(e,n)
                if original<=1:self.assertEqual(self.dll.height(e,n),original)
                self.assertTrue(math.isfinite(self.dll.height(e,n)))

    def test_house_placements_cover_authored_sectors_without_overlap_or_water(self):
        plan=self.plan
        self.assertEqual(len(plan['settlements']),27)
        self.assertGreater(len(plan['buildings']),4500)
        self.assertGreater(len(plan['foliage']),12000)
        self.assertEqual(len({b['id'] for b in plan['buildings']}),len(plan['buildings']))
        for b in plan['buildings']:
            self.assertGreaterEqual(b['groundMin'],5)
            self.assertLessEqual(b['groundMax']-b['groundMin'],.120001)
            self.assertLessEqual(b['z']-b['groundMin'],.020001)
            self.assertAlmostEqual(b['groundMax']-b['z'],.1)
        # All occupied lots use a 50m grid; actual footprints leave >=35m between homes.
        for s in plan['settlements']:
            lots=[b for b in plan['buildings'] if b['id'].startswith(s['id']+'_house_')]
            self.assertEqual(len(lots),s['buildingCount'])
            for i,b in enumerate(lots):
                for c in lots[i+1:]:
                    self.assertTrue(abs(b['east']-c['east'])>=b['width'] or abs(b['north']-c['north'])>=b['depth'])

    def test_vegetation_stays_outside_urban_corridors(self):
        for p in self.plan['foliage']:
            for s in self.plan['settlements']:
                self.assertFalse(abs(p['east']-s['east'])<420 and abs(p['north']-s['north'])<420)

    def test_terrain_envelope_contains_both_possible_cell_diagonals(self):
        step=population.STEP
        # A saddle exposes the difference between a bilinear and triangle surface.
        surface=population.sampled_surface(lambda e,n:10+e*n*.001)
        lo,hi=population.ground_envelope(surface,step*.4,step*.4,step*.5,step*.5)
        z00=10;z10=10;z01=10;z11=(math.floor((10+step*step*.001)*16+.5))/16
        for ix in range(16,65):
            for iy in range(16,65):
                u,v=ix/100,iy/100
                diag1=z00*(1-max(u,v))+z11*min(u,v)+z10*max(0,u-v)+z01*max(0,v-u)
                diag2=z00*max(0,1-u-v)+z11*max(0,u+v-1)+z10*min(u,1-v)+z01*min(v,1-u)
                self.assertLessEqual(lo,min(diag1,diag2)+1e-6)
                self.assertGreaterEqual(hi,max(diag1,diag2)-1e-6)

    def test_invalid_dimensions_and_tolerances_are_rejected(self):
        for dims in ([math.nan,9,14],[.01,9,14],[100,9,14]):
            with self.assertRaises(ValueError):population.build_plan(lambda e,n:10,dims)
        with self.assertRaises(ValueError):population.build_plan(lambda e,n:10,[11,9,14],max_relief=10)

if __name__=='__main__':unittest.main()
