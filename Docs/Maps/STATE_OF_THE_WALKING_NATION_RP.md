# STATE OF THE WALKING NATION RP — carte et traversées

> Spécification de conception pour la future carte native Unreal. Ce document fixe l’implantation et les proportions; il ne prétend pas que le monde jouable est déjà généré.

## Échelle

- Emprise cible : environ 31 × 31 km (environ 961 km²).
- Deux continents principaux : environ 300 km² de terre chacun.
- Quatre îles principales : au moins 50 km² chacune, soit au moins 200 km² en tout.
- Eau libre : environ 150 km².
- Les quelque 11 km² restants servent de hauts-fonds et d’estran intertidal : visibles à marée basse, submergés à marée haute.
- Les îles et les continents sont des surfaces terrestres jouables; elles ne sont pas soustraites du total de terre.

## Trois traversées continentales

1. **Grand pont routier** : liaison visible entre les deux continents, avec accès, postes de contrôle et itinéraires de contournement.
2. **Tunnel routier sous-marin** : seconde liaison séparée du pont, avec portails, ventilation, éclairage de secours et accès de maintenance.
3. **Chaîne d’îlots intertidaux** : passage à pied seulement pendant la fenêtre de marée basse. L’eau remonte ensuite et rend le trajet impraticable; aucun accès permanent ne doit contourner cette contrainte.

Les îles principales restent accessibles par bateau. La chaîne d’îlots est un passage supplémentaire, soumis aux marées, et non un pont permanent.

## Répartition du monde

- Un continent accueille la grande agglomération, ses quartiers résidentiels, zones commerciales et périphérie.
- Le second privilégie les petites villes, villages, routes régionales, campagne et installations de secours.
- Les quatre îles ont des fonctions distinctes : port et logistique, refuge habité, site de quarantaine, et secteur isolé à explorer.
- Prévoir plusieurs refuges habités et approvisionnables sur les continents et les îles.
- Les villes restent majoritairement intactes et reconnaissables. Les dégâts, véhicules abandonnés et barrages sont localisés autour des axes contaminés, checkpoints et sites d’évacuation; ne pas transformer toute la ville en ruines.

## Boucle RP survie

- Le pont, le tunnel, le port et le passage à marée basse créent des choix de trajet et des contrôles de circulation.
- Les refuges ont des niveaux d’accès et d’approvisionnement différents.
- Le cycle de marée doit annoncer clairement l’ouverture et la fermeture du passage intertidal.
- Les ambiances s’inspirent de fictions d’épidémie et de survie, sans reprendre leurs lieux, logos ou personnages.

## Validation requise avant publication

- Mesurer les surfaces de terre, d’eau, des deux continents et des quatre îles dans le monde Unreal.
- Vérifier que les trois traversées relient effectivement les zones prévues et que le passage intertidal ferme à marée haute.
- Ouvrir la carte dans l’éditeur natif et le build jouable, puis confirmer les refuges et les routes accessibles.
