# ANOMALIA UE5 — lot survie : endurance et température (20 octobre 2026)

Ce lot ajoute des **sources C++ UE5 à compiler**, PAS une fonctionnalité validée dans l'éditeur.

## Fonctionnalités du prototype

- `UAnomaliaZPrigimaliaVitalsComponent` est attaché à `AAnomaliaZPrigimaliaSurvivor`.
- **Maj gauche** demande le sprint. Le serveur valide la demande et la réserve d'endurance, applique les vitesses, et réplique le résultat aux clients.
- Endurance de 0 à 100 : dépense initiale de 12 points/s quand le personnage court et se déplace ; récupération de 8 points/s à l'arrêt ou en marche. Une jauge épuisée doit récupérer à 25 pour reprendre le sprint.
- Température corporelle initiale à 37 °C, influencée progressivement par une **température ambiante constante** configurable entre -50 et 60 °C.
- Hors de la zone corporelle 35–40 °C, un premier modèle de dégâts applique 0,15 point de vie/s côté serveur.
- Endurance et température corporelle sont ajoutées aux données `survival` du **profil propre au joueur et au serveur** ; les anciens profils sans ces champs restent compatibles.
- Les nouveaux paramètres sont chargés et sauvegardés par `UAnomaliaZPrigimaliaConfigLibrary` et figurent dans le catalogue des réglages.

### Exemple de configuration

Le champ `survival.ambientTemperatureC` est ajouté dans `unreal/Config/AnomaliaZPrigimalia/config.json`.
Chaque serveur peut le remplacer dans `Saved/Servers/<server-id>/config.json` sans toucher aux autres serveurs.
La lecture accepte les valeurs numériques finies et les borne dans [-50, 60] ; l'enregistrement rejette les valeurs hors de cette plage.

## Limites : ne pas confondre code source et fonction terminée

- Pas encore de météo, de pluie, d'humidité, de variations de température par région, de vêtements thermiques, de maladies, de soin ou de HUD natif final.
- Pas encore de corps à récupérer après décès, réapparition complète ou respawn multijoueur validé.
- Pas de preuve de compilation UE5, ni d'essai de déplacement sur carte, ni de mesure de fluidité/réplication réseau.
- Les tests `tests/test_ue5_vitals_source.py` contrôlent des invariants **statiques** et non le fonctionnement du moteur.

## Vérifications nécessaires dans UE 5.8 sur Windows

1. Compiler `AnomaliaZPrigimaliaEditor` et relever les diagnostics C++ et Unreal Header Tool.
2. Lancer deux joueurs Play In Editor en mode client/serveur.
3. Vérifier le sprint, la baisse/récupération de stamina, l'épuisement et l'arrêt à 0 PV.
4. Définir des températures ambiantes différentes sur deux serveurs distincts, vérifier l'isolation.
5. Sauvegarder puis reconnecter un joueur avec une identité réseau configurée ; vérifier stamina, température, santé, faim et inventaire. Tester aussi le chargement d'un ancien profil sans les nouveaux champs.
6. Vérifier que les RPC non propriétaires ne peuvent pas forcer une valeur de stamina, et que les valeurs sauvegardées invalide sont rejetées.

La version JS/Three.js/Electron d'ANOMALIA n'est ni modifiée ni supprimée.
