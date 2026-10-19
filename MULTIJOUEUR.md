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
