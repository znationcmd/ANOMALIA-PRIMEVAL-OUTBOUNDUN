# Inventaire ANOMALIA — fusion des références, 28 octobre 2026

## Version disponible dans le test
Le test Survival utilise une première interface native à trois zones : proximité/véhicule à gauche, personnage réellement équipé au centre, stockage à droite, mains en bas et actions sur la pile sélectionnée. Fond sombre, sélection turquoise, coordonnées et dimensions réelles des piles. Banque dans son propre onglet. Aucun visuel propriétaire des jeux de référence copié.

Le lanceur existant ANOMALIA_Test_Survival_20261028_40659474346.cmd ouvre la copie C:\ANOMALIA-Validation\c40543166274\unreal. I ouvre l'inventaire de la version compilée. Aucun déploiement du nouveau DLL dans C:\ANOMALIA\unreal ; aucun changement de personnage principal.

## Compilé et testé
Compilation Editor réellement réussie : [40668678314](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40668678314), après compilation réussie de la fabrique partagée et du recadrage 40667659731. Cible Game de cette refonte différée.

Essai PIE [40669554052](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40669554052), artefact 12808190603 : processus terminé avec code 0, état HYBRID_INVENTORY_RENDER_AND_BOUND_ACTIONS_PASSED_NOT_MANUAL_NETWORK_ACCEPTANCE, erreurs du rapport vides. **11 contrôles réussis**, plus restauration de la caméra à la fermeture :
- Profil natif isolé, pawn équipé réel, grille UMG réelle.
- Onglets inventaire/banque sans remplacement des données.
- Sélection, séparation/fusion sans perte de quantité, passage en mains, rangement via cible personnelle et action de pile, rotation d'un objet 1×2.
- Consommation native : quatre pommes deviennent trois, avec effet de survie ; poids final 2,9000001 kg.

Deux captures UI réelles conservées : Inventory_hybrid00000.png et Inventory_bank00000.png. L'inspection d'une reprise identique a montré la disposition, le personnage entier et la banque séparée. La grille était trop petite dans le viewport éditeur : adaptation DPI préparée ci-dessous. Les captures incluent l'éditeur et le message de lumière non reconstruite de la carte de test.

Entrées de contrôle par callbacks UMG effectivement liés, sans souris/clavier physiques. Pas de recette réseau, jeu packagé ou transfert bancaire réalisé. Les erreurs génériques LogAutomationTest au démarrage GPU et avertissements d'API déjà constatés restent ouverts ; rapport de fonctions réussi ne signifie pas journal global sans erreurs.

Les premières itérations de contrôle ont échoué sur une API Python indisponible, la lecture de propriétés protégées puis des noms UObject instables. Les scripts et reçus d'échec restent conservés. La sélection du test se fait finalement par l'infobulle de la pile, sans supposer que le suffixe UObject est son identifiant.

## Préparé, pas encore actif : grandes cases et Tab
- Cases et libellés adaptés à la taille et au DPI du viewport.
- Ajout de +ActionMappings=(ActionName="Inventory",Key=Tab), en conservant I et la manette.
- Tab simple ferme l'écran avant la navigation Slate ; Shift+Tab garde la navigation inverse. Indication TAB / ÉCHAP dans le bouton de fermeture.

Ces changements sont versionnés, mais **pas encore installés dans le binaire du test**. [40677534343](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40677534343) a compilé l'unité DPI puis échoué au lien : DLL tenue ouverte par deux processus UnrealEditor.exe, erreur LNK1104. Artefact 12811217796.

La reprise Tab [40678240912](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/40678240912) est bloquée AVANT écriture des sources/INI : seulement 2 220 519 424 octets de RAM disponibles pour un seuil opérationnel de 4 Gio. Artefact 12810809677. Disque libre mesuré 9 847 853 056 octets ; aucune suppression effectuée. Fermer le test et l'éditeur ANOMALIA permet de libérer DLL et mémoire avant la reprise. Le workflow contrôle aussi les sessions Unreal actives et les laisse ouvertes.

Les sauvegardes avant modification et les empreintes sont exigées dans la copie de validation. Les sources natives et la configuration de cette copie peuvent être en avance sur le binaire tant que la reprise n'est pas passée. Le stamp de cache 3d044d6de6108eb99dc15a597920828e6dab79f5 ne remplace pas les reçus de patch.

## Limites fonctionnelles
Les cases portent encore nom/quantité et infobulle, **pas de miniatures rendues des objets 3D**. La tenue est lue depuis les meshes réellement portés ; les emplacements vestimentaires ne sont pas des boutons d'équipement fonctionnels. Restent les miniatures, rangements propres aux vêtements, équipement depuis l'inventaire, persistance/réplication d'apparence, glisser-déposer souris vers une case arbitraire et recette manuelle/manette/deux joueurs. Aucune fusion GitHub.

## Fichiers
- unreal/Source/AnomaliaPrimeval/AnomaliaInventoryWidget.h/.cpp
- unreal/Source/AnomaliaPrimeval/AnomaliaSurvivor.cpp : ouverture partagée sans changer les données de survie.
- unreal/Config/DefaultInput.ini : ajout Tab, autres raccourcis conservés.
- unreal/Content/Python/verify_anomalia_inventory_hybrid.py
- .github/workflows/ue5-inventory-hybrid-compile.yml et ue5-inventory-hybrid-runtime.yml
- tests/test_ue5_inventory_source.py : suivi du raccourci I vers la fabrique partagée et sa restriction au joueur local.
