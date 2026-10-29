# P0 — Déplacement tactique d'ANOMALIA (UE5)

Cette modification agit sur le **vrai** `AAnomaliaZPrigimaliaSurvivor`. Elle réutilise `UAnomaliaZPrigimaliaVitalsComponent` pour l'endurance, `UAnomaliaZPrigimaliaInventoryComponent` pour le poids, `UAnomaliaZPrigimaliaItemEffectsComponent` pour les conséquences de blessures/douleurs et `UCharacterMovementComponent` pour la capsule, sans ajouter une seconde endurance.

## Intégré dans le code (validation native attendue)

- Sept allures progressives de 150 à 575 cm/s avant la vitesse de sprint existante. `Alt` maintenu + molette change l'allure par étapes; sans `Alt`, la molette reste disponible pour les autres interactions.
- Joystick gauche : déplacement analogique déjà existant. Bouton de sprint manette déjà existant. `C` / bouton droit manette : accroupissement moteur Unreal avec changement de capsule (hauteur cible 60 cm). Aucun effet « juste animation ».
- Masse réelle calculée depuis les piles du vrai inventaire, ralentissement déterministe, effet de fatigue déjà répliquée et de douleur déjà simulée. Accélération/freinage adaptés à la charge. Le sprint est refusé si accroupi ou si 45 kg et plus sont portés.
- Sprint et marche rapide consomment l'endurance existante du serveur, dont la récupération est ralentie par charge et fatigue. Le sprint maximal reste indépendant du cran de marche ; les allures 5 et 6 redescendent au cran normal en cas d'épuisement.
- `PaceStep` est borné côté serveur, répliqué aux clients, et appliqué par le composant de déplacement réel. Le calcul de vitesse reste déterministe côté client, mais la prédiction complète des transitions de postures et des variations de charge sous latence n'est **pas validée**.
- Test natif `Anomalia.Native.TacticalMovement.SpeedLoadFatigueAndCrouch` ajouté, avec vérifications numériques et vraie classe Survivor.

## Non réalisé / non validé

La compilation UE 5.8, les tests en jeu et multijoueur ne sont pas encore confirmés. Aucune animation humaine réaliste, nouveaux squelettes, Control Rig, IK, Motion Matching, posture intermédiaire, reptation, appui d'arme, franchissement, glissade, ragdoll, blessure par membre reliée au personnage, sons de pas ni certification console n'est annoncée comme terminée. Ces éléments exigent des assets et une validation native dans les scènes de test.

Le modèle E39 existant, les versions validées de ses ouvrants, les installations Windows et les sauvegardes restent inchangés. Les commandes disponibles ne remplacent pas la configuration future Enhanced Input complète.
