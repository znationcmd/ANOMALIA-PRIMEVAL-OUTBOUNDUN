# Première version de test Windows installée — 22 octobre 2026

Source testée : `bba112c3657d29a3152383dbcf248072579d0b7c`.
Exécution : https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39793020313

L'installation autonome a réussi le 22 octobre 2026 à 16 h 58, heure de Paris.
Le workflow global poursuit séparément les contrôles des imports et du grand monde ; leur résultat ne doit pas être déduit de cette validation de la petite zone.

## Lancement sur le PC

Raccourci Bureau : **ANOMALIA - Jouer**.

Exécutable réellement installé et lancé pendant le test :

```text
C:\Users\utilisateur\AppData\Local\CMD\ANOMALIA-Windows\versions\bba112c3657d29a3152383dbcf248072579d0b7c-1a8d7627\AnomaliaZPrigimalia.exe
```

Données persistantes : `%LOCALAPPDATA%\CMD\ANOMALIA-Windows\userdata\Saved`.
Le rapport confirme `validationSaveIsolationVerified: true`, `existingUserFilesPreserved: 11` et `PACKAGED_WINDOWS_INSTALLED_AND_SMOKE_TESTED`.
Les essais utilisent une jonction vers des données de validation séparées, puis l'installation attache les données réelles après les contrôles. Les versions précédentes sont conservées.

## Vérifications réussies

- Compilation Editor et Game avec UE 5.8.3 et tests natifs.
- Scénario d'interaction et d'inventaire dans Play In Editor.
- Construction/cook Windows et lancement réel D3D11/SM5 de l'exécutable autonome.
- Bouton Jouer (delegate natif, pause/reprise), déplacement par entrées clavier, traversée de la porte d'une maison.
- Ramassage de loot dans l'inventaire natif ; ouverture et fermeture de l'inventaire.
- Entrée, accélération, direction, caméra intérieure et sortie des trois véhicules de la zone : voiture, SUV et camion.
- Sauvegarde explicite et restauration de l'inventaire et de la position lors d'un second processus du jeu.
- Nouveau lancement et même scénario de gameplay depuis la copie installée avant son activation.
- Capture GPU de la copie installée inspectée : Santé, Soif, Faim, Endurance, Fatigue et Température sont visibles.

Preuves conservées dans cette exécution GitHub : `packaged-playable-install-diagnostics` (artefact `12435586660`) et `ANOMALIA-Windows-Test` (`12436155172`, environ 550 Mo). Le paquet téléchargeable exclut les dossiers Saved temporaires. Ces identifiants désignent cette version précise.

## Limites réelles

Cette livraison est une première zone de test 3D, avec des bâtiments et véhicules originaux provisoires, un sol plat et des arbres primitifs. La capture montre un avertissement d'éclairage non reconstruit (45 objets). Le rendu réaliste final reste à développer.

La conduite terrestre repose encore sur une physique de prototype ; elle ne valide pas des suspensions Chaos réalistes. Aucun essai avec une manette physique n'a été effectué. Les contrôles automatisés du menu ne constituent pas une validation de toutes les interactions par clic à l'écran.

Le sang demandé n'est pas encore implémenté : l'endurance constitue un indicateur supplémentaire, pas son remplacement. L'utilisation/consommation et le déplacement/jet des objets depuis l'interface, les blessures/soins complets et la sauvegarde de la position des véhicules restent incomplets.

Les nouveaux modules C++ de suivi, hygiène, famille, grossesse, fractures et stockage des créatures compilent dans cette source, mais leur présence ne prouve pas leur raccordement au personnage, aux interfaces, à la persistance ou à la sécurité multijoueur. Les grands catalogues, dinosaures et outils ne sont pas déclarés terminés.

Aucune version Xbox, PS5, Android ou iPhone n'est validée. Le lancement après un véritable redémarrage Windows et une mise à jour automatique de bout en bout restent à vérifier.
