# ANOMALIA — suivi commun des ressources 3D
Mise à jour : 23 octobre 2026.

Ce registre complète le [suivi des véhicules](../vehicles/FULL_VEHICLE_WORKLIST.md) et celui des [bâtiments et décors](FULL_ENVIRONMENT_WORKLIST.md). Données structurées : [asset-sourcing-register.json](asset-sourcing-register.json).

## État concret
- 69 nouvelles fiches regroupées sans URL en double : 49 ressources Poly Haven CC0 et 20 candidats Sketchfab indexés.
- 314 identifiants uniques des deux catalogues d'objets conservés : 35 avec au moins une source candidate, 279 encore sans source dans ce registre. La double référence car_battery est fusionnée dans le suivi seulement; les fichiers de gameplay sont inchangés.
- Les 210 demandes groupées de véhicules sont conservées. 15 groupes ont des candidats de recherche, 32 des variantes déjà référencées, 11 uniquement une référence historique, 152 aucun candidat enregistré.
- 12 pièces de construction et 14 types d'objets homestead sont également recensés séparément; ils ne sont pas additionnés aux 314 IDs.
- 49 sources Poly Haven téléchargées avec leurs buffers et textures, vérification de dépendances et SHA-256. 32 IDs ont au moins un candidat téléchargé. Aucun import Unreal, compilation ou validation de rendu exécuté ici. Voir [le reçu](item-source-download-receipt-20261023.json) et [les instructions Work](ITEMS_WORK_HANDOFF_20261023.md).

## Lire les états correctement
PAGE_LUE décrit la consultation initiale de la fiche. Les 49 sources Poly Haven ont depuis été récupérées; collisions, échelle, rig, gameplay et rendu UE restent à vérifier. INDEX_SEUL signifie candidat trouvé dans l'index de recherche; de nombreuses pages Sketchfab ont répondu HTTP 403. La licence annoncée ne prouve pas les droits de l'uploader. Aucune source n'est marquée comme intégrée.

Les 49 ressources Poly Haven suivent la [licence CC0 publiée par le fournisseur](https://polyhaven.com/license). Les sources Sketchfab restent soumises à vérification de provenance et à attribution. Une base civile ou générique ne valide pas une version militaire, une carrosserie ou un modèle précis.

## Véhicules, bâtiments et objets trouvés
| ID source | Ressource | Correspondances | Vérification restante |
| --- | --- | --- | --- |
| ph_hatchet | [Hachette](https://polyhaven.com/a/hatchet) | item:hatchet | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_wooden_axe | [Hache en bois](https://polyhaven.com/a/wooden_axe) | family:axes | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_screwdriver | [Tournevis](https://polyhaven.com/a/screwdriver) | item:screwdriver | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_flathead_screwdriver | [Tournevis plat](https://polyhaven.com/a/flathead_screwdriver) | item:screwdriver | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_pliers | [Pince](https://polyhaven.com/a/pliers) | item:pliers | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_crowbar_01 | [Pied-de-biche](https://polyhaven.com/a/crowbar_01) | item:crowbar | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_sledgehammer_01 | [Masse](https://polyhaven.com/a/sledgehammer_01) | item:sledgehammer | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_handsaw_wood | [Scie à bois](https://polyhaven.com/a/handsaw_wood) | item:handsaw | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_rusted_hacksaw | [Scie à métaux](https://polyhaven.com/a/rusted_hacksaw) | item:hacksaw | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_rusted_spade_01 | [Bêche](https://polyhaven.com/a/rusted_spade_01) | item:shovel | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_pipe_wrench | [Clé à griffe](https://polyhaven.com/a/pipe_wrench) | item:wrench | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_wooden_hammer_01 | [Marteau](https://polyhaven.com/a/wooden_hammer_01) | item:hammer | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_picke_dirty_01 | [Pioche](https://polyhaven.com/a/picke_dirty_01) | item:pickaxe | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_binoculars | [Jumelles](https://polyhaven.com/a/binoculars) | item:binoculars | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_portable_generator | [Générateur portable](https://polyhaven.com/a/portable_generator) | item:generator | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_small_plastic_torch | [Lampe torche](https://polyhaven.com/a/small_plastic_torch) | item:flashlight | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_portable_searchlight | [Projecteur portable](https://polyhaven.com/a/portable_searchlight) | family:floodlights | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_plastic_jerrycan | [Bidon plastique](https://polyhaven.com/a/plastic_jerrycan) | item:water_in_fuel_can | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_metal_jerrycan_green | [Jerrican métallique](https://polyhaven.com/a/metal_jerrycan_green) | item:water_in_fuel_can | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_Barrel_01 | [Fût métallique](https://polyhaven.com/a/Barrel_01) | item:metal_barrel | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_Barrel_02 | [Fût plastique](https://polyhaven.com/a/Barrel_02) | item:plastic_barrel | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_vintage_lighter | [Briquet](https://polyhaven.com/a/vintage_lighter) | item:lighter | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_brass_pan_01 | [Poêle](https://polyhaven.com/a/brass_pan_01) | item:frying_pan | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_brass_pot_02 | [Marmite](https://polyhaven.com/a/brass_pot_02) | item:cooking_pot | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_food_apple_01 | [Pomme](https://polyhaven.com/a/food_apple_01) | item:apple | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_food_pears_asian_01 | [Poires asiatiques](https://polyhaven.com/a/food_pears_asian_01) | item:pear | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_long_life_food | [Conserves et carton alimentaire](https://polyhaven.com/a/long_life_food) | item:canned_beans, item:sardines | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_wine_bottles_01 | [Bouteilles de vin et vin pétillant](https://polyhaven.com/a/wine_bottles_01) | item:red_wine, item:white_wine, item:rose_wine, item:champagne | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_medical_box | [Boîte de soins](https://polyhaven.com/a/medical_box) | item:rp_recovery_kit | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_medical_tape | [Ruban médical](https://polyhaven.com/a/medical_tape) | family:medical | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_old_gas_mask | [Masque à gaz ancien](https://polyhaven.com/a/old_gas_mask) | item:gas_mask | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_digital_wrist_watch | [Montre numérique](https://polyhaven.com/a/digital_wrist_watch) | item:rp_watch | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_rubber_boots | [Bottes en caoutchouc](https://polyhaven.com/a/rubber_boots) | family:boots | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_cigarette_pack | [Paquet de cigarettes](https://polyhaven.com/a/cigarette_pack) | item:cigarette | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_propane_tank | [Bouteille de propane](https://polyhaven.com/a/propane_tank) | family:gas_containers | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_old_tyre | [Pneu usagé](https://polyhaven.com/a/old_tyre) | family:vehicle_tyres | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_service_pistol | [Pistolet de service](https://polyhaven.com/a/service_pistol) | family:handguns | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_bolt_action_rifle_7_62 | [Fusil à verrou 7,62](https://polyhaven.com/a/bolt_action_rifle_7_62) | family:rifles | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_Sofa_01 | [Canapé](https://polyhaven.com/a/Sofa_01) | env:decor_rooms, homestead:Sofa | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_Shelf_01 | [Étagère](https://polyhaven.com/a/Shelf_01) | env:decor_storage | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_painted_wooden_cabinet | [Meuble de rangement](https://polyhaven.com/a/painted_wooden_cabinet) | env:decor_storage | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_wooden_table_02 | [Table](https://polyhaven.com/a/wooden_table_02) | env:decor_rooms, homestead:Table | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_street_lamp_01 | [Lampadaire](https://polyhaven.com/a/street_lamp_01) | env:decor_lights, env:decor_street | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_modular_chainlink_fence | [Clôture grillagée modulaire](https://polyhaven.com/a/modular_chainlink_fence) | env:decor_gardens, homestead:Fence | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_pine_tree_01 | [Pin](https://polyhaven.com/a/pine_tree_01) | env:nature_forest | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_fir_tree_01 | [Sapins](https://polyhaven.com/a/fir_tree_01) | env:nature_forest | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_fern_02 | [Fougères](https://polyhaven.com/a/fern_02) | env:nature_ground | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_shrub_01 | [Buisson](https://polyhaven.com/a/shrub_01) | env:nature_ground | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| ph_watering_can_metal_01 | [Arrosoir](https://polyhaven.com/a/watering_can_metal_01) | family:farming_tools | Sources téléchargées, dépendances vérifiées ; import et validation UE à faire. |
| v_f35 | [F-35A](https://sketchfab.com/3d-models/f-35-a-lightning-ii-war-mode-full-pack-c2fd326b8a714c0d91d7d1b41e0a86e2) | vehicle:military_aircraft_f_35_lightning_ii | 1,2M triangles annoncés; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| v_f22 | [F-22 Raptor](https://sketchfab.com/3d-models/f22-raptor-free-2a64abf0866a405c865466c7642ca689) | vehicle:military_aircraft_f_22_raptor | Animation et textures Substance annoncées; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| v_mirage2000 | [Mirage 2000](https://sketchfab.com/3d-models/mirage-2000-b1a103c2c1fb463ebcf5a54004368221) | vehicle:military_aircraft_mirage_2000 | 32,7k triangles annoncés; fiche indexée complète. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| v_leclerc | [Char Leclerc](https://sketchfab.com/3d-models/char-leclerc-84a0918d2f534c2eb003ab3cb3029c03) | vehicle:armored_tactical_char_leclerc | L'auteur décrit une nouvelle texture de son ancien modèle; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| v_unimog | [Unimog Truck](https://sketchfab.com/3d-models/unimog-truck-72caf995b6064890b7bc62371cc79f36) | vehicle:military_trucks_mercedes_benz_unimog | Optimisation jeu et crédit auteur annoncés; version militaire à adapter; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| v_ka52 | [Ka-52 PBR](https://sketchfab.com/3d-models/pbr-kamov-ka-52-6f29175ef23940fcb4c5364240e169f7) | vehicle:military_helicopters_kamov_ka_52_alligator | PBR annoncé; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| v_b2 | [B-2 Spirit PBR](https://sketchfab.com/3d-models/pbr-b-2-spirit-b16592b1083948a49ae2afa90d190a08) | vehicle:military_aircraft_b_2_spirit | PBR annoncé; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| v_q5 | [Audi Q5 Sportback](https://sketchfab.com/3d-models/2022-audi-q5-s-line-sportback-7f3ddb0b4ff840b68890781234fc521d) | vehicle:audi_q5_q5_sportback | Version Sportback seulement; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| v_e46 | [BMW E46 MSport](https://sketchfab.com/3d-models/bmw-e46-msport-614c2f1660474178a1d4717b7492d1c7) | vehicle:bmw_3_generations_e46 | Variante E46 seulement; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| v_rib | [Bateau pneumatique d'assaut](https://sketchfab.com/3d-models/assault-boat-0d4fca4f2e014cd7b6aefd4653b1508c) | generic:supplement_2 | 4K PBR annoncé; correspond à la catégorie pneumatique, marque Zodiac non établie; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| v_sprinter_ambulance | [Ambulance Sprinter 413](https://sketchfab.com/3d-models/rettungswagen-krankenwagen-ambulance-e6c4858d34f0440394c2aa772ebaca38) | generic:generic_ambulance | Modèle crédité à Spaehling; origine et détails à contrôler. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| b_panel | [Immeuble résidentiel modulaire](https://sketchfab.com/3d-models/modular-russian-panel-house-7bef9b27b4c54a03b64e2f395fef3d7f) | env:world_hlm, env:world_residences | Architecture résidentielle russe; référence partielle pour immeubles, pas un HLM français certifié; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| b_villa | [Villa avec piscine et intérieur](https://sketchfab.com/3d-models/small-villa-6fc3a756dacd40af8c6e4e3b8e674ea2) | env:world_villas_pool | 113,9k triangles; cuisine/bureau/salle de bains/chambre annoncés. NoAI à respecter. Page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| b_hospital | [Hôpital de Pori, bâtiment principal](https://sketchfab.com/3d-models/pori-city-hospital-16-main-hospital-building-1acf49182b3a4248a0dc1cddb2e2e976) | env:world_hospital | Fiche publiée le 25 septembre 2026; intérieur non confirmé; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| b_fire | [Caserne de pompiers](https://sketchfab.com/3d-models/fire-station-34988c59a010496cacc06d0580a116dd) | env:world_emergency | Textures et formats OBJ/FBX annoncés; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| b_police | [Poste de police urbain](https://sketchfab.com/3d-models/city-police-station-f6ba27f0426c4eefabce32d17e87fd35) | env:world_emergency | Modélisation 3ds Max et textures annoncées; ne valide pas gendarmerie française; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| b_shed | [Abri agricole usé](https://sketchfab.com/3d-models/worn-shed-pbr-game-ready-be6edd62e55a4f9a99da940fc164a5b9) | env:world_farms, homestead:TractorShed | PBR et porte séparée annoncés; dimensions pour tracteur non vérifiées; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| i_m4a1 | [Colt M4A1](https://sketchfab.com/3d-models/colt-m4a1-carbine-fa4a73faf4234e5db4066335074a7655) | item:m4a1 | FBX, PBR 4K, viseur 2K annoncés; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| i_famas | [FAMAS](https://sketchfab.com/3d-models/famas-7d35e14ad8874d148ce9cc46e5765a6b) | item:famas | Variante exacte et PBR à vérifier; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |
| i_backpack | [Sac tactique PBR](https://sketchfab.com/3d-models/tactical-backpack-game-ready-pbr-dea541825b8d4fd5a8c4fbb68f0ed62f) | item:assault_backpack | Base candidate pour sac d'assaut; adaptation au corps à vérifier; page directe HTTP 403. Aucun fichier inspecté; licence, provenance, intérieur et réalisme à vérifier. |

## Les 314 objets, sans omission
Un candidat peut nécessiter une adaptation ou ne couvrir qu'une variante; consulter sa note ci-dessus. A_RECHERCHER signifie absence de source dans ce registre, pas preuve qu'aucun modèle n'existe. Les comportements de gameplay antérieurement testés ne sont pas réévalués par cette recherche.

| ID objet | Libellé | Catégorie | Sources candidates |
| --- | --- | --- | --- |
| m4a1 | M4A1 | assault_weapons | i_m4a1 |
| akm | AKM | assault_weapons | À rechercher |
| ak74 | AK74 | assault_weapons | À rechercher |
| aks74u | AKS74U | assault_weapons | À rechercher |
| fal_lar | FAL LAR | assault_weapons | À rechercher |
| ka101 | KA101 | assault_weapons | À rechercher |
| m16a2 | M16A2 | assault_weapons | À rechercher |
| aug_a1 | AUG A1 | assault_weapons | À rechercher |
| aug_ax | AUG AX | assault_weapons | À rechercher |
| famas | FAMAS | assault_weapons | i_famas |
| mosin_9130 | Mosin 9130 | hunting_precision_weapons | À rechercher |
| blaze | Blaze | hunting_precision_weapons | À rechercher |
| tundra | Tundra | hunting_precision_weapons | À rechercher |
| cr527 | CR527 | hunting_precision_weapons | À rechercher |
| savanna | Savanna | hunting_precision_weapons | À rechercher |
| winchester70 | Winchester70 | hunting_precision_weapons | À rechercher |
| vsd_svd | VSD SVD | hunting_precision_weapons | À rechercher |
| vss | VSS | hunting_precision_weapons | À rechercher |
| pioneer | Pioneer | hunting_precision_weapons | À rechercher |
| scout | Scout | hunting_precision_weapons | À rechercher |
| m24 | M24 | hunting_precision_weapons | À rechercher |
| mlock91 | Mlock91 | handguns_smg_shotguns | À rechercher |
| fx45 | FX45 | handguns_smg_shotguns | À rechercher |
| ij70 | IJ70 | handguns_smg_shotguns | À rechercher |
| kolt1911 | Kolt1911 | handguns_smg_shotguns | À rechercher |
| deagle | Deagle | handguns_smg_shotguns | À rechercher |
| cr75 | CR75 | handguns_smg_shotguns | À rechercher |
| p1 | P1 | handguns_smg_shotguns | À rechercher |
| derringer | Derringer | handguns_smg_shotguns | À rechercher |
| amphibias | AmphibiaS | handguns_smg_shotguns | À rechercher |
| usg45_ump | USG45 UMP | handguns_smg_shotguns | À rechercher |
| sg5k_mp5 | SG5K MP5 | handguns_smg_shotguns | À rechercher |
| bk133 | BK133 | handguns_smg_shotguns | À rechercher |
| bk43 | BK43 | handguns_smg_shotguns | À rechercher |
| bk12 | BK12 | handguns_smg_shotguns | À rechercher |
| bizon | Bizon | handguns_smg_shotguns | À rechercher |
| scorpion | Scorpion | handguns_smg_shotguns | À rechercher |
| 308_win | 308 Win | ammunition | À rechercher |
| 762x54r | 762x54R | ammunition | À rechercher |
| 762x39 | 762x39 | ammunition | À rechercher |
| 556x45 | 556x45 | ammunition | À rechercher |
| 545x39 | 545x39 | ammunition | À rechercher |
| 9x19 | 9x19 | ammunition | À rechercher |
| 45_acp | 45 ACP | ammunition | À rechercher |
| 380_auto | 380 Auto | ammunition | À rechercher |
| 22_lr | 22 LR | ammunition | À rechercher |
| 12g_buckshot | 12g buckshot | ammunition | À rechercher |
| 12g_slug | 12g slug | ammunition | À rechercher |
| 12g_rubber | 12g rubber | ammunition | À rechercher |
| hunting_scope | hunting scope | weapon_accessories | À rechercher |
| pso1_scope | PSO1 scope | weapon_accessories | À rechercher |
| acog_scope | ACOG scope | weapon_accessories | À rechercher |
| kobra_sight | Kobra sight | weapon_accessories | À rechercher |
| rifle_suppressor | rifle suppressor | weapon_accessories | À rechercher |
| pistol_suppressor | pistol suppressor | weapon_accessories | À rechercher |
| bottle_suppressor | bottle suppressor | weapon_accessories | À rechercher |
| stanag_magazine | STANAG magazine | weapon_accessories | À rechercher |
| ak_magazine | AK magazine | weapon_accessories | À rechercher |
| weapon_cleaning_kit | weapon cleaning kit | weapon_accessories | À rechercher |
| fire_axe | fire axe | tools | À rechercher |
| hatchet | hatchet | tools | ph_hatchet |
| sledgehammer | sledgehammer | tools | ph_sledgehammer_01 |
| shovel | shovel | tools | ph_rusted_spade_01 |
| pickaxe | pickaxe | tools | ph_picke_dirty_01 |
| hacksaw | hacksaw | tools | ph_rusted_hacksaw |
| handsaw | handsaw | tools | ph_handsaw_wood |
| screwdriver | screwdriver | tools | ph_screwdriver, ph_flathead_screwdriver |
| pliers | pliers | tools | ph_pliers |
| crowbar | crowbar | tools | ph_crowbar_01 |
| hammer | hammer | tools | ph_wooden_hammer_01 |
| wrench | wrench | tools | ph_pipe_wrench |
| hunting_knife | hunting knife | tools | À rechercher |
| kitchen_knife | kitchen knife | tools | À rechercher |
| bone_knife | bone knife | tools | À rechercher |
| chainsaw | chainsaw | tools | À rechercher |
| nails_box | nails box | craft_materials | À rechercher |
| wire | wire | craft_materials | À rechercher |
| barbed_wire | barbed wire | craft_materials | À rechercher |
| metal_sheet | metal sheet | craft_materials | À rechercher |
| camo_net | camo net | craft_materials | À rechercher |
| rope | rope | craft_materials | À rechercher |
| burlap | burlap | craft_materials | À rechercher |
| duct_tape | duct tape | craft_materials | À rechercher |
| animal_hide | animal hide | craft_materials | À rechercher |
| tree_bark | tree bark | craft_materials | À rechercher |
| log | log | craft_materials | À rechercher |
| plank | plank | craft_materials | À rechercher |
| long_stick | long stick | craft_materials | À rechercher |
| short_stick | short stick | craft_materials | À rechercher |
| hiking_backpack | hiking backpack | backpacks | À rechercher |
| field_backpack | field backpack | backpacks | À rechercher |
| hunting_backpack | hunting backpack | backpacks | À rechercher |
| drysack | drysack | backpacks | À rechercher |
| assault_backpack | assault backpack | backpacks | i_backpack |
| improvised_backpack | improvised backpack | backpacks | À rechercher |
| hunting_jacket | hunting jacket | tops | À rechercher |
| bdu_jacket | BDU jacket | tops | À rechercher |
| field_jacket | field jacket | tops | À rechercher |
| tactical_jacket | tactical jacket | tops | À rechercher |
| firefighter_jacket | firefighter jacket | tops | À rechercher |
| gorka_jacket | gorka jacket | tops | À rechercher |
| hi_vis_jacket | hi vis jacket | tops | À rechercher |
| sweater | sweater | tops | À rechercher |
| leather_jacket | leather jacket | tops | À rechercher |
| parka | parka | tops | À rechercher |
| raincoat | raincoat | tops | À rechercher |
| doctor_jacket | doctor jacket | tops | À rechercher |
| paramedic_jacket | paramedic jacket | tops | À rechercher |
| cargo_pants | cargo pants | pants | À rechercher |
| combat_pants | combat pants | pants | À rechercher |
| jeans | jeans | pants | À rechercher |
| hunting_pants | hunting pants | pants | À rechercher |
| firefighter_pants | firefighter pants | pants | À rechercher |
| doctor_pants | doctor pants | pants | À rechercher |
| paramedic_pants | paramedic pants | pants | À rechercher |
| ballistic_helmet | ballistic helmet | headwear | À rechercher |
| tactical_helmet | tactical helmet | headwear | À rechercher |
| motorcycle_helmet | motorcycle helmet | headwear | À rechercher |
| construction_helmet | construction helmet | headwear | À rechercher |
| cap | cap | headwear | À rechercher |
| beanie | beanie | headwear | À rechercher |
| cowboy_hat | cowboy hat | headwear | À rechercher |
| boonie_hat | boonie hat | headwear | À rechercher |
| balaclava | balaclava | headwear | À rechercher |
| gas_mask | gas mask | headwear | ph_old_gas_mask |
| gas_mask_filter | gas mask filter | headwear | À rechercher |
| plate_carrier | plate carrier | vests | À rechercher |
| press_vest | press vest | vests | À rechercher |
| tactical_vest | tactical vest | vests | À rechercher |
| flak_vest | flak vest | vests | À rechercher |
| military_boots | military boots | shoes_gloves | À rechercher |
| hiking_shoes | hiking shoes | shoes_gloves | À rechercher |
| rangers | rangers | shoes_gloves | À rechercher |
| hunting_boots | hunting boots | shoes_gloves | À rechercher |
| work_gloves | work gloves | shoes_gloves | À rechercher |
| surgical_gloves | surgical gloves | shoes_gloves | À rechercher |
| tactical_gloves | tactical gloves | shoes_gloves | À rechercher |
| sterile_bandage | Bandage stérile | medical_supplies | À rechercher |
| rags | Chiffons pour pansement | medical_supplies | À rechercher |
| morphine | Antalgique médical RP | medical_supplies | À rechercher |
| epinephrine | Stimulant médical RP | medical_supplies | À rechercher |
| blood_test_kit | Kit de diagnostic sanguin | medical_supplies | À rechercher |
| blood_bag | Poche de sang (soins simplifiés) | medical_supplies | À rechercher |
| iv_kit | iv kit | medical_supplies | À rechercher |
| saline | Solution de perfusion (jeu) | medical_supplies | À rechercher |
| splint | Attelle — soulagement provisoire | medical_supplies | À rechercher |
| tetracycline | Antibiotique RP | medicine | À rechercher |
| charcoal_tablets | Traitement antitoxique RP | medicine | À rechercher |
| water_purification_tablets | Traitement pour eau — objet de jeu | medicine | À rechercher |
| vitamins | Vitamines RP | medicine | À rechercher |
| iodine | Antiseptique RP | hygiene | À rechercher |
| disinfectant_spray | Désinfectant pour plaies RP | hygiene | À rechercher |
| alcohol_90 | Alcool antiseptique — usage externe RP | hygiene | À rechercher |
| canned_bacon | Bacon en conserve | canned_food | À rechercher |
| canned_peaches | Pêches en conserve | canned_food | À rechercher |
| canned_beans | Haricots en conserve | canned_food | ph_long_life_food |
| sardines | Sardines en conserve | canned_food | ph_long_life_food |
| tuna | Thon en conserve | canned_food | À rechercher |
| pate | Pâté en conserve | canned_food | À rechercher |
| cat_food | Nourriture pour chat | canned_food | À rechercher |
| dog_food | Nourriture pour chien | canned_food | À rechercher |
| beef | Viande bovine crue | fresh_food | À rechercher |
| pork | Viande de porc crue | fresh_food | À rechercher |
| chicken | Volaille crue | fresh_food | À rechercher |
| animal_fat | Graisse animale | fresh_food | À rechercher |
| apple | Pomme | fresh_food | ph_food_apple_01 |
| pear | Poire | fresh_food | ph_food_pears_asian_01 |
| plum | Prune | fresh_food | À rechercher |
| tomato | Tomate | fresh_food | À rechercher |
| potato | Pomme de terre | fresh_food | À rechercher |
| mushroom | Champignon non identifié | fresh_food | À rechercher |
| raw_fish | Poisson cru | fresh_food | À rechercher |
| pipsi | Pipsi | drinks | À rechercher |
| notacola | Notacola | drinks | À rechercher |
| spite | Spite | drinks | À rechercher |
| mad_monk | Mad Monk | drinks | À rechercher |
| vodka | Vodka RP | drinks | À rechercher |
| whisky | Whisky RP | drinks | À rechercher |
| rum | Rhum RP | drinks | À rechercher |
| red_wine | Vin rouge RP | drinks | ph_wine_bottles_01 |
| white_wine | Vin blanc RP | drinks | ph_wine_bottles_01 |
| rose_wine | Vin rosé RP | drinks | ph_wine_bottles_01 |
| champagne | Vin pétillant RP | drinks | ph_wine_bottles_01 |
| water_bottle | Bouteille d’eau | drinks | À rechercher |
| military_canteen | Gourde militaire | drinks | À rechercher |
| water_in_fuel_can | water in fuel can | drinks | ph_plastic_jerrycan, ph_metal_jerrycan_green |
| filter_canteen | Gourde filtrante | drinks | À rechercher |
| cooking_pot | cooking pot | cooking | ph_brass_pot_02 |
| frying_pan | frying pan | cooking | ph_brass_pan_01 |
| portable_gas_stove | portable gas stove | cooking | À rechercher |
| gas_canister | gas canister | cooking | À rechercher |
| cooking_tripod | cooking tripod | cooking | À rechercher |
| matches | matches | cooking | À rechercher |
| lighter | lighter | cooking | ph_vintage_lighter |
| camping_tent | camping tent | camping_storage | À rechercher |
| military_tent | military tent | camping_storage | À rechercher |
| car_tent | car tent | camping_storage | À rechercher |
| plastic_barrel | plastic barrel | camping_storage | ph_Barrel_02 |
| metal_barrel | metal barrel | camping_storage | ph_Barrel_01 |
| crafted_wooden_crate | crafted wooden crate | camping_storage | À rechercher |
| sea_chest | sea chest | camping_storage | À rechercher |
| sleeping_bag | sleeping bag | camping_storage | À rechercher |
| bear_trap | bear trap | camping_storage | À rechercher |
| generator | generator | power_lighting | ph_portable_generator |
| cable_reel | cable reel | power_lighting | À rechercher |
| floodlight | floodlight | power_lighting | À rechercher |
| car_battery | car battery | power_lighting | À rechercher |
| 9v_battery | 9v battery | power_lighting | À rechercher |
| flashlight | flashlight | power_lighting | ph_small_plastic_torch |
| headlamp | headlamp | power_lighting | À rechercher |
| chemlight | chemlight | power_lighting | À rechercher |
| flare | flare | power_lighting | À rechercher |
| compass | compass | navigation | À rechercher |
| gps_player_map | gps player map | navigation | À rechercher |
| gps_receiver | gps receiver | navigation | À rechercher |
| binoculars | binoculars | navigation | ph_binoculars |
| rangefinder | rangefinder | navigation | À rechercher |
| walkie_talkie | walkie talkie | navigation | À rechercher |
| truck_battery | truck battery | vehicle_engine_parts | À rechercher |
| spark_plug | spark plug | vehicle_engine_parts | À rechercher |
| glow_plug | glow plug | vehicle_engine_parts | À rechercher |
| radiator | radiator | vehicle_engine_parts | À rechercher |
| wheel_ada | wheel ada | vehicle_body_parts | À rechercher |
| wheel_gunter | wheel gunter | vehicle_body_parts | À rechercher |
| wheel_olga | wheel olga | vehicle_body_parts | À rechercher |
| wheel_m1025 | wheel m1025 | vehicle_body_parts | À rechercher |
| truck_tire | truck tire | vehicle_body_parts | À rechercher |
| car_door | car door | vehicle_body_parts | À rechercher |
| car_hood | car hood | vehicle_body_parts | À rechercher |
| car_trunk | car trunk | vehicle_body_parts | À rechercher |
| replacement_headlight | replacement headlight | vehicle_body_parts | À rechercher |
| empty_water_bottle | Bouteille d’eau vide | camping_storage | À rechercher |
| empty_military_canteen | Gourde militaire vide | camping_storage | À rechercher |
| empty_filter_canteen | Gourde filtrante vide | camping_storage | À rechercher |
| dirty_water_bottle | Bouteille d’eau non traitée | drinks | À rechercher |
| eur_note_5 | Billet RP de 5 EUR | rp_cash | À rechercher |
| eur_note_10 | Billet RP de 10 EUR | rp_cash | À rechercher |
| eur_note_20 | Billet RP de 20 EUR | rp_cash | À rechercher |
| eur_note_50 | Billet RP de 50 EUR | rp_cash | À rechercher |
| eur_note_100 | Billet RP de 100 EUR | rp_cash | À rechercher |
| eur_note_200 | Billet RP de 200 EUR | rp_cash | À rechercher |
| eur_note_500 | Billet RP de 500 EUR | rp_cash | À rechercher |
| rp_wallet | Portefeuille | rp_valuables | À rechercher |
| rp_cash_bundle | Liasse RP scellée (objet, non convertible automatiquement) | rp_valuables | À rechercher |
| rp_jewellery | Bijou | rp_valuables | À rechercher |
| rp_watch | Montre | rp_valuables | ph_digital_wrist_watch |
| gold_bar_1g | Lingot d’or de 1 g | rp_precious_metals | À rechercher |
| gold_bar_10g | Lingot d’or de 10 g | rp_precious_metals | À rechercher |
| gold_bar_100g | Lingot d’or de 100 g | rp_precious_metals | À rechercher |
| gold_bar_250g | Lingot d’or de 250 g | rp_precious_metals | À rechercher |
| gold_bar_500g | Lingot d’or de 500 g | rp_precious_metals | À rechercher |
| gold_bar_1000g | Lingot d’or de 1000 g | rp_precious_metals | À rechercher |
| gold_nugget | Pépite d’or | rp_precious_metals | À rechercher |
| gold_ore | Minerai d’or | rp_precious_metals | À rechercher |
| silver_bar_100g | Lingot d’argent de 100 g | rp_precious_metals | À rechercher |
| platinum_bar_100g | Lingot de platine de 100 g | rp_precious_metals | À rechercher |
| rough_diamond | Diamant brut | rp_gemstones | À rechercher |
| cut_diamond | Diamant taillé | rp_gemstones | À rechercher |
| ruby | Rubis | rp_gemstones | À rechercher |
| emerald | Émeraude | rp_gemstones | À rechercher |
| sapphire | Saphir | rp_gemstones | À rechercher |
| amethyst | Améthyste | rp_gemstones | À rechercher |
| opal | Opale | rp_gemstones | À rechercher |
| cooked_beef | Viande bovine cuite | canned_food | À rechercher |
| cooked_pork | Viande de porc cuite | canned_food | À rechercher |
| cooked_chicken | Volaille cuite | canned_food | À rechercher |
| cooked_fish_fillet | Filet de poisson cuit | canned_food | À rechercher |
| bread_loaf | Pain | canned_food | À rechercher |
| rice_meal | Riz préparé | canned_food | À rechercher |
| vegetable_soup | Soupe de légumes | canned_food | À rechercher |
| orange_juice | Jus de fruits | drinks | À rechercher |
| drinking_water_carton | Eau potable en carton | drinks | À rechercher |
| rp_recovery_kit | Trousse de soins RP — intoxication | medical_supplies | ph_medical_box |
| rp_substance_cocaine | Cocaïne — accessoire RP | rp_substances | À rechercher |
| rp_substance_crack | Crack — accessoire RP | rp_substances | À rechercher |
| rp_substance_amphetamine | Amphétamine — accessoire RP | rp_substances | À rechercher |
| rp_substance_methamphetamine | Méthamphétamine — accessoire RP | rp_substances | À rechercher |
| rp_substance_mdma | MDMA — accessoire RP | rp_substances | À rechercher |
| rp_substance_methylphenidate | Méthylphénidate — accessoire RP | rp_substances | À rechercher |
| rp_substance_modafinil | Modafinil — accessoire RP | rp_substances | À rechercher |
| rp_substance_heroin | Héroïne — accessoire RP | rp_substances | À rechercher |
| rp_substance_opium | Opium — accessoire RP | rp_substances | À rechercher |
| rp_substance_fentanyl | Fentanyl — accessoire RP | rp_substances | À rechercher |
| rp_substance_oxycodone | Oxycodone — accessoire RP | rp_substances | À rechercher |
| rp_substance_codeine | Codéine — accessoire RP | rp_substances | À rechercher |
| rp_substance_tramadol | Tramadol — accessoire RP | rp_substances | À rechercher |
| rp_substance_methadone | Méthadone — accessoire RP | rp_substances | À rechercher |
| rp_substance_buprenorphine | Buprénorphine — accessoire RP | rp_substances | À rechercher |
| rp_substance_diazepam | Diazépam — accessoire RP | rp_substances | À rechercher |
| rp_substance_alprazolam | Alprazolam — accessoire RP | rp_substances | À rechercher |
| rp_substance_clonazepam | Clonazépam — accessoire RP | rp_substances | À rechercher |
| rp_substance_zolpidem | Zolpidem — accessoire RP | rp_substances | À rechercher |
| rp_substance_ghb | GHB — accessoire RP | rp_substances | À rechercher |
| rp_substance_barbiturates | Barbituriques — accessoire RP | rp_substances | À rechercher |
| rp_substance_lsd | LSD — accessoire RP | rp_substances | À rechercher |
| rp_substance_psilocybin | Psilocybine — accessoire RP | rp_substances | À rechercher |
| rp_substance_mescaline | Mescaline — accessoire RP | rp_substances | À rechercher |
| rp_substance_dmt | DMT — accessoire RP | rp_substances | À rechercher |
| rp_substance_ketamine | Kétamine — accessoire RP | rp_substances | À rechercher |
| rp_substance_pcp | PCP — accessoire RP | rp_substances | À rechercher |
| rp_substance_nitrous_oxide | Protoxyde — objet RP — accessoire RP | rp_substances | À rechercher |
| rp_substance_cannabis | Cannabis — accessoire RP | rp_substances | À rechercher |
| rp_substance_cannabis_resin | Résine de cannabis — accessoire RP | rp_substances | À rechercher |
| rp_substance_cannabis_oil | Huile de cannabis — accessoire RP | rp_substances | À rechercher |
| rp_substance_synthetic_cannabinoid | Cannabinoïde synthétique — accessoire RP | rp_substances | À rechercher |
| rp_substance_vet_sedative | Sédatif vétérinaire RP — accessoire RP | rp_substances | À rechercher |
| rp_substance_anomaly_azure | Composé fictif Azur — accessoire RP | rp_substances | À rechercher |
| rp_substance_anomaly_ember | Composé fictif Braise — accessoire RP | rp_substances | À rechercher |
| rp_substance_anomaly_spore | Spore fictive ANOMALIA — accessoire RP | rp_substances | À rechercher |
| cigarette_butt | Mégot | rp_tobacco | À rechercher |
| cigarette | Cigarette | rp_tobacco | ph_cigarette_pack |
| hand_rolled_cigarette | Cigarette roulée | rp_tobacco | À rechercher |
| cigar | Cigare | rp_tobacco | À rechercher |
| tobacco_pouch | Pochette de tabac | rp_tobacco | À rechercher |

## Construction et ameublement
Pièces de construction depuis src/construction.js : foundation, piles, floating, underwater, wall, window, doorway, door, ceiling, roof, stairs, ramp.
Objets homestead depuis AnomaliaHomesteadStation.h : Bed, Table, Chair, Sofa, Wardrobe, Kitchen, Lamp, Cow, Chicken, Beehive, Doghouse, Barn, Fence, TractorShed.
Les sources génériques correspondantes ne remplacent pas la recherche d'un lit, d'une cuisine complète, d'une armoire, d'une niche, d'une ruche ou d'une grange adaptés. Animaux Cow/Chicken sont recensés dans le code mais ne sont pas des objets de décoration.

## Sources écartées ou suspendues
- [F-35 bohmerang](https://sketchfab.com/3d-models/f-35-lightning-ii-fighter-jet-free-b1ab1c0090e34b0fbfe667e706023e6d) : Licence non commerciale.
- [F-35B Battlefield 2042](https://sketchfab.com/3d-models/f-35b-lightning-ii-fa3e9c175c244bedb457582f08cf8e31) : Modèle extrait de Battlefield 2042 selon l'auteur.
- [F-35A DCS](https://sketchfab.com/3d-models/f-35a-lightning-ii-a06d6113cfb44a0aa7b8f17106aca9c4) : Origine mod communautaire DCS; droits de réutilisation de la source non établis; en attente, ne pas importer.
- [Leclerc War Thunder](https://sketchfab.com/3d-models/leclerc-s1-war-thunder-1b65a5b9cfc6481487e6efbb18059653) : Origine War Thunder; ne pas importer sans droits de l'ayant droit.
- [HMS Queen Elizabeth Modern Warships](https://sketchfab.com/3d-models/hms-queen-elizabeth-r08-aircraft-carrier-b7394547685749ae9e1c48afe29586ab) : Origine Modern Warships annoncée; droits non établis.
- [Hôpital The Evil Within 2](https://sketchfab.com/3d-models/the-hospital-4-of-4-a9c83a4b678c43e2a84426472b9ca0c7) : Origine autre jeu; ne pas importer.
- [Caserne San Francisco Banobano](https://sketchfab.com/3d-models/fire-station-97c5cfa041e440c38362332ce566184e) : Licence non commerciale.
- [Modern Bathroom](https://polyhaven.com/a/modern_bathroom) : HDRI, pas un bâtiment ni des sanitaires 3D.
- [Service Pistol / Bolt Action Rifle génériques](https://polyhaven.com/a/service_pistol) : Sources CC0 valables comme références mais identité exacte non établie; pas de correspondance automatique aux armes nommées.

## Origine des modèles DayZ
[DayZ présente une équipe d'artistes](https://dayz.com/article/general/DayZ-Team-Evolution-n2) qui produit personnages, environnements, bâtiments, armes et équipements. Les données sous [DayZ Public License](https://www.bohemia.net/en/licenses/dayz-public-license-dpl) restent limitées à DayZ et à un usage non commercial. Elles ne constituent pas une banque libre pour ANOMALIA sous Unreal. Les créations tierces exigent leur propre licence.

## Prochaines recherches ciblées
Les sources présentes doivent d'abord être inspectées. Les lignes À rechercher restent la file de travail : vêtements complets, variantes exactes d'armes, accessoires, médicaments, matériaux, pièces automobiles, objets RP, gammes automobiles restantes, sous-marins/navires nommés, défense française et bâtiments entièrement accessibles. Maintenir les exclusions du propriétaire, ne pas acheter et ne pas supprimer l'existant.
