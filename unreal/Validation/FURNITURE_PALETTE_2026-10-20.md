# Palette native d’ameublement — 20 octobre 2026

État : **SOURCE ONLY**. Aucun lancement ni compilation Unreal réalisé pour ce lot.

## Développement

- `AnomaliaFurnitureWidget.h/.cpp` : interface native UMG en français, catalogue des 12 types autorisés, actions sur la sélection, annulation/rétablissement, retour de résultat serveur. Textes de la palette déclarés avec LOCTEXT pour leur future collecte par la localisation Unreal.
- Confirmation de suppression en deux étapes. Le dialogue conserve l’identifiant demandé, jamais une nouvelle sélection au moment de confirmer. Fermer, annuler ou choisir une autre action abandonne cette confirmation. Aucun fichier ni meuble n’est supprimé pendant ce développement.
- `AnomaliaFurnitureComponent` : ouverture/fermeture, sélection du type à placer, raccordement des actions aux RPC existants. Aucun propriétaire ni serveur n’est choisi par la palette. Les contrôles serveur de distance, collision, propriété et persistance restent applicables.
- Curseur et focus gérés à l’ouverture ; déplacement et caméra bloqués pendant la palette. L’inventaire ferme la palette avant d’ouvrir son propre écran, pour équilibrer les compteurs de blocage d’entrée. Fermeture au retrait du composant et restitution des entrées au contrôleur qui a ouvert le widget.

## Commandes prévues après compilation

F2 : catalogue ; choisir un type ferme le catalogue ; B en visant le sol : placement de ce type (lit par défaut). G : sélectionner un meuble existant ; T : déplacement vers le point visé ; H : rotation. F2 donne accès à la rotation, la suppression confirmée et l’historique. Échap ou Fermer quitte la palette. Aucune prévisualisation fantôme ajoutée : les modèles restent des cubes temporaires.

## Vérifications exécutées

- 77 tests Python réussis, dont les contrôles de source et les tests du pilote de compilation utilisant des environnements simulés. Les messages de compilation émis par ces simulations ne sont pas des résultats Unreal réels.
- Noyau de transactions recompilé avec g++ C++17, avertissements en erreurs et UndefinedBehaviorSanitizer ; exécution réussie. Ce test porte sur les règles portables, pas sur UMG, les RPC ou la physique.
- `git diff --check` réussi.

## Validation restante

Compiler avec UnrealBuildTool 5.8 puis vérifier dans l’éditeur : création du widget, lisibilité aux différentes résolutions, navigation clavier/manette, touches F2/Échap, changement de type puis placement, sélection/déplacement/rotation, annulation/rétablissement, confirmation annulée/validée, sélection détruite entre demande et confirmation, refus serveur, alternance inventaire/palette, sortie du personnage et déconnexion. Puis deux clients sur deux serveurs indépendants avec sauvegarde/rechargement.

Blocage inchangé : moteur et environnement Unreal distants non accessibles dans cette session. La liaison personnelle Epic/GitHub confirmée ne fournit pas automatiquement un moteur exécutable à cet environnement. Aucune fusion vers main ni promesse de version jouable.
