# ANOMALIA — archipel original, lot terrain

Demande : grande île découpée, montagnes marquées au nord, îles séparées, plages et désert au sud-est. Aucun fichier des cartes Deer Isle, Namalsk, Lux ou Nasdas n'est copié.

- Dimensions : 48 × 48 km, 2304 km² au total.
- Mesure du relief analytique à pas de 25 m : 890,634 km² strictement au-dessus de la mer.
- Sommet échantillonné : 1757,97 m ; fonds environ -445 m.
- Huit masses terrestres de plus de 1 km² à la résolution 3025 ; île principale environ 752,6 km².
- Résolution de base 3025 × 3025, pas 15,873 m. Ce n'est pas le niveau de détail final.
- 576 composants Landscape, sections 63 quads, 2 × 2 sections par composant.
- Import C++ réel via ALandscape::Import et découpage LandscapeSubsystem::ChangeGridSize en cellules de 2 composants, sur un nouveau monde World Partition.
- Matériau de repérage des biomes : plages, végétation, désert, roche et neige. Pas encore de textures PBR, végétation, routes, villes, ponts ou océan physique.
- Point de départ choisi sur une altitude côtière positive.

## Exécution et protection des données

Le workflow natif compile puis exécute `unreal/Scripts/create_archipelago_world.py` dans UnrealEditor-Cmd. Nouvelle carte : `/Game/Maps/ANOMALIA_Archipelago_v2`.
Une carte existante à cet emplacement est préservée, jamais régénérée automatiquement. Les anciennes heightmaps, cartes et sauvegardes ne sont pas modifiées.
Les packages de la carte, ses acteurs externes et le matériau sont conservés ensemble dans l'artefact `ue5-archipelago-world`.
Le rapport du run doit établir la création réelle, 576 composants et 576 composants de collision avant acceptation.

## État au commit de développement

Le noyau de génération a été compilé et exécuté avec g++ ; les contraintes de superficie, altitude, océan périphérique et précision 16 bits passent. Ce test n'est pas une compilation UE5. La création de la carte sous UE5 reste à confirmer par le prochain run natif. Aucun test visuel, de déplacement, de multijoueur ou de performances n'est déclaré réussi.
