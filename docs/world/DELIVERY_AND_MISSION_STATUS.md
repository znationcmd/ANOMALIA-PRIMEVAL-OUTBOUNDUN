# ANOMALIA — livraison suivie et critères de jeu réel

Branche de travail/livraison : `ue5/reactive-world-expeditions-20261025`.
Pull Request : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/pull/38

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
