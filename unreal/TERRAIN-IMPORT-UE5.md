# ANOMALIA PRIMEVAL — terrain World Partition : procédure UE 5.8

## Ce qui est codé (ne pas confondre avec une carte jouable)

- `scripts/ue5/generate-terrain.py` **existant et conservé** :
  144 fichiers `.r16` de 1009 × 1009 échantillons (sources haute définition, 48 × 48 km).
- `scripts/ue5/generate-playtest-terrain.py` **nouveau** :
  144 fichiers `.r16` de 253 × 253 échantillons, même fonction géographique et
  mêmes limites de 48 × 48 km. Vérification stricte des 264 joints entre tuiles,
  des tailles de fichiers et des écritures non destructives.
- `scripts/ue5/create-first-world.py` : demande à **Unreal Editor** de produire
  un vrai niveau `ANOMALIA_FirstTest.umap` avec petite plateforme, point
  d'apparition et lumière. **Ce niveau ne contient pas encore le terrain**.
- **Aucun fichier `.umap` de la grande carte n'est généré dans GitHub** ;
  aucun essai Play-in-Editor de cette carte n'a été exécuté.

L'option allégée utilise 253 échantillons par tuile, soit environ **15,87 m
entre les points** et **576 composants Landscape au total** avec
63 quads/section et 2 × 2 sections par composant. C'est une résolution
**de test**, pas le relief final au niveau de détail voulu.

L'option originale haute résolution utilise environ **3,97 m entre
les points**, mais totaliserait **9216 composants** avec ce même découpage :
**ne pas importer la version haute résolution complète d'un seul coup
dans un premier essai**, spécialement sur un PC portable.

## Préparation sur ton PC Windows

1. Installer Unreal Engine 5.8, Visual Studio avec C++ et Python avec NumPy.
2. Cloner le projet ANOMALIA depuis GitHub (garder la version JS inchangée).
3. Ouvrir PowerShell à la racine du dépôt, lancer :

   ```powershell
   python -m pip install numpy
   python scripts/ue5/generate-playtest-terrain.py
   python scripts/ue5/generate-playtest-terrain.py --verify-only
   ```

4. Le dossier `unreal/TerrainPreview/` contient 144 fichiers
   `ANOMALIA_x0_y0.r16` ... `ANOMALIA_x11_y11.r16` (environ 18,4 Mo
   hors manifeste) et `draft-terrain-manifest.json`.
5. La génération peut être relancée sans réécrire les mêmes fichiers.
   Si un fichier est différent, **elle s'arrête sans le remplacer**.
   Conserver le dossier original `unreal/TerrainSource/` pour les détails finaux.

## Option rapide : préparer la carte World Partition par script

Après installation du moteur, du compilateur C++ et compilation du projet,
tu peux lancer ceci dans PowerShell à la racine du dépôt :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ue5\bootstrap-draft-landscape.ps1
```

Cette commande :

1. Génère les **144 tuiles de terrain de test** (sans modifier les sources HD).
2. Contrôle les 264 joints et les **empreintes SHA256** des fichiers.
3. Demande à Unreal Editor de créer `/Game/Maps/ANOMALIA_TerrainDraft.umap`
   en mode **World Partition**.
4. S'arrête sans remplacer un fichier `.umap` qui existe déjà.

**Important :** le niveau est alors un **conteneur World Partition vide** ;
le terrain `.r16` doit toujours être importé avec le panneau **Landscape**
dans Unreal, comme décrit plus bas. Cette commande ne certifie pas la
compilation du jeu, la jouabilité, la présence de routes ni le multijoueur.

**GitHub :** installer `git lfs` avant de synchroniser les binaires Unreal
(`.umap`, `.uasset`). Les caches d'Unreal et les tuiles générées restent
sur le PC et sont ignorés par Git. Les projets et ressources déjà suivis
ne sont pas supprimés.

## Import dans Unreal Engine 5.8

Il faut réellement effectuer ces actions **dans Unreal Editor** :

1. Compiler le projet Unreal C++ `AnomaliaZPrigimalia.uproject`.
2. Dans **Fichier → Nouveau niveau**, créer un niveau **Open World**
   avec **World Partition**, puis l'enregistrer sous
   `/Game/Maps/ANOMALIA_TerrainDraft`. Ne pas écraser
   `ANOMALIA_FirstTest.umap`, ni une autre carte existante.
3. Ouvrir **Landscape** (Maj + 2) → **Gérer** → **Import from File**.
4. Choisir le premier fichier `unreal/TerrainPreview/ANOMALIA_x0_y0.r16`.
   Accepter l'importation **des tuiles** quand Unreal la propose.
5. Vérifier qu'il détecte les 144 tuiles (12 × 12). Définir l'échelle
   Landscape : **X = Y = 1587,301587 cm** pour 253 échantillons couvrant
   4 km, **Z = 200 cm** pour les hauteurs encodées entre -512 et +512 m.
   **Important :** voir la section « Correction d'échelle » ci-dessous.
6. Examiner l'aperçu d'import. **Le nord est au début des lignes des .r16**.
   La case **Flip Y Axis** doit être contrôlée visuellement : vérifier
   les côtes et la continuité. Ne pas la cocher automatiquement.
7. Ajuster Grid Size / Region Size pour World Partition suivant le PC,
   puis cliquer **Import** et sauvegarder le niveau.
8. Ouvrir le niveau, placer un **PlayerStart au-dessus du sol** si
   nécessaire, puis tester Play-in-Editor, collision, déplacements,
   inventaire et chargement World Partition sur un secteur réduit.

### Correction d'échelle — lire avant import

Chaque tuile mesure exactement **4000 mètres** pour **252 intervalles**
entre les 253 échantillons. L'échelle est donc :

```text
4000 m × 100 cm/m ÷ (253 - 1) = 1587.301587 cm par unité Landscape XY
```

**Cette valeur (1587,301587) prime** sur tout chiffre recopié d'un
profil différent. Le manifeste automatisé sera maintenu cohérent avec
cette valeur. Éviter de confondre un pas de 3,968 m (tuiles 1009)
avec le pas de 15,873 m du profil de test.

Un import de 48 km n'est pas une preuve de performance optimale ;
contrôler la mémoire et le nombre de composants dans l'éditeur.

## À terminer après ce premier terrain

Routes, villes, bâtiments, océan, reliefs sous-marins, matériaux de
landscape, streaming vérifié, IA, dinosaures, zombies, véhicules (Chaos,
flottabilité, vol), sauvegarde des constructions, serveur dédié, editor
ANOMALIA, UI définitive et installateur Windows. Ne pas confondre
fichiers sources, test GitHub et jeu Unreal jouable.

Références Epic Games UE 5.8 :
- https://dev.epicgames.com/documentation/en-us/unreal-engine/importing-and-exporting-landscape-heightmaps-in-unreal-engine
- https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-technical-guide-in-unreal-engine
