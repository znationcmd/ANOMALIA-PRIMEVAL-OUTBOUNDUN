# Portière conducteur réelle — validation native en cours

La carrosserie CC0 d'origine contient une coque continue et des lignes de joints,
pas des ouvrants. La révision v2 découpe réellement la portière côté volant
(+Y dans ce modèle), au lieu d'animer une poignée sur une coque encore fermée.
Les fichiers et assets v1 sont conservés dans leur propre espace de noms.

## Implémenté, pas encore validé dans Unreal

- Maillage de porte séparé avec la tôle d'origine, vitre, joint, poignée et
  rétroviseur ; pivot sur charnière, bord extrudé et peau intérieure de 4,5 cm.
- Ouverture réelle dans le maillage de carrosserie, chants de l'ouverture et
  conservation de l'aire initiale lors de la partition des triangles. La découpe
  interpolant normales/UV conserve les matériaux d'origine.
- Six dérivés dans NativeDemoSedan_v2, source CC0 contrôlée par SHA-256. Les
  modèles dérivés sont reproductibles par script, sans remplacer les originaux.
- Composant C++ plaçable/configurable dans les Blueprints : angle, vitesse,
  verrouillage, état d'ouverture, collision mobile et arrêt devant un obstacle.
  Collision non soudée au châssis ; les dimensions de collision du châssis sont
  calculées avec la porte fermée pour conserver le réglage physique validé.
- E en visant la vraie porte : requête existante du survivant, ciblage de la
  géométrie, portée/ligne de vue/santé/contrôleur vérifiés par le serveur. Pas de
  cible fournie par le client. État et angle répliqués ; réseau en jeu non testé.
- Import Unreal dans un espace v2 distinct, collision convexe de porte et
  assignation sur le vrai véhicule du terrain de validation.

## Vérifié localement

Quatre tests de découpe passent : conservation d'aire, interpolation des UV,
arêtes extérieures sans extrusion de la diagonale interne, exclusion du côté
opposé/roue/toit/porte arrière. Les six fichiers passent le validateur Khronos
glTF sans erreur ni avertissement. Les 154 tests Python passent également.
Ces résultats ne constituent pas une compilation Unreal ou un essai en jeu.

## Critères Unreal avant déclaration de livraison

Compiler Editor/Game ; vérifier en jeu la porte fermée bloquant un tracé, le
verrouillage refusant l'interaction, l'ouverture réelle de 70 degrés autour de la
charnière et sa collision quittant l'ouverture, puis la fermeture restaurant la
collision. Utiliser la même interaction serveur que E, sans assigner l'angle
dans le test. Conserver une capture réelle de la porte ouverte. La même berline
doit repasser les 26 contrôles de conduite, y compris freinage et sortie rapide.

Premier essai natif 40370309818, source f01ca18 : compilation Editor refusée,
erreur C2065 dans le nouveau composant. La macro DOREPLIFETIME attend le paramètre
OutLifetimeProps ; le paramètre avait un autre nom. Correction soumise ensuite.
Aucun test d'ouverture en jeu n'a été exécuté par cet essai échoué.

## Non terminé

Les trois autres portières, capot et coffre restent intégrés à la carrosserie.
Animations humaines d'entrée/sortie, sons, clés/inventaire, démontage/réparation,
dégâts/salissure et sauvegarde de porte restent à réaliser. Le système n'impose
pas encore une séquence d'entrée animée : la possession de conduite existante
est conservée. Seule la carte d'essai reçoit cet assemblage v2 à ce stade ; le
jeu installé et les sauvegardes ne sont pas remplacés.
