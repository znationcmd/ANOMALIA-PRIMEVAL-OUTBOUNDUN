# Portière conducteur réelle — validation native en cours

La carrosserie CC0 d'origine contient une coque continue et des lignes de joints,
pas des ouvrants. La révision v3 découpe réellement la portière côté volant
(-Y après import Unreal), au lieu d'animer une poignée sur une coque encore fermée.
Les fichiers et assets v1/v2 sont conservés dans leurs propres espaces de noms.

## Implémenté, pas encore validé dans Unreal

- Maillage de porte séparé avec la tôle d'origine, vitre, joint, poignée et
  rétroviseur ; pivot sur charnière, bord extrudé et peau intérieure de 4,5 cm.
- Ouverture réelle dans le maillage de carrosserie, chants de l'ouverture et
  conservation de l'aire initiale lors de la partition des triangles. La découpe
  interpolant normales/UV conserve les matériaux d'origine.
- Six dérivés dans NativeDemoSedan_v3, source CC0 contrôlée par SHA-256. Les
  modèles dérivés sont reproductibles par script, sans remplacer les originaux.
- Composant C++ plaçable/configurable dans les Blueprints : angle, vitesse,
  verrouillage, état d'ouverture, collision mobile et arrêt devant un obstacle.
  Collision non soudée au châssis ; les dimensions de collision du châssis sont
  calculées avec la porte fermée pour conserver le réglage physique validé.
- E en visant la vraie porte : requête existante du survivant, ciblage de la
  géométrie, portée/ligne de vue/santé/contrôleur vérifiés par le serveur. Pas de
  cible fournie par le client. État et angle répliqués ; réseau en jeu non testé.
- O depuis le siège conducteur : ouvrir/fermer via la même architecture de
  commande serveur que le contact et les vitesses, réservé au conducteur courant.
- Import Unreal dans un espace v3 distinct, collision convexe de porte et
  assignation sur le vrai véhicule du terrain de validation.

## Vérifié localement

Cinq tests de géométrie passent : conversion d'axes, conservation d'aire, interpolation des UV,
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

L'essai 40370893849 (source 54688be) a ensuite compilé et passé 31 contrôles sur
la berline, mais la capture réelle a révélé une mauvaise conversion du côté de
la charnière. Cette passe n'est donc pas une acceptation visuelle de la porte.
La révision v3 corrige la position et le sens d'ouverture, conserve v2, compare
les origines importées dans Unreal, exige que carrosserie + porte fermée
recomposent les bornes du modèle d'origine, et corrige les côtés des roues pour
présenter leurs jantes vers l'extérieur. Les tests techniques précédents ne
valident pas ces nouvelles corrections : compilation et captures fraîches requises.

Les journaux montrent aussi des configurations suivies modifiées dans le checkout
du PC de validation avant récupération du code. La chaîne sauvegarde désormais
les fichiers suivis modifiés et leur patch hors du checkout avant l'étape de
changement de version ; chaque copie est vérifiée par empreinte. Une sauvegarde
existante n'est jamais remplacée. Cette protection n'altère pas le jeu installé.

## Non terminé

Les trois autres portières, capot et coffre restent intégrés à la carrosserie.
Animations humaines d'entrée/sortie, sons, clés/inventaire, démontage/réparation,
dégâts/salissure et sauvegarde de porte restent à réaliser. Le système n'impose
pas encore une séquence d'entrée animée : la possession de conduite existante
est conservée. Seule la carte d'essai reçoit cet assemblage v3 à ce stade ; le
jeu installé et les sauvegardes ne sont pas remplacés. Le contrôle de fermeture
depuis le siège est ajouté en v3 ; il n'inclut pas encore une animation du bras.
