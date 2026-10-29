# Zone jouable : rendu v2 et mise à jour automatique vérifiés

Source installée : `e5e5a33195f2ed0f9685a98d907d5adf57826c21`.
Exécution : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39810974804

## Résultat réel

Le 22 octobre 2026, vers 18 h 10 (Paris), la copie autonome Windows a été construite, lancée, testée et installée automatiquement. Le raccourci Bureau **ANOMALIA - Jouer** a été relu et pointe vers la version active :

```text
C:\Users\utilisateur\AppData\Local\CMD\ANOMALIA-Windows\versions\e5e5a33195f2ed0f9685a98d907d5adf57826c21-259eaa9e\AnomaliaZPrigimalia.exe
```

Le rapport indique `PACKAGED_WINDOWS_INSTALLED_AND_SMOKE_TESTED`, `trigger: push`, `updatedExistingInstallation: true`, `activeVersionAndShortcutVerified: true`, `validationSaveIsolationVerified: true` et 11 fichiers utilisateur existants conservés sans modification. La version précédente était `54828093b2e03618121a18703ec572b3d23412e9`.

Les données réelles restent dans `%LOCALAPPDATA%\CMD\ANOMALIA-Windows\userdata\Saved`. Les versions précédentes et les données de validation sont conservées. Aucun arrêt d'une partie utilisateur n'est demandé : une partie déjà ouverte doit être fermée puis relancée pour utiliser le nouvel exécutable.

## Graphismes

Sept matériaux procéduraux originaux différencient prairie, asphalte, écorce, feuillage, pierre, pavement et peinture routière. La scène comporte désormais des marquages, des trottoirs, des arbustes, des pierres, des volumes de feuillage et du relief d'arrière-plan. Les décors ajoutés ne modifient pas les collisions des parcours testés.

Les deux lumières utilisent une mobilité dynamique ; l'éclairage d'ambiance est capturé en temps réel. La capture de la copie installée a été inspectée : les nouvelles surfaces et les nouvelles silhouettes sont visibles, le HUD reste lisible et l'avertissement « LIGHTING NEEDS TO BE REBUILT » a disparu.

Les maisons et véhicules existants sont conservés. Cette étape reste un rendu provisoire : les arbres et collines utilisent des volumes simples, le sol jouable reste plat, le relief périphérique est décoratif, et les détails photoréalistes ainsi que les mesures de performances restent à réaliser.

## Vérification avant activation

Le premier essai de mise à jour avait installé une version jouable contenant encore l'ancienne scène : le retour zéro du processus Editor n'était pas une preuve d'exécution réussie du script Python. Le journal détaillé a ensuite révélé une connexion de matériau incorrecte.

Le générateur utilise maintenant les noms d'entrées fournis par Unreal. Il écrit un reçu unique seulement après la sauvegarde de la scène et la vérification des lumières. Le pilote de packaging exige ce reçu et le bon commit avant de cuisiner les assets. Le test de l'exécutable vérifie à son tour le matériau de prairie, les deux lumières dynamiques et au moins 120 éléments du décor v2 dans la carte cuisinée.

Les deux tests Python de régression vérifient notamment qu'un ancien reçu ou un retour zéro sans nouveau reçu ne permet pas de construire un paquet. Ils sont intégrés aux contrôles GitHub de source. La compilation et les tests natifs, les interactions PIE, le gameplay autonome, le rechargement de sauvegarde et le même scénario dans la copie installée ont réussi pour cette source.

L'artefact `packaged-playable-install-diagnostics` (`12440077315`) contient le reçu de scène, les rapports du jeu et de l'installation et les captures. Le reçu indique `PLAYABLE_LOOK_V2_SAVED`, sept matériaux, 183 acteurs possédés et `dynamicLights: true`.

## Fonctionnement des mises à jour

Les modifications des sources surveillées sur la branche de travail déclenchent automatiquement compilation, essais et installation sur ANOMALIA-PC. Seul un paquet validé peut devenir actif. Le même raccourci est actualisé et sa cible est vérifiée après chaque activation. Les contrôles du grand monde et de la copie Editor continuent ensuite séparément de la livraison autonome.

Le PC doit rester allumé, connecté et le runner disponible. Le démarrage du runner à la connexion Windows est déjà configuré ; un véritable redémarrage Windows n'a pas été testé dans ce lot. Cette validation ne constitue pas un test des versions consoles ou mobiles.
