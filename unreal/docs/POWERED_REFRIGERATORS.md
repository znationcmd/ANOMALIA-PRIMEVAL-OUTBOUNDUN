# ANOMALIA'Z PRIGIMALIA — Réfrigérateurs alimentés (prototype UE5)

Le jeu natif contient désormais le **code C++** du réfrigérateur, du générateur et de l'interface UMG. Ce n'est **pas encore une compilation ni une validation en jeu**. Le dépôt ne contient pas les cartes `.umap` définitives ou les meshes du jeu PC de l'utilisateur.

## Inclus dans la branche

- `AAnomaliaRefrigerator` : 40 unités de nourriture/boisson, température interne répliquée, consigne 0–12 °C, vieillissement des aliments dépendant de la température, état marche/arrêt, alimentation par générateur situé à 15 m au maximum.
- `AAnomaliaPowerGenerator` : carburant limité, consommation 0,6 L/h par défaut, arrêt quand le réservoir est vide, état et carburant répliqués.
- `UAnomaliaInventoryComponent` : fraîcheur (0–1) attachée à chaque pile, fusion pondérée, division et transfert sans régénération magique, sauvegarde rétrocompatible avec les profils sans champ `freshness01`.
- `AAnomaliaSurvivor` : touche Interagir **E** à moins de 3 m d'un frigo; fenêtre d'objets et température, boutons Déposer 1 / Retirer 1. Les RPC passent par le pawn du client, puis le serveur revalide distance, type, quantité et capacité.
- Sauvegardes serveur isolées : `Saved/Servers/<serverId>/refrigerators/<PersistentId>.json` et `Saved/Servers/<serverId>/generators/<PersistentId>.json`; temp file puis remplacement, limites strictes sur IDs, valeurs et quantités. Sauvegarde toutes les 60 s + à la fermeture. **Définir un ID stable et unique pour chaque instance**.
- En l'absence d'alimentation, le frigo revient progressivement vers la température ambiante. Pendant un arrêt serveur, les aliments subissent par prudence un vieillissement à température ambiante (aucune production électrique inventée pendant l'arrêt).
- Aucun fichier `types.xml` ou réglage DayZ n'est utilisé dans ce système.

## Raccordement sur une vraie carte

1. Compiler le projet natif Unreal sur la machine équipée d'UE5 et des outils C++.
2. Dans ANOMALIA Editor/UE5, créer deux Blueprints enfants : `BP_ANOMALIA_Generator` (parent `AAnomaliaPowerGenerator`) et `BP_ANOMALIA_Refrigerator` (parent `AAnomaliaRefrigerator`). Attribuer les **meshes 3D réels du projet**, collisions, son et effets d'ouverture au composant `VisualMesh`.
3. Assigner ces classes dans le GameMode (propriétés `GeneratorClass` et `RefrigeratorClass`), ou placer les Blueprints dans le niveau. Pour un objet placé, spécifier un `PersistentId` unique et affecter son `PowerGenerator` dans le panneau Détails.
4. Pour le placement serveur par coordonnées, copier le contenu de `Config/Anomalia/appliances.example.json` dans `Saved/Servers/<serverId>/appliances.json` **en remplaçant toutes les coordonnées d'exemple par des positions contrôlées de la vraie map**. Le GameMode crée au plus 32 générateurs et 128 frigos, et relie chaque `generatorId`. Chaque ID doit être unique. Aucun véhicule, joueur ou base existant n'est modifié.
5. Démarrer un générateur avec du carburant, placer le frigo à moins de 15 mètres, ouvrir par la touche E, transférer des aliments, vérifier une baisse progressive de la température vers 4 °C et un ralentissement mesurable du vieillissement.
6. Faire un test d'arrêt/redémarrage et un test multijoueur (deux clients voient le même contenu, la température et la fraîcheur).

**Limites** : l'électrification est une liaison directe d'acteur dans la portée du câble, **pas** un système de câble visuel physiquement déroulé. Le frigo n'est pas déjà placé sur SKARVIK/RACCONIA, faute de niveau UE5 réel disponible dans le dépôt. Les valeurs de péremption sont des règles de gameplay initiales et ne représentent pas une norme alimentaire. Aucune consommation/empoisonnement à partir d'un aliment avarié n'est encore implémenté dans le système de survie UE5.

La logique C++ et son test natif `Anomalia.Native.FoodPreservation` doivent être compilés puis exécutés via Unreal Editor avant de déclarer le lot fonctionnel.


## Extension — générateur portable, chargeur 12 V et lumières de chantier

- **Générateur portable** : vraie instance d'acteur UE5 à déplacer sans le dupliquer en objet d'inventaire ; le joueur peut le porter et le reposer par l'interface (E à moins de 3 mètres), à condition qu'il soit arrêté. Le serveur vérifie la distance et le sol sous la nouvelle position. Le placement, le carburant et l'état de marche sont sauvegardés par serveur. Un jerrican `gasoline_canister` de l'inventaire ajoute 5 L au réservoir (maximum 30 L). L'appareil doit rester dans un rayon de 15 m des consommateurs.
- **Chargeur de batterie 12 V** : un joueur peut insérer une `car_battery` depuis son inventaire et récupérer la même batterie avec son état de charge. Le pourcentage est sauvegardé dans la pile de l'inventaire (`batteryCharge01`) et dans le chargeur. Un chargeur alimenté augmente la charge de 25 points de pourcentage par heure par défaut, et ne charge rien sans batterie, générateur ou carburant. Une LED UE5 indique la charge en cours.
- **Projecteur de chantier** : un vrai `USpotLightComponent` UE5 projette de la lumière dans le niveau, avec intensité, portée et cône ajustables. L'état allumé/éteint est répliqué, change automatiquement lors des coupures de courant et est sauvegardé.
- **Écran des appareils** : la touche E à moins de 3 m ouvre l'interface du générateur, du chargeur ou du projecteur le plus proche. Boutons d'allumage, carburant, porter/poser, insérer/retirer batterie, allumer/éteindre projecteur. Toutes les actions passent par des RPC de personnage possédé, puis des contrôles côté serveur.
- **Placement par carte et serveur** : le fichier `appliances.json` accepte désormais `batteryChargers` (64 max) et `workLights` (128 max), en complément des `generators` (32) et `refrigerators` (128). Exemple dans `Config/Anomalia/appliances.example.json`. Les coordonnées de cet exemple sont **fictives** et ne doivent pas être déployées telles quelles sur les vraies cartes.
- **Modèles visuels** : aucun `.uasset`, `.umap`, `.fbx` ou `.glb` de ces appareils n'est présent dans le dépôt GitHub. Les composants `VisualMesh` doivent être associés aux véritables assets locaux après audit du projet installé ; le système de lumière possède toutefois un composant d'éclairage UE5 natif.
- **Installation Windows** : l'utilisateur peut ouvrir `INSTALLER-ELECTRICITE-ANOMALIA.cmd` (à télécharger depuis cette branche). Son script PowerShell `scripts/ue5/Install-Anomalia-Electricite.ps1` cherche le projet `AnomaliaPrimeval.uproject`, compare les fichiers à une révision GitHub de référence, crée des sauvegardes, applique les sources seulement si l'état local est compatible, puis tente les builds `Editor` et `Game`. En cas d'échec, retour automatique aux sources d'origine. Il n'édite ni les cartes, ni les assets 3D, ni les sauvegardes utilisateur, ni l'exécutable empaqueté.
- **Vérification nécessaire** : compiler le module natif et exécuter `Anomalia.Native.FoodPreservation` et `Anomalia.Native.ElectricalDefaults` dans UE5 ; placer les vrais meshes et appareils dans la carte en cours, vérifier un cycle complet (dépôt de viande → refroidissement → panne de carburant → chauffage → recharge batterie → éclairage → redémarrage).

**Important :** les fichiers ont été publiés sur une branche de développement ; il n'y a aucune preuve d'installation sur le PC de l'utilisateur, aucune compilation UE5 vérifiée ici, ni intégration d'un modèle réaliste sur SKARVIK/RACCONIA. Le lanceur Windows n'est pas un build final du jeu.
