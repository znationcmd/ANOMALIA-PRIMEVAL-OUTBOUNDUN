# ANOMALIA — Lot 2 : vêtements, soins, argent et accessoires

104 modèles convertis en GLB et rechargés pour vérifier leur géométrie : 92 vêtements/accessoires, 8 modèles d'argent, 2 comprimés, 2 plantes de cannabis. 14 téléchargements d'origine complets, dont 10 packs MakeHuman CC0. La seringue reste au format Blender et n'est pas incluse dans l'import automatique. Le flacon Grab3D n'a pas pu être téléchargé (HTTP 503).

## Import dans UE5 par Work

Extraire l'archive complète. Activer Python Editor Script Plugin et les plugins Interchange du projet, puis exécuter import_batch2_ue5.py dans Unreal Editor. Chaque modèle est importé sous /Game/ExternalSources/ItemBatch2/<id>. Les dossiers déjà présents sont ignorés, les fichiers sont vérifiés par SHA-256 et le résultat est écrit dans unreal-import-batch2-report.json. Aucun import UE5 n'a été exécuté dans cette session.

12 vêtements ont un ancien en-tête AGPL3 en contradiction avec le manifeste et la page du pack CC0. Ils sont conservés pour examen et ignorés par l'importeur. Une paire de bottes a une texture absente du pack et est également ignorée. Les licences et auteurs individuels sont conservés dans metadata/ et les reçus. Les fichiers d'origine sont récupérables via les URL et empreintes du reçu.

## Validation encore nécessaire

Les vêtements sont des maillages statiques : adaptation au personnage, poids de squelette, animations et interactions restent à réaliser. Les matériaux MakeHuman ont été convertis de Phong vers une approximation PBR ; vérifier les textures, transparences, normales et rendu. Les bump maps et cartes spéculaires d'origine ne sont pas automatiquement transformées en normales ou roughness.

Les vêtements ont été convertis des décimètres MakeHuman aux mètres glTF. Les objets OpenGameArt gardent leurs coordonnées : vérifier leur taille avant utilisation. Les fichiers ne sont pas approuvés comme rendu photoréaliste final ; aucun asset n'est annoncé comme 16K. Les catégories historiques/fantastiques présentes dans les packs restent des variantes facultatives.

L'argent correspond à des dollars et liasses, pas au pack d'euros précédemment repéré. Les plantes de cannabis sont des accessoires de jeu ; elles ne couvrent pas résine, huile ou cocaïne. Les comprimés sont génériques et ne représentent pas un médicament précis. Les sources Sketchfab restent en attente de connexion dans le navigateur utilisé par Work ; la capture du compte sur Safari ne partage pas sa session.

Sources : https://static.makehumancommunity.org/assets/assetpacks.html ; https://opengameart.org/content/money ; https://opengameart.org/content/pills-3d-models ; https://opengameart.org/content/cannabis-plants ; https://opengameart.org/content/syringe

Unités : https://static.makehumancommunity.org/makehuman/docs/exports_and_file_formats.html

UE : https://dev.epicgames.com/documentation/unreal-engine/importing-assets-using-interchange-in-unreal-engine

## Livraison et reproduction

Archive enregistrée : ANOMALIA_Items_Vetements_Batch2_UE5.zip, 345535874 octets, 104 GLB. Identifiant du fichier conservé dans asset-sourcing-register.json. Contrôle CRC réussi. Scripts vérifiés syntaxiquement ; géométrie de chaque GLB rechargée avec nombre de triangles conservé, indices dans les limites et coordonnées finies.

Pour refaire la préparation depuis les sources officielles, utiliser Python avec trimesh==5.1.1, numpy==2.3.5, Pillow==12.3.0 et py7zr==1.1.4. Copier docs/art/item-source-batch2-download-receipt-20261023.json vers unreal/Saved/ItemBatch2/pinned-source-receipt.json pour activer la vérification des fichiers d'origine, puis :

```sh
python scripts/ue5/download-item-batch2.py unreal/Saved/ItemBatch2
python scripts/ue5/prepare-item-batch2-glb.py unreal/Saved/ItemBatch2
```

Copier scripts/ue5/import-item-batch2.py à côté de conversion-receipt.json, puis l'exécuter dans Unreal Editor. Aucun import n'est lancé par les deux commandes de préparation. Vérifier le rapport avant de relier les assets au gameplay. Les vêtements historiques et fantaisie du pack ne doivent pas remplacer automatiquement les vêtements modernes demandés.
