# Inventaire ANOMALIA — contrôles réels

## Version du 28 octobre : disposition de référence et usure

L'interface native suit maintenant la disposition demandée : panneaux gris/noirs translucides à gauche et à droite, personnage agrandi au centre, bandeaux fins de rangements et panneau Mains avec vraie vignette d'arme. Le grand en-tête bleu et la barre d'actions générale ont été retirés. Les actions sont contextuelles à la pile choisie ; espèces et solde bancaire restent au-dessus du personnage.

Huit vignettes sont réellement rendues à partir des modèles présents : cinq pièces Survival portées, pomme, haricots en conserve et fusil Quantum SM_Rifle_Olive. Capture orthographique, matériau UI avec inversion de l'opacité, fond transparent ; pas d'image de DayZ copiée et pas de correspondance approchée entre objets. Les autres objets conservent leur nom tant qu'un modèle exact n'a pas été validé. Le rendu n'est pas une reproduction à l'identique des assets, du personnage policier ou de la pose armée de DayZ.

Compilation Editor 5.8.3 réussie : [40712350609](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40712350609). Cible Game de cette refonte non reconstruite.

Essai PIE [40714225658](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40714225658), artefact 12827867107 : **34 contrôles passés, code de sortie 0, erreurs du rapport vides**. Quatre captures réelles : inventaire, banque, craft, état d'usure. La capture d'inventaire de 600400 octets a l'empreinte SHA-256 6f0ef4fc2eb5b2ebf0dfc92f787dc910418b7e021586af91cbfa47aad44fbad5.

Les tests ont exercé les actions UMG liées, les huit rendus GPU et leur masque alpha, le ramassage d'un objet enregistré, les quatre recettes, les rangements, la consommation, la reprise du cargo d'un vêtement manquant et la restauration de caméra. Les entrées physiques souris/clavier et le multijoueur ne sont pas testés.

L'usure des piles d'objets est calculée côté serveur, enregistrée et conservée lors du rangement. Les piles de conditions différentes ne fusionnent pas ; les nouvelles acquisitions ne réparent pas les objets déjà abîmés. Une modification d'usure exige un objet unique, une catégorie compatible et une valeur positive finie. Aucun RPC ne permet au client d'imposer une usure ou une réparation.

Les emplacements de vêtements réellement portés s'usent avec la distance au sol et les dégâts reçus ; l'objet compatible tenu en mains est aussi endommagé lors d'un impact. Les valeurs d'équilibrage sont provisoires : 0,2 % par 100 m et 10 % des dégâts reçus pour les emplacements portés, 5 % des dégâts reçus pour l'objet tenu. La marche mesurée sur 982,77 cm a fait passer la veste de 93 à 92,98617 %. Un fusil a conservé 86,5 % après usure/dégâts ; la veste à 0 % a gardé tout son cargo et son état a été rechargé. Aucun fichier d'objet n'est détruit.

L'état des vêtements est actuellement attaché à l'emplacement modulaire, pas à une instance de vêtement équipée depuis une pile d'inventaire. L'usure par tir/rechargement, les réparations et les variantes visuelles déchirées restent à intégrer. Un état à zéro ne supprime pas un rangement ni son contenu.

Régression native [40714519929](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40714519929) : **26 tests réussis, code 0**, dont migration d'inventaire, stockage, loot/persistance et pièces/clés/coffre E39.

Les itérations échouées restent conservées : connexion d'entrée de matériau corrigée (40708906419), fixture de rotation chevauchant le fusil (40709250764), plantage de fermeture 0xC0000005 après contrôles réussis (40710599089), appel Python non exposé du composant de déplacement (40713100275). La fermeture utilise maintenant le chemin natif de l'inventaire ; le dernier essai est sorti avec code 0, sans prétendre avoir identifié toutes les causes historiques de plantage.

Portée : C:\\ANOMALIA-Validation\\c40543166274\\unreal et profils de test distincts. Le lanceur Survival du bureau utilise cette copie. Aucun déploiement de DLL dans C:\\ANOMALIA\\unreal, aucun personnage principal remplacé, aucun asset Fab publié, aucune fusion. Les erreurs génériques d'automatisation au démarrage GPU et avertissements déjà signalés restent ouverts.
