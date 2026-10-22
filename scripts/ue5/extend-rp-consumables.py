"""Add original RP definitions; effects use fictional points, not real doses or recipes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def save(name, data):
    (ROOT/'public/config'/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def extend():
    loot=json.loads((ROOT/'public/config/loot_items_catalog.json').read_text())
    rp=json.loads((ROOT/'public/config/rp_items_catalog.json').read_text())
    index={row['id']:row for row in loot['items']}
    def add(target, ident, label, category, use=None, weight=.05, tier=1, enabled=True):
        row=dict(id=ident,displayName=label,category=category,minTier=tier,maxTier=5,nominal=8 if enabled else 0,min=0,
                 lifetimeSeconds=3600,restockSeconds=600,quantity=1,enabled=enabled,weightKg=weight,
                 maxStack=20,inventoryWidth=1,inventoryHeight=1)
        if use: row['use']=use
        existing=next((x for x in target['items'] if x['id']==ident),None)
        if existing is None: target['items'].append(row)
    def medical(ident,label,effect,required=None):
        row=index[ident];row['displayName']=label;row['weightKg']=min(row.get('weightKg',1),.25)
        row['use']=dict(action='heal',effect=effect)
        if required: row['use']['requiredItem']=required
    # These are simplified game treatments, not clinical claims.
    index['sterile_bandage']['use']['effect']='bandage'
    index['water_purification_tablets'].update(displayName='Traitement pour eau — objet de jeu',weightKg=.02,
        use=dict(action='purify',requiredItem='dirty_water_bottle',returnItem='water_bottle'))
    add(loot,'dirty_water_bottle','Bouteille d’eau non traitée','drinks',
        dict(action='drink',thirst=30,effect='raw_food',returnItem='empty_water_bottle'),weight=1)
    for ident,label,effect,required in [
        ('rags','Chiffons pour pansement','rags',None),('morphine','Antalgique médical RP','analgesic',None),
        ('epinephrine','Stimulant médical RP','stimulant',None),('blood_test_kit','Kit de diagnostic sanguin','diagnostic',None),
        ('blood_bag','Poche de sang (soins simplifiés)','blood','iv_kit'),('saline','Solution de perfusion (jeu)','saline','iv_kit'),
        ('splint','Attelle — soulagement provisoire','splint',None),('tetracycline','Antibiotique RP','antibiotic',None),
        ('charcoal_tablets','Traitement antitoxique RP','antidote',None),('vitamins','Vitamines RP','vitamins',None),
        ('iodine','Antiseptique RP','disinfectant',None),('disinfectant_spray','Désinfectant pour plaies RP','disinfectant',None),
        ('alcohol_90','Alcool antiseptique — usage externe RP','disinfectant',None)]: medical(ident,label,effect,required)
    for ident,label in [('beef','Viande bovine crue'),('pork','Viande de porc crue'),('chicken','Volaille crue'),
                        ('animal_fat','Graisse animale'),('mushroom','Champignon non identifié'),('raw_fish','Poisson cru')]:
        index[ident].update(displayName=label,weightKg=.3,use=dict(action='eat',hunger=12,effect='raw_food'))
    for ident,label in [('vodka','Vodka RP'),('whisky','Whisky RP'),('rum','Rhum RP'),('red_wine','Vin rouge RP'),
                        ('white_wine','Vin blanc RP'),('rose_wine','Vin rosé RP'),('champagne','Vin pétillant RP')]:
        index[ident].update(displayName=label,weightKg=.5,use=dict(action='drink',effect='alcohol',restrictedGroup='alcohol'))
    for ident,label in [('cooked_beef','Viande bovine cuite'),('cooked_pork','Viande de porc cuite'),('cooked_chicken','Volaille cuite'),
                        ('cooked_fish_fillet','Filet de poisson cuit'),('bread_loaf','Pain'),('rice_meal','Riz préparé'),('vegetable_soup','Soupe de légumes')]:
        add(rp,ident,label,'canned_food',dict(action='eat',hunger=25),weight=.3)
    for ident,label in [('orange_juice','Jus de fruits'),('drinking_water_carton','Eau potable en carton')]:
        add(rp,ident,label,'drinks',dict(action='drink',thirst=35),weight=.5)
    add(rp,'rp_recovery_kit','Trousse de soins RP — intoxication','medical_supplies',dict(action='heal',effect='recovery'),weight=.25)
    families={
        'stimulant':[('cocaine','Cocaïne'),('crack','Crack'),('amphetamine','Amphétamine'),('methamphetamine','Méthamphétamine'),
                     ('mdma','MDMA'),('methylphenidate','Méthylphénidate'),('modafinil','Modafinil')],
        'opioid':[('heroin','Héroïne'),('opium','Opium'),('fentanyl','Fentanyl'),('oxycodone','Oxycodone'),('codeine','Codéine'),
                  ('tramadol','Tramadol'),('methadone','Méthadone'),('buprenorphine','Buprénorphine')],
        'depressant':[('diazepam','Diazépam'),('alprazolam','Alprazolam'),('clonazepam','Clonazépam'),('zolpidem','Zolpidem'),
                      ('ghb','GHB'),('barbiturates','Barbituriques')],
        'hallucinogen':[('lsd','LSD'),('psilocybin','Psilocybine'),('mescaline','Mescaline'),('dmt','DMT'),
                        ('ketamine','Kétamine'),('pcp','PCP'),('nitrous_oxide','Protoxyde — objet RP')],
        'cannabinoid':[('cannabis','Cannabis'),('cannabis_resin','Résine de cannabis'),('cannabis_oil','Huile de cannabis'),
                       ('synthetic_cannabinoid','Cannabinoïde synthétique')],
        'veterinary':[('vet_sedative','Sédatif vétérinaire RP')],
        'anomaly':[('anomaly_azure','Composé fictif Azur'),('anomaly_ember','Composé fictif Braise'),('anomaly_spore','Spore fictive ANOMALIA')],
    }
    for family, rows in families.items():
        for ident,label in rows:
            add(rp,'rp_substance_'+ident,label+' — accessoire RP','rp_substances',dict(action='rp',effect=family,restrictedGroup='substances'),weight=.01,tier=3)
    add(rp,'cigarette_butt','Mégot','rp_tobacco',weight=.001,enabled=False)
    for ident,label in [('cigarette','Cigarette'),('hand_rolled_cigarette','Cigarette roulée'),('cigar','Cigare')]:
        add(rp,ident,label,'rp_tobacco',dict(action='smoke',effect='nicotine',restrictedGroup='tobacco',requiredItem='lighter',returnItem='cigarette_butt'),weight=.01)
    add(rp,'tobacco_pouch','Pochette de tabac','rp_tobacco',weight=.05)
    rp['description']='Original ANOMALIA RP inventory. Substance family effects are fictional game points, not medical guidance, real doses or manufacturing recipes. Individual 3D models remain provisional.'
    loot['description']='Original ANOMALIA loot definitions consumed by native Unreal inventory and world loot. Supported use rules are authoritative; specialist weapon, tool and medical gameplay remains incomplete.'
    save('loot_items_catalog.json',loot);save('rp_items_catalog.json',rp)
    print('Distinct items:',len({x['id'] for x in loot['items']+rp['items']}))
    print('Use definitions:',sum('use' in x for x in loot['items']+rp['items']))

if __name__=='__main__': extend()
