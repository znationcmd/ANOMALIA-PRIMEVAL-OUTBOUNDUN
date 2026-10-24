"""Audit priority mods and emit integration gaps without upgrading references to assets."""
from collections import Counter
import csv,hashlib,json,re
from pathlib import Path
import xml.etree.ElementTree as ET

ALIASES={
 'SNAFU_Weapons':['Snafu'],'Mortys Weapons':['Morty Weapons',"Morty's Weapons V2"],
 'Forward Operator Gear':['Forward Operator Gear 2026'],
 'MMG - Mightys Military Gear':['MMG Gear','MMG Gear County Camos'],
 'WindstrideClothing':['Windstride'],'4KBOSSKVehiclePackage':['4KBOSSKVehicles'],
 'RUSForma_vehicles':['RusForma'],'CJ187-LootChest':['CJ187'],
 'Terje Medicine':['TerjeMedicine'],'Terje Skills':['TerjeSkills'],
 'DayZ-Expansion-Bundle':['DayZ-Expansion-Shared'],
 'DayZ-Expansion-Licensed':[],
}
CORRECT_IDS={'CodeLock':'1646187754','Trader Mod':'1590841260','TraderPlus':'2458896948'}

def write_csv(path,rows,fields=None):
    fields=fields or sorted(set(key for row in rows for key in row))
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fields,delimiter=';');writer.writeheader()
        for row in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()})

def norm(s):return re.sub('[^a-z0-9]','',s.lower())

def main():
    root=Path('catalogue-output');payload=json.loads((root/'catalogue_ANOMALIA.json').read_text());records=payload['records']
    originals=list(csv.DictReader(open('catalogue-input/mods_a_inventorier.csv',encoding='utf-8-sig'),delimiter=';'))
    discoveries=json.load(open('workshop-metadata/priority-mods-discovery.json'));by_name={row['requested']:row for row in discoveries}
    details=json.load(open('workshop-metadata/details-api.json'))['response']['publishedfiledetails']
    details+=json.load(open('workshop-metadata/corrected-details-api.json'))['response']['publishedfiledetails']
    by_id={row['publishedfileid']:row for row in details};rows=[];gaps=[]
    for requested in originals:
        name=requested['mod'];discovery=by_name[name]
        id=CORRECT_IDS.get(name,discovery.get('selected',{}).get('id',''));detail=by_id.get(id,{})
        aliases={norm(s) for s in [name,*ALIASES.get(name,[])]}
        matched=[r for r in records if any(norm(s) in aliases for s in r['sourceContexts'])]
        config=[r for r in matched if 'config_definition' in r['evidenceKinds']]
        documented=[r for r in matched if 'author_documentation_reference' in r['evidenceKinds']]
        description=detail.get('description','');low=description.lower()
        license_status='autorisation_UE5_absente'
        if any(s in low for s in ['dayz only','dayz platform','no derivative','not allowed to be','repack','reupload','non-commercial','noncommercial','non commercial']):license_status='restrictions_explicites_pas_de_reutilisation_UE5'
        source_status='definitions_publiques_partielles' if config else 'documentation_auteur_partielle' if documented else 'references_marchand_ou_script_seulement' if matched else 'classes_non_recuperees'
        row=dict(mod_demande=name,workshop_id=id,titre_workshop=detail.get('title',''),steam_creator_id=detail.get('creator',''),
                 url='https://steamcommunity.com/sharedfiles/filedetails/?id='+id,
                 identite='identifiant_corrige_source_auteur_verifiee' if name in CORRECT_IDS else discovery.get('status'),
                 metadata_api_obtenue=detail.get('result')==1,workshop_derniere_revision_unix=detail.get('time_updated'),version_mod_semantique='non_verifiee',
                 references=len(matched),fiches_avec_definition_config=len(config),fiches_documentees_auteur=len(documented),
                 statut_classes=source_status,statut_licence=license_status,
                 dependances='non_verifiees_integralement',source_complet=False,compatibilite_DayZ_130='non_testee',
                 integres_UE5=0,fonctionnels=0,testes=0,source_aliases=sorted(aliases))
        rows.append(row)
        if not config:gaps.append(dict(type='mod',identifiant=name,raison=source_status,source=row['url'],action='Obtenir les metadonnees de configuration de la version exacte aupres de auteur; ne pas reutiliser les actifs du mod.'))
        if discovery.get('error'):gaps.append(dict(type='source_http',identifiant=name,raison=discovery['error'],source=discovery.get('selected',{}).get('url',discovery['searchUrl']),action='Metadata Workshop obtenue par API publique; fichiers de classes non fournis par cette API.'))
    write_csv(root/'inventaire_mods_prioritaires.csv',rows)
    (root/'inventaire_mods_prioritaires.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    contexts=Counter(s for r in records for s in r['sourceContexts'])
    write_csv(root/'autres_contextes_mods.csv',[dict(contexte=name,references=count,definition_createur_non_deduite_du_nom=True) for name,count in sorted(contexts.items()) if name!='DayZ_officiel'])
    write_csv(root/'journal_non_importes.csv',[dict(id_anomalia=r['id'],classe=r['classname'],contexte=r['mod'],categorie=r['categoryCode'],
             raison='Modele original ou licence UE5 et integration gameplay non verifies',source=r['sourceUrls'][0],integre_UE5=False,fonctionnel=False,teste=False) for r in records])
    for label,reason in [('DayZ_CfgVehicles','Registre client complet config.bin/PBO non fourni'),('DayZ_CfgWeapons','Registre client complet config.bin/PBO non fourni'),('DayZ_CfgMagazines','Registre client complet config.bin/PBO non fourni'),('DayZ_CfgAmmo','Registre client complet config.bin/PBO non fourni')]:
        gaps.append(dict(type='registre_runtime_manquant',identifiant=label,raison=reason,source='https://github.com/BohemiaInteractive/DayZ-Script-Diff',action='Exporter seulement les noms et parents depuis une installation possedee; les scripts ne prouvent pas toutes les definitions config.'))
    gaps.append(dict(type='source_http',identifiant='PolyHaven_API',raison='HTTP 403 sur assets?t=models',source='https://api.polyhaven.com/assets?t=models',action='Les candidats du registre ANOMALIA existant sont listes separement; ne pas contourner le refus.'))
    write_csv(root/'sources_manquantes_et_blocages.csv',gaps)
    maps={'Chernarus':'chernarusplus','Livonia':'enoch','Sakhal':'sakhal','Nasdara':'nasdara'}
    sets={};counts={}
    for name,folder in maps.items():
        file=Path('dayz-official')/('dayzOffline.'+folder)/'db/types.xml'
        classes=ET.parse(file).getroot().findall('type');sets[name]={row.get('name') for row in classes}
        counts[name]=dict(typeEntries=len(classes),exactClassnames=len(sets[name]),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),nominalZero=sum(row.findtext('nominal')=='0' for row in classes))
    union=set.union(*sets.values())
    write_csv(root/'presence_classes_quatre_cartes.csv',[dict(classe=classname,**{name:classname in names for name,names in sets.items()},signification='Presence dans types.xml; absence ne prouve pas absence du jeu') for classname in sorted(union)])
    (root/'verification_quatre_cartes.json').write_text(json.dumps(dict(maps=counts,unionExactClassnames=len(union),completeRuntimeRegistry=False),indent=2))
    # Keep observations, world entities and static editor props usable separately.
    for kind,file in [('world_editor','catalogue_monde_editor.json'),('world_entity','catalogue_entites_monde.json')]:
        (root/file).write_text(json.dumps(dict(schemaVersion=1,referenceOnly=True,complete=False,records=[r for r in records if r['recordKind']==kind]),ensure_ascii=False,separators=(',',':')))
    summary=json.loads((root/'verification_extraction.json').read_text())
    summary.update(priorityModsExamined=len(rows),priorityModsWithApiMetadata=sum(r['metadata_api_obtenue'] for r in rows),priorityModsWithConfigEvidence=sum(r['fiches_avec_definition_config']>0 for r in rows),priorityModsWithAnyClassReference=sum(r['references']>0 for r in rows),currentFourMapCounts=counts)
    (root/'verification_extraction.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print({k:v for k,v in summary.items() if k not in ('caseSensitiveCollisions','currentFourMapCounts')})

if __name__=='__main__':main()
