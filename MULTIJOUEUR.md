# ANOMALIA — serveurs indépendants, ANOMALIA Editor et mises à jour Windows (pré-alpha)

## Isolation des serveurs

Chaque serveur dédié dispose de son identifiant stable `SERVER_ID` (exemple `rp-ajaccio`) et d'un répertoire séparé `SERVER_DATA_ROOT/servers/<SERVER_ID>/world.json`. Les plans d'ANOMALIA Editor, le mode RP/PVP/PVE et les futures données du monde sont propres à cet identifiant. Les identifiants sont validés : aucune traversée de dossier n'est acceptée. Deux serveurs différents ne lisent ni n'écrivent le même plan.

Dans le client Windows, les fichiers de configuration personnels sont rangés sous `%APPDATA%/anomalia-primeval-outboundun/profiles/solo/config` ou `profiles/remote-<empreinte de l'adresse>/config`. Un changement de serveur sélectionne un profil distinct. Les paramètres de chaque utilisateur restent locaux ; ils ne modifient pas le serveur d'autrui. Les fichiers de configuration globaux historiques ne sont pas effacés.

La sauvegarde solo n'est pas réécrite pendant une session multijoueur. À la déconnexion, un instantané du personnage et de sa carte solo est restauré. L'éditeur de carte multijoueur est autorisé seulement au propriétaire authentifié avec la clé privée `SERVER_ADMIN_KEY` (ou le jeton fourni par l'hôte Windows) ; les autres joueurs reçoivent les mises à jour sans pouvoir les publier. Le code local `ANOMALIA-EDITOR-2026` n'accorde **aucun** droit réseau.

## Mode RP, PVP, PVE ou mixte

Au moment d'héberger sur Windows, sélectionner le mode. Un serveur Node autonome utilise `GAME_MODE=rp`, `pvp`, `pve` ou `mixed`. Le prototype PVP applique des dégâts décidés côté serveur ; en mode mixte les zones protégées RP ne subissent pas de tirs entre joueurs. Les collisions, le système de factions et la sécurité anticheat ne sont pas encore complets.

## Mise à jour du jeu installé

L'installateur Windows porte l'emblème ANOMALIA. Une fois installée, l'application recherche les **versions officielles publiées dans GitHub Releases** au démarrage et toutes les six heures. Une version plus récente est téléchargée puis installée lors de la fermeture de l'application. Un simple commit GitHub ne déclenche pas une mise à jour des joueurs : il faut créer une version numérotée, un tag GitHub `vX.Y.Z` correspondant à `package.json` et publier le nouvel installateur avec le manifeste `latest.yml`. Les fichiers utilisateurs et les répertoires des serveurs ne font pas partie de l'installateur et ne sont pas supprimés lors de la mise à jour. Les exécutables restent non signés tant qu'aucun certificat de signature n'est configuré.

## Historique — première connexion multijoueur (0.5)

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

Il s’agit d’une première couche réseau de présence, pas encore d’un serveur de survie complet. Les inventaires, le loot, la banque, les véhicules, l’IA, les dinosaures, les constructions et les événements restent locaux. Il n’y a pas encore de dégâts entre joueurs, de persistance serveur, de comptes ou d’autorité serveur sur ces systèmes. Les outils admin sont ceux du prototype solo. Ils ne constituent pas une administration sécurisée pour un serveur public RP/PvP.

Le serveur est livré dans le dépôt source et se lance séparément. L’installateur Windows est le client du jeu.

## Bâtiments et éditeur local

Hôpital, police, gendarmerie, caserne de pompiers, caserne militaire, armurerie, boutique et maison possèdent des intérieurs avec des entrées ouvertes. Un héliport et des pontons complètent les emplacements. Ils utilisent des modèles procéduraux originaux, pas les ressources graphiques de DayZ. Les façades des grandes tours générées restent décoratives.

L’éditeur est accessible depuis le menu de démarrage ou avec F4 en solo. Code de cette version : `ANOMALIA-EDITOR-2026`. C’est un verrou local de confort, pas un système de droits serveur. Sélectionner le catalogue, cliquer « Placer au clic », puis sur le terrain. Les coordonnées et la rotation se modifient dans le panneau ; duplication, suppression, annulation/rétablissement et import/export JSON sont disponibles. La composition est conservée dans la sauvegarde locale. Les positions importées sont limitées à la carte et à 300 objets.

Déplacement de caméra : ZQSD/WASD, Maj pour accélérer, Espace/Ctrl pour monter/descendre, clic droit maintenu pour regarder. L’import/export produit un fichier ANOMALIA ; il ne charge pas directement les projets DayZ Editor ni les PBO.

Dans la version Windows, le bouton « Héberger en réseau local » lance le serveur intégré sur le port 2303 sans installation de Node.js. Le mot de passe saisi est appliqué à l’hébergement. Les adresses LAN détectées s’affichent pour les communiquer aux invités ; cliquer ensuite sur Rejoindre pour jouer sur son propre serveur. Le serveur s’arrête à la fermeture du jeu. Le pare-feu Windows peut demander l’autorisation réseau lors du premier hébergement. La page HTML seule propose de rejoindre un serveur déjà lancé et ne peut pas en héberger un.

## Version 0.6 — début de survie

Une nouvelle sauvegarde commence sur une plage : soif, froid, très peu de provisions, aucune arme offerte. L’eau et un manteau sont des objets réels au sol ; les objectifs avancent après consommation de l’eau puis équipement du manteau. Une berline conduite en vue extérieure ou intérieure se trouve à proximité. L’extérieur utilise désormais un modèle GLB Innerscene CC0 à l’échelle réelle ; son habitacle reste simplifié et les autres véhicules gardent leurs modèles procéduraux. Le rendu global ne correspond pas encore à celui de DayZ/ARK.

Les sauvegardes existantes continuent à leur ancien emplacement. Le bouton « Nouvelle survie — plage » conserve une copie de la sauvegarde précédente avant de commencer. L’éditeur est directement accessible dans le menu principal par « Éditeur de carte » (ou F4 en jeu). Le code de cette version reste ANOMALIA-EDITOR-2026.

## Version 0.7 — terres et construction

Carte de 48 × 48 km (2304 km² au total). Deux continents supplémentaires, Borée et Austral, portent la surface émergée estimée à 374,521875 km², calculée à partir de la hauteur réelle du terrain avec une grille de 25 mètres, au-dessus de la surface de l’eau à 0,5 m. Le calcul exclut les cellules sous la mer. Les cellules dont les quatre coins et le centre sont secs représentent 371,011875 km² : le seuil de 300 km² conserve ainsi une marge importante. Les chiffres sont des estimations discrétisées du terrain, pas une mesure analytique exacte du rivage. Reproduire avec npm run measure:land.

B ouvre la construction modulaire. Choisir bois, pierre ou métal, puis fondation, pilotis, plateforme flottante ancrée, fondation sous-marine, mur, fenêtre, cadre, porte, plancher supérieur, toit, escalier ou rampe. Les textures existantes de bois et de roche sont utilisées ; les panneaux de métal ont un matériau PBR. Les matériaux sont consommés à la pose. Récolter des matériaux dans une zone terrestre depuis le menu B ; le métal nécessite une ville. Les ressources locales sont limitées et se renouvellent après dix minutes.

R tourne la prévisualisation, E/clic pose, Échap annule. Les murs et les toits nécessitent une fondation ou un plancher. Les planchers supérieurs nécessitent un mur porteur. Une porte nécessite son cadre. Les supports ne peuvent pas être démolis avant les éléments qui en dépendent. La démolition rend la moitié des matériaux. Limite actuelle : 1500 pièces et quatre étages supérieurs. Les planchers et les escaliers sont parcourables ; E ouvre ou ferme les portes.

Les pilotis rejoignent le fond marin ; les plateformes flottantes sont ancrées et ne se pilotent pas comme un bateau. Les fondations sous-marines reposent sur le fond réel. J permet de plonger, Espace de remonter et Ctrl de descendre ; l’oxygène apparaît dans le HUD. Les pièces sous-marines ne créent pas de poche d’air et ne sont pas pressurisées. La simulation de vagues, de pression et de flottabilité des bâtiments n’est pas implémentée.

Les constructions restent locales à la sauvegarde dans cette version : leur synchronisation multijoueur n’est pas encore implémentée. Il ne s’agit pas d’une reproduction complète du système ARK (pas de réseau de tuyaux, électricité, raids structurels ou propriété de tribu).
