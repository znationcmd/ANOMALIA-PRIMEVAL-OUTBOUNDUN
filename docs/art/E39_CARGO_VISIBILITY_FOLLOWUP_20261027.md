# E39 — contrôle du volume de coffre conservé

La validation Windows v7 40508316839 a réussi sur le code
`f3fb57424d46513c60f6de772d1cae1483c6e8b7`. Les rapports de l’artefact
`12743537263` ont été relus et la capture réelle `actual-panel-trunk-open.png`
a été inspectée. Les 61 contrôles physiques passent : six ouvrants, collisions,
verrouillage des panneaux, stabilité, conduite et freinage. Le châssis dérive au
maximum de 0,4382 cm pendant les cycles et atteint 0,08431 cm/s. Il ne s’agit pas
d’une validation multijoueur, du paquet installé ou de la carte principale.

La capture présente encore une grande surface intérieure peu lisible. Elle ne
permet pas à elle seule de décider de supprimer un maillage. L’îlot `frame` a
été isolé : il comporte un fond et des parois, pas seulement un écran opaque.
Les onze GLB v7 ont été reproduits à partir du même GLB Black Snow dont le SHA256
est `984a9daab49b5a31c45bbc284c657fa5898a010f2201c003358cb6b6f411751d`.

Le contrôle géométrique exige maintenant un fond orienté vers le haut, et non
une paroi verticale à la bonne hauteur. Six colonnes de l’intérieur du coffre
sont sondées jusqu’au fond ; chacune doit être libre sur au moins 20 cm. Les
mesures v7 confirment 26,59 à 27,54 cm entre le fond et le plan d’essai à 92 cm
du sol du modèle. Cela décrit ces six points, pas la capacité complète du coffre.
Les trois lignes de vue depuis l’arrière et les tests couvercle fermé restent
obligatoires. Le résultat étendu est enregistré séparément dans
`bmw-e39-cargo-clearance-audit-20261027.json`.

Aucun maillage, matériau, angle, collision ou réglage physique de l’E39 n’est
remplacé. Le format historique du reçu inclus dans le manifest v7 est préservé ;
la régénération de tous les ouvrants réussit sans réécrire les fichiers existants.
Les onze GLB restent sans erreurs ni avertissements au validateur glTF.

Six nouveaux tests vérifient notamment le refus d’une paroi verticale, d’une
sous-face tournée vers le bas, d’un couvercle mobile et d’un volume trop faible.
Les tests d’îlots, de découpe et de fermeture des peaux des panneaux sont conservés.

## Suite nécessaire

- Capture native rapprochée et oblique avec positions de caméra enregistrées,
  éclairage et matériaux du coffre lisibles ; ne pas conclure au photoréalisme
  à partir des seules lignes de vue CPU.
- Finition du compartiment moteur et de l’habitacle, positions des sièges,
  personnage conducteur et animations d’entrée/sortie.
- Vérification native des nouveaux systèmes de pièces, clés et échanges de
  cargaison ajoutés après le code v7 testé. Le succès v7 ne valide pas ces ajouts.
- Tests manuels, réseau, persistance et paquet installé.

Les corrections de compilation trouvées dans le composant de survie des
véhicules sont suivies séparément avec les validations natives de la PR #44.
La même E39 rouge, ses roues et ses six ouvrants sont conservés.

## Contrôles exécutés après ce rapport initial

Le run Windows 40549172851 a produit quatre nouvelles captures GPU : coffre fermé, vue arrière ouverte, vue oblique et vue du dessus. Les vues oblique et du dessus ont été inspectées : le fond et les parois du coffre sont visibles. L’intérieur reste peu détaillé visuellement, mais la surface observée ne justifie pas de supprimer la cuve du coffre.

Ces captures réutilisent les onze meshes v7 et vérifient leurs métadonnées SHA. Elles sont une prévisualisation statique dans un monde d’éditeur non sauvegardé, avec pivots d’origine ; elles ne sont pas un nouvel essai de conduite ou de réseau.

Le run natif 40546939481 de la PR #44 a également réussi le test VehicleKeyPartsCargoAndRecovery, parmi 26 tests natifs. Cette preuve porte sur les sources corrigées et le monde de test isolé ; elle ne remplace pas un essai GPU des nouveaux services sur le code e6b7967 ou une vérification dans le jeu installé.

Restent : finition des matériaux, compartiment moteur/habitacle, animations du conducteur, multijoueur, persistance en session et paquet installé. Aucun remplacement de la BMW existante n’est effectué.
