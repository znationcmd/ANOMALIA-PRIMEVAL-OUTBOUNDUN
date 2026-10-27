# Portière conducteur réelle — validation native réussie

La carrosserie CC0 d'origine contient une coque continue et des lignes de joints,
pas des ouvrants. La révision v3 découpe réellement la portière côté volant
(-Y après import Unreal), au lieu d'animer une poignée sur une coque encore fermée.
Les fichiers et assets v1/v2 sont conservés dans leurs propres espaces de noms.

## Implémenté et vérifié sur le terrain de validation Unreal

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

## Vérifications Unreal effectuées

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

## Résultat confirmé de la révision v3

Exécution 40373839123 réussie, source
`ba6cf00dc9c4c1c7ccccdc9a6bbb4027489946ba`. Editor et Game compilés sur Windows
avec UE 5.8.3 ; 24 tests natifs passent (19 sans avertissement, cinq avec
avertissements, zéro échec). Le véhicule de référence passe 26 contrôles et la
berline v3 passe 33 contrôles dans le vrai jeu.

Les sept contrôles supplémentaires de la berline vérifient le vrai maillage de
porte, la recomposition des bornes d'origine en position fermée, la collision
fermée, le refus d'ouverture verrouillée, la rotation sur charnière et la sortie
de la collision hors de l'ouverture, la fermeture rétablissant la collision,
puis l'ouverture/fermeture commandée par le conducteur depuis son siège.

Les API serveur employées par E et O sont exercées par le test automatisé ;
aucune affectation directe de l'angle ne simule l'ouverture. La nouvelle capture
réelle d'Unreal a été inspectée : portière du côté conducteur, ouverture visible
vers l'habitacle et jante extérieure visible. L'import vérifie les origines des
deux maillages, en plus des dimensions et empreintes. Les anciens résultats v2
ne sont pas présentés comme preuve d'acceptation visuelle.

Freinage de cette berline : 50,55 km/h en 12,32 m / 1,73 s / 0,816g ;
80,00 km/h en 29,61 m / 2,64 s / 0,850g ; adhérence réduite, 80,05 km/h en
56,00 m / 5,07 s / 0,450g. Sortie en roulant mesurée à 2629,38 cm/s
(94,66 km/h), sans limite de vitesse de sortie imposée au gameplay.

Preuves du run : compilation/tests 12674341653 ; référence 12674651293 ;
import de six pièces 12673922596 ; conduite de la berline et capture réelle
`actual-driver-door-open.png` dans 12674816990. Les rapports portent
diagnosticOnly=false, packagedGameTested=false et installed=false.
La sauvegarde préalable des modifications suivies a aussi été exécutée avec
succès hors du checkout sur le PC de validation.

## Non terminé

Les trois autres portières, capot et coffre restent intégrés à la carrosserie.
Animations humaines d'entrée/sortie, sons, clés/inventaire, démontage/réparation,
dégâts/salissure et sauvegarde de porte restent à réaliser. Le système n'impose
pas encore une séquence d'entrée animée : la possession de conduite existante
est conservée. Seule la carte d'essai reçoit cet assemblage v3 à ce stade ; le
jeu installé et les sauvegardes ne sont pas remplacés. Le contrôle de fermeture
depuis le siège est ajouté en v3 ; il n'inclut pas encore une animation du bras.
Les commandes clavier/manette manuelles, le multijoueur à deux clients et
l'arrêt de porte contre un personnage en jeu restent à éprouver séparément.
Les vitres du modèle source sont déclarées opaques : transparence, matériaux
et finitions de l'habitacle restent à reprendre avant une acceptation graphique.
