import importlib.util
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/'scripts/catalogue/build_reference_catalogue.py'
spec=importlib.util.spec_from_file_location('catalogue',PATH);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)

class ExtractTests(unittest.TestCase):
    def test_real_case_variants_and_zero_nominal_survive(self):
        rows=M.xml_classes('<types><type name="Thing_Black"><nominal>0</nominal></type><type name="thing_black"><nominal>4</nominal></type></types>')
        self.assertEqual([r['classname'] for r in rows],['Thing_Black','thing_black'])
        self.assertEqual(rows[0]['nominal'],0)
        self.assertEqual(rows[1]['nominal'],4)
    def test_event_children_are_classes_event_names_are_not(self):
        rows=M.xml_classes('<events><event name="VehicleEvent"><children><child type="Sedan_02"/><child type="Sedan_02_Red"/></children></event></events>')
        self.assertEqual([r['classname'] for r in rows],['Sedan_02','Sedan_02_Red'])
    def test_ui_items_and_random_preset_names_are_not_classes(self):
        self.assertEqual(M.xml_classes('<inputs><item name="UAJump"/></inputs>'),[])
        rows=M.xml_classes('<randompresets><cargo name="FoodPreset"><item name="Apple"/></cargo></randompresets>')
        self.assertEqual([r['classname'] for r in rows],['Apple'])
    def test_nested_config_health_and_forward_declarations_excluded(self):
        rows,errors=M.config_classes('class CfgVehicles {class ItemBase; class MyItem: ItemBase {scope=2; class DamageSystem {class Health {scope=0;};};};};')
        self.assertEqual(errors,[]);self.assertEqual(len(rows),1)
        self.assertEqual((rows[0]['classname'],rows[0]['scope'],rows[0]['parent']),('MyItem',2,'ItemBase'))
    def test_comments_strings_and_conditionals_do_not_become_classes(self):
        rows,_=M.config_classes('// class Fake {};\nclass CfgVehicles {class Real {scope=1;description="class Bogus { }";};};')
        self.assertEqual([r['classname'] for r in rows],['Real'])
        rows,_=M.config_classes('#ifdef FEATURE\nclass CfgAmmo {class Bullet {scope=2;};};\n#endif')
        self.assertTrue(rows[0]['conditional'])
    def test_json_variants_are_preserved_but_description_is_not_inventory(self):
        rows=M.json_classes({'ClassName':'Gun','Variants':['Gun_Black','gun_black'],'Description':'NotAClass','Attachments':['Mag_20Rnd']})
        self.assertEqual({r['classname'] for r in rows},{'Gun','Gun_Black','gun_black','Mag_20Rnd'})
    def test_nominal_zero_adds_technical_tag_without_changing_item_category(self):
        primary,tags,_=M.classify('Raincoat_Black',[{'nominal':0}])
        self.assertEqual(primary,'G');self.assertIn('Z',tags)

if __name__=='__main__':unittest.main()
