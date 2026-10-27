# E39 — simulation et mécanique de survie

Demande du 27 octobre 2026 : conserver la même BMW E39 et obtenir une conduite
crédible sur sec, sous la pluie, sur neige et dans le sable, avec pièces
amovibles, vraie clé de démarrage/verrouillage et coffre utilisable.

Forza Motorsport est une référence de qualité demandée, pas un niveau acquis.
Le profil Chaos actuellement accepté est un banc de validation, pas encore une
calibration homologuée du modèle exact. Les 61 contrôles précédents ne valident
ni la météo, ni la maintenance, ni une clé physique, ni le stockage du coffre.

## Critères de réalisation

- Pneus : adhérence par roue et matériau réellement touché, charges, freinage
  ABS, transfert de charge, glissement combiné, propulsion et différentiel.
- Conditions : sec, chaussée mouillée, eau à vitesse élevée, neige, glace,
  sable meuble ; pneus adaptés et résistance au roulement, sans imposer une
  vitesse artificielle. Météo visuelle et état physique doivent correspondre.
- Mesures : freinages répétés à vitesse égale, accélération, virages, perte et
  reprise d’adhérence, transition et adhérence dissymétrique. Documenter les
  paramètres provisoires et les écarts à une référence mesurée.
- Radiateur, batterie et bougies : retrait/pose depuis l’inventaire réel,
  accès physique au compartiment, moteur arrêté, conservation des objets,
  batterie déchargée, refroidissement, surchauffe et conséquences moteur.
- Clé : objet d’inventaire lié à l’identité persistante d’un seul véhicule ;
  mauvaise clé, clé absente, verrouillage et démarrage refusés ; état visible
  des portes, pas une simple autorisation associée au nom du joueur.
- Coffre : ouvrir et déverrouiller avant transfert ; portée et ligne de vue
  vérifiées par le serveur, limites de grille/poids, dépôt et retrait sans
  duplication ni perte, restauration après redémarrage. Chargement ajouté à
  la masse physique et au centre de gravité selon son emplacement.
- Sauvegarde : identité stable, clé/serrure, pièces, fluides et contenu ;
  échanges joueur/véhicule atomiques ou journalisés et récupérables.
- Utilisation réelle : commandes et interface accessibles au joueur,
  réplication et erreurs compréhensibles ; aucun système inactif présenté
  comme terminé.

## État au début de cette extension

Coffre v7 : doublure du couvercle séparée de la coque fixe, audit géométrique
réussi ; validation Windows en cours. Conduite v6 : 61 contrôles réussis,
24 tests natifs sans échec, 35 contrôles de régression de la berline d’origine.
Les systèmes de cette nouvelle demande ne sont pas encore acceptés.

## Précision d’interface du joueur — inventaire de proximité, 27 octobre

- Aucun menu garage séparé : le véhicule voisin figure dans Proximité à gauche
  ou dans l’en-tête de l’inventaire habituel.
- Pièces à slots uniques : batterie, radiateur, bougie, quatre roues ; le
  démarrage est refusé si une pièce fonctionnelle requise manque ou est détruite.
- Carrosserie amovible : quatre portes, capot et couvercle de coffre ; retrait
  et pose doivent modifier les vrais maillages et collisions, sans substitution.
- Compartiments : capot/coffre physiquement ouverts avant de voir et manipuler
  les slots concernés. La portée et les obstacles sont vérifiés sur le serveur.
- Commandes souhaitées PS5 : pavé tactile pour ouvrir ; maintenir Croix pour
  prendre/déplacer puis relâcher/valider sur une destination ; stick pour la
  navigation ; Carré pour transfert rapide vers mains/coffre. Tester aussi le
  clavier/souris et la navigation sans pointeur. Aucune certification ou
  validation PS5 implicite : la plateforme native actuelle de test est Windows.
- Sécurité des pièces : tournevis pour batterie/radiateur ; démonte-roue pour
  roues. La serrure du véhicule et les fixations des pièces restent distinctes.
- Coffre : cargaison générique configurable selon le véhicule (références
  demandées 1000/4000 cellules ou plus), avec limites de poids et de masse réelles.
- Sacs remplis transférables sans aplatir/perdre leur contenu. Identités de
  contenants, profondeur limitée, cycles interdits et calcul récursif du poids ;
  sauvegarde atomique de l’arbre d’objets. Ne pas simuler cette fonction en
  transférant seulement une pile « sac » vide.

## Première implémentation native — validation à venir

Code en préparation : composant de clé physique unique et mécanique,
interverrouillage réel du démarrage (batterie, radiateur, bougie, clé, état
moteur), serrures des six ouvrants, coffre de 1000 cellules/100 kg et échanges
journalisés avec le profil joueur. Une charge déposée augmente la masse du
châssis. La recharge, le refroidissement et la surchauffe sont une première
modélisation de jeu à calibrer ; les pièces ne possèdent pas encore chacune
leur propre identité/condition conservée hors du véhicule.

L’interface est ajoutée à l’inventaire existant, avec Proximité à gauche,
visibilité des slots selon les ouvrants, dépôt/retrait, retrait vers les mains,
Croix maintenu pour sélectionner puis relâché sur une destination et Carré
pour le transfert rapide. Le schéma générique Unreal réserve Special Left à
l’inventaire et Special Right à la pause ; le routage du pavé tactile dépend
encore du pilote/du support plateforme et n’est pas accepté sur une PS5.

Les essais natifs définis couvrent clé, absence de pièces, mauvais véhicule,
charge, rejets de compte périmé, transfert vers les mains et reprise de journal
après plusieurs redémarrages. Le parcours E39 doit aussi exercer maintenance
capot/coffre ouverts, réinstallation, remplissage, verrouillage et masse réelle.
**Ces nouveaux essais ne sont pas encore passés sur le poste Unreal.**

Restent à implémenter/valider : pneus et météo détaillés, roues et carrosserie
démontables, fixations au tournevis/démonte-roue, inventaires de sacs imbriqués,
conditions individuelles des pièces, position du centre de masse du chargement,
finition des pièces 3D et essais physiques de manette/console. Ne pas décrire
cette première implémentation comme le système DayZ/Forza complet demandé.
