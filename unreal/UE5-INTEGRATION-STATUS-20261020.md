# ANOMALIA’Z PRIGIMALIA — fusion des sources UE5 (20/10/2026)

Cette branche intègre **sans supprimer le code existant** les deux lignes de
travail précédemment séparées :

- Survie native C++ (faim, soif, santé, fatigue, endurance, température),
  inventaire, couchage, stations agricoles et sauvegardes par serveur.
- Source de paysage 48 × 48 km et premier niveau **World Partition** :
  génération de heightmaps de test de 253 points, contrôles d'intégrité des
  144 tuiles et 264 joints, scripts UE Editor pour créer des cartes .umap
  non destructivement.

Le projet `AnomaliaPrimeval.uproject` active `PythonScriptPlugin` pour
l'exécution explicite des scripts dans Unreal Editor. Les contrôles AZERTY
(Z/Q) et QWERTY (W/A) sont définis dans DefaultInput.ini.

## Ce que cette fusion ne prouve pas

- Aucun binaire Unreal Engine compilé, aucune vraie carte .umap générée
  dans cette session, aucun Play-in-Editor confirmé.
- `ANOMALIA_TerrainDraft` reste un conteneur vide **jusqu'à import manuel**
  de la Landscape depuis les .r16.
- Maison, animaux, véhicules, créatures et UI finale n'ont pas encore leurs
  assets, interactions et tests natifs complets.
- Les serveurs officiels 5 PVE + 5 PVP + 5 RP sont des configurations,
  **pas des serveurs hébergés et en ligne**.

## Reprise sur un PC équipé d'Unreal 5.8

1. Ouvrir et compiler `unreal/AnomaliaPrimeval.uproject` avec UE5 C++.
2. Pour une petite carte de test, lancer `scripts/ue5/create-first-world.ps1`.
3. Pour préparer le grand terrain, lancer
   `scripts/ue5/bootstrap-draft-landscape.ps1`, puis importer les 144 tuiles
   dans l'éditeur Landscape de `ANOMALIA_TerrainDraft`.
4. Tester réellement les déplacements, sauvegardes, multijoueur,
   partitionnement et chargement, puis corriger les erreurs UE rapportées.
5. Conserver les branches d'origine et la version JS/Three.js.

Ne pas annoncer de migration « terminée à 100 % » avant ces étapes.
