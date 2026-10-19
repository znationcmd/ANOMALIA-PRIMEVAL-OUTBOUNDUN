# ANOMALIA — Multijoueur RP / PVP / PVE / Mixte et ANOMALIA Editor (pré-alpha)

## Modes de serveur

Depuis **Multijoueur → Mode du serveur → Héberger en réseau local**, le propriétaire peut choisir :

- **RP** : jeu de rôle sans dégâts entre joueurs ; bâtiments RP et règles propres aux communautés.
- **PVP** : tirs et dégâts entre joueurs autorisés par le serveur (prototype balistique avec angle/portée et limitation de cadence).
- **PVE** : coopératif ; tous les tirs entre joueurs sont rejetés par le serveur.
- **Mixte** : PVP hors des zones protégées ; les centres urbains RP (Hélion, hôpitaux, ports) bloquent les dégâts entre joueurs.

Le serveur contrôle ces règles : **un joueur ne peut pas activer le PVP en modifiant uniquement son client**. Ce premier combat PVP n'a pas encore de balistique, collisions, inventaire et anti-triche complets.

### ANOMALIA Editor (F4)

ANOMALIA Editor permet de placer et déplacer les bâtiments, sélectionner, dupliquer, supprimer, annuler/rétablir et exporter/importer le plan JSON. En solo, le code local d'activation continue de fonctionner ; **ce code n'octroie aucun privilège multijoueur**. Sur un serveur, seul le propriétaire connecté avec un jeton privé émis par l'hôte Windows peut ouvrir ANOMALIA Editor et publier la carte. Les joueurs ordinaires reçoivent la carte et les modifications automatiquement, mais leurs tentatives d'édition sont refusées. Les placements validés et le mode sont sauvegardés dans `world-server.json` dans les données de l'application de l'hôte Windows ; un serveur Node autonome utilise le fichier spécifié par `SERVER_DATA_FILE`, ou `server-data/world.json` par défaut.

La carte du serveur partage actuellement les constructions de **l'éditeur**. Les abris individuels, véhicules, créatures, banque et inventaires ne sont pas encore synchronisés ou persistés côté serveur ; ne pas annoncer un monde multijoueur complet. Le serveur autonome accepte `GAME_MODE=rp|pvp|pve|mixed` et `SERVER_ADMIN_KEY`. Il faut protéger le jeton propriétaire, qui ne doit jamais être partagé avec les joueurs.


Le menu affiche ANOMALIA PRIMEVAL OUTBOUNDUN et propose Solo, Multijoueur et Paramètres. Le menu de démarrage est traduit en français (par défaut), allemand, russe, italien, anglais, japonais, chinois simplifié et espagnol. La langue et la qualité graphique sont conservées. Les interfaces historiques de survie et d’administration restent en français : la traduction intégrale du jeu est encore à réaliser.

## Lancer un serveur sur Windows ou Linux

Installer Node.js 22, récupérer ce dépôt, puis exécuter :

```sh
npm install
npm run server
```

Le serveur écoute sur le port TCP 2303. Dans le jeu : Multijoueur → indiquer un nom → adresse `ws://localhost:2303` sur le même PC, ou `ws://ADRESSE_LAN_DU_SERVEUR:2303` sur un autre ordinateur du réseau → Rejoindre.

Pour une connexion Internet, l’hôte doit rendre le port accessible et communiquer son adresse. Un serveur sous HTTPS nécessite un relais TLS avec WebSocket sécurisé (`wss://`). Aucun serveur public n’est déployé automatiquement et aucune ouverture réseau n’est effectuée par le jeu.

Options du serveur : variables d’environnement `PORT`, `SERVER_PASSWORD`, `MAX_PLAYERS` (16 par défaut, plafond 64 ; aucune charge à 64 joueurs n’a été validée). Sous PowerShell :

```powershell
$env:SERVER_PASSWORD="choisir-un-mot-de-passe"
npm run server
```

## Ce qui est synchronisé

Connexion réelle par WebSocket, identifiant unique, présence des autres survivants, positions et orientation à 10 mises à jour par seconde, retrait lors de la déconnexion, validation de la vitesse et des limites de carte, mot de passe, limite de joueurs et de messages. Les survivants commencent au point commun X 0 / Z 180.

## Limites actuelles

Il s’agit d’une première couche réseau de présence, pas encore d’un serveur de survie complet. Les inventaires, le loot, la banque, les véhicules, l’IA, les dinosaures, les abris individuels et les événements restent locaux. Les plans de bâtiments ANOMALIA Editor sont désormais synchronisés avec contrôle d’accès et sauvegarde sur l'hôte. Le PVP expérimental dispose de tirs/dégâts vérifiés côté serveur, mais pas encore d'inventaire de munitions autoritaire, de collision balistique exhaustive, de comptes persistants ni d'une économie synchronisée. ANOMALIA Editor partagé est protégé par un jeton de propriétaire côté serveur, mais le panneau admin solo, les commandes de modération avancées, la persistance des survivants et les protections anti-triche restent à développer pour des serveurs publics RP/PVP.

Le serveur est livré dans le dépôt source et se lance séparément. L’installateur Windows est le client du jeu.

## Bâtiments et éditeur local

Hôpital, police, gendarmerie, caserne de pompiers, caserne militaire, armurerie, boutique et maison possèdent des intérieurs avec des entrées ouvertes. Un héliport et des pontons complètent les emplacements. Ils utilisent des modèles procéduraux originaux, pas les ressources graphiques de DayZ. Les façades des grandes tours générées restent décoratives.

ANOMALIA Editor est accessible depuis le menu de démarrage, ou avec F4 en solo et pour le propriétaire du serveur multijoueur. Code de cette version : `ANOMALIA-EDITOR-2026`. C’est un verrou local de confort, pas un système de droits serveur. Sélectionner le catalogue, cliquer « Placer au clic », puis sur le terrain. Les coordonnées et la rotation se modifient dans le panneau ; duplication, suppression, annulation/rétablissement et import/export JSON sont disponibles. La composition est conservée dans la sauvegarde locale. Les positions importées sont limitées à la carte et à 300 objets.

Déplacement de caméra : ZQSD/WASD, Maj pour accélérer, Espace/Ctrl pour monter/descendre, clic droit maintenu pour regarder. L’import/export produit un fichier ANOMALIA ; il ne charge pas directement les projets DayZ Editor ni les PBO.

Dans la version Windows, le bouton « Héberger en réseau local » lance le serveur intégré sur le port 2303 sans installation de Node.js. Le mot de passe saisi est appliqué à l’hébergement. Les adresses LAN détectées s’affichent pour les communiquer aux invités ; cliquer ensuite sur Rejoindre pour jouer sur son propre serveur. Le serveur s’arrête à la fermeture du jeu. Le pare-feu Windows peut demander l’autorisation réseau lors du premier hébergement. La page HTML seule propose de rejoindre un serveur déjà lancé et ne peut pas en héberger un.

## Version 0.6 — début de survie

Une nouvelle sauvegarde commence sur une plage : soif, froid, très peu de provisions, aucune arme offerte. L’eau et un manteau sont des objets réels au sol ; les objectifs avancent après consommation de l’eau puis équipement du manteau. Une berline conduite en vue extérieure ou intérieure se trouve à proximité. L’extérieur utilise désormais un modèle GLB Innerscene CC0 à l’échelle réelle ; son habitacle reste simplifié et les autres véhicules gardent leurs modèles procéduraux. Le rendu global ne correspond pas encore à celui de DayZ/ARK.

Les sauvegardes existantes continuent à leur ancien emplacement. Le bouton « Nouvelle survie — plage » conserve une copie de la sauvegarde précédente avant de commencer. L’éditeur est directement accessible dans le menu principal par « Éditeur de carte » (ou F4 en jeu). Le code de cette version reste ANOMALIA-EDITOR-2026.
