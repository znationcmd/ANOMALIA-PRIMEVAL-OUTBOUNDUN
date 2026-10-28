# Inventaire ANOMALIA — 28 octobre 2026

## Présentation native
Trois zones : **À proximité** à gauche, **personnage réel vêtu** au centre, **rangements des vêtements** à droite ; mains sous le personnage. Fonds sombres, contours cyan, cases adaptées au DPI. Les phrases d'aide et rappels de manette ont été retirés. Les boutons de proximité affichent seulement nom et quantité ; leur action prend l'objet.

Les espèces physiques et le solde bancaire apparaissent au-dessus du personnage. L'onglet FABRICATION comporte quatre recettes natives ; TRANSFERTS conserve les opérations bancaires existantes.

## Compilation réellement exécutée
- Tab + DPI : [40678901767](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40678901767), réussite.
- Rangements, argent et craft : 40681165103, réussite.
- Proximité et reprise des rangements : [40691913211](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40691913211), Editor 5.8.3, code 0, artefact 12818155396.
- Présentation épurée : [40692598129](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40692598129), réussite.

Ces compilations mettent à jour la cible Editor dans **C:\\ANOMALIA-Validation\\c40543166274\\unreal**, utilisée par le lanceur Survival du bureau. La cible Game n'a pas été reconstruite pour cette refonte. Le projet installé C:\\ANOMALIA\\unreal n'est pas modifié. I et Tab sont configurés ; clavier physique non testé.

## Fonctionnement des rangements
Les meshes effectivement portés accordent leur rangement : veste 200 cases, pantalon 200, petit sac 350, gants 2, chaussures 4 ; gilet 300 si présent, coiffure 2 si présente. Poches existantes conservées. Les petites capacités des gants/coiffure/chaussures sont provisoires. Les 14 kg de capacité de masse restent distincts du nombre de cases.

Les destinations de rangement sont des actions serveur. Une pièce contenant des objets ne peut pas être retirée par SetClothingMesh. Si un mesh disparaît autrement, son rangement occupé reste accessible en retrait seul ; les objets ne sont pas supprimés. La relecture accepte cet état uniquement pour les sept identifiants réservés de vêtements, sans relâcher les règles des autres compartiments.

## Proximité
La liste affiche jusqu'à 64 ramassables accessibles à moins de 250 cm, actualisée toutes les 0,5 seconde lorsque son contenu change. Le serveur vérifie le joueur propriétaire, l'identité enregistrée du ramassable, sa génération, sa portée, la visibilité, la capacité et le transfert durable par le système de loot existant. Le client ne fournit ni quantité ni identité d'objet arbitraire. Les coffres et fonctions de service du véhicule restent disponibles.

## Craft et argent
Recettes : tissu ×2 → pansement ; chiffons ×6 → corde ; bois ×2 + chiffons ×4 → attelle ; fibres ×6 + tissu ×4 → selle, coût du prototype existant. Serveur : recette fermée, ressources vérifiées, poids/espace vérifiés, sauvegarde atomique avant publication, matériaux conservés en cas d'échec. Aucun comportement de montage d'une selle annoncé.

Les espèces sont calculées depuis les piles de billets physiques existantes ; aucun second registre d'argent créé. Le solde bancaire provient du compte existant.

## Validation et limites
Le premier essai 40669554052 avait passé 11 contrôles de callbacks UMG et restauration de caméra (code 0), avant les nouvelles fonctions.
Essai réel [40692693342](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40692693342), artefact 12817243545 : **25 contrôles réussis, processus code 0, erreurs du rapport vides, caméra restaurée**. Trois captures UI inspectables : inventaire, transferts et fabrication. Actions UMG liées réellement exécutées : rangement veste/sac, retrait d'une veste vide et refus si occupée, sauvegarde/relecture du cargo de sac manquant en retrait seul, espèces 50 EUR issues d'un billet physique, quatre recettes avec consommation des matériaux, refus de recette inconnue et de ramassable nul. Une volaille crue enregistrée dans un nouveau scope privé a été listée et ramassée par le bouton de proximité, avec augmentation exacte du stock. Les configurations de loot de ce test n'affectent que inventory-hybrid-40692693342. Aucun clavier physique, réseau ou transfert bancaire effectué. Inspection de la capture : vêtements Survival visibles sur le corps, argent au-dessus, proximité gauche ; libellés de petites cases encore tronqués et avertissement moteur de lumière superposé. La finition visuelle complète n'est pas acceptée.

Le personnage central porte réellement les meshes Survival (veste, pantalon, chaussures, gants, sac). **Les cases d'objets et en-têtes de vêtements ne disposent pas encore de miniatures rendues des modèles 3D.** L'équipement vestimentaire depuis une pile d'inventaire, la persistance/réplication des choix d'apparence, le masquage du corps, le glisser-déposer souris et le multijoueur ne sont pas acceptés. Les captures UI incluent l'éditeur et l'avertissement de lumière non reconstruite de la carte de test.

Les erreurs génériques LogAutomationTest au démarrage GPU et avertissements d'API déjà relevés restent ouverts. Aucun asset Fab Standard publié, aucun profil utilisateur réinitialisé, aucun changement de pawn principal, aucune fusion GitHub.
