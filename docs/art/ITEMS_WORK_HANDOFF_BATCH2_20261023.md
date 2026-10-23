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
