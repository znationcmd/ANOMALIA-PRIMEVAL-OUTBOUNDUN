# Ville RP protégée et expédition du commissariat

Demande du 25 octobre 2026. Statut : exigences enregistrées, non implémentées.
La démonstration UE5 et la première berline validée restent prioritaires.

## Ville RP dans une zone protégée

- Ville accessible entourée entièrement de murs, avec une grande porte réellement
  animée, des collisions et une navigation compatibles joueurs, PNJ et véhicules.
- Commerces avec intérieurs utilisables, comptoirs, stockage et interactions réelles.
  Réserver les emplacements des commerces de nourriture/eau, vêtements, outils,
  soins, mécanique/pièces/carburant et équipements de survie ; compléter selon
  les catalogues et métiers RP existants, sans créer de doublons.
- Traders et vendeurs PNJ, ainsi que boutiques/stands tenus par des joueurs.
- Achats, ventes, prix, stocks, inventaires et propriété contrôlés par le serveur.
  Une transaction doit débiter et livrer ensemble ou être annulée entièrement.
- Stocks de PNJ et fréquence de renouvellement configurables. Stocks de joueurs
  alimentés par leurs objets réels ; caisse et marchandise persistantes.
- Identifiants stables des boutiques, vendeurs, porte et enceinte ; droits des
  propriétaires/employés et outils d'administration réutilisés s'ils existent.
- Protection de zone imposée côté serveur : dégâts entre joueurs, projectiles,
  explosifs, attaques de créatures et collisions offensives des véhicules à
  prendre en compte. Pas uniquement un message ou un indicateur d'interface.
- Conditions d'entrée, règles RP et exceptions administratives configurables ;
  aucun assouplissement des permissions globales du serveur.

## Commissariat de la plus grande ville

Créer un lieu original inspiré de l'atmosphère d'exploration et d'énigmes de
Resident Evil 2. Ne pas reproduire le bâtiment RPD à l'identique, ses plans,
personnages, symboles, textes, musiques, modèles ou autres assets propriétaires.

- Grand commissariat avec hall, bureaux, archives, cellules, locaux techniques,
  escaliers et espaces souterrains réellement explorables selon le plan original.
- Enchaînement d'accès : trouver des indices et clés, résoudre des mécanismes,
  débloquer les pièces et atteindre une salle finale avec récompenses réglables.
- Portes à clés avec véritables ouvrants, serrures, collisions, sons et états
  répliqués. Chaque clé correspond à des accès explicites validés côté serveur.
- Énigmes originales avec indices lisibles et mécanismes animés ; solution et
  progression configurables. Prévoir un parcours praticable en solo et en groupe.
- Zombies dans le bâtiment et chiens zombies originaux avec meshes squelettiques,
  Animation Blueprints, déplacements, perception, poursuite, attaques, dégâts,
  réactions et mort réels. Navigation intérieure et portes à tester ; une animation
  en boucle ou un nom ajouté au catalogue ne valide pas l'IA.
- Assets originaux ou licences compatibles, aucune dépense sans accord.

## Réapparition des clés à chaque redémarrage

Règle demandée : les clés de cette expédition réapparaissent à chaque redémarrage
du serveur. Cette réinitialisation reste isolée du reste du monde persistant.

- Chaque instance de serveur conserve un identifiant de session de démarrage et
  chaque point de clé un identifiant stable. Une clé est créée au plus une fois
  par point et par session, même si la cellule World Partition est rechargée.
- Réserver puis sauvegarder l'apparition avant de la rendre récupérable, avec
  récupération des transactions interrompues. Ne pas recréer une clé à chaque
  connexion d'un joueur ou rechargement de cellule.
- Définir explicitement la validité des anciennes clés : par défaut, clés de quête
  liées à leur session ; les anciennes ne déverrouillent pas un nouveau parcours.
  Ne pas effacer les autres objets ou sauvegardes du personnage.
- État des portes, énigmes, ennemis et récompenses configuré séparément du respawn
  des clés ; une porte déjà ouverte ne doit pas permettre de répéter une récompense
  personnelle non prévue. La réinitialisation éventuelle du donjon est dédiée.
- Prévoir plusieurs possibilités d'accès ou un remplacement contrôlé des clés
  perdues pour éviter qu'un groupe puisse bloquer durablement le parcours.
- Autorisations et périmètre des récompenses par personnage/groupe/serveur explicites.

## Validation avant acceptation

Tester en solo et avec plusieurs joueurs : enceinte sans passage involontaire,
grande porte et véhicules, protections aux frontières de zone, PNJ et commerces,
vente simultanée de la dernière unité, achats avec inventaire plein, reconnexion,
sauvegarde/reprise, clé correcte/absente/périmée, redémarrage et rechargement de
cellule sans clés dupliquées, progression d'énigmes, IA dans les escaliers/portes,
attaques des chiens zombies et récompenses non rejouables.

À ce stade aucun bâtiment, commerce, zombie, chien zombie, énigme ou test de
cette extension n'est déclaré intégré, compilé ou vérifié en jeu.
