# ANOMALIA — JavaScript → Unreal Engine 5.8 — passage de relais

Branche : `feature/loot-tiers-radiation-config-20261021`. Tous les prototypes JavaScript sont conservés.

## Modules natifs ajoutés en parallèle

| Prototype JS | Port C++ UE5 | Statut réel |
|---|---|---|
| `src/tracking-system.js` | `AnomaliaTrackingSubsystem.{h,cpp}` | État/temps des indices ; génération de décals et déclenchement par dégâts/déplacements absents |
| `src/hygiene-system.js` | `AnomaliaHygieneComponent.{h,cpp}` | Jauges et actions ; composant non ajouté au personnage, UI/ressources/réplication absentes |
| `src/family-system.js` | `AnomaliaFamilySubsystem.{h,cpp}` | Registres, soins, âge, compétences ; aucun acteur enfant/IA/sauvegarde |
| `src/family-pregnancy.js` | `AnomaliaPregnancySubsystem.{h,cpp}` | Durée/consentement/naissance logique ; l'âge et les confirmations doivent être validés par le serveur |
| `src/cryo-storage.js` | `AnomaliaCryoSubsystem.{h,cpp}` | État/autorisation basique ; identité/admin client-provided non fiable, ne pas exposer au réseau sans refonte |
| `src/npc-recruitment.js` | `AnomaliaNpcRecruitmentSubsystem.{h,cpp}` | Chaîne non létale, station, 8 rôles, progression, déploiement en 2 phases ; pas d'acteurs 3D/persistance |
| `src/mod-manager.js` | `AnomaliaModResolver.{h,cpp}` | Validation, tri topologique, détection cycles, checksum, chemin JSON ; aucun téléchargement/installation |

## À connecter avant d'annoncer « fonctionnel »

1. **PNJ** : alimenter `RegisterWorldNpc` depuis le spawn serveur, vérifier frappe non létale/câble/collision/inventaire/distance réelles, relier `AdmitNpc` au retrait contrôlé de l'acteur, stocker les données par serveur. À la sortie : `BeginDeployment`, vérifier le point de spawn, créer le PNJ, `FinishDeployment(true)` seulement si le spawn a réellement réussi, sinon `FinishDeployment(false)`. Raccorder l'IA aux huit métiers et à la base.
2. **Mods** : `UAnomaliaModResolver::ResolveMods` est un *plan* de dépendances ; la présence de `bSigned=true` dans un manifeste n'est **pas une vérification cryptographique**. Vérifier signature/hash sur les octets du fichier, compatibilité moteur/plateforme, provenance, accord explicite, espace disque et politique d'exécution avant toute installation. Tester `Anomalia.Native.ModResolver` dans l'Editor.
3. **Cryo** : durcir les identités et les droits à partir du serveur, assurer atomiquement capture + retrait de l'acteur, re-spawn avec position validée, puis sauvegarde isolée par serveur.
4. **Famille/hygiène/traque** : connexion aux acteurs, affichage, consommation et validation de ressources, sauvegardes, évènements/animations, confidentialité/permissions et réplication.

## Tests et portée

- `tests/test_ue5_npc_recruitment_source.py` : tests statiques de couverture du code ; ils **ne compilent pas** UE5.
- `unreal/Source/AnomaliaPrimeval/Tests/AnomaliaModResolverTests.cpp` : scénarios Unreal d'ordre des dépendances, de cycles, de consentement et de chemins ; ils doivent être **compilés et exécutés dans l'Editor**.
- Aucun résultat de compilation, de test PIE, de paquet Windows ni de déploiement Xbox/PlayStation/mobile n'est revendiqué pour ces ports nouveaux.
- Ne pas remplacer le C++ déjà existant pour inventaire, économie, blessures, véhicules et autres systèmes sans comparaison fonctionnelle préalable.
