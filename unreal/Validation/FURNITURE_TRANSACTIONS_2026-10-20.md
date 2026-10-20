# Ameublement natif — lot du 20 octobre 2026

État UE5 : **SOURCE ONLY**. Le moteur n'est pas disponible dans l'environnement de travail. Le nouveau noyau de règles C++ indépendant a été compilé et exécuté avec g++, pas avec UnrealBuildTool. Les collisions, RPC, acteurs, fichiers et commandes dans UE restent à valider dans Unreal.

## Développement ajouté

- `Furniture/AnomaliaFurnitureRules.h` : transactions de placement, déplacement, rotation et suppression confirmée ; permissions par propriétaire ; undo/redo par propriétaire limité à 32 actions ; 256 objets maximum par monde ; validation des identifiants, types, coordonnées et import atomique.
- `UAnomaliaFurnitureSubsystem` : adaptateur Unreal serveur. Charge uniquement `Saved/Servers/<id>/Construction/world.json`, conserve les extensions JSON inconnues des objets et du document, refuse d'écraser un fichier modifié extérieurement depuis son chargement. Une transaction passe par un état candidat : échec de sauvegarde = état mémoire non validé et nouveaux acteurs provisoires retirés. Les anciens fichiers `Editor/world.json` ne sont pas modifiés par ce système.
- `UAnomaliaFurnitureComponent` : requêtes RPC sur le personnage propriétaire, sans paramètre client permettant de choisir le serveur ou le propriétaire. Identité déduite côté GameMode ; fréquence limitée à quatre requêtes par seconde. Les commandes Blueprint de placement, déplacement, suppression confirmée, annulation et rétablissement peuvent être raccordées à une future palette UMG.
- `AAnomaliaHomesteadStation` : identifiant de placement et mouvement répliqués, composant mobile pour permettre les déplacements. Les éléments de décor historiques sans identifiant de placement restent hors des transactions joueurs.
- `AAnomaliaSurvivor` : composant créé sur chaque personnage et commandes clavier raccordées au prototype 3D. La position est issue d'un tracé depuis la caméra ; le serveur contrôle de nouveau distance (10 m), support et occupation. Les collisions sont celles des cubes temporaires : ce validateur devra évoluer avec les vrais modèles.
- Identité solo : si aucune identité réseau valide n'existe, seule une partie `NM_Standalone` avec contrôleur local utilise `local-solo`. Les identifiants réseau déjà valides sont conservés ; aucune identité de secours n'est accordée aux joueurs multijoueurs.

## Commandes du prototype après compilation UE

| Commande | Action |
| --- | --- |
| B en visant un sol proche | Poser un lit temporaire |
| G en visant un meuble de joueur | Sélectionner son identifiant |
| T en visant le nouvel emplacement | Demander le déplacement du meuble sélectionné |
| H | Rotation de 90 degrés du meuble sélectionné |
| Ctrl+Z / Ctrl+Y en visant le sol | Annuler / rétablir une action personnelle |

Le serveur décide si une sélection est modifiable ; sélectionner visuellement le meuble d'un autre joueur n'accorde aucun droit. La suppression passe par `RequestRemove(id, true)` après confirmation à intégrer dans l'interface. Pas de touche de suppression destructive ajoutée.

En solo, le prototype est accessible. En multijoueur il est désactivé par défaut : le GameMode doit activer explicitement `bEnableFurniturePrototype` sur un serveur de test de confiance. Il s'agit encore d'un mode créatif : matériaux, coûts, règles RP/PVP et zones de construction ne sont pas intégrés. Aucun système EOS/Steam authentifié n'a été validé dans cette session.

## Tests réellement exécutés

- Noyau portable : compilation et exécution g++ C++17 avec `-Wall -Wextra -Werror -fsanitize=undefined`. Tests réussis : permissions interpropriétaires, coordonnées non finies/hors limites, suppression confirmée, undo/redo isolé, conservation des autres objets, import invalide sans mutation partielle, copie de transaction non validée, rechargement, limites de taille et d'historique.
- Suite Python : 77 tests réussis. Quatre nouveaux contrôles de frontière sont statiques : ils ne prouvent pas le comportement de RPC ou de fichiers dans Unreal.
- Test UE ajouté : `Anomalia.Native.FurnitureTransactions`. Son inscription sera automatiquement exigée par le pilote natif. **Non exécuté ici**.
- Le contrôle GitHub compile uniquement le noyau portable ; aucune preuve de compilation du module UE n'est générée par ce contrôle.

Commande de reproduction hors Unreal :

```sh
g++ -std=c++17 -Wall -Wextra -Werror -fsanitize=undefined -I unreal/Source/AnomaliaPrimeval tests/furniture_rules_test.cpp -o /tmp/anomalia-furniture-rules
/tmp/anomalia-furniture-rules
```

## Restant et blocage

Reste : compilation UE 5.8, validation en scène et à deux clients, tests de panne disque/reconnexion dans le moteur, vraie palette UMG avec sélection/aperçu/confirmation, ressources et coûts, construction de maisons, formes de collision finales, modèles réels, support zones et matériaux. L'historique undo/redo est limité à la session et n'est pas rechargé après redémarrage ; les meubles eux-mêmes sont sérialisés.

L'accès personnel Epic ↔ GitHub du propriétaire est confirmé. Le nouveau contrôle du connecteur renvoie toujours 404 sur `EpicGames/UnrealEngine`. `UE_ROOT` est absent et aucun moteur exécutable n'est installé ici ; cela ne remet pas en cause la liaison du compte utilisateur. Aucun code privé Epic n'a été copié dans ce dépôt. Aucune fusion vers main.
