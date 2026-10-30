# ANOMALIA — migration JS → UE5.8 : réglages monde et fusion de configuration

Branche : `feature/loot-tiers-radiation-config-20261021`.
Les modules JS `src/world-settings-ui.js` et `src/config-fusion.js` restent inchangés.

## Nouveaux fichiers Unreal

- `unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaWorldSettingsLibrary.h/.cpp`
- `unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaConfigFusionLibrary.h/.cpp`
- `unreal/Source/AnomaliaZPrigimalia/Tests/AnomaliaZPrigimaliaWorldSettingsTests.cpp`
- `unreal/Source/AnomaliaZPrigimalia/Tests/AnomaliaZPrigimaliaConfigFusionTests.cpp`

### World settings

Les 15 options du prototype JS sont représentées par `FAnomaliaZPrigimaliaWorldSettings` (mode, difficulty, xp, harvest, loot, foodDrain, waterDrain, staminaDrain, taming, breeding, hatching, maturation, dayLength, nightLength, maxPlayers). `NormalizeWorldSettings` borne les valeurs numériques et rejette les modes inconnus. `SaveWorldSettings` / `LoadWorldSettings` utilisent les méthodes existantes de `UAnomaliaZPrigimaliaConfigLibrary` pour stocker un JSON atomiquement dans `Saved/Servers/<server-id>/World/world-settings.json`; aucun stockage global ou dans le profil d'un autre joueur.

**Non intégré :** l'interface UMG et les autres systèmes UE (IA, reproduction, survie, loot, heure du jour) n'appliquent pas encore automatiquement les valeurs. Le réglage `maxPlayers` est un réglage local souhaité, pas une preuve que la capacité réelle d'un serveur dédié a changé. Éviter de surcharger `config.json` ou de fusionner les profils joueurs.

### Config fusion

`ParseIniToJson`, `FlattenIniJson`, `MergeConfigJson` et `BuildFusionReport` reprennent le modèle non destructif avec la précédence `defaults < legacy < canonical < server`, des conflits explicites et douze domaines (serveur, permissions, gameplay, advanced, loot, events, vehicles, maps, creatures, economy, mods, persistence).

Les routines ne lisent/écrivent/suppriment aucun fichier de configuration : elles opèrent uniquement sur des chaînes JSON/INI et signalent les clés dangereuses. Les couches JSON conservent leurs types (booléens, tableaux, nombres, objets). `BuildFusionReport` retourne un objet JSON `{"domains":[...]}` contrairement au tableau JS brut. Vérifier cet emballage lors du raccordement.

## Pour Work / compilation

1. Faire compiler le module UE5.8 via le job Windows natif et exécuter `Anomalia.Native.WorldSettings` et `Anomalia.Native.ConfigFusion` dans l'Editor.
2. Confirmer le round-trip de sauvegarde dans un dossier serveur isolé, y compris rejet de `../escape`, sans toucher aux sauvegardes joueurs.
3. Connecter l'UI des réglages du monde au chargement et à l'enregistrement de `FAnomaliaZPrigimaliaWorldSettings`, puis uniquement aux mécaniques dont les paramètres sont réellement implémentés.
4. Éviter d'importer automatiquement les fichiers DayZ/ARK originaux dans les systèmes natifs sans validation : la fusion produit des données/reports, pas un interpréteur universel.
5. La vérification actuelle est seulement une **comparaison statique** des 15 clés et 12 domaines ; les tests Unreal ont été ajoutés, mais leur exécution et la compilation ne sont **pas confirmées**.
