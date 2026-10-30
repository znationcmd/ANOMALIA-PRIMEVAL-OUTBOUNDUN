# ANOMALIA — vol, navigation et train : lot source du 20 octobre 2026

État de ce lot : **SOURCE ONLY**. La compilation native réussie du commit 30a04b0 ne couvre pas ces modifications. Les calculs indépendants du moteur sont compilés et exécutés avec g++17/UBSan ; les composants Unreal, collisions, caméras et commandes réseau exigent une nouvelle compilation et un test en jeu. Aucune image de modèle réaliste n'est présentée comme un véhicule intégré.

## Modifications exécutables dans le code

- Conservation des 28 définitions existantes ; ajout `airplane` (avion de transport léger) et `train` (locomotive). L'enum Rail est ajouté en fin pour conserver les valeurs antérieures.
- Le pawn existant sélectionne désormais un déplacement spécifique pour chaque catégorie. Les véhicules terrestres conservent leur mouvement antérieur ; ils ne deviennent pas des véhicules Chaos par cette modification.
- Avion : poussée vers l'avant, gravité, portance dépendante de la vitesse, perte de portance à faible vitesse, commandes de tangage/roulis/lacet avec autorité liée à la vitesse longitudinale, virage par inclinaison.
- Hélicoptères d'attaque et de transport : poussée, maintien d'altitude moteur allumé, collectif montée/descente, inclinaison, lacet, chute sans carburant. Modèle simplifié, sans simulation complète de rotor/autorotation.
- Jet-ski, zodiac, bateau, porte-avions et navire de guerre : propulsion uniquement dans une région navigable déclarée, ressort amorti de flottaison, inertie, freinage, direction liée au mouvement. Accélération/lacet réduits pour les grands navires.
- Sous-marin : propulsion, plongée/remontée et limites surface/fond de la région. Les fonds détaillés sont traités par collision de la carte, lorsque celle-ci existe.
- Train : accélération, marche arrière limitée, freinage, suivi d'une spline de voie, arrêt aux extrémités et sur collision, boucle de voie optionnelle. Pas de train volant quand aucune voie n'est affectée.
- Déplacement autoritaire sur le serveur, balayages de collision et sous-pas limités à 60 Hz. Les clients reçoivent le mouvement de l'acteur ; aucune prédiction/réconciliation avancée n'est revendiquée.
- Commandes client envoyées à 20 Hz, valeurs non finies rejetées, remise à zéro après une seconde sans entrée et en fin de possession. Hélicoptères/avions consomment aussi du carburant à l'arrêt moteur en marche.
- Caméras intérieure/extérieure natives commutables. Position intérieure réglable sur le composant ; aucun cockpit 3D n'est fourni par ce lot.

## Utiliser après compilation Unreal

1. Ajouter des acteurs natifs `AnomaliaZPrigimaliaNavigableWater` à la carte. Le centre Z + `SurfaceOffset` définit la surface ; l'étendue basse du volume définit le fond minimal. Le volume doit couvrir au moins 200 cm de profondeur. Il ne dessine pas d'eau : fournir le rendu de l'océan et les collisions réels séparément.
2. Pour le train, placer un acteur `AnomaliaZPrigimaliaRailTrack`, donner un `RouteId` unique et éditer la spline `Track`. Aucun rail 3D n'est généré. Les portions requises doivent être chargées ; le traitement de longues voies World Partition reste à développer.
3. Le fichier `Saved/Servers/<serverId>/vehicles.json` continue de définir les apparitions. Pour le train, préciser `routeId` et `trackDistanceCm` ; sa position doit se trouver à moins de 500 cm de la position correspondante sur la voie. Une voie absente ou ambiguë rejette cette apparition.
4. Paramètres facultatifs par entrée : `thrustAcceleration` 0–10000 cm/s² (0 = catégorie par défaut), `stallSpeedCm` 100–20000 cm/s, `waterlineOffsetCm` 0–1000 cm. Types invalides et nombres non finis rejetés. Les réglages précédents de carburant/vitesse restent valables. Le fichier d'exemples de ce lot n'active aucune apparition automatiquement.
5. Les modèles doivent être intégrés et associés par Blueprint (`Body`) avant d'obtenir des véhicules visibles. Les apparitions du GameMode utilisent encore la classe de base : un registre de classes/modèles est nécessaire pour déployer ces Blueprints depuis les fichiers serveur.

## Commandes lorsque le véhicule est possédé

| Action | Clavier | Manette PC |
| --- | --- | --- |
| Accélération / arrière | Z ou W / S | Stick gauche vertical |
| Direction / lacet | Q ou A / D | Stick gauche horizontal |
| Tangage avion/hélicoptère | Flèches haut / bas | Stick droit vertical |
| Roulis avion/hélicoptère | Flèches gauche / droite | Stick droit horizontal |
| Collectif hélicoptère / plongée sous-marin | Espace / Ctrl gauche | Gâchette droite / gauche |
| Freinage | Maj gauche | Gâchette supérieure gauche |
| Caméra intérieure/extérieure | V | Clic stick droit |
| Sortir | E | Bouton gauche de façade |
| Regard | Souris | Commandes manette de regard à compléter |

## Vérifications et limites

Les scénarios C++ hors moteur vérifient la chute sans carburant, l'absence de vol stationnaire pour un avion arrêté, la portance inversée, le collectif, la convergence de flottaison, l'absence de propulsion hors eau, la plongée, les entrées NaN/Inf, les vitesses bornées, le freinage sans inversion, les extrémités/boucles de voie et les pas invalides. `Anomalia.Native.TransportDynamics` ajoute des contrôles au prochain lancement Unreal, et le pilote de validation exige sa présence dans le rapport.

À valider/développer : modèles PBR et intérieurs réalistes, collisions dimensionnées par modèle (la sphère du prototype est conservée), roues/chenilles Chaos, flotteurs multi-points et vagues réelles, pont mobile de porte-avions et atterrissage, effets/sons, passagers physiques, wagons/attelage/aiguillages/déraillements, armement embarqué, dégâts/réparation, stockage des véhicules, persistance complète des voies/états de vol et essais multiclients. La sauvegarde actuelle des positions initiales n'est pas présentée comme une sauvegarde de toute la simulation.

Aucun fichier de sauvegarde existant ni branche n'a été supprimé. Les anciens formats DayZ/ARK restent des sources de migration, pas des modules exécutables UE.
