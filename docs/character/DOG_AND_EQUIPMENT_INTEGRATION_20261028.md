# Chien et attaches ANOMALIA — résultat réel du 28 octobre 2026

## Résultat vérifié

Un premier berger allemand natif est réellement présent, animé et contrôlable par les commandes du menu de proximité dans une carte Survival isolée. La ceinture et les accessoires utilisent l'inventaire natif ; le fusil est visible verticalement à côté du sac. Aucune fusion ni modification des DLL du projet installé.

- Moteur : UE 5.8.3, changelist 58210709.
- Copie validée : C:\\ANOMALIA-Validation\\c40543166274\\unreal\\AnomaliaZPrigimalia.uproject.
- Raccourci Bureau créé et relu : ANOMALIA_Test_Dog_40757731172.cmd.
- Carte sauvegardée : /Game/Anomalia/CompanionTests/GermanShepherd_40757731172/L_Dog_Playtest.
- Blueprint sauvegardé : /Game/Anomalia/CompanionTests/GermanShepherd_40757731172/BP_Anomalia_GermanShepherd, enfant de AAnomaliaZPrigimaliaDogCompanion ; comportement C++ réel.
- Profil privé : dog-playtest-40757731172. Le lanceur passe explicitement AnomaliaZPrigimaliaServerId et utilise UnrealEditor -game ; aucun raccourci existant remplacé.
- Le raccourci est créé, mais son lancement manuel par double-clic n'a pas été testé. La carte sauvegardée a bien été rechargée et exécutée en PIE.

## Terminé et testé

### Compagnon
- Association serveur au joueur possédé ; l'association automatique est une option explicitement activée sur l'acteur de cette carte d'essai.
- Marche/course et animation d'attente depuis les véritables clips du pack.
- Suivi de la trace du joueur avec CharacterMovement, collisions de capsule et sans téléportation de suivi.
- Commandes « Suivre » et « Pas bouger » réellement reliées aux boutons du menu À proximité.
- Dégâts non mortels : 10 000 points de dégâts laissent le chien vivant à 1 point de vie, blessé. La récupération testée est un hook serveur de traitement, sans consommation médicale ni bouton de soin.
- Vérification de propriété : un autre survivant ne peut pas réassigner le chien ; RPC d'ordre réservé au propriétaire et contrôles de distance/possession côté serveur.
- Le clip d'attente fourni comporte des poses de jeu ; il ne remplace pas une animation assise, couchée ou d'attaque.

Mesures du dernier PIE : joueur 1276.70 cm ; chien 1202.42 cm ; distance finale 100.68 cm. Déplacement réel d'os observé en espace composant.

### Inventaire et visuels
- Ceinture physique, deux chargeurs séparés, menottes, sacoche médicale ; emplacement exclusif et compatibilité serveur.
- Sacoche montée avec rangement 4 × 3 ; retrait d'une sacoche pleine ou d'un support encore chargé refusé.
- Attaches de ceinture et contenu médical sauvegardés sur disque puis rechargés sans perte ni duplication.
- Arme latérale, couchage et eau montés dans les emplacements du sac ; leur identité et leur poids restent ceux des piles d'inventaire.
- Fusil Quantum réellement fixé au composant du sac sur spine_03.
- Défaut visuel détecté dans la première capture (fusil horizontal à travers le torse), corrigé après inspection. Position contrôlée : centre environ 27,85 cm derrière le personnage et 29,13 cm sur le côté ; demi-hauteur 55,20 cm.
- Vrais aperçus des chargeurs M4 et AK rendus depuis les modèles locaux. Deux textures 256 × 256 non vides vérifiées par lecture GPU (1353 et 1626 couleurs distinctes).
- Les sacs médicaux, ceinture, menottes, couchage et gourde n'ont pas tous leur modèle 3D associé. Leur présence dans les emplacements n'est pas annoncée comme un rendu 3D complet.
- Le gilet Survival compatible n'est pas porté par ce personnage d'essai. Les règles du gilet sont implémentées, mais l'équipement et le rendu d'un gilet porté n'ont pas été spécifiquement exercés.
- Les capacités provisoires des anciens vêtements n'ont pas été rééquilibrées ; le profil d'essai utilise une limite de poids de 100 kg pour les fixtures, pas un nouveau réglage du jeu principal.

## Preuves

| Vérification | Exécution | Résultat |
| --- | --- | --- |
| Correctif de migration des inventaires | 40720599355, tentative 2 | Compilation Editor et régressions réussies |
| Compagnon C++ | 40753209118 | Compilation Editor, 28/28 tests natifs |
| Correction de pose du fusil et icônes | 40757419153 | Compilation Editor et tests natifs réussis |
| Premier PIE complet | 40756695141 | 14 contrôles, sortie 0, deux captures |
| PIE final après contrôle visuel | 40757731172 | 16 contrôles, sortie 0, trois captures ; artefact 12847610637 |

Les tests natifs incluent DogOwnershipAndNonLethalDamage, EquipmentAttachments, InventoryLayoutMigration, StorageGrids, transactions de loot et régressions E39/masse/coffre. Les entrées PIE utilisent les callbacks UMG et API natifs ; aucun test physique clavier/souris annoncé.

Les trois captures ont été inspectées. Le fusil est vertical sur le côté du sac et les chargeurs utilisent leurs modèles ; un clip d'attente du chien peut le faire se dresser pendant son animation de jeu.
Les avertissements génériques du démarrage GPU (LogAutomationTest Condition failed, collision de noms Python et API dépréciées) restent documentés et non résolus.

### Échecs conservés
- 40723219349 : le pack se charge et ses sept animations correspondent au squelette, mais deux références de pack manquent : BP_GermanShepherd1 et SK_GoldenRetriever_Macey_01. Les assets tiers ne sont pas écrasés pour masquer ce problème ; le nouveau compagnon utilise son propre Blueprint natif et les assets exacts du berger allemand.
- 40752746330 : erreurs de compilation dans le nouveau code (paramètre masquant Instigator et nom requis par la macro de réplication), corrigées avant le build réussi.
- 40753850470 : fuite de World après duplication brute de carte ; création remplacée par LevelEditorSubsystem.new_level_from_template.
- 40754287772 : attente d'association au joueur ; sortie anormale à la fermeture conservée.
- 40755412299 : option d'association non persistée. Correction : valeur de classe laissée désactivée et override explicite sur l'acteur placé, vérifié après rechargement.
- 40755858755 : le script interprétait la chaîne d'erreur vide renvoyée par Python comme un échec de sauvegarde ; correction et comparaison réelle des contenus après lecture.
- 40756210557 : les contrôles de suivi, arrêt, blessure et sauvegarde passent, mais l'inspection tente de lire un champ privé. Inspection remplacée par les composants publics réellement enregistrés sur l'acteur.
- Les références Python aux objets PIE sont relâchées avant la fermeture ; les deux essais complets suivants terminent avec code 0. Cela ne constitue pas une explication de tous les plantages GPU historiques.

## Implémenté mais pas encore validé

- Réplication du chien et routage RPC : pas de session à deux joueurs.
- Récupération non mortelle après sortie du monde (KillZ) : code présent, pas de chute KillZ exercée.
- Parcours complexe, escaliers, portes mobiles et obstacles nouveaux : seul le suivi sur la carte plane a été vérifié ; la trace du joueur ne remplace pas un système complet de navigation.
- Lancement manuel du raccourci, touches physiques, cible Game distincte et build packagé.
- Les attaches gilet et les familles d'armes autres que le fusil de démonstration n'ont pas toutes été exercées visuellement.

## Reste à développer

- Assis, couché, attaque : clips appropriés et comportement d'attaque réel. Aucun bouton décoratif correspondant ajouté.
- Autres races et choix dans le catalogue de personnages : une seule race réelle disponible.
- Équipement du chien, stockage de ses sacs, poids et effets de protection.
- Persistance de l'identité, de la santé et de l'équipement du chien après reconnexion.
- Soin du chien relié à une transaction d'inventaire et animations/transitions plus complètes.
- Modèles manquants des accessoires humains, silhouettes des emplacements, équipement physique des vêtements depuis des piles et persistance de l'apparence.
- Usure par tir/réparation et textures déchirées ; l'usure existante reste celle documentée séparément.

## Assets utilisés et préservation

Pack utilisateur : /Game/German_Shepherd_3D_Model ; modèle SK_GermanShepherd_01 ; squelette SKEL_Dogs_type1 ; animations Idle_Playing, Walk_Loop et Run_Loop. Sept clips compatibles chargés au total.
Arme : /Game/QuantumCharacter/Mesh/Rifle/SM_Rifle_Olive.
Chargeurs : m4noskel_Magazine_Default_Unreal et AKRifle_magazine du lot ImportedFab/Batch_40561644379.
Les packs sources et les fichiers sous C:\\ANOMALIA\\unreal ne sont pas remplacés. Aucun asset Fab binaire n'est publié sur GitHub ; seulement code, scripts et rapports.
Monkey B3 reste inventorié séparément (modèle/squelette/physique et 19 noms d'animations FBX), sans comportement de compagnon ni lecture d'animations Unreal annoncée validée.

Fichiers principaux : AnomaliaZPrigimaliaDogCompanion.h/.cpp, Tests/AnomaliaZPrigimaliaDogCompanionTests.cpp, AnomaliaZPrigimaliaInventoryComponent.cpp, AnomaliaZPrigimaliaInventoryWidget.h/.cpp, verify_anomalia_dog_playtest.py et workflows de compilation/validation. PR44 reste en brouillon. BMW E39, autres véhicules, cartes principales et configurations des serveurs sont préservés.
