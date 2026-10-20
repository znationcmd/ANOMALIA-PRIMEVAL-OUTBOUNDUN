# Véritable modèle d'avion — intégration progressive

État : source GLB présente et vérifiée ; import et liaison du modèle au pawn natif préparés pour le runner UE5. Pas encore validés dans Unreal à la rédaction de ce document.

Le véhicule `airliner` est ajouté sans retirer les 30 catégories précédentes. Il dispose d'un véritable modèle extérieur d'avion de ligne sans logo (amvlab, CC BY 4.0), de géométrie arrondie, de matériaux et d'une image embarquée. Le fichier original et sa licence sont conservés dans SourceAssets/Vehicles/airliner. Le modèle source comporte 4 628 sommets de position ; ses dimensions après transformation sont environ 37,68 × 35,48 × 11,32 m. Ce modèle de départ n'est pas présenté comme un intérieur complet ni comme un asset photoréaliste final de jeu AAA.

Le préparateur conserve l'original, vérifie SHA-256, applique les transformations de noeud aux positions/normales et refuse les hiérarchies/animations qu'il ne sait pas conserver. L'importeur natif vérifie les deux empreintes, le nombre de maillages, les matériaux, les dimensions réelles en centimètres, la sauvegarde du StaticMesh et sa liaison à un pawn natif temporaire. Aucun niveau utilisateur n'est enregistré par ce test.

Tous les IDs reconnus du catalogue peuvent désormais charger leur StaticMesh canonique à /Game/Anomalia/Vehicles/<id>/SM_<id>. Le modèle est affiché par le composant Body du pawn existant, y compris pour les apparitions issues du fichier serveur. Un asset absent conserve les visuels éventuels du Blueprint ; aucun cube n'est créé en remplacement. Le chemin d'asset ne provient pas d'un client. Les transformations et distances de caméra originales sont restaurées lors du retrait d'un modèle automatique.

Le workflow de compilation lance maintenant l'import après les compilations et les tests natifs. Il exige un rapport neuf avec le SHA du commit et nativePresentationBound=true, puis conserve les véritables assets .uasset et leurs matériaux comme artefact. Un import réussi demeure IMPORTED_NOT_PLAYTESTED : aucun pilotage ni rendu en jeu n'est prouvé par ce contrôle sous NullRHI.

Restent : import natif réel à vérifier, capture du rendu Unreal, orientation/caméra à ajuster, collisions du modèle raccordées au déplacement (la sphère du prototype est encore utilisée), tests de décollage/atterrissage, animation du train d'atterrissage, intérieur, sièges/passagers et essais réseau.

Les modèles libres identifiés chez Innerscene pour un hélicoptère moyen, un chasseur, une locomotive et un bateau ne sont pas livrés par ce lot : leur téléchargement a renvoyé HTTP 403 depuis cet environnement. Aucun fichier absent n'est déclaré installé. Les autres catégories, y compris porte-avions, navire de guerre et sous-marin, doivent encore recevoir des assets appropriés.

Les sauvegardes et fichiers de configuration existants ne sont pas remplacés. Le runner utilise clean:false pour conserver les fichiers non suivis et les journaux ; cela ne constitue pas une sauvegarde hors machine.
