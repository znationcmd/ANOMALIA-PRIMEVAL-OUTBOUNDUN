import importlib.util
import math
from pathlib import Path
import unittest
import ctypes
import re
import shutil
import subprocess
import tempfile

PATH=Path(__file__).resolve().parents[1]/'unreal/Scripts/residential_replacement.py'
SPEC=importlib.util.spec_from_file_location('replacement',PATH)
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)

class ReplacementTests(unittest.TestCase):
 def item(self,i=0,yaw=0):return dict(id=f'settlement_0_0_house_{i}',east=25.,north=75.,yaw=yaw)
 def place(self,item,origin=(300.,-200.,400.),extent=(1200.,1700.,800.),limits=(20.,20.05)):
  return M.placement(item,origin,extent,None,lambda *args:limits)
 def test_every_variant_fits_its_parcel_with_uniform_scale_and_road_clearance(self):
  found=set()
  for i in range(100):
   item=self.item(i);result=self.place(item);found.add(result['model'])
   width,depth,height=M.MODELS[result['model']]
   self.assertLessEqual(result['footprintMetres'][0],width+1e-8)
   self.assertLessEqual(result['footprintMetres'][1],depth+1e-8)
   self.assertLessEqual(result['heightMetres'],height+1e-8)
   self.assertGreaterEqual(result['roadClearanceMetres'],2)
   self.assertEqual(result,self.place(item))
  self.assertEqual(found,set(M.MODELS))
 def test_offcentre_scans_remain_centred_after_both_parcel_rotations(self):
  origin=(300.,-200.,400.);extent=(1200.,1700.,800.)
  for yaw in (0,180):
   result=self.place(self.item(yaw=yaw),origin,extent);scale=result['scale']
   c,s=math.cos(math.radians(yaw)),math.sin(math.radians(yaw));location=result['locationCm']
   self.assertAlmostEqual(location[0]+(c*origin[0]-s*origin[1])*scale,2500)
   self.assertAlmostEqual(location[1]+(s*origin[0]+c*origin[1])*scale,-7500)
   self.assertAlmostEqual(location[2]+(origin[2]-extent[2])*scale,2005-45)
 def test_expanded_footprint_that_reaches_slopes_or_water_is_preserved(self):
  for limits,reason in (((20,20.4),'expanded-footprint-relief'),((4,4.1),'wet-or-high'),((250,251),'wet-or-high')):
   self.assertEqual(self.place(self.item(),limits=limits)['rejected'],reason)
 def test_invalid_native_bounds_and_artist_rotations_are_refused(self):
  for extent in ((0,1,1),(1,float('nan'),1)):
   with self.assertRaises(ValueError):self.place(self.item(),extent=extent)
  with self.assertRaises(ValueError):self.place(self.item(yaw=45))

 @unittest.skipUnless(shutil.which('g++'),'Native terrain compiler unavailable')
 def test_every_real_town_parcel_against_the_actual_cpp_terrain_and_imported_scan_sizes(self):
  root=PATH.parents[2]
  pop_spec=importlib.util.spec_from_file_location('population',root/'unreal/Scripts/archipelago_population.py')
  pop=importlib.util.module_from_spec(pop_spec);pop_spec.loader.exec_module(pop)
  include=root/'unreal/Source/AnomaliaPrimeval/World'
  sites=[tuple(map(float,row)) for row in re.findall(r'\{\s*(-?\d+),\s*(-?\d+)\s*\}',(include/'AnomaliaInhabitedHeight.h').read_text())]
  with tempfile.TemporaryDirectory() as d:
   cpp=Path(d)/'height.cpp';library=Path(d)/'height.so'
   cpp.write_text('#include "AnomaliaInhabitedHeight.h"\nextern "C" double height(double e,double n){return AnomaliaInhabited::Height(e,n);}\n')
   subprocess.run(['g++','-shared','-fPIC','-O2','-std=c++17','-I',str(include),str(cpp),'-o',str(library)],check=True,capture_output=True)
   native=ctypes.CDLL(str(library));native.height.argtypes=[ctypes.c_double,ctypes.c_double];native.height.restype=ctypes.c_double
   plan=pop.build_plan(native.height,[11.056,9.146751708984375,14.67],sites=sites)
   self.assertEqual(len(plan['buildings']),4760)
   # Actual dimensions recorded by the native residential importer, in cm.
   dimensions={'country_house_scan':(5811.3912353515625,5854.7669677734375,2012.8880615234375),
               'abandoned_brick_house_scan':(6464.907470703125,4968.48193359375,2097.3974609375)}
   surface=pop.sampled_surface(native.height);accepted=0
   for item in plan['buildings']:
    extent=tuple(x/2 for x in dimensions[M.model_for(item['id'])])
    result=M.placement(item,(0,0,0),extent,surface,pop.ground_envelope)
    if 'rejected' not in result:
     accepted+=1;self.assertGreaterEqual(result['roadClearanceMetres'],2)
     self.assertLessEqual(result['groundReliefMetres'],.12)
   self.assertGreaterEqual(accepted,4700)
   print(f'Native terrain: {accepted}/4760 scanned exteriors fit; {4760-accepted} original parcels retained.')

if __name__=='__main__':unittest.main()
