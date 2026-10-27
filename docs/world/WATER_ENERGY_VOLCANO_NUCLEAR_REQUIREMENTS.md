# Eau, énergie, volcan et centrale nucléaire — demandes du 25 octobre 2026

Statut : exigences à intégrer après validation de la première berline Chaos.
Ce document ne signifie pas que les lieux ou mécanismes existent déjà en jeu.

## Eau et purification

- Placer un lac et des rivières sur la véritable carte, avec eau visible, collisions
  adaptées, nage et interactions de remplissage reliées à l'inventaire serveur.
- Leur eau est contaminée et dangereuse à boire sans traitement.
- **Règle de jeu explicitement demandée : une tablette de chlore rend potable
  l'eau contaminée, y compris l'eau radioactive.** C'est une convention fictive
  d'ANOMALIA, pas une propriété du chlore dans le monde réel.
- Une tablette et la quantité d'eau définie par recette sont consommées
  atomiquement ; le contenant est conservé. Pas de duplication ni de récompense
  supplémentaire en rejouant la requête.
- Des fontaines et points d'eau potables dans les villes et villages permettent
  de boire et remplir les contenants. La qualité doit rester identifiable.
- Réutiliser `water_purification_tablets`, `dirty_water_bottle`, `water_bottle`
  et la transaction persistante de `UAnomaliaInventoryComponent::TryUseStack`.
  La recette actuelle traite une bouteille sale ; la contamination radioactive,
  les sources naturelles et les fontaines restent à intégrer et tester.

## Carburants et plateforme pétrolière

- Stations-service utilisables pour collecter du carburant dans des contenants
  compatibles, puis alimenter véhicules et générateurs réels.
- Plateforme pétrolière sur l'eau avec pétrole récupérable et danger configurable.
- Recette fictive pétrole + peau animale dans une forge pour fabriquer de
  l'essence. Quantités, durée, rendement et consommation réglables côté serveur.
- Réutiliser l'identifiant carburant et le réseau électrique existants ; vérifier
  les catalogues avant d'ajouter des identifiants ou recettes en double.

## Île volcanique et temple

- Île avec volcan, lave animée visible et véritable danger thermique/dégâts.
- Passage praticable menant à un temple secret, accès et énigmes persistants.
- Assets 3D licenciés, navigation, collisions, sons et optimisation à valider
  dans Unreal. Une texture ou un nom de catalogue ne valide pas ces lieux.

## Centrale nucléaire et instruments

- Grande centrale sur la carte principale, zones radioactives et accès progressif.
- Compteur Geiger : comptage CPS/CPM avec sons, dépendant du champ simulé.
- Radiamètre : débit de dose simulé en µSv/h ou mSv/h, selon profil serveur.
- Contaminamètre : contamination surfacique simulée en Bq/cm².
- Spectromètre : identification de signatures de sources fictives configurées.
- Les quatre instruments lisent un même modèle de danger serveur avec leurs
  unités/rôles distincts ; ne pas convertir automatiquement CPM en dose sans un
  profil de capteur. Batteries, portée, permissions, protections et dose cumulée
  doivent être configurables et persistantes lorsque pertinent.

## Conditions de validation

Essais solo et multijoueur : remplir, boire avant/après traitement, traiter eau
radioactive selon la règle fictive ci-dessus, demandes simultanées et rejouées,
contenants pleins, inventaire plein, redémarrage pendant transaction, ravitaillement
véhicule/générateur, production d'essence, traversée lave/temple, détection hors et
dans zone nucléaire, protection et sauvegarde. Aucun de ces essais supplémentaires
n'est annoncé réalisé à ce stade.
