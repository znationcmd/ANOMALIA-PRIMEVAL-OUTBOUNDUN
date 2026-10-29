# ANOMALIA — correction du blocage Unreal Engine 5.8 (20/10/2026)

Le journal UnrealBuildTool fourni par l'utilisateur confirme **MSVC 14.50.35717**
et **Windows SDK 10.0.26100.0** trouvés. Le problème restant est :

```text
AnomaliaZPrigimaliaEditor modifies the values of properties:
UndefinedIdentifierWarningLevel: Off != Error
UnreachableCodeWarningLevel: Off != Error
ReturnTypeWarningLevel: Off != Error
DanglingWarningLevel: Off != Error
```

Le projet utilisait `DefaultBuildSettings = BuildSettingsVersion.V5`
dans ses deux fichiers `.Target.cs`. Le premier correctif en `BuildSettingsVersion.V6` ne suffisait pas pour la version locale du moteur : une fenêtre **Target Upgrade Required** indique expressément `BuildSettingsVersion.V7`. Nous passons donc **les deux cibles** à `BuildSettingsVersion.V7`.

La correction est fondée sur la demande précise de l'outil Unreal installé chez l'utilisateur, pas sur une compilation native déjà réussie.

Ne pas employer `bOverrideBuildEnvironment=true` pour contourner
la vérification des binaires partagés de l'éditeur installé. Le mode
`TargetBuildEnvironment.Unique` n'est pas nécessaire pour cette correction.

## Sur le PC qui a déjà téléchargé une archive ZIP du dépôt

**Le ZIP existant n'est pas mis à jour automatiquement par GitHub.**

1. Fermer le message d'erreur Unreal (et l'éditeur s'il fonctionne).
2. Depuis le dossier du projet extrait `.../unreal/Source/`, ouvrir
   `AnomaliaZPrigimaliaEditor.Target.cs` dans le Bloc-notes.
3. Remplacer **uniquement** `BuildSettingsVersion.V5` par
   `BuildSettingsVersion.V7` et enregistrer.
4. Faire la même modification dans `AnomaliaZPrigimalia.Target.cs`.
5. Double-cliquer `AnomaliaZPrigimalia.uproject`, accepter `Yes` pour
   reconstruire les modules. Si besoin, clic droit sur le fichier
   `.uproject` → Generate Visual Studio project files, puis réessayer.
6. Si la compilation échoue encore, transmettre le **nouveau**
   `%LOCALAPPDATA%/UnrealBuildTool/Log.txt` : des problèmes C++ distincts
   peuvent apparaître après la correction du contrôle des cibles.

Cette modification ne touche ni les sauvegardes ni les assets. **Ne pas
supprimer** `Binaries`, `Intermediate`, `Saved`, `Content`
ni le code JS avant diagnostic complémentaire.

## Vérification à distance

La CI GitHub vérifie uniquement les `Target.cs` et les fichiers sources.
Une compilation Unreal réelle sur le PC Windows est indispensable. Aucun
résultat de compilation native ne doit être revendiqué avant examen
du journal UnrealBuildTool provenant de la machine Windows.
