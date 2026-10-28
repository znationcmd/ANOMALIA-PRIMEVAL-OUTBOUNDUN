# Inventaire ANOMALIA — fusion des deux références du 28 octobre

La nouvelle interface native UMG reprend la répartition proximité / personnage / équipement de la référence DayZ et le fond sombre, la grille et les états turquoise de la seconde référence. Aucun visuel, logo ou asset propriétaire des jeux de référence n'est copié.

## Comportement
- Proximité/entretien/cargaison à gauche, personnage réellement équipé au centre, stockage spatial à droite.
- Les rectangles suivent les dimensions, rotation et coordonnées réelles des piles. Sélection d'une pile pour afficher ses actions existantes dans le bandeau inférieur.
- Mains séparées ; onglets inventaire et banque. Aucun onglet de fabrication ou cosmétique sans système fonctionnel.
- Caméra locale temporaire devant le vrai pawn, tenue et animations existantes conservées ; restauration du point de vue précédent à la fermeture, sans rotation du personnage ni possession d'un duplicata.
- Fonctions serveur d'inventaire, identifiants, poids, comptes et profils conservés. Pas de changement de catalogue ni de protocole réseau.
- Vignettes pour l'instant typographiques avec nom/quantité et infobulle : ce ne sont pas encore des miniatures rendues des modèles 3D. Les parties de tenue affichées sont une lecture des meshes portés ; équipement de vêtements depuis inventaire non ajouté dans cette refonte.

## Fichiers
- unreal/Source/AnomaliaPrimeval/AnomaliaInventoryWidget.h/.cpp
- unreal/Content/Python/verify_anomalia_inventory_hybrid.py
- .github/workflows/ue5-inventory-hybrid-compile.yml
- .github/workflows/ue5-inventory-hybrid-runtime.yml

## Validation à cet instant
Premier essai de compilation 40665933684 : échec sur deux noms locaux masquant UWidget::Slot, corrigés. Reprise 40666544749 bloquée AVANT copie des sources par marge disque insuffisante pour deux cibles.

Compilation réelle Editor réussie : [40666836482](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40666836482), artefact 12805968352 ; unité widget recompilée, bibliothèque et DLL liées. Cible Game du nouvel inventaire différée. Budget de reprise fondé sur les sorties PDB/objet déjà présentes et une marge ; réserve disque de 6 Gio conservée. Sources précédentes sauvegardées et empreintes vérifiées avant écriture, uniquement dans C:\ANOMALIA-Validation\c40543166274.

Le stamp natif de cache reste 3d044d6de6108eb99dc15a597920828e6dab79f5 ; le reçu source-patch-receipt identifie les nouvelles sources. Ne pas confondre ce stamp avec la révision de la refonte.

L'essai PIE 40666964997 est en cours ; aucune recette visuelle ou d'action annoncée avant son rapport final. Essai automatisé par callbacks UMG, pas une manipulation physique de souris/clavier. Aucun résultat réseau, jeu packagé ou déploiement dans C:\ANOMALIA\unreal.

## À terminer
Miniatures 3D des objets, équipement vestimentaire depuis l'inventaire et synchronisation/persistance d'apparence, glisser-déposer souris vers une case arbitraire, recette manuelle clavier/manette et deux joueurs. Les actions existantes de déplacement vers les mains et d'échange véhicule restent dans leur chemin natif.
