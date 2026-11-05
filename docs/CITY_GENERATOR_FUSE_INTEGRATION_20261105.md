# Fusible et courant des villes/villages — 5 novembre 2026

Demande: rétablir le courant d'une ville ou d'un village en installant un fusible dans son générateur local.

## Base existante retrouvée
ReactiveWorld/WorldStateSubsystem et WorldMechanism gèrent les générateurs à carburant, câbles explicites, consommateurs, surcharges, réplication de l'état et sauvegardes serveur par carte.
Les connexions sont explicites et limitées en distance: ne pas alimenter toutes les villes par proximité ou simple nom.

## Changement source sur la branche sécurisée
- Definition.RequiredFuseItem: identifiant de l'objet exigé, facultatif pour préserver les générateurs existants.
- State.InstalledFuseItem: identité du composant installé, sauvegardée avec le générateur et répliquée dans son état.
- Première interaction avec un générateur qui exige le fusible: installation d'un objet réel via la transaction d'inventaire existante, ou échec avec restauration de l'état si l'objet manque.
- Le générateur ne fournit aucun courant avec un fusible absent ou différent. Il ne consomme pas de carburant dans ce cas.
- Réseaux fixes des villes/villages: bRequiresFuel=false et RequiredFuseItem configuré; le bon fusible rétablit le courant sans carburant.
- Générateurs des bases des joueurs hors des localités: bRequiresFuel=true; ils utilisent du carburant et restent indépendants du réseau de la ville.
- Le réglage par défaut conserve le fonctionnement à carburant des définitions existantes; les réseaux fixes doivent être configurés explicitement.
- À l’installation du fusible d’un réseau fixe, l’alimentation est activée. L’interrupteur permet ensuite l’arrêt/remise en marche.
- Tests natifs étendus: fusible absent/incorrect/correct, coupure, pause de consommation, identité conservée après redémarrage. Ces ajouts ne sont pas encore annoncés comme compilés ou exécutés.

## Travail restant dans le véritable projet
Vérifier l'identifiant de fusible du catalogue; créer/configurer les définitions locales sans écraser les assets; placer de vrais modèles de générateurs et coffrets dans les villes/villages existants; raccorder lampadaires, bâtiments, portes motorisées, ascenseurs et stations selon le plan réel.
Les consommateurs à mouvement doivent s'arrêter de façon cohérente et permettre une évacuation, sans chute du joueur ni téléportation.
Les lignes de métro/téléphérique peuvent nécessiter une alimentation dédiée à définir après inventaire des gares.

Le retrait/récupération du fusible, l'usure et le sabotage ne sont pas implémentés par ce changement. Ne pas annoncer ces interactions comme disponibles.

## Validation obligatoire
Compiler le module; exécuter les tests natifs et une transaction d'inventaire réelle en PIE; vérifier l'indépendance de deux réseaux de villes, la coupure par panne sèche/arrêt, le streaming, les sauvegardes et deux joueurs.
Le projet principal sur D: utilise encore le module legacy AnomaliaPrimeval selon l'audit. Ce code AnomaliaZPrigimalia de la branche ne doit pas être présenté comme déployé ou jouable dans D: avant migration/compilation et vérification réelle.
