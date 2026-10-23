"""Keep every user request visible; visual references never count as finished vehicles."""
import argparse
import collections
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MILITARY={'military_aircraft','military_helicopters','naval','submarines','military_motorcycles','armored_tactical','military_trucks','air_defense','anti_tank','coastal_defense'}
LINKS={
 'military_aircraft_c_130_hercules':['c130_hercules'],
 'military_aircraft_eurofighter_typhoon':['eurofighter_typhoon'],
 'military_helicopters_ah_64_apache':['ah64d_apache'],
 'military_helicopters_mil_mi_24_hind':['mi24_hind'],
 'armored_tactical_m1a2_abrams':['m1a2_abrams'],
 'naval_classe_arleigh_burke':['arleigh_burke'],
 'submarines_classe_ohio':['ohio_ssgn'],
 'armored_tactical_humvee':['humvee_hmmwv'],
 'civilian_and_utility_aliases_m1025':['humvee_hmmwv'],
 'naval_landing_craft_air_cushion':['lcac'],
 'submarines_classe_seawolf':['seawolf']
}
LABELS={'military_aircraft':'Avions militaires','military_helicopters':'Hélicoptères militaires','naval':'Navires militaires','submarines':'Sous-marins','military_motorcycles':'Motos militaires','armored_tactical':'Chars et blindés','military_trucks':'Camions militaires','air_defense':'Défense antiaérienne','anti_tank':'Véhicules antichars','coastal_defense':'Défense côtière','civilian_and_utility_aliases':'Véhicules et alias supplémentaires','audi':'Audi','mercedes_benz':'Mercedes-Benz','bmw':'BMW','bmw_3_generations':'BMW Série 3 par génération','bmw_5_generations':'BMW Série 5 par génération','bmw_7_generations':'BMW Série 7 par génération','bmw_iconic_coupes':'BMW coupés','bmw_x_generations':'BMW X par génération'}

def build():
    folder=ROOT/'docs/vehicles';index=json.loads((folder/'requested-models-index.json').read_text());rows=[];earlier=[]
    for item in index['registers']:
        register=json.loads((folder/item['file']).read_text());assert len(register['models'])==item['groupedRequestCount']
        earlier+=register.get('earlierRequestsRetained',[])
        for request in register['models']:
            military=request['category'] in MILITARY or request['requestId']=='civilian_and_utility_aliases_m1025'
            rows.append(dict(requestId=request['requestId'],requestedLabel=request['requestedLabel'],category=request['category'],domain=request['requestedDomain'],militaryRelated=military,sourceRegister=item['file'],relatedPriorRequests=request.get('relatedPriorRequests',[]),variantLabelPreserved=True,exactVehicleFinished=False,referenceSources=[],state='MODELE_EXACT_A_PRODUIRE_OU_ACQUERIR'))
    assert len(rows)==index['groupedRequestCount'] and len({r['requestId'] for r in rows})==len(rows)
    sources={m['id']:m for name in ['military-assets-sources.json','military-assets-extension-sources.json'] for m in json.loads((folder/name).read_text())['models']}
    for row in rows:
        for key in LINKS.get(row['requestId'],[]):
            if key in sources:row['referenceSources'].append(dict(assetId=key,url=sources[key]['url'],state='SOURCE_VISUELLE_CONFIGUREE_IMPORT_ET_VARIANTE_A_VERIFIER'))
        if row['referenceSources']:row['state']='REFERENCE_VISUELLE_PARTIELLE_VEHICULE_NON_TERMINE'
    summary=dict(groupedRequests=len(rows),militaryCategoryRequests=sum(r['category'] in MILITARY for r in rows),militaryAliasRequests=sum(r['requestId']=='civilian_and_utility_aliases_m1025' for r in rows),militaryRelatedGroupedRequests=sum(r['militaryRelated'] for r in rows),civilianGroupedRequests=sum(not r['militaryRelated'] for r in rows),additionalMetroRequest=True,exactVehiclesFullyValidated=0)
    report=dict(schemaVersion=1,scope='ALL_REQUESTS_RETAINED_NOT_A_FINISHED_VEHICLE_CATALOGUE',summary=summary,variantPolicy=index['variantPolicy'],notes=['One grouped request may name several chassis, body styles or weapon configurations. None is silently dropped.','An artist reference variant does not validate the complete requested group.','The M1025 alias overlaps the Humvee family but remains a separate explicit request.','The earlier generic vehicle requests and the additional metro remain in scope.'],earlierGenericRequests=earlier,requests=rows,metro=json.loads((folder/'metro-extension-2026-10-21.json').read_text()))
    lines=['# Liste complète des véhicules demandés','',f"{summary['groupedRequests']} entrées groupées conservées : {summary['militaryCategoryRequests']} entrées dans les catégories militaires, plus l’alias M1025/Humvee, et {summary['civilianGroupedRequests']} autres entrées. Le métro et ses wagons s’ajoutent à cette liste.",'','Une entrée peut regrouper plusieurs versions. Toutes les désignations sont conservées. Aucun véhicule exact n’a encore satisfait tous les critères de conduite, de physique, d’habitacle, de dégâts et de multijoueur. Une référence visuelle est une étape de travail.','', '## Ensemble militaire à traiter','']
    categories=list(dict.fromkeys(r['category'] for r in rows if r['militaryRelated']))
    for category in categories:
        members=[r for r in rows if r['category']==category and r['militaryRelated']]
        lines+=['### '+LABELS[category], '', '| Demande originale | État concret |','| --- | --- |']
        for row in members:
            state='Référence visuelle : '+', '.join(r['assetId'] for r in row['referenceSources'])+' ; véhicule encore à terminer' if row['referenceSources'] else 'Modèle exact à produire ou acquérir'
            lines.append('| '+row['requestedLabel'].replace('|','/')+' | '+state+' |')
        lines+=['']
    lines+=['## Autres véhicules à traiter','']
    for category in dict.fromkeys(r['category'] for r in rows if not r['militaryRelated']):
        lines+=['### '+LABELS[category],'','| Demande originale | État |','| --- | --- |']
        for row in rows:
            if row['category']==category and not row['militaryRelated']:lines.append('| '+row['requestedLabel'].replace('|','/')+' | Variante exacte et comportement à valider |')
        lines+=['']
    lines+=['## Métro et demandes génériques antérieures','','Métro : motrice et voiture voyageurs importées dans Unreal ; trois voitures suiveuses dans le code serveur. La rame complète, les passagers et les portes ne sont pas encore validés en jeu.','','Les demandes antérieures restent conservées : '+', '.join(earlier)+'.','']
    return report,'\n'.join(lines)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();report,markdown=build()
    outputs={'full-vehicle-worklist.json':json.dumps(report,ensure_ascii=False,indent=2)+'\n','FULL_VEHICLE_WORKLIST.md':markdown}
    for name,text in outputs.items():
        file=ROOT/'docs/vehicles'/name
        if args.check:
            if not file.exists():raise RuntimeError('Missing complete worklist: '+name)
            if name.endswith('.json'):
                saved=json.loads(file.read_text())
                actual={r['requestId']:r for r in saved['requests']}
                if len(actual)!=len(report['requests']) or len(saved['requests'])!=len(actual):raise RuntimeError('Missing or duplicate original vehicle request')
                # Sourcing is edited incrementally. Preserve its evidence while checking the immutable request identity.
                for row in report['requests']:
                    for key in ['requestId','requestedLabel','category','domain','militaryRelated','sourceRegister','relatedPriorRequests','variantLabelPreserved']:
                        if actual[row['requestId']].get(key)!=row[key]:raise RuntimeError('Original request changed: '+row['requestId']+'/'+key)
                for key,value in report['summary'].items():
                    if saved['summary'].get(key)!=value:raise RuntimeError('Request summary changed: '+key)
            else:
                saved=file.read_text()
                for row in report['requests']:
                    if row['requestedLabel'].replace('|','/') not in saved:raise RuntimeError('Request absent from readable worklist: '+row['requestId'])
        else:
            if file.exists() and name.endswith('.json'):
                prior=json.loads(file.read_text());previous={r['requestId']:r for r in prior.get('requests',[])}
                for row in report['requests']:
                    evidence=previous.get(row['requestId'],{})
                    for key,value in evidence.items():
                        if key not in row or key in ['referenceSources','state']:row[key]=value
                report={**prior,**report};text=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
            elif file.exists():
                # The readable worklist contains later sourcing notes; never erase them on regeneration.
                previous=file.read_text()
                missing=[r['requestedLabel'].replace('|','/') for r in report['requests'] if r['requestedLabel'].replace('|','/') not in previous]
                text=previous+('\n## Requests restored\n\n'+'\n'.join('- '+label for label in missing)+'\n' if missing else '')
            file.write_text(text)
    print(json.dumps(report['summary']))
if __name__=='__main__':main()
