# ANOMALIA PRIMEVAL OUTBOUNDUN — intégration Sketchfab UE 5.8

**Statut actuel (28 octobre 2026)** : catalogue de **37 références** issues des captures et **13 fiches candidates** pour téléchargement. **0 archive 3D téléchargée via cette PR, 0 `.uasset` généré et 0 véhicule prêt à conduire**. Les 13 fiches sont des *candidates* : l'API officielle vérifie encore la disponibilité et la licence. Les autres fiches restent à retrouver, à confirmer ou ne sont pas téléchargeables. Aucune ressource payante ni aucun fichier 3D de tiers n'est redistribué dans Git.

## Prérequis

- Windows 11, Python 3.10+, Unreal Engine **5.8** sur le PC local.
- Dans **Unreal Editor → Edit → Plugins**, activer **Python Editor Script Plugin** et le module d'import de formats **glTF via Interchange**, si disponible sur cette version. Redémarrer l'éditeur après activation.
- Une connexion Sketchfab personnelle et un **jeton d'API officiel** autorisant la récupération. Ne jamais communiquer ce jeton en conversation, dans GitHub ou dans un fichier versionné.
- Lire et respecter les licences. `CC BY` impose attribution ; les logos, noms de marques et livrées de F1 peuvent nécessiter d'autres autorisations. **Ne pas publier les modèles sans avoir vérifié tous les droits nécessaires.**

## Procédure Windows (une commande)

1. Faire une copie locale du **dépôt GitHub sur la branche correspondante** et vérifier que `unreal/AnomaliaPrimeval.uproject` existe.
2. Double-cliquer `scripts/ue5/Importer_Sketchfab_ANOMALIA.bat` (ou l'exécuter dans l'invite de commandes).
3. Saisir le jeton quand demandé en console masquée. Le programme consulte uniquement les fiches éligibles à travers l'API officielle, récupère les archives dans `Téléchargements/ANOMALIA_Sketchfab_Staging`, et les extrait avec contrôle de chemin, de taille et de format.
4. S'il y a au moins un téléchargement réussi, le lanceur ouvre l'éditeur Unreal en mode commande et importe les fichiers glTF dans **`/Game/Imported/Sketchfab/<modele_uid>`**, sans remplacer les assets existants.
5. Lire `rapport_recepisse.json` et `unreal_import_report.json` dans ce dossier local. Aucun résultat ne doit être considéré réussi si les objets importés ne sont pas présents dans le navigateur de contenu Unreal.

Pour configurer un autre chemin de l'éditeur, définir avant de lancer le `.bat` la variable `UE_EDITOR` vers le véritable `UnrealEditor-Cmd.exe`. On peut aussi exécuter séparément :

```cmd
python scripts\ue5\sketchfab_acquire.py --download
"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "unreal\AnomaliaPrimeval.uproject" -ExecutePythonScript="scripts\ue5\sketchfab_import_unreal.py"
```

## Limitations vérifiées

- Le catalogue `unreal/Config/Anomalia/sketchfab-vehicles.json` **ne contient pas** de fichiers `.gltf`, `.glb`, `.uasset`, `.umap` ni de fichiers propriétaires récupérés auprès de Sketchfab.
- Les entrées sans UID / sans licence vérifiable sont ignorées, y compris le modèle BMW S1000RR 2019 dont la fiche ne propose pas de téléchargement. Le camion « CAMION » n'est pas nécessairement le même modèle que l'Actros utilisé en alternative.
- **BMW E38 ≠ BMW E39** : rien n'efface, ne remplace ou ne renomme la E39, les modèles et données du jeu existants.
- Les imports Unreal créent des maillages et matériaux *si le plugin d'importation les prend en charge*. **Ils ne créent pas de Blueprints de véhicules, de roues physiques Chaos, d'animations, d'entrées/portes, ni de conduite.** Les modèles de la catégorie `formula_one`, par exemple, doivent encore être associés à un Blueprint `AAnomaliaVehiclePawn` après vérification manuelle du maillage, de l'échelle, des roues et des droits.
- Les fichiers obtenus restent **hors Git**, dans un dossier local. Ne pas publier automatiquement de modèles tiers sur un dépôt public, même lorsqu'ils sont téléchargeables.
- Le lanceur ne peut pas ouvrir la session du navigateur d'un autre ordinateur. L'API Sketchfab exige une authentification active et n'offre pas de récupération anonyme de ZIP.
- La mise à disposition d'une fiche **ne garantit pas** le droit de distribuer le modèle dans un jeu. Les marques et livrées doivent être examinées indépendamment des Creative Commons du maillage.

## Contrôles statiques

```bash
python scripts/ue5/sketchfab_acquire.py
python -m unittest discover -s tests -p test_sketchfab_pipeline.py -v
```

Ces tests **ne compilent pas** Unreal Engine 5.8 et n'importent pas de modèles sur le PC de l'utilisateur. Ils prouvent seulement la logique du catalogue, les garde-fous de l'importation et le comportement non destructif.