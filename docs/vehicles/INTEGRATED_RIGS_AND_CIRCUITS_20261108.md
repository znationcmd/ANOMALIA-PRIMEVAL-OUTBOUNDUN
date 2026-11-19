# Véhicules complets animés et circuits — travail du 8 novembre 2026

Le lot préserve les 229 demandes regroupées du registre véhicules. Aucun nouveau véhicule n'est déclaré conduisible.

Le mode natif intégré permet de conserver une carrosserie et des roues déjà incluses dans un vrai SkeletalMesh.
Il exige un Animation Blueprint compatible, un asset physique non vide, quatre os de roues uniques, quatre classes de roues et quatre rayons valides. Les pièces statiques supplémentaires sont refusées pour éviter les doubles carrosseries/roues.
Les véhicules modulaires existants gardent leur mode et leurs réglages par défaut.
Le mode intégré conserve les classes de roues et l'asset physique de la source ; aucun asset physique partagé n'est réécrit.

Candidat concret : /Game/Ako_Mini_Map_sys/Example_Content_Demo/blueprint_proj/pawn_proj/vehicle/BP_vehicle_pawn et son Sk_AUDI_CAR.
Le squelette et l'asset physique ont été constatés dans l'ancien reçu 42379630246. Cela ne valide ni son adaptation ANOMALIA, ni sa conduite.
Le profil adapté reste à créer après compilation native, puis à tester sur SKARVIK : entrée/sortie, possession, démarrage, accélération, freinage, braquage, suspension, collisions et sauvegarde.

Circuits : reprendre uniquement les sources déjà présentes dans le manifeste d'import, avec les termes Shanghai, circuit, racetrack, karting, drift et motocross.
L'import ciblé réutilise les reçus SHA256 et conserve les sources échouées ; il ne les réimporte pas aveuglément.
Les plans de circuits du prototype web ne constituent pas des circuits installés dans Unreal et leurs coordonnées ne sont pas reprises.
Le placement dans SKARVIK attend la vérification des transformations de scène, de l'échelle, des licences, des matériaux et de la continuité des collisions. Le terrain de motocross ne sera pas inventé si sa source n'est pas retrouvée.

Validation disponible : sept assertions portables de séparation des modes visuels. Compilation UE5 du changement, Blueprint adapté et conduite PIE restent à exécuter. Les rapports ne donnent aucun pourcentage de jouabilité.
