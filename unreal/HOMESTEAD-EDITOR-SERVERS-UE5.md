# ANOMALIA UE5 — Maison, ferme, repos, Editor et serveurs

ÉTAT : sources et outils en cours de portage vers UE5.8.
Aucune compilation ou test dans Unreal Engine n'a été confirmé.
La version navigateur et les données des serveurs existants ne sont pas supprimées.

## C++ UE5 ajouté

- Fatigue de 0 à 100 répliquée et enregistrée dans le profil joueur.
- Touche R près d'un lit (maximum 2,5 m) pour dormir/réveiller le personnage.
  Pendant le sommeil, le mouvement est bloqué et la fatigue diminue.
- Acteur placeable : lit, table, chaise, canapé, armoire, cuisine, lampe,
  grange, clôture, niche, abri tracteur, vache, poule, ruche.
- Les acteurs utilisent actuellement un cube Unreal temporaire : PAS de
  modèles 3D finis, animations, troupeaux, production saisonnière ou IA.
- Touche E à moins de 2,75 m des stations de ferme : 1 lait, œuf ou miel.
  Le serveur valide l'action, le délai de récolte de 120 s et l'inventaire.
- Tracteur ajouté au catalogue (prototype de configuration, pas une vraie
  conduite agricole).

## ANOMALIA Editor et Tools — premier socle hors ligne

Le fichier scripts/ue5/anomalia-editor-tools.py permet de créer, lister et
retirer des meubles et objets de ferme dans le dossier STRICTEMENT propre au
serveur : Saved/Servers/<id>/Editor/world.json.

Exemples dans un terminal depuis la racine du dépôt :

    python scripts/ue5/anomalia-editor-tools.py --server-id personal_1 add bed01 bed 0 0 100 0
    python scripts/ue5/anomalia-editor-tools.py --server-id personal_1 add cow01 cow 400 0 100 0
    python scripts/ue5/anomalia-editor-tools.py --server-id personal_1 list
    python scripts/ue5/anomalia-editor-tools.py new-mod my_furniture_pack
    python scripts/ue5/anomalia-editor-tools.py lint-mod mods/my_furniture_pack

Le GameMode importe les objets autorisés de son propre dossier au début de la
partie (maximum 256 placements, coordonnées validées). Les documents invalides
ne sont pas écrasés. Un monde personnel ne modifie pas un autre serveur.

ANOMALIA Tools génère pour le moment un manifeste de mod JSON PC data-only.
Cela N'EST PAS encore un paquet Unreal Engine, un éditeur 3D en jeu, un
Workshop opérationnel ni un outil de distribution de mods cross-play.
L'accès aux mods sur console exige des validations adaptées des fabricants,
et la possibilité d'utiliser certains scripts ou contenus peut être limitée.

## Navigateur de serveurs prévu

15 emplacements OFFICIELS de configuration : 5 PVE, 5 PVP, 5 RP.
Classe C++ : UAnomaliaZPrigimaliaServerBrowserLibrary. Les filtres All/PVE/PVP/RP
fonctionnent sur des structures de données C++.
Ces emplacements NE SONT PAS des serveurs réellement hébergés, ouverts,
accessibles ni connectés à CMD Hosting. L'interface UMG reste à développer.

## Étapes non terminées

1. Compiler C++ avec Unreal Engine 5.8 et valider les tests réseau.
2. Fournir modèles 3D, collisions, animations, IA animaux et véhicules.
3. Développer une vraie interface UMG ANOMALIA Editor avec permissions,
   placement 3D, déplacement, rotation, sauvegardes et annulation.
4. Faire des tests d'isolation avec au moins deux serveurs et plusieurs clients.
5. Packager, signer et publier les mods sur PC/consoles selon leurs contraintes.
6. Relier les serveurs réellement installés à CMD Hosting et faire les essais.

Les tests Python sont des contrôles de source et d'écriture hors ligne,
pas une preuve d'exécution dans Unreal Engine.
