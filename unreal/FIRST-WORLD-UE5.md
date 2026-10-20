# ANOMALIA — premier niveau Unreal Engine 5.8 (étape non destructive)

**État : le script est prêt dans GitHub ; le moteur UE5 n'a PAS été exécuté ici.**
Ce lot ne transforme pas les 144 tuiles de relief en carte finale et ne certifie
ni compilation UE5, ni exécution, ni multijoueur.

## Sur Windows

1. Cloner le dépôt complet via GitHub Desktop (branche de travail fusionnée ou sélectionnée).
2. Installer Unreal Engine 5.8 ainsi que **Visual Studio 2022**, charge de travail
   « Développement de jeux en C++ », SDK Windows et composants C++.
3. Ouvrir `unreal/AnomaliaPrimeval.uproject` et **compiler le projet C++**.
   Si la compilation échoue, réparer les erreurs avant de continuer.
4. Ouvrir PowerShell à la racine du dépôt, puis lancer :

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\ue5\create-first-world.ps1
   ```

   Si UE5 se trouve ailleurs, passer `-EngineRoot "D:\EpicGames\UE_5.8"`.

5. Vérifier que **le vrai moteur Unreal** a créé le fichier
   `unreal/Content/Maps/ANOMALIA_FirstTest.umap`.
6. Ouvrir ce niveau dans l'éditeur, puis utiliser **Play** pour vérifier manuellement
   l'apparition du personnage, la caméra, ZQSD/WASD, le saut et l'inventaire.
   Le rapport est dans `unreal/Saved/AnomaliaMigration/first-world-report.json`.

Le script s'arrête si la carte existe déjà : aucune destruction, aucun écrasement.
Il ne change pas `DefaultEngine.ini` et ne touche pas au jeu navigateur existant.

## Terrain définitif — restant à faire

Le générateur `scripts/ue5/generate-terrain.py` fournit des sources `.r16`
(12 × 12 tuiles de 1009 points, échelle XY 396,8254 cm, Z 200 cm).
Pour importer la vraie carte, utiliser Landscape > Import dans UE5 et valider
le placement, l'orientation des tuiles, les hauteurs, les bords, le niveau de la mer,
le streaming World Partition et les performances. Les fichiers `.r16` ne sont
pas des niveaux `.umap`.

La route, les bâtiments, la mer navigable, les fonds marins, les créatures,
les véhicules réalistes et l'éditeur ANOMALIA demandent encore du développement.
Un test statique Python/GitHub n'est pas une preuve de compilation dans UE5.
