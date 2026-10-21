# ANOMALIA — Loot tiers et radiation (configuration initiale)

Ces fichiers complètent les configurations existantes sans les remplacer : `public/config/loot_tiers.json` et `public/config/radiation_zones.json`.

**État : CONFIGURATION UNIQUEMENT, NON ACTIVE DANS UNREAL.** Les paramètres ne sont pas encore reliés au runtime UE5. Les positions sont des exemples à valider sur la carte, pas des points de spawn actifs. Aucune modification de sauvegardes.

## À intégrer avant de déclarer fonctionnel

1. Lire et valider les deux JSON côté serveur dédié, avec priorité aux surcharges par serveur, journaliser les erreurs et garder une configuration de secours.
2. Associer chaque bâtiment réellement accessible à son type et son tier, placer des points de fouille dans les intérieurs, relier les catégories aux objets existants de `types.xml`, gérer quantités, rareté, réapparition et persistance.
3. Ajouter `DynamicRadiation` au système existant `events.xml` / `cfgeventspawns.xml` sans supprimer les crashs existants, synchroniser début/fin et position, appliquer les dégâts sur le serveur, protections et filtres.
4. Mettre à jour le catalogue central `src/config-catalog.js` après validation des consommateurs existants et ajouter tests unitaires + multijoueur.
5. Tester le parcours complet : apparition sans équipement, fouille, eau, nourriture, soins, redémarrage serveur, puis événement radioactif de 900 secondes.

Le niveau de loot 5 ne doit pas empêcher les nouveaux joueurs de trouver les ressources vitales en tier 1. Les valeurs restent des paramètres de départ à équilibrer.
