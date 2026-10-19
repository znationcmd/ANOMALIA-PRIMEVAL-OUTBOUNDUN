# ANOMALIA — connexion multijoueur expérimentale (0.5)

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
