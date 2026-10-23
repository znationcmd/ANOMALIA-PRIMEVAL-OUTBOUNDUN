# ANOMALIA — bâtiments, végétation et décoration
Mise à jour : 23 octobre 2026. Complément au [suivi des véhicules](../vehicles/FULL_VEHICLE_WORKLIST.md).
Objectif : véritables ressources 3D détaillées et texturées, proportions réalistes et cohérence du monde. Un prototype géométrique ou une fiche de vente ne vaut pas validation finale.

## Ressources déjà consignées — ne pas les rechercher de nouveau
Le [manifeste existant](realism-validation-sources.json) contient sources, licences annoncées, tailles et empreintes de fichiers. Le [rapport de validation](REALISM_VALIDATION_20261022.md) décrit une carte séparée de validation et ses limites. Son contenu ne prouve pas que toute la carte jouable possède ces ressources.

| Groupe | Source existante | Couverture restante |
| --- | --- | --- |
| Maison individuelle à étage | Innerscene detached_house, manifeste existant | Une maison ne couvre pas villages, lotissements, HLM ou villas avec piscine. Intérieurs meublés et portes fonctionnelles à terminer/valider. |
| Arbre | Poly Haven Island Tree 02, manifeste existant | Diversité d'essences, biomes, densités, vent et collisions à couvrir. |
| Herbe, rochers, sol forestier, asphalte | Poly Haven, manifeste existant | Ne couvre pas toute la végétation, les routes, les matériaux et les décors demandés. |

## Nouvelles sources candidates
| ID | Source | Ce qui est annoncé | État réel |
| --- | --- | --- | --- |
| buildings_modular | [Modular Building Set](https://www.fab.com/listings/474a0598-ed86-40b6-baa1-c801d96ef4ab) | Gratuit, Unreal, pièces modulaires réalistes. Intérieurs prévus seulement au premier niveau présenté; mobilier intérieur non fourni. | Candidat; licence à relever à l'acquisition, fichiers et UE 5.8 non testés. Ne couvre pas automatiquement les HLM ni tous les bâtiments accessibles. |
| trees_hornbeam | [European Hornbeam](https://www.fab.com/listings/c6f917b6-ffcb-4b86-9d9f-5274ba7f6a8e) | Gratuit, Unreal, 27 variantes : 10 arbres de forêt, 4 de champ, 8 jeunes arbres et 5 semis; vent/saisons et LOD annoncés. | Fiche ouverte; aucun téléchargement ni import. Une seule essence déclinée, pas 27 espèces. Respecter restrictions NoAI annoncées. |
| urban_park | [City Park Environment Collection](https://www.fab.com/listings/11cc2abb-126c-4452-9fe4-6f2381d96544) | Gratuit, Unreal. Parc, végétation, bancs, ponts, statues, fontaines, kiosques, aires de jeux, poubelles. [Présentation Epic](https://www.unrealengine.com/blog/free-city-park-environment-collection-now-available) | Candidat commun à végétation/décorations; ne pas compter le même pack deux fois. Détail visuel et performance sur UE 5.8 à tester. |

La gratuité d'une ancienne promotion ne suffit pas : Modular Old Town a été offert temporairement en septembre 2024; ne pas le classer gratuit aujourd'hui sans vérifier la fiche actuelle. Aucun achat autorisé par ce suivi.

## Groupes à couvrir explicitement
Les exemples ci-dessous décrivent le périmètre demandé; ils ne constituent pas un catalogue de ressources déjà trouvées.

| ID stable | Demande | État de recherche |
| --- | --- | --- |
| world_hlm | HLM, immeubles d'habitation et cités dans les grandes villes | Source spécifique à rechercher; pack modulaire seulement partiel |
| world_residences | Résidences, appartements, halls, escaliers et balcons | À rechercher; aucun ensemble complet validé |
| world_lotissements | Lotissements, maisons et jardins | Une maison déjà référencée; diversité à compléter |
| world_villas_pool | Villas avec piscine en bord de plage | Ressources réalistes spécifiques à rechercher |
| world_villages | Villages et maisons régionales | À rechercher et assembler |
| world_shops | Commerces et bâtiments de ville | Pack modulaire candidat partiel |
| world_hospital | Hôpitaux et espaces médicaux | À rechercher |
| world_emergency | Police, gendarmerie, casernes de pompiers | À rechercher |
| world_military | Bases militaires et bunkers | À rechercher |
| world_farms | Fermes, granges et bâtiments agricoles | À rechercher |
| world_ports | Ports et bâtiments portuaires | À rechercher |
| world_airports | Aéroports, hangars et tours de contrôle | À rechercher |
| world_stations | Gares ferroviaires, stations de métro et tunnels | À rechercher; véhicules suivis dans le registre véhicule |
| world_roads | Routes, autoroutes, chemins, ponts et tunnels | Asphalte référencé; ouvrages et ensemble du réseau à compléter |
| nature_forest | Arbres et forêts tempérées | Island Tree 02 existant, charme européen candidat; diversité à compléter |
| nature_jungle | Arbres tropicaux, jungle et végétation de plage | À rechercher |
| nature_ground | Buissons, herbes, fleurs, fougères et végétation basse | Herbe existante et parc candidat; ensemble incomplet |
| nature_rocks | Rochers, sols, falaises et grottes | Rochers/sol forestier existants; autres groupes à compléter |
| decor_rooms | Mobilier chambres et salons | À rechercher |
| decor_kitchen | Cuisines et équipements | À rechercher |
| decor_bathroom | Salles de bains et sanitaires | À rechercher |
| decor_storage | Armoires, étagères et rangement | À rechercher |
| decor_lights | Éclairages intérieurs et extérieurs | À rechercher; ressources du parc à inventorier |
| decor_street | Bancs, poubelles, panneaux, lampadaires et mobilier urbain | Parc candidat partiel; inventaire exact à vérifier |
| decor_gardens | Clôtures, portails, terrasses, jardins et décoration de piscine | À rechercher; parc candidat partiel |
| decor_small | Petits objets, tableaux et accessoires de décoration | À rechercher |

## Règles de mise à jour
- Consulter d'abord ce fichier et les manifestes existants. Conserver chaque ID, source et motif de refus; ajouter les nouvelles sources au groupe correspondant.
- Une source commune à plusieurs catégories reste une seule ressource. Les versions/formats alternatifs ne sont pas de nouveaux modèles.
- États séparés : source repérée, accès/licence vérifiés, fichier inspecté, import Unreal, rendu validé, interactions/collisions validées, performance/multijoueur/sauvegarde vérifiés.
- Pour les bâtiments : tester ouvertures, étages accessibles, collisions, portes, éclairage et placement du mobilier. Pour les végétaux : LOD, vent, matériaux et densité. Pour les objets : échelle, collision et placement.
- Les exclusions agricoles et maritimes du propriétaire restent appliquées. Aucun fichier ni fonctionnalité existante à supprimer.
- Cette mise à jour ajoute des références et un suivi. Aucun nouveau modèle téléchargé ou importé, aucune nouvelle compilation ni validation visuelle exécutée.
