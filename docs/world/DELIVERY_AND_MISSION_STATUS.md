# ANOMALIA — livraison suivie et critères de jeu réel

**Priorité utilisateur actualisée : canal de validation unique, sans remplacement du jeu installé.**
Les étapes d’installation du jeu et du projet Editor sont désactivées pendant la
validation de la nouvelle démonstration. Les indications de livraison automatique
ci-dessous décrivent le mécanisme précédent, actuellement suspendu.

Branche de travail/livraison : `ue5/reactive-world-expeditions-20261025`.
Pull Request : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/pull/38

## Dernière validation réelle — portière conducteur, 26 octobre 2026

Source `ba6cf00dc9c4c1c7ccccdc9a6bbb4027489946ba`, exécution réussie
https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40373839123.
Editor et Game compilés avec UE 5.8.3 ; 24 tests natifs passent (cinq avec
avertissements), ainsi que 154 tests Python et cinq tests de géométrie. Six
maillages glTF sans erreur/avertissement sont réellement importés dans Unreal.

La berline v3 passe 33 contrôles en jeu et le véhicule de référence 26. Sa
portière conducteur possède une vraie découpe de carrosserie, un maillage avec
vitre/joints/rétroviseur, une charnière et une collision mobile. E à l'extérieur
et O depuis le siège emploient des commandes validées par le serveur. Les tests
automatisés exercent ces API et la capture réelle montre l'ouverture du bon côté.
Une première inversion de côté a été rejetée après inspection visuelle malgré
ses tests techniques réussis ; le contrôle de recomposition du modèle fermé et
les origines d'import vérifiées couvrent maintenant cette erreur.

Freinage mesuré de cette version : 12,32 m depuis 50,55 km/h, 29,61 m depuis
80,00 km/h et 56,00 m depuis 80,05 km/h à adhérence réduite. Voir
`docs/art/SEDAN_DRIVER_DOOR_NATIVE_STATUS.md` pour les identifiants des preuves.
Cette validation reste limitée à la scène d'essai solo. Autres ouvrants,
animations humaines, transparence des vitres, dégâts, persistance automobile,
réseau, routes et zone photoréaliste restent inachevés. Aucun package de cette
version n'est installé. Les modifications locales suivies du checkout de
validation sont désormais sauvegardées avant récupération des prochaines versions.

## Validation physique précédente — 26 octobre 2026

Source `bf4cacbe22ba879825ff882c55745332854b8760`, exécution réussie
https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40349559923.
Editor et Game compilés avec UE 5.8.3 ; 24 tests natifs passent (cinq avec
avertissements), ainsi que 154 tests Python locaux. Le véhicule de référence et
la berline d'art original passent chacun 26 contrôles dans le vrai jeu, avec les
paramètres normaux du projet, sans option de diagnostic.

Le ressort transmis au moteur et le mode de suspension sont corrigés : les roues
portent réellement le châssis et leur adhérence dépend de leur charge. Freinages
mesurés de la berline : 12,23 m depuis 50,39 km/h, 29,80 m depuis 80,28 km/h,
55,97 m depuis 80,02 km/h à adhérence réduite. Contact, panne/ravitaillement,
rapports, frein à main, phares/clignotants et sortie rapide avec élan passent
également. Rapports et captures réelles : `docs/art/CHAOS_ROAD_NATIVE_STATUS.md`.

Cette étape valide la conduite calibrée sur terrain plat en solo. Elle ne clôture
pas les ouvrants/animations, dégâts, sauvegarde automobile, réseau, conduite sur
routes et obstacles, maison aménagée, forêt photoréaliste ou démonstration 1 km².
Aucun nouveau package ni remplacement du jeu installé. L'aéroport apocalyptique,
les ULM 2/4, l'aéroglisseur fermé de huit places et le parachutisme sont enregistrés
dans `APOCALYPTIC_AIRPORT_ULM_HOVERCRAFT_PARACHUTE.md`, à réaliser ensuite.

## Livraison et version réellement lancée

Les changements du runtime, des configurations, des scripts de scène et de
préparation des assets sur cette branche déclenchent maintenant automatiquement
la chaîne complète de compilation, tests natifs, préparation des modèles,
cuisson, exécution GPU et installation sur le PC possédé. Le préfixe
`[pc-update]` n'est plus nécessaire pour qu'une amélioration soit livrée.
Les commits `[ci-config]` restent sans installation ; `[native-only]` demande
explicitement une validation native sans livraison. La validation séparée
`ue5-reactive-world.yml` est réservée à ce cas et au déclenchement manuel pour
éviter deux travaux simultanés sur le même poste.

Cela ne fusionne pas automatiquement les autres PR. Un modèle présent dans une
branche d'essai ne devient pas jouable sans intégration, collisions, interactions
et validation dans l'exécutable. L'ancien canal historique de la branche
`ue5/driveable-roster-city-20261023` est encore présent pour compatibilité ;
il faut éviter de lui pousser un ancien contenu comme nouvelle livraison.

Le menu principal et le menu pause affichent le commit compilé. Il provient d'un
fichier généré avant compilation et déclaré comme dépendance externe UBT : une
nouvelle révision invalide le cache de compilation. Les rapports de l'exécutable
contiennent ce même `buildCommit`. Le package et l'installation refusent une
identité différente du commit attendu. Une ancienne fenêtre déjà ouverte garde
son ancien code jusqu'à sa fermeture normale ; l'installateur ne tue pas la partie.
Les sauvegardes existantes restent séparées de la validation et sont conservées.

## Modification visuelle de la scène principale

Commit soumis à validation : `6f2ba89f465fc9a7c6cab94515a415b3f55ba7e5`.
Exécution : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40190674748

- Le sol cubique devient un véritable maillage de terrain PBR avec collision.
- Le relief se situe autour des parcelles existantes. Maison, garage, villa,
  approvisionnements, points de sauvegarde et couloir routier restent plats.
- La route devient le maillage d'asphalte PBR avec ses marquages intégrés.
- 32 arbres supplémentaires et 96 touffes d'herbe forment un pourtour boisé.
- Les 20 arbres, 24 rochers, 24 touffes et deux extérieurs scannés déjà livrés
  restent présents ; leurs positions verticales suivent le nouveau terrain.
- Les formes provisoires de canopée, collines et anciens marquages sont conservées
  mais masquées. Aucun asset ou système existant n'est supprimé.

Textures CC0 déjà référencées ; géométrie du terrain originale ANOMALIA.
Aucun téléchargement payant. La route et la parcelle de départ sont vérifiées
par l'exécutable ; les tests de relief ne prouvent pas une qualité photoréaliste.
Ce changement ne fournit pas encore l'intérieur détaillé des maisons ni une
nouvelle conduite physique. La carte principale reste une petite zone jouable.

## État des trois missions

| Demande | Écrit / compilé précédemment | Encore nécessaire avant de dire « jouable » |
| --- | --- | --- |
| POI et ressources régionales | Filtrage du vrai loot par POI, test natif | Placer les POI de production, régler dangers/conditions/crafts et routes alternatives |
| Ponts et infrastructures | Dépôts, recettes, états, journal durable et réplication | Modèles détruit/étapes/réparé, parcours dans la carte, IA et traversée véhicule |
| Électricité | Réseau de câbles, carburant, charges, surcharge ; projections lampe/porte | Installation réelle du bunker ; solaire, éolien, batteries, fusibles, pannes et appareils spécialisés |
| Accès et portail | Carte consommable, conditions événement/power, durée, téléportation contrôlée | Terminal, destination et effets réels ; essai complet de retour, déconnexion et protections |
| Événements | État serveur temporisé persistant | Météo visible, réglages complets et interactions environnementales |
| ORACLE, PRIMEVAL, Cryptes | Pas de chaîne complète intégrée | Objets, étapes, indices, costumes/oxygène, dangers, animations, récompenses et parcours |
| Lieux nommés | 54 panneaux enregistrés dans les 27 localités de la grande carte Editor | Contrôle visuel et noms/placement des vrais ports et bases militaires |
| Bâtiments | Porte à charnière native avec collision, verrou, animation et contrôles serveur | Adapter de vrais intérieurs, portes montées dans la carte, sons, clés, dégâts, persistance, navigation IA, coulissantes/doubles |
| Véhicules | Catalogue, carburant, conducteur et sortie contrôlée ; conduite actuelle simplifiée | PR #37 : contacts roues non validés ; habitacles, panneaux séparés, sièges passagers, mécanique, coffre et tests réseau |
| Dinosaures vivants | Aucun système natif complet de créature animée/montable | Modèles licenciés riggés, animations, IA, apprivoisement, possession et restitution de contrôle |
| Creature Vault | PR #30 : persistance de métadonnées, non intégrée ici | Capture/libération transactionnelles d'acteurs vivants, vrai conteneur d'inventaire, terminal 3D, permissions, reprise après panne |
| Élevage et automatisations | Aucun parcours natif complet validé | Reproduction, génétique, bébés, œufs, production et simulation hors connexion côté serveur |
| ANOMALIA Editor / CMD Hosting | Champs natifs de définitions exposés Unreal/Blueprints | Outils graphiques dédiés, connexions aux vrais paramètres serveur et tests de bout en bout |

Ne pas remplacer les développements existants par un second gestionnaire.
Ne pas confondre les catalogues JSON, tests de règles ou métadonnées avec les
créatures, véhicules et bâtiments réellement utilisables.

## Références et étude technique

Les pages Epic demandées ont été consultées :

- https://dev.epicgames.com/documentation/unreal-engine/how-to-set-up-vehicles-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/opening-doors-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/chaos-modular-vehicles-overview

Le système Chaos classique attend des roues, un squelette, un Physics Asset,
un Animation Blueprint et une courbe de couple. Changer seulement le Static Mesh
d'un FloatingPawnMovement ne satisfait pas la conduite demandée.

Les deux pages Wiki Bohemia demandées répondent 403 lors de la lecture directe.
La page des portes apparaît dans l'index de recherche, ce qui ne constitue pas
une lecture intégrale. Les fichiers texte officiels `Test_Building/config.cpp`,
`model.cfg`, `readme.txt`, `Test_SmartCar/config.cpp` et son `CarScript.c` ont été
lus dans https://github.com/BohemiaInteractive/DayZ-Samples pour analyser axes,
battants, collisions, positions d'interaction et commandes moteur/transmission.
Aucun de leurs fichiers n'est incorporé au projet.

## Validation obligatoire restante

Deux vrais clients : dépôts concurrents, sièges réservés, portes et conteneurs.
Redémarrage de serveur et interruption de capture/libération sans perte ni copie.
World Partition : restauration des infrastructures, portes et créatures.
Véhicule + IA : traversée du pont et accès aux pièces ouvertes.
Cartes absentes/consommées, tempête terminée, portail fermé, destination occupée.
Monture : mort/déconnexion, sortie obstruée, caméra, selle et permissions.
Chaque future déclaration doit associer le commit à une preuve native fraîche,
puis à une preuve de jeu réel ; une compilation seule ne clôture pas ces critères.

## Étape 4 bis — architecture universelle après la première berline

Condition de départ : berline complète testée dans UE5.8, pas seulement une
configuration ou un test de véhicule de référence. Les corrections des fonctions
partagées doivent bénéficier aux véhicules déjà intégrés qui utilisent ces mêmes
classes/composants. Un nouveau nom de catalogue n'est pas un véhicule accepté.

- Réutiliser moteur/carburant/transmission, freinage, direction, suspensions, dégâts,
  panneaux mobiles, sièges/passagers, entrées/sorties animées, caméras, inventaire,
  réparation, sauvegarde et validation réseau lorsque ces fonctions sont compatibles.
- Garder les profils et modèles propres à chaque véhicule ; distinguer notamment
  motos/quads/poids lourds. La mer et le vol gardent leur simulation spécialisée.
- Ne pas étendre aux autres véhicules avant que la berline passe contacts roues,
  accélération, direction, freinage, marche arrière, obstacles, animations, carburant,
  dégâts et sauvegarde/rechargement dans le jeu natif.
- Pour chaque intégration ultérieure : vrai modèle licencié et riggé, configuration,
  essai de conduite, collisions, entrée/sortie, persistance et tests multijoueurs.

Les travaux de `ue5/chaos-road-driving-20261025` sont intégrés dans cette branche
pour poursuivre cette validation sans dispersion. Le modèle Epic Offroad sert de
référence technique à la physique ; il n'est pas présenté comme la berline finale.
