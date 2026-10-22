# Ajouts vérifiés le 22 octobre 2026

Les commits 7395044/eb7ac76, 7b8c391 et 6778885 ajoutent quatre modules JavaScript. Ils sont préservés. Ils ne sont importés ni par l’application principale ni par les systèmes C++ Unreal : leur présence ne constitue pas une fonctionnalité en jeu.

| Ajout | Dans les fichiers | Raccordé Unreal / interface | Vérification actuelle |
|---|---|---|---|
| Traces de pas et de sang | src/tracking-system.js | Non : pas de génération par déplacement/blessure, décals ou réplication | Capacité bornée, rejet des valeurs non finies, identifiants uniques après saturation |
| Toilettes, urinoir, douche, baignoire, lavabo | src/hygiene-system.js | Non : pas d’indicateurs natifs, équipements interactifs ou consommation d’eau | Conservation des besoins en cas d’horloge invalide/rétrograde ; eau requise pour lavage |
| Famille, soins, croissance et suivi d’un parent | src/family-system.js | Non : pas de PNJ enfant, animation, IA, inventaire ou sauvegarde Unreal | Copies des parents et des instantanés isolées ; confirmations booléennes explicites |
| Grossesse et naissance non explicites et optionnelles | src/family-pregnancy.js | Non : pas de lien avec les familles ni de création réelle du PNJ enfant | Durée valide ; confirmation explicite ; pas de naissance anticipée par modification d’un instantané |

Corrections : le tampon de traces pouvait générer des identifiants répétés et boucler sans fin avec une capacité négative. Des références exposées permettaient de changer les parents autorisés ou la date de naissance en modifiant un objet retourné. Des chaînes de caractères étaient acceptées à la place de confirmations booléennes. Une horloge invalide pouvait vider artificiellement les indicateurs d’hygiène. Ces défauts ont des tests de régression dans tests/new-survival-modules.test.mjs.

Validation : 85 tests JavaScript réussis, dont quatre nouveaux scénarios couvrant ces modules. Les contrôles GitHub sont étendus à ces fichiers. Aucun test Unreal de ces quatre fonctionnalités n’est revendiqué.

Les actions familiales devront recevoir leurs identités, confirmations et états des personnages depuis le serveur. Les booléens de ce prototype ne constituent pas une authentification ni une vérification d’âge. La persistance complète, les ressources consommées, les modèles et les interactions restent à développer. Ces ajouts restent après la livraison Windows dans l’ordre de priorité.

## Première version Windows

La source ddc892e a produit un véritable paquet Windows et lancé l’exécutable en D3D11/SM5. Le scénario a validé HUD natif, trois maillages de véhicules cuits, déplacement clavier, passage dans une porte de maison, ramassage dans l’inventaire et ouverture/fermeture de son interface. Il a échoué lors de la montée dans un véhicule ; le paquet n’a donc pas été activé sur le Bureau.

La source 8e9de74 désactive la prise de contrôle automatique par l’IA des véhicules garés, ajoute le menu Jouer/Pause avec réglages graphiques et sauvegarde/quitter, le freinage du prototype terrestre, la caméra première/troisième personne, la sauvegarde de position limitée à la même carte et un second lancement de l’exécutable pour vérifier le rechargement. Ces changements doivent passer la compilation et les essais natifs : au dernier contrôle, le job Windows attendait un runner disponible.

Les indicateurs natifs actuels sont santé, faim, soif, endurance, fatigue et température. Le sang demandé n’est pas encore natif. Consommer/jeter depuis l’interface, soins/blessures, art réaliste, physique finale des véhicules et persistance de leurs positions restent incomplets. Les versions console/mobile et le cross-play ne sont pas disponibles.


## Point vérifié après reconnexion du PC — 22 octobre, 14 h 45 (Paris)

ANOMALIA-PC a repris le job 39776127606. Compilation Editor + Game et 9 tests natifs réussis ; scénario PIE réussi. Le paquet Windows a ensuite réussi le menu Jouer (appel du vrai bouton), les déplacements, l’entrée de maison, le ramassage, l’inventaire, la montée/conduite/direction/caméra intérieure/sortie de trois véhicules et un second processus vérifiant la restauration de l’inventaire et de la position.

Le job 39778199620 a aussi réussi le lancement de la copie installée. Son activation a été refusée par le contrôle de conservation des fichiers Saved : le test partageait les journaux et réglages avec les données du joueur. Le correctif conserve désormais les essais dans un Saved séparé puis raccorde les données du joueur après validation. Aucun raccourci Jouer n’est encore annoncé comme livré.

Les sources corrigent aussi le moment de construction des arbres UMG avant Slate, les polices et le défilement du menu. La prochaine capture du paquet inclut le HUD. Le contrôle visuel de ces derniers changements reste à faire ; les anciens tests de texte et de délégués ne suffisent pas à attester les pixels affichés.

L’exécution 39778199620 s’est arrêtée en échec à 14 h 41 pendant le contrôle GPU de la grande carte, sans journal final disponible via GitHub. La nouvelle validation 39780341789 attend un runner affecté. Aucune cause de déconnexion ou d’arrêt matériel n’est établie. Les contrôles lourds du monde ne seront plus lancés après un échec antérieur de livraison Windows.

Depuis le premier audit, des sous-systèmes C++ Tracking, Family et Pregnancy ont été ajoutés en parallèle et préservés. L’appel FVector::IsFinite incorrect du suivi a été remplacé par les contrôles ContainsNaN d’Unreal 5.8. Ces structures natives ne prouvent toujours pas la présence de décals, animations, PNJ enfants, permissions serveur et sauvegardes complètes des nouveaux systèmes. Leur compilation complète et leurs essais restent en attente du runner.
