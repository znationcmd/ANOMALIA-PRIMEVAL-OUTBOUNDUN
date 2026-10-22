"""Apply ANOMALIA's requested footprints; preserves every catalogue row and ID."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def footprint(row):
    ident=row['id'];category=row['category']
    if ident in {'water_in_fuel_can','gas_canister'}: return 2,3
    if ident in {'empty_water_bottle','empty_military_canteen','empty_filter_canteen'}: return 1,3
    if ident in {'stanag_magazine','ak_magazine'}: return 1,2
    if ident in {'fire_axe','hatchet'}: return 1,5
    if ident in {'shovel','pickaxe','sledgehammer'}: return 2,3
    if ident=='rp_recovery_kit': return 2,3
    if ident in {'blood_bag','saline','iv_kit','disinfectant_spray'}: return 1,2
    if category=='canned_food': return 1,2
    if category=='drinks': return (1,2) if ident in {'pipsi','notacola','spite','mad_monk'} else (1,3)
    if category=='assault_weapons': return 3,3
    if category=='hunting_precision_weapons': return 3,4
    if category=='handguns_smg_shotguns':
        if ident in {'bk133','bk43','bk12'}: return 3,4
        if ident in {'usg45_ump','sg5k_mp5','bizon','scorpion'}: return 2,3
        return 1,3
    if category=='tops': return 2,4
    if category=='pants': return 2,3
    if category=='vests': return 2,3
    if category=='backpacks': return 3,4
    if category=='headwear': return (1,1) if ident=='gas_mask_filter' else (2,2)
    if category=='shoes_gloves': return (1,2) if 'gloves' in ident else (2,2)
    if ident in {'camping_tent','military_tent','car_tent','plastic_barrel','metal_barrel','sea_chest'}: return 3,4
    if ident in {'cooking_pot','frying_pan','generator','car_battery','truck_battery','radiator'}: return 2,3
    if category=='vehicle_body_parts': return 3,4
    return row.get('inventoryWidth',1),row.get('inventoryHeight',1)

def apply():
    for name in ['loot_items_catalog.json','rp_items_catalog.json']:
        path=ROOT/'public/config'/name;data=json.loads(path.read_text())
        for row in data['items']: row['inventoryWidth'],row['inventoryHeight']=footprint(row)
        data['inventoryLayoutVersion']=2
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__': apply()
