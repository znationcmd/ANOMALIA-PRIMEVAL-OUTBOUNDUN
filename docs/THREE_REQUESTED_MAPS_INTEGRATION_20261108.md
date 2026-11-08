# Trois nouvelles cartes — intégration du 8 novembre 2026

- YUDINAVIA : 12,5 × 12,5 km ; relief original inspiré de la Scandinavie.
- MOSCOVIE : 10 × 10 km ; terrain urbain et lit de rivière, bâtiments à intégrer.
- CORSIVIA : 15 × 15 km ; île montagneuse dont les quatre bordures sont sous le niveau marin.

Le catalogue comporte 18 identités. Les 15 entrées antérieures sont préservées.
Les nouvelles références Unreal sont vérifiées par DoesPackageExist ; elles ne constituent pas une validation de gameplay.
Le lanceur Editor accepte les trois identifiants en paramètre MapId et refuse une carte absente.
La commande Editor/Tools maps --catalog <catalogue> --project-root <projet> montre les dimensions et l'existence des packages.

La procédure Windows vise D:/ANOMALIA/unreal, sauvegarde les sources avant une fusion étroite et compile le module réellement installé.
Elle refuse un en-tête local personnalisé plutôt que le remplacer. Chaque destination de niveau doit être absente, y compris ses dossiers World Partition.
Les reliefs sont des ébauches procédurales originales, pas des relevés géographiques de Moscou ou de Corse. Eau rendue, végétation, villes, routes, métro, navigation et gameplay restent à intégrer puis tester. Aucun pourcentage de jouabilité n'est attribué.

Validation locale : six tests du catalogue du bot ; compilation C++ portable et contrôle des dimensions, hauteurs encodables et côtes de CORSIVIA ; syntaxe Python ; essai de fusion sur une copie synthétique du module ancien avec sauvegardes et refus des modifications locales inattendues.
La compilation Windows, l'enregistrement des niveaux et les tests Editor/PIE nécessitent les reçus du workflow mission-three-requested-maps.yml. Une exécution en attente ne vaut pas installation réussie.

Le test antérieur de SKARVIK 42473256181 a échoué au contrôle de routage de la carte principale installée, avant ouverture d'Unreal ; il ne valide ni n'invalide le rendu SM5 des nouvelles cartes.
