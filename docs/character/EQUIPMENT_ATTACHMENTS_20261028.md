# Équipements modulaires — 28 octobre 2026

État : implémentation native enregistrée, validation finale BLOQUÉE. Pas de fusion ni installation dans C:\ANOMALIA\unreal.

## Emplacements implémentés

| Support | Attaches |
| --- | --- |
| Ceinture physique tactical_belt | Holster/pistolet, fourreau/couteau, gourde, sacoche médicale, chargeur 1, chargeur 2, menottes |
| Sac à dos réellement porté | Arme latérale, couchage, bouteille/gourde, sacoche médicale, radio, bâton lumineux |
| Gilet réellement porté | Chargeur gauche, chargeur droit, sacoche médicale, grenades, holster/pistolet |

« Charges sur les côtés » interprété comme chargeurs ; aucun système de charges explosives ajouté.
Les IDs acceptés sont une liste serveur explicite. Une pile doit être séparée en unités avant fixation.
Les nouveaux objets natifs ont une masse et un encombrement ; pas de nouveau peuplement de loot promis.
Menottes, radio et grenades sont des objets d'inventaire ; arrestation, communications et explosifs ne sont pas implémentés par cette modification.

## Comportement

- Les attaches sont des emplacements à un objet, affichés en rangées sous leur support. Elles ne sont jamais utilisées automatiquement comme de grandes grilles.
- Les emplacements vides peuvent recevoir l'objet sélectionné uniquement s'il est compatible. Les objets fixés restent sélectionnables et récupérables par les actions natives.
- Le holster doit être équipé avant son pistolet ; même principe pour le fourreau.
- Une sacoche médicale montée crée un rangement 4 × 3. Ce rangement est lié à sa fixation actuelle, et non à une identité portable de sacoche avec contenu.
- Pour déplacer/retirer une sacoche, il faut la vider ; pour retirer un support, il faut détacher ses accessoires. Le transfert d'un conteneur plein complet n'est pas implémenté.
- Les piles conservent identifiant, quantité et condition. Toutes comptent une seule fois dans le poids. Les données empruntent la sauvegarde et la réplication existantes ; pas de registre secondaire.
- Si un support disparaît, les objets restent accessibles en récupération. Les RPC d'inventaire existants exécutent les contrôles côté serveur.
- Le panneau utilise les modèles exacts lorsqu'ils sont disponibles et garde un nom explicite autrement. Les silhouettes graphiques de tous les emplacements manquants restent à réaliser.
- Le fusil Quantum peut créer un composant 3D fixé à un os de colonne vérifié du sac. Ce placement n'a pas encore été vérifié en PIE : orientation, traversées et animation restent à contrôler.
- Aucune compatibilité automatique des vêtements Quantum avec Survival/Manny/Quinn.
- Pas de nouvel équipement 3D fictif : modèle confirmé de ceinture, sacoche textile, couchage, gourde et menottes encore nécessaire pour achever tous les visuels.
- Gilet Survival compatible non présent sur le personnage d'essai actuel. Les emplacements ne sont accordés que lorsqu'un mesh de gilet est réellement porté.
- Capacité des anciens vêtements et stockage des gants/bottes inchangés ; ce travail ne constitue pas un rééquilibrage DayZ.

## Vérifications réellement exécutées

1. Run 40719380076 : audit local des modèles et accessoires réussi. Chargeurs AK/M4 et holster Quantum repérés ; caisse médicale disponible, mais une caisse n'est pas une sacoche. Aucun chien confirmé.
2. Run 40719649552, commit 3723ec8c9720699101917be2d52ffb59fd0bcce0 : compilation Editor UE 5.8.3 réussie, 28 actions UBT. Artefact 12828589525.
3. Même run : 27 tests natifs exécutés, 26 réussis. Nouveau test Anomalia.Native.EquipmentAttachments réussi (0 erreur) : compatibilité, séparation des chargeurs, exclusivité, rangement médical, protection des parents, relecture et récupération. Ces tests utilisent un monde isolé ; un mesh transitoire vide sert exclusivement de fixture pour l'autorisation des supports, pas de personnage intégré.
4. Régression détectée : InventoryLayoutMigration échoue. Le contrôle général de placement interdisait également le remplissage initial des compartiments de récupération pendant migration.
5. Correctif af1fc57259398abe58f42a12aa6b926c70403420 : privilège limité au chemin de migration existant. Il ne s'applique pas aux dépôts, pickups ou requêtes d'équipement normaux.
6. Run 40720599355 : recompilation du correctif BLOQUÉE AVANT écriture des sources par la garde mémoire : 1 186 844 672 octets libres, minimum 4 Gio ; disque libre 9 409 437 696 octets, réserve 6 Gio maintenue. Aucun test de ce correctif annoncé réussi.
7. Audit 40720821012 : UnrealEditor PID 6068 occupe environ 5,76 Go ; environ 2,06 Go de RAM libres à cette mesure. Aucune application utilisateur arrêtée.
8. Le contrôle CI des sources a initialement échoué parce que huit objets natifs supplémentaires n'étaient pas dans la liste d'exceptions. Liste native explicite ajoutée, anciens IDs et masses toujours vérifiés. Runs 40720606336 et 40720832811 réussis.

Aucune nouvelle session PIE, capture, manipulation physique clavier/souris, cible Game ou session à deux joueurs validée pour ces attaches.
La copie de validation contient encore le premier binaire tant que le correctif n'a pas pu être recompilé. Le projet installé et les sauvegardes utilisateur n'ont pas été modifiés.

## Chien

Créateur officiel : https://retrostylegames.itch.io/german-shepherd-3d-dog-model-free
Archive annoncée : RSG_DogsPack_GermanShepherd_UE5_1.zip, environ 45 Mo.
Le créateur annonce usage commercial/personnel gratuit et squelette spécifique ; assis/couché/attaque non confirmés.
Run 40719795327 : accès à la page publique refusé HTTP 403, reçu BLOCKED_PUBLIC_CREATOR_HTTP conservé. Aucun téléchargement/import, aucune protection contournée, aucun compagnon natif annoncé terminé.
Recherche de fichiers joints : aucun résultat pour les noms Monkey, RSG_DogsPack et GermanShepherd ; cela n'établit pas leur absence du compte Fab.

## Monkey B3

Ajout signalé par l'utilisateur après l'audit initial. Recherche de nom de fichier dédiée préparée et lancée dans Content original/validation, FabImports, Téléchargements et projets Unreal.
Identification non confirmée au moment de cette rédaction ; ne pas supposer qu'il s'agit d'un chien ou d'un véhicule. Reçu final à compléter à la fin du run 40721361727.

## Fichiers

AnomaliaInventoryComponent.h/.cpp ; AnomaliaInventoryWidget.h/.cpp ; Tests/AnomaliaEquipmentAttachmentTests.cpp ; tests/test_ue5_inventory_source.py ; workflows de compilation, recherche d'assets et acquisition du chien.
BMW E39, véhicules, cartes, pawn principal et données Fab originaux préservés. PR44 reste en brouillon.
