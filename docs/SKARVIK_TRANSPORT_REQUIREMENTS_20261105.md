# SKARVIK — transports demandés le 5 novembre 2026

Intégrer dans la carte principale existante. Préserver les cartes, rails, bâtiments, modèles et sauvegardes originaux.

## Ascenseurs et boutons
Retrouver les modèles d'ascenseur et de bouton fournis par l'utilisateur sur C:/D: et dans les projets UE5 séparés.
Installer uniquement dans les bâtiments avec cage, cabine, portes et paliers réellement accessibles.
Relier boutons d'appel et commandes intérieures aux étages; arrêt aligné au palier, portes fermées pendant le trajet, présence des passagers conservée.
Valider entrées/sorties, collisions des portes, transport du personnage et synchronisation multijoueur. Ne pas déclarer un bâtiment accessible sur le seul placement de la cabine.

## Téléphériques
Deux liaisons demandées: ville vers montagnes enneigées; ville vers désert.
Réutiliser le véritable modèle importé, ses cabines, gares et pylônes lorsqu'ils existent.
Déterminer les villes de départ et les coordonnées à partir du relief réel et du catalogue des villes; aucune coordonnée supposée n'est une implantation validée.
Tracer les câbles, vérifier la garde au sol, le franchissement du relief, l'accès piéton aux gares et le transport des passagers.

## Métro
Réseau sous les villes de SKARVIK avec au moins une station accessible par ville.
Utiliser le projet CitySubwayTrainModular/Subway_Train déjà retrouvé et les ressources compatibles.
Prévoir tunnels continus, quais, escaliers/ascenseurs, entrée dans les rames, arrêt en station et circulation sans traverser le terrain.
Décompter les villes et stations depuis les identifiants réellement présents; le nombre de villages ne doit pas être confondu avec celui des villes.

## Train de surface
Une gare par ville, raccordée aux rails déjà présents.
Conserver et réutiliser les rails existants; vérifier continuité, courbes, raccordements, aiguillages nécessaires, ponts et quais.
Le code RailTrack/RailCarriage/TransportMovement existe dans la branche. Sa présence ne prouve ni les lignes de la carte principale ni une circulation fonctionnelle.

## Preuves attendues
Inventaire des modèles/Blueprints/dépendances; coordonnées réelles des stations; graphe des lignes et extrémités raccordées; compilation et vérification Blueprint; trajets complets en PIE avec passagers; accès aux quais et bâtiments; mesures de performance; journaux/captures et commits.
État initial de cette extension: exigences enregistrées, implantation et essais non réalisés.
