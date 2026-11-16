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
