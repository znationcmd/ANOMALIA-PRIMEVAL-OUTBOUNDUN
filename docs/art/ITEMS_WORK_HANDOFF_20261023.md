# Sources téléchargées pour Work — 2026-10-23

49 modèles Poly Haven CC0 effectivement téléchargés : glTF, buffers et textures. 32 IDs d'inventaire ont au moins un candidat téléchargé ; cela ne valide pas une correspondance exacte ni leur gameplay. Voir asset-sourcing-register.json et item-source-download-receipt-20261023.json.

Archives à extraire dans des dossiers distincts : ANOMALIA_Items_Decors_UE5.zip (47 modèles), ANOMALIA_Sapin_UE5.zip et ANOMALIA_Pin_UE5.zip. Chaque archive contient README_WORK_UE5.md, un reçu SHA-256, les sources et import_sources_ue5.py. Les fichiers lourds sont livrés séparément du Git.

Inclut bottes, masque à gaz, montre, boîte et ruban médical, pommes, poires, conserves/lait, bouteilles, outils, jerricans, générateur, éclairages, armes statiques, meubles, clôture et végétation. Les conserves sont un ensemble de modèles ; les noms du catalogue ne garantissent pas une correspondance exacte.

Aucun import Unreal n'a été exécuté ici. Work doit importer, inspecter les résultats puis mettre à jour le registre uniquement avec les chemins d'assets et les résultats réellement observés. Le script évite les dossiers existants, vérifie les sources et produit son propre rapport. Ne pas annoncer vêtement riggé, véhicule pilotable ou objet utilisable à partir d'un simple mesh.

## Pistes encore sans fichiers

Modèles ci-dessous repérés sur des fiches/index publics. Vérifier individuellement licence, attribution, disponibilité et provenance avant téléchargement. Connexion Sketchfab bloquée à l'étape Google par la vérification automatique, faute d'autorisation explicite pour ce compte. Aucun fichier Sketchfab n'est inclus.

- Collection médicale : https://sketchfab.com/3d-models/medical-supplies-collection-eae9fc470e674c458791cf00b892340f
- Comprimé : https://sketchfab.com/3d-models/pilltablet-6b8eefa77b83465494bca7f99b1ab1db
- Flacon : https://sketchfab.com/3d-models/pill-bottle-lowpoly-9b9bcca98f7249ee93a58adfd7b1e7f8
- Billets et pièces euros : https://sketchfab.com/3d-models/multi-lowpoly-euro-full-set-banknotes-coins-6d59dd1c79b3472e90d095334744a345
- Veste cuir : https://sketchfab.com/3d-models/female-leather-jacket-free-model-1dc7708fd7bd4ea1b035f4c48dbd7868
- Accessoire fictif sachet : https://sketchfab.com/3d-models/cocaine-baggie-a8ef621c050143ca93caf28cb2cb937b
- Accessoires fictifs pack : https://sketchfab.com/3d-models/drug-pack-af40636101a3437786e2998f96b716f4

Ces pistes ne couvrent pas toute la demande : poursuivre vêtements, nourriture, médicaments, monnaie, accessoires, véhicules et bâtiments manquants en préservant les exclusions déjà enregistrées.

## Récupération reproductible depuis le dépôt

L'enregistrement durable des archives a échoué à l'étape de préparation. Les sources restent récupérables exactement grâce au reçu versionné. Depuis la racine du dépôt :

```sh
python scripts/ue5/restore-registered-item-sources.py
```

Le script restaure les URL et SHA-256 consignés vers unreal/Saved/ItemSourceCache, préserve les fichiers existants qui diffèrent et copie l'importeur à côté du reçu. Il n'importe rien dans UE. Dans Unreal Editor, exécuter ensuite unreal/Saved/ItemSourceCache/import_sources_ue5.py. Les 49 modèles originaux ont passé les vérifications de dépendances, textures et indices de géométrie (179 primitives). Les trois archives ont passé leur contrôle CRC ; l'importeur est vérifié syntaxiquement, pas exécuté dans UE.
