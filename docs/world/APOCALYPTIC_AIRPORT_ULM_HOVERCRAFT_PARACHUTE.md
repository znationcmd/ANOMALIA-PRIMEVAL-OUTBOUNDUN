# Aéroport apocalyptique, ULM, aéroglisseur et parachutisme

Demande du 26 octobre 2026. État : exigences enregistrées, non implémentées,
non compilées et non vérifiées en jeu. La première berline et sa démonstration
native restent prioritaires. Aucun autre véhicule n'est déclaré terminé avant
sa validation complète. Ce document n'ajoute pas de faux véhicules au catalogue.

## Grand aéroport sur la carte principale

Réutiliser l'emplacement/identité d'aéroport existant s'il est présent dans les
assets de carte ; ne pas ajouter un doublon. Nom original, identifiant stable et
panneaux réels, en cohérence avec les autres localités ANOMALIA.

- Grande piste d'atterrissage utilisable : profil initial proposé 2800 x 45 m,
  configurable après vérification du terrain et des distances d'approche. Voies
  de circulation et aire de stationnement reliées, sols/collisions physiques.
- Aérogare explorable avec halls, contrôle, bagages, sanitaires, salles techniques,
  tour de contrôle, garages, dépôts de carburant et hangars à avions accessibles.
- Décor apocalyptique original : corps de victimes non graphiques, valises et
  bagages dispersés, véhicules abandonnés, traces d'évacuation, dommages et
  végétation. Éviter de bloquer systématiquement toute la piste et les accès.
- Les valises récupérables sont de vrais conteneurs reliés à l'inventaire et au
  loot serveur. Séparer les objets décoratifs des conteneurs interactifs.
- Catalogue de ressources aéronautiques, outils, carburant et indices ; variantes
  et taux de loot réglables. Relier le POI au système de ressources déjà présent.
- Réparations éventuelles de portes, éclairage/balisage et alimentation via les
  systèmes existants, sans dupliquer les gestionnaires.
- Navigation IA, World Partition/HLOD, collisions, noms et états persistants ;
  licences et budgets de géométrie/textures documentés pour chaque asset.

## Deux ULM distincts

La nomenclature française demandée correspond à :

| Véhicule | Modèle physique requis |
| --- | --- |
| Classe 2 : pendulaire | Aile portante et chariot, pilotage par déplacement relatif de masse, poussée d'hélice, vitesse air/vent, décrochage et atterrissage. |
| Classe 4 : autogire | Rotor sustentateur en autorotation, propulsion distincte, régime rotor, prérotation selon modèle, roulage/décollage et atterrissage ; comportement distinct d'un hélicoptère. |

Vrais meshes/squelettes ou pièces mobiles, hélices/rotors animés, train et cockpit,
caméras, carburant, pièces/dégâts, sièges et entrée/sortie. Partager seulement les
composants compatibles (permissions, inventaire, sièges, carburant, sauvegarde).
Ne pas utiliser la simulation à pneus pour le vol, ni déplacer simplement l'acteur
par translation. Éprouver décollage, virage, panne et atterrissage dans Unreal.

Référence de classification, pas import de modèles ou entraînement aéronautique :
DGAC, formulaire R8-ULM-F002 (classes 2 à 4) :
https://www.ecologie.gouv.fr/sites/default/files/documents/R8-ULM_F002_FR_classe_2_4.pdf

## Aéroglisseur fermé de huit places

Créer un modèle original ANOMALIA à cabine fermée inspiré du type commercial
995ED. La capacité demandée est huit places au total ; plan initial : un pilote
et sept passagers, configurable. Ne pas présenter cette répartition comme une
spécification constructeur du 995ED.

- Cabine intérieure accessible, vitrages, portes, sièges réservés, points d'entrée
  et de sortie distincts, stockage et masse transportée.
- Véritable sustentation par coussin d'air, jupe et turbines animées, poussée et
  direction spécialisées. Transition eau/plage/terre sans téléportation.
- Dérive/inertie latérale, freinage adapté, obstacles, pentes et hauteur de survol
  cohérente ; ce n'est ni une voiture cachée ni un bateau rendu flottant.
- Carburant/énergie, avaries, réparations et persistance serveur. Le système de
  sièges doit permettre à huit joueurs de voyager sans double réservation.
- Nom, modèle et textures originaux ou légalement exploitables ; ne pas extraire
  les fichiers du fabricant ni employer ses logos sans droit.

Référence technique vérifiée, non licence d'asset :
https://www.griffonhoverwork.com/products/hovercraft/995ed-hovercraft/

## Parachutisme du personnage

- Parachute réel équipable dans l'inventaire, voile/suspentes/harnais modélisés et
  animés, états rangé/en chute/ouverture/voile ouverte/atterri/endommagé.
- Sortie d'aéronef contrôlée par le serveur, conservation de l'élan de l'appareil,
  restitution du même personnage et de son inventaire, siège libéré une seule fois.
- Chute libre, ouverture et freinage aérodynamique progressif, pilotage, vent,
  vitesse de descente et atterrissage. Aucun bouton de téléportation au sol.
- Vérifier l'équipement et l'espace pour l'ouverture. Une ouverture trop basse,
  une collision ou une voile endommagée ne garantit pas un atterrissage sûr ;
  conséquences et options serveur à configurer dans le gameplay.
- Réplication pour les autres joueurs, transition fiable de contrôle/caméra et
  traitement de déconnexion/mort sans duplication ni perte d'équipement.
- Ne pas confondre le parachute individuel du personnage avec un parachute de
  récupération de l'appareil complet, qui serait une fonctionnalité distincte.

## Critères d'acceptation avant annonce de livraison

Une vraie scène Unreal doit montrer aérogare/hangar/piste accessibles, bagage
ramassé et sauvegardé, vol de chaque ULM avec retour au sol, parcours amphibie de
l'aéroglisseur avec huit places testées en réseau, puis saut, ouverture, pilotage
et atterrissage du même personnage. Tester perte d'énergie, collision, sortie,
déconnexion et rechargement World Partition. Fournir compilation, captures
réelles et rapports distincts implémenté/compilé/testé/non terminé.

Aucune dépense, aucun asset sans licence compatible, aucun système existant
supprimé et aucune modification forcée de l'installation actuelle.
