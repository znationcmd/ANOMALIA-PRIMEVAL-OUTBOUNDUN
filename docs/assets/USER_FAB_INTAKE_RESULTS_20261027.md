# Ressources 3D ANOMALIA — état réel au 27 octobre 2026

La sélection photographiée est enregistrée dans USER_FAB_SELECTION_20261027.json : 83 entrées lisibles, avec titres incomplets signalés. Les nouvelles priorités de transport, secours et loot sont consignées séparément dans PRIORITY_TRANSPORT_EMERGENCY_SURVIVAL_20261027.json.

## Imports et téléchargements effectivement exécutés

| Exécution | Résultat confirmé |
| --- | --- |
| 40560637249 | Inventaire Windows du projet et des caches Fab ; fichiers locaux retrouvés. |
| 40561644379 | 18 packs, 52 fichiers source importés/sauvegardés/rechargés : 238 StaticMesh, 85 Material, 18 MaterialInstanceConstant et 195 Texture2D. |
| 40568581362 | 14 fichiers de modèles réussis sur 15 ; 220 StaticMesh, 88 SkeletalMesh, 10 Skeleton, 88 PhysicsAsset, 124 AnimSequence, 23 Material, 109 MaterialInstanceConstant et 129 Texture2D consignés. Un personnage marin échoue. |
| 40569633783 | Textures PBR exactes reliées sur sept packs d’armes FBX ; nouveaux matériaux/textures et sauvegarde des meshes importés avant modification. Sources Fab d’origine préservées. |
| 40571617245 | Six sources Poly Haven effectivement téléchargées sur le PC : pommes, poires, conserves, vin, boîte médicale et ruban médical ; SHA-256 et dépendances glTF vérifiés. |
| 40571935754 | Six sources Poly Haven importées/sauvegardées/rechargées, 20 meshes ; zéro erreur dans le rapport d’import. |
| 40572389726 | Archives originales CC0 de comprimés mxc2 et de plantes Yughues téléchargées, hashées et extraites dans de nouveaux dossiers. |
| 40573064314 | Import des quatre modèles de comprimés/plantes lancé ; consulter le résultat avant d’en annoncer le succès. |

Les imports sont dans la copie native de validation : C:\ANOMALIA-Validation\c40543166274\unreal. Ils ne sont pas encore copiés dans le Content du projet installé. Les sources sont conservées dans C:\ANOMALIA\FabImports.

Les slots de matériaux non vides ne suffisent pas à valider les textures : le contrôle GPU a révélé plusieurs armes blanches. La réparation a traité sept jeux de textures précisément identifiés ; Police Pistol et le mapping des quatre matériaux du FPS Rifle 1 restent à résoudre.

## Contrôles visuels réels

- 40568460995 : cinq captures et une galerie séparée sauvegardée. Jerrican, caisses, Mauser et plusieurs GLB texturés ; défauts des FBX constatés.
- 40571772475 : sept nouvelles captures après réparation, avec le tramway, le métro et le bus. Captures inspectées : armes corrigées texturées ; bus visible ; tramway avec éléments séparés à assembler ; métro toujours sans textures.
- L’éclairage de ces galeries est sommaire. Les échelles normalisées sont uniquement celles des aperçus ; les meshes sources ne sont pas redimensionnés.
- Les variantes d’accessoires de la M4 sont des pièces séparées et ne constituent pas encore une arme configurée et fonctionnelle.
- Le journal du premier contrôle GPU contient 20 messages LogAutomationTest « Condition failed » dont l’origine reste à isoler. Les captures ont été produites ; cela ne constitue pas une recette globale sans erreurs.

## Transports demandés

- Gold Coast G:Link Light Rail Tram : fichiers Unreal réellement importés, matériaux/textures et une séquence présents ; assemblage, pivots, portes et circulation/passagers non validés.
- Subway Car TTC : cinq meshes et neuf matériaux importés ; textures non retrouvées par l’import FBX. Rendu et fonctionnement non acceptés.
- Marcopolo Ideale 770 : 35 meshes, 32 instances de matériaux et 35 textures importés ; modèle visible en GPU, conduite et intérieur/passagers non testés.
- Train complet et téléphérique : candidats documentés, fichiers non acquis. La cabine de téléphérique seule ne fournit pas câbles, pylônes, stations ni simulation.
- Pompiers, police, ambulance et militaires : fiches individuelles documentées avec états d’acquisition séparés. Aucun achat effectué. Les modèles extraits de GTA et les candidats non commerciaux identifiés ne sont pas utilisés.

## Erreur constatée

Le FBX navy_better_fbx.fbx possède plusieurs racines dans la hiérarchie des os ; Unreal rejette l’import skeletal. Le fichier original est conservé. Aucun aplatissement du modèle ni suppression de racines n’est présenté comme une intégration fonctionnelle.

Le métro a également émis des erreurs de nom de package terminant par une barre oblique pendant l’import ; les objets ensuite consignés ont été sauvegardés/rechargés, mais le lot global n’est pas une recette sans erreurs.

## Espace et préservation

Le contrôle initial a mesuré environ 12 Go libres et a arrêté le lot complet avant copie. L’utilisateur a ensuite libéré de la place ; le contrôle suivant a mesuré 22 427 312 128 octets libres. Les scripts conservent une réserve et ne suppriment aucun fichier pour gagner de la place.

Le scan global initial a atteint son plafond de 22 000 modèles durant l’exploration supplémentaire du moteur. Il ne représente pas un inventaire exhaustif de tous les disques.

La BMW E39, les véhicules existants, les cartes/World Partition, les sauvegardes, les configurations et les personnages par défaut sont préservés. Aucune fusion. Aucun binaire Fab publié dans ce dépôt public.

## Acceptation gameplay restante

Un import ou une capture d’éditeur ne prouve pas la conduite, les passagers, la prise en main d’une arme, le tir/rechargement, les effets des consommables, l’inventaire connecté, la sauvegarde/reconnexion ou le réseau. Ces fonctionnalités restent à implémenter/intégrer et à tester. Les validations des personnages et de la BMW sont documentées séparément.
