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
