"""Build factual class references, not copied DayZ gameplay or artistic assets.

Inputs are read-only local clones at recorded revisions. Case-sensitive source
identities and per-occurrence provenance survive consolidation. No UE integration
status is inferred from a classname, a market mention or a successful extraction.
"""
import argparse
from collections import Counter,defaultdict
import csv,datetime,hashlib,json,re,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

IDENT=re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,150}\Z')
ROOTS={'CfgVehicles','CfgWeapons','CfgMagazines','CfgAmmo','CfgNonAIVehicles'}
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()

def tokens(text):
    expression=r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|[A-Za-z_]\w*|\d+(?:\.\d+)?|[{}:;=]|[^\s]'
    return [(m.group(),m.start()) for m in re.finditer(expression,text) if not m.group().startswith(('//','/*'))]

def config_classes(text):
    """Parse config scopes and inheritance without mistaking nested Health for an item.
    Conditional branches remain provisional; arbitrary preprocessing is never run.
    """
    ts=tokens(text);out=[];errors=[]
    def scope(start,end,parents):
        i=start
        while i<end:
            if ts[i][0]!='class' or i+1>=end:i+=1;continue
            name=ts[i+1][0];j=i+2;base=''
            if j<end and ts[j][0]==':':
                if j+1<end:base=ts[j+1][0]
                j+=2
            while j<end and ts[j][0] not in ('{',';'):j+=1
            if j==end:break
            if ts[j][0]==';':i=j+1;continue
            depth=1;k=j+1
            while k<end and depth:
                depth+=(ts[k][0]=='{')-(ts[k][0]=='}');k+=1
            if depth:errors.append(dict(offset=ts[i][1],error='unbalanced_class_braces',classname=name));break
            direct=[];level=0
            for value,_ in ts[j+1:k-1]:
                if value=='{':level+=1
                elif value=='}':level-=1
                elif level==0:direct.append(value)
            own_scope=None
            for p in range(len(direct)-2):
                if direct[p:p+2]==['scope','='] and direct[p+2].isdigit():own_scope=int(direct[p+2])
            if len(parents)==1 and parents[0] in ROOTS and IDENT.fullmatch(name):
                out.append(dict(classname=name,parent=base,configRoot=parents[0],scope=own_scope,
                                line=text.count('\n',0,ts[i][1])+1,
                                conditional=bool(re.search(r'^\s*#\s*(if|ifdef|ifndef|define)',text,re.M))))
            scope(j+1,k-1,parents+[name]);i=k
    scope(0,len(ts),[])
    return out,errors

def xml_classes(text):
    root=ET.fromstring(text);out=[]
    if root.tag not in {'types','spawnabletypes','randompresets','events','prototype','eventgroupdef'}:return out
    def walk(node,path):
        kind=None;name=None;details={}
        if node.tag=='type' and node.get('name'):
            name=node.get('name');is_type=root.tag=='types'
            kind='economy_type' if is_type else 'spawnable_type_reference'
            if is_type:
                for field in ('nominal','min'):
                    value=node.findtext(field)
                    details[field]=int(value) if value is not None and value.strip().lstrip('-').isdigit() else None
                details['sourceCategories']=[n.get('name') for n in node.findall('category')]
        elif node.tag=='item' and node.get('name'):name=node.get('name');kind='attachment_or_cargo_reference'
        elif node.tag=='child' and node.get('type'):name=node.get('type');kind='event_child_reference'
        elif root.tag=='prototype' and node.tag=='group' and node.get('name'):name=node.get('name');kind='world_prototype_reference'
        if name and IDENT.fullmatch(name):out.append(dict(classname=name,evidenceKind=kind,location=path,**details))
        for i,child in enumerate(node):walk(child,path+'/'+child.tag+'['+str(i)+']')
    walk(root,'/'+root.tag)
    return out

def json_classes(data):
    out=[]
    scalar={'classname','class_name','itemclassname','item_classname','itemclass'}
    arrays={'variants','attachments','spawnattachments','inventoryattachments'}
    def walk(value,path):
        if isinstance(value,dict):
            for key,item in value.items():
                low=key.lower()
                if low in scalar and isinstance(item,str) and IDENT.fullmatch(item):out.append(dict(classname=item,evidenceKind='json_class_reference',location=path+'/'+key))
                elif low in arrays and isinstance(item,list):
                    for i,name in enumerate(item):
                        if isinstance(name,str) and IDENT.fullmatch(name):out.append(dict(classname=name,evidenceKind='json_variant_reference',location=path+'/'+key+'/'+str(i)))
                walk(item,path+'/'+key)
        elif isinstance(value,list):
            for i,item in enumerate(value):walk(item,path+'/'+str(i))
    walk(data,'');return out

RULES=[
 ('AB',r'^(land_|bldr_|wreck_|static_|building_|tree_|bush_|rock_|expansionprop)|hologram|bookholo'),
 ('AA',r'^(animal_|zmb|survivor)|^dayzanimal|^animalbase|expansionai'),
 ('B',r'^(ammo_|ammobox_|mag_|bullet_|shell_|expansionammo)|magazine|speedloader|arrow|bolt_'),
 ('C',r'suppressor|silencer|optic|scope|compensator|buttstock|hndgrd|handguard|bipod|railadapter|pistolgrip|recoilpad'),
 ('E',r'grenade|claymore|landmine|plastic_explosive|detonator|explosive|tripwire|beartrap|breaching'),
 ('F',r'helmet|headgear|headtorch|balaclava|bandana|gasmask|respirator|nvg|goggles|glasses|beret|beanie|ushanka|baseballcap|boonie|^hat_|mask|cowboyhat|officerhat|cap_'),
 ('H',r'pants|trousers|jeans|skirt|shorts|gloves|boots|shoes|sneakers|jogging|wellies'),
 ('G',r'jacket|hoodie|tshirt|t_shirt|shirt|sweater|dress|coat|parka|blouse|raincoat|jumpsuit|tracksuit|ghilliesuit'),
 ('I',r'vest|platecarrier|pouches|holster|belt|armband|chestrig'),
 ('J',r'backpack|bag|rucksack|crate|chest|barrel|container|ammobox|protectorcase|firstaidkit|lockers|cabinet|storage|safe_'),
 ('AC',r'cannabis|cocaine|heroin|drug|cigarette|bitcoin|wallet|creditcard|ruble|dollar|euro|money|goldbar|silverbar|coin'),
 ('O',r'terje(ampoule|pill|injector|salve|surgery)|medicine|bandage|disinfect|saline|bloodbag|bloodtest|morphine|epinephrine|tetracycline|charcoal|vitamin|purification|chelat|surgical|thermometer|splint|painkiller|defibrill|antibiotic|antiseptic'),
 ('M',r'fillet|steak|guts|pelt|lard|bones|feather|sardines|mackerel|carp|salmon|trout|tuna|rabbit|foxpelt|cowpelt|pigpelt'),
 ('L',r'apple|pear|plum|berries|tomato|pepper|pumpkin|zucchini|potato|mushroom|agaric|boletus|seed|plantmaterial|herb|corn|wheat|fruit'),
 ('N',r'waterbottle|canteen|soda|cannister|bottle|kvass|pipsi|spite|cola|fronta|coffee|tea_|beer|liquid|waterpouch'),
 ('K',r'canned|can_|boxcereal|rice|powderedmilk|peaches|beans|spaghetti|bacon|pate|food|crisps|cracker|biscuit|jam|honey|chocolate|cookz|candy'),
 ('U',r'^(hatchback|sedan|offroad|civilian|truck|car_|boat_|expansion(mh6|uh1h|uh60|an2|uaz|vodnik|tractor|helicopter|zodiac)|rag_(atv|landrover|humvee|baja|derby|gaz|schoolbus|mtvr|zil|jeep))|wheel|radiator|sparkplug|glowplug|carbattery|truckbattery|headlight|helicopter|motorcycle|motorbike|gyrocopter|propeller|windscreen|jerrycan|gasoline|gascanister|door_|hood_|trunk_|carkey'),
 ('A',r'^(ak|aks|aug|asval|b95|cz[0-9]|colt|deagle|fal|famas|fnx|glock|izh|m16|m4a|m79|makarov|mkii|mosin|mp5|mp133|mp443|pp19|repeater|ruger|sks|svd|saiga|scout|ump|vss|winchester|ssg|vikhr|scr17|expansion(m9|m16|m14|aw|benelli|dt11|g36|kar98|k98|m1a|m1|mp7|rpg|stannag))|snafu_|morty.*(rifle|pistol)|rifle|shotgun|firearm'),
 ('D',r'knife|bayonet|machete|sword|spear|axe|hatchet|crowbar|baseballbat|sledgehammer|pitchfork|sickle|cleaver|brassknuckles'),
 ('S',r'fishing|fishhook|hook|bait|lure|worm|fertilizer|greenhouse|garden|watering|compost|chickencoop|beehive'),
 ('Q',r'plank|woodenlog|nail|metalplate|barbedwire|metalwire|sandbag|brick|concrete|cement|fence|watchtower|codelock|combinationlock|rag_bb_|foundation|wallkit|floorkit|roofkit|stair|construction'),
 ('R',r'tent|shelter|sleepingbag|bed|chair|table|couch|sofa|fridge|fireplace|stove|oven|lamp|carpet|furnace|shelf|furniture|gazebo'),
 ('T',r'compass|gps|map|rangefinder|binocular|radio|walkietalkie|transceiver|battery9v|detector|dosimeter|computer|laptop|usb|tablet'),
 ('Y',r'christmas|xmas|halloween|easter|gift|santa|witch|pumpkinhead|carnival|anniversary'),
 ('W',r'keycard|key_|keychain|note|paper|book|document|quest|mission|treasure|airdrop|dogtag|collectible|receipt'),
 ('V',r'military|army|ballistic|combat|dogtag'),
 ('X',r'nbc|cbrn|decontam|heatpack|namalsk|coldpack|radiation'),
 ('P',r'tool|sewing|ducttape|leather|epoxy|whetstone|matchbox|lighter|handdrill|torch|glowstick|rope|pliers|handsaw|hacksaw|hammer|shovel|screwdriver|wrench|canopener|cookingpot|fryingpan|generator|cable|lockpick|repair|hook|rag|stone')]

def classify(name,observations,ancestors=()):
    combined=' '.join([name,*ancestors]).lower()
    if any(o.get('configRoot')=='CfgAmmo' for o in observations):primary='B';reason='config_root'
    elif any(o.get('configRoot')=='CfgMagazines' for o in observations):primary='B';reason='config_root'
    else:
        primary=next((code for code,pattern in RULES if re.search(pattern,combined)),'Z');reason='name_or_inheritance_heuristic'
    tags={primary}
    for code,pattern in RULES:
        if code in ('V','X','Y','AC') and re.search(pattern,combined):tags.add(code)
    if any(o.get('nominal')==0 or o.get('scope') in (0,1) for o in observations):tags.add('Z')
    return primary,sorted(tags),reason

def module_for(repo,path):
    text=path.as_posix();parts=path.parts
    if repo['id'] in ('official-ce','official-scripts'):return 'DayZ_officiel'
    if repo['id']=='expansion-source':
        match=re.search(r'(?:DayZExpansion/|0_DayZExpansion_)([A-Za-z0-9]+)',text)
        return 'DayZ-Expansion-'+(match[1] if match else 'Shared')
    if repo['id']=='terje':return parts[0]
    if repo['id']=='rag-wikis':
        match=re.search(r'docs/mods/([^/]+)',text)
        names={'baseitems':'RaG_BaseItems','basebuilding':'RaG_BaseBuilding','core':'RaG_Core','hunting-cabin':'RaG_Hunting_Cabin'}
        return names.get(match[1],'RaG_'+match[1]) if match else 'RaG_Documentation'
    if repo['id']=='community-market':return parts[1] if len(parts)>2 and parts[0]=='Market' else 'Community_Market'
    if repo['id']=='expansion-missions':return 'DayZ-Expansion-Shared'
    return repo['mod']

def clean_code(text):
    return re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"',lambda m:'\n'*m.group().count('\n')+' '*(len(m.group())-m.group().count('\n')),text)

def build(manifest,input_dir,out):
    out.mkdir(parents=True,exist_ok=True);observations=[];sources=[];errors=[];definitions=[]
    for repo in manifest['repositories']:
        root=Path(repo['directory']);revision=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
        repo['resolvedRevision']=revision
        for file in sorted(root.rglob('*')):
            if not file.is_file() or '.git' in file.relative_to(root).parts:continue
            rel=file.relative_to(root);ext=file.suffix.lower()
            if ext not in ('.xml','.json','.cpp','.hpp','.h','.c','.md','.map'):continue
            if file.stat().st_size>16_000_000:errors.append(dict(source=str(rel),repo=repo['id'],reason='metadata_file_over_limit'));continue
            if repo['id']=='rag-wikis' and not (ext=='.md' and ('class-name' in file.name or 'class_names' in file.name or 'class-name' in str(rel))):continue
            raw=file.read_bytes()
            try:text=raw.decode('utf-8-sig')
            except UnicodeDecodeError:
                text=raw.decode('cp1252',errors='replace')
                errors.append(dict(repo=repo['id'],source=repo['url']+'/blob/'+revision+'/'+rel.as_posix(),reason='legacy_encoding_fallback_cp1252',error='UTF-8 decode failed; verify source text encoding'))
            mod=module_for(repo,rel)
            url=repo['url']+'/blob/'+revision+'/'+rel.as_posix();parsed=[]
            try:
                if ext=='.xml':parsed=xml_classes(text)
                elif ext=='.json':parsed=json_classes(json.loads(text))
                elif ext in ('.cpp','.hpp','.h'):
                    classes,failures=config_classes(text)
                    parsed=[dict(entry,evidenceKind='config_definition',location='line:'+str(entry['line'])) for entry in classes]
                    errors.extend(dict(repo=repo['id'],source=url,**e) for e in failures)
                    if re.search(r'^\s*#\s*(define|include|if)',text,re.M):errors.append(dict(repo=repo['id'],source=url,reason='preprocessor_not_expanded_runtime_registry_still_required'))
                elif ext=='.c':
                    clean=clean_code(text)
                    for match in re.finditer(r'\bclass\s+([A-Za-z_]\w*)\s*(?:(?:extends|:)\s*([A-Za-z_]\w*))?\s*\{',clean):
                        entry=dict(classname=match[1],parent=match[2] or '',evidenceKind='script_implementation',location='line:'+str(clean.count('\n',0,match.start())+1))
                        definitions.append((repo,rel,url,revision,mod,entry))
                elif ext=='.map':
                    for number,line in enumerate(text.splitlines(),1):
                        name=line.split('|',1)[0].strip()
                        if IDENT.fullmatch(name):parsed.append(dict(classname=name,evidenceKind='editor_placement_reference',location='line:'+str(number)))
                elif repo['id']=='rag-wikis':
                    for number,line in enumerate(text.splitlines(),1):
                        if line.startswith('|'):
                            for name in re.findall(r'`((?:RaG_|Rag_)[A-Za-z0-9_]+)`',line):parsed.append(dict(classname=name,evidenceKind='author_documentation_reference',location='line:'+str(number)))
            except (ET.ParseError,json.JSONDecodeError,UnicodeError,ValueError) as error:
                errors.append(dict(repo=repo['id'],source=url,reason='parse_error',error=str(error)))
            if parsed or ext in ('.xml','.json','.c') or file.name.lower()=='config.cpp':
                sha=hashlib.sha256(file.read_bytes()).hexdigest()
                sources.append(dict(repo=repo['id'],mod=mod,url=url,revision=revision,file=rel.as_posix(),sha256=sha,extracted=len(parsed),license=repo['license']))
            map_name=next((name for token,name in manifest['maps'].items() if token.lower() in str(rel).lower()),'')
            for entry in parsed:observations.append(dict(entry,origin='official' if repo['id'].startswith('official') else 'mod',mod=mod,sourceUrl=url,sourceRevision=revision,sourceFile=rel.as_posix(),sourceLicense=repo['license'],map=map_name,repo=repo['id']))
    ancestry=defaultdict(set)
    for *_,entry in definitions:
        if entry['parent']:ancestry[entry['classname']].add(entry['parent'])
    def chain(name,seen=None):
        seen=set() if seen is None else seen
        if name in seen:return set()
        seen.add(name);result=set(ancestry[name])
        for parent in list(result):result.update(chain(parent,seen))
        return result
    roots={'ItemBase','InventoryItem','Inventory_Base','Weapon_Base','Magazine','Magazine_Base','Clothing_Base','CarScript','BoatScript','Boat','AnimalBase','DayZAnimal','DayZInfected','House','BuildingBase','BaseBuildingBase','EntityAI'}
    for repo,rel,url,revision,mod,entry in definitions:
        parents=chain(entry['classname'])
        if not (parents & roots):continue
        observations.append(dict(entry,ancestors=sorted(parents),origin='official' if repo['id'].startswith('official') else 'mod',mod=mod,sourceUrl=url,sourceRevision=revision,sourceFile=rel.as_posix(),sourceLicense=repo['license'],map='',repo=repo['id']))
    hashes={source['url']:source['sha256'] for source in sources}
    for observation in observations:observation['sourceSha256']=hashes.get(observation['sourceUrl'])
    # Deduplicate only identical factual observations. Nominal differences, case,
    # source map, revision, file, evidence location and mod overrides are retained.
    unique={json.dumps(row,sort_keys=True,ensure_ascii=False):row for row in observations}
    observations=sorted(unique.values(),key=lambda row:(row['classname'],row['mod'],row['sourceUrl'],row['location']))
    groups=defaultdict(list)
    known_vanilla={row['classname'] for row in observations if row['origin']=='official'}
    definition_owners=defaultdict(set)
    for row in observations:
        if row['evidenceKind']=='config_definition':definition_owners[row['classname']].add(row['mod'])
    for row in observations:
        row['observationId']='obs_'+hashlib.sha256(json.dumps(row,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:24]
        if row['repo']=='official-ce':
            row['versionEvidence']='1.30_current_map_template' if row['sourceFile'].split('/')[0] in {'dayzOffline.chernarusplus','dayzOffline.enoch','dayzOffline.sakhal','dayzOffline.nasdara'} else 'historical_or_seasonal_template_version_unverified'
        else:row['versionEvidence']='1.30.164200' if row['repo']=='official-scripts' else 'source_revision_only_runtime_1.30_compatibility_unverified'
        owner=row['mod']
        if row['classname'] in known_vanilla:owner='DayZ_officiel'
        elif row['repo']=='community-market' and len(definition_owners[row['classname']])==1:owner=next(iter(definition_owners[row['classname']]))
        groups[(owner,row['classname'])].append(row)
    categories=list(csv.DictReader((input_dir/'checklist_categories.csv').open(encoding='utf-8-sig'),delimiter=';'));titles={row['code']:row['categorie'] for row in categories}
    records=[]
    for (mod,name),rows in sorted(groups.items()):
        ancestors=sorted(set(parent for row in rows for parent in row.get('ancestors',[])))
        primary,tags,reason=classify(name,rows,ancestors)
        kind='world_editor' if primary=='AB' else 'world_entity' if primary=='AA' else 'technical_reference' if primary=='Z' else 'item_or_equipment_reference'
        records.append(dict(id='ref_'+hashlib.sha256((mod+'\0'+name).encode()).hexdigest()[:20],classname=name,mod=mod,categoryCode=primary,category=titles[primary],categoryTags=tags,
            classificationMethod=reason,classificationVerified=False,recordKind=kind,
            evidenceKinds=sorted(set(row['evidenceKind'] for row in rows)),maps=sorted(set(row['map'] for row in rows if row['map'])),
            naturalLootByMap=[dict(map=row['map'],nominal=row['nominal'],sourceUrl=row['sourceUrl']) for row in rows if row.get('nominal') is not None],
            configDefinitionFound=any(row['evidenceKind']=='config_definition' for row in rows),
            sourceUrls=sorted(set(row['sourceUrl'] for row in rows)),sourceObservationIds=[row['observationId'] for row in rows],
            sourceContexts=sorted(set(row['mod'] for row in rows)),
            versionEvidence=sorted(set(row['versionEvidence'] for row in rows)),
            ue5=dict(referenced=True,imported=False,visibleInEditor=False,functional=False,testedPC=False,testedMultiplayer=False,assetPath=None,evidence=None),
            originalAsset=dict(source=None,license=None,approved=False),massGrams=None,gridSize=None,attachmentSlots=None,recipes=None,
            anomaliaGameplayReady=False))
    payload=dict(schemaVersion=1,generatedAt=NOW,requestedDayZVersion='1.30',officialScriptBuild='1.30.164200',complete=False,referenceOnly=True,
                 categories=categories,sourceRepositories=manifest['repositories'],records=records)
    (out/'catalogue_ANOMALIA.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n')
    with (out/'observations_sources.jsonl').open('w',encoding='utf-8') as stream:
        for row in observations:stream.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
    columns=['id_anomalia','classe_dayz_reference','mod_source','categorie_code','categorie','tags','catalogue_type','preuve','sources','cartes','status_UE5','integre_UE5','visible_Editor','fonctionnel','teste_PC','teste_multijoueur','asset_UE5_path','asset_licence','classement_a_valider']
    with (out/'catalogue_UE5_ANOMALIA.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,columns,delimiter=';');writer.writeheader()
        for item in records:writer.writerow(dict(zip(columns,[item['id'],item['classname'],item['mod'],item['categoryCode'],item['category'],'|'.join(item['categoryTags']),item['recordKind'],'|'.join(item['evidenceKinds']),'|'.join(item['sourceUrls']),'|'.join(item['maps']),'reference_uniquement',False,False,False,False,False,'','','true'])))
    def write_csv(filename,rows,fields=None):
        fields=fields or sorted(set(k for row in rows for k in row))
        with (out/filename).open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fields,delimiter=';');writer.writeheader()
            for row in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})
    write_csv('observations_sources.csv',observations)
    write_csv('sources_revisions.csv',sources)
    write_csv('couverture_par_categorie.csv',[dict(code=code,categorie=titles[code],references=sum(r['categoryCode']==code for r in records),definitions_config=sum(r['categoryCode']==code and r['configDefinitionFound'] for r in records),classement_verifie=0,integres_UE5=0,fonctionnels=0,testes_PC=0,complet=False) for code in titles])
    write_csv('journal_erreurs_extraction.csv',errors,['repo','source','reason','error','offset','classname'])
    collisions=defaultdict(set)
    for item in records:collisions[(item['mod'],item['classname'].casefold())].add(item['classname'])
    summary=dict(records=len(records),exactClassnames=len({r['classname'] for r in records}),sourceObservations=len(observations),sources=len(sources),errors=len(errors),
                 caseSensitiveCollisions=[dict(mod=key[0],classes=sorted(names)) for key,names in collisions.items() if len(names)>1],
                 economyClassnames=len({row['classname'] for row in observations if row['evidenceKind']=='economy_type' and row['origin']=='official'}),
                 currentFourMapsEconomyClassnames=len({row['classname'] for row in observations if row['evidenceKind']=='economy_type' and row.get('versionEvidence')=='1.30_current_map_template'}),
                 configDefinitions=sum(r['configDefinitionFound'] for r in records),mods=len({r['mod'] for r in records if r['mod']!='DayZ_officiel'}),
                 naturalLootZeroObservations=sum(row.get('nominal')==0 for row in observations),complete=False,ue5Imported=0)
    (out/'verification_extraction.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='caseSensitiveCollisions'},ensure_ascii=False),flush=True)
    return payload

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--input',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();build(json.loads(args.manifest.read_text()),args.input,args.out)
