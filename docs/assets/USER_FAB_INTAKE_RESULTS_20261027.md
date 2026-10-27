# Sélection Fab de l’utilisateur — prise en charge réelle du 27 octobre 2026

La sélection photographiée est enregistrée dans USER_FAB_SELECTION_20261027.json : 83 entrées lisibles, certaines avec titres incomplets. Ces titres incomplets ne servent pas à choisir automatiquement un asset.

## Inventaire effectivement exécuté

Exécution Windows : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40560637249

- Projet installé présent : C:\ANOMALIA\unreal\AnomaliaPrimeval.uproject.
- Téléchargements retrouvés dans le FabLibrary temporaire et dans le FabLibrary du VaultCache Epic.
- Exemples de fichiers réels : m4noskel.fbx, mp5_game_ready.glb, mauser98k.glb, revolver.glb, les FBX des fusils à pompe/1911/M14, le jeu de munitions, le jerrican et les FBX Military Supplies.
- Autres modèles locaux : sous-marin, tramway, bus, yacht, hélicoptère, porte-avions, voiture, opérateur FSB, marin, singe et vache. Leur présence ne valide ni conduite, ni animation, ni vêtements séparables.
- AR70, CommercialPlane, les mannequins, Quantum et Survival ont déjà des dossiers dans le Content installé. Ils ne sont pas remplacés par l’import.
- Le scan global a atteint sa limite de 22 000 modèles pendant l’exploration supplémentaire des ressources du moteur ; ne pas présenter ce scan comme un inventaire exhaustif de tous les disques.

## Espace disque et limitation constatée

Le premier contrôle a mesuré 12 282 372 096 octets disponibles sur C: et 3 042 441 395 octets de sources locales à préserver. L’import complet a été arrêté avant copie pour conserver la réserve de travail.

Le lot a été réduit aux identifiants explicites des armes et petits objets. Les archives originales restent en cache ; seuls les fichiers extraits et leurs dépendances sont copiés et vérifiés par SHA-256. Aucun fichier utilisateur n’est supprimé pour gagner de la place.

L’espace de travail conseillé (estimation, pas mesure de l’import complet) est au moins 50 Go libres, idéalement 100 Go pour traiter les gros environnements et caches Unreal. Le total réel de toute la sélection ne peut pas être déduit des captures seules.

## Premier import effectivement terminé

Exécution : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40561644379

Le run 40561644379 a réussi : 18 packs, 52 fichiers de modèles, 238 StaticMesh, 85 Material, 18 MaterialInstanceConstant et 195 Texture2D. Les objets ont été sauvegardés et rechargés par le script. Les reçus font autorité. Il ne s’agit pas encore d’un import dans le projet installé.

- Sources copiées uniquement vers un nouveau répertoire C:\ANOMALIA\FabImports\UserSelection_<run>.
- Cible d’import : copie native de validation C:\ANOMALIA-Validation\c40543166274\unreal.
- Namespace neuf /Game/Anomalia/ImportedFab/Batch_<run>.
- Remplacement d’assets désactivé ; refus d’un namespace préexistant ; contrôle du chargement des objets, des matériaux vides, des squelettes et de la sauvegarde.
- Aucun asset binaire Fab n’est publié dans ce dépôt public.
- La carte principale, les véhicules existants et la BMW E39 ne sont pas modifiés.
- Un import de mesh ne constitue pas une arme fonctionnelle ni un objet d’inventaire connecté. Prise en main, sockets, rechargement, tir, effets, dégâts, inventaire et réseau restent à intégrer et tester.

## Packs non retrouvés et formats particuliers

Tactical Soldier Outfit for MetaHuman : fiche identifiée https://www.fab.com/listings/8547291f-699f-45b3-87ca-3fdf2db85bb7 ; le créateur fournit un vêtement MetaHuman et décrit un fichier .mhpkg, avec FBX/Blender. Aucune compatibilité directe avec nos squelettes Survival/Quantum n’est déduite de cette fiche.

FPS Weapon Bundle : fiche identifiée https://www.fab.com/listings/8aeb9c48-b404-4dcd-9e56-1d0ecedba7f5 ; le créateur annonce 7 armes et 4 accessoires avec rigs. Les fichiers de ce pack n’ont pas été retrouvés dans le Content installé lors du scan.

Les acquisitions ou téléchargements Fab manquants ne sont pas annoncés comme effectués. Les licences/versions exactes et les accès aux fichiers doivent être confirmés pack par pack avant leur utilisation finale.

## Reprise après nettoyage et contrôle visuel réel

- L’utilisateur a signalé avoir récupéré 20 Go. Le contrôle suivant sur C: a effectivement mesuré 22 427 312 128 octets libres à 19:22 UTC.
- Le run 40568460995 a produit cinq captures GPU et une galerie séparée sauvegardée sous /Game/Anomalia/ImportedFab/Batch_40561644379/QA/L_Fab_Imported_Review. Les captures ont été inspectées.
- Le jerrican et les caisses ont des textures visibles ; le Mauser, le MP5, le revolver et d’autres imports GLB affichent leurs matériaux.
- Plusieurs FBX apparaissent blancs malgré des slots de matériaux non vides : les textures séparées n’ont pas été automatiquement reliées. Le seul contrôle « aucun slot vide » était donc insuffisant pour valider l’apparence.
- La M4 est un kit de pièces séparées : la galerie montre sa géométrie d’origine, pas une configuration d’arme assemblée et fonctionnelle.
- Les échelles et positions de pièces de certains modèles restent à vérifier avant utilisation en jeu. La normalisation des aperçus n’a pas changé les meshes sources.
- Le journal GPU contient aussi 20 messages LogAutomationTest « Condition failed » ; les captures sont produites, mais ce journal ne doit pas être présenté comme entièrement sans erreurs. Leur origine reste à isoler.
- Une réparation des jeux de textures précisément identifiés est préparée pour sept packs, avec sauvegarde des meshes importés et création de nouveaux matériaux dans leur namespace. Police Pistol et le mapping des matériaux du FPS Rifle 1 restent à résoudre.
- Reprise des packs locaux différés : run 40568581362. Son résultat ne doit pas être supposé avant la fin.
- Aucun de ces contrôles n’établit encore une arme jouable, une conduite de véhicule, une apparence persistante ou le multijoueur.

Les modèles restent dans la copie de validation jusqu’au contrôle des problèmes constatés. Aucune fusion dans la branche principale.
