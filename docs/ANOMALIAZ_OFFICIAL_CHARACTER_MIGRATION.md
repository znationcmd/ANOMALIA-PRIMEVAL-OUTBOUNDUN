# ANOMALIA'Z PRIGIMALIA — Migration officielle des survivants

État : le coordinateur central et ses tests de sécurité sont implémentés. La passerelle Unreal GameMode vers le service n'est PAS encore activée sur les serveurs de production.

## Comportement demandé

- Même survivant sur tous les serveurs **officiels ANOMALIA'Z 1PP**, et un autre survivant sur tous les serveurs **officiels ANOMALIA'Z 3PP**.
- Conservation de l'inventaire porté (y compris les objets en mains), de l'apparence et de l'état de santé réellement sérialisés. Jamais de bases, caches, tentes, barils, constructions ou véhicules de la carte.
- Si le serveur officiel change : apparition aléatoire à un point intérieur approuvé de la carte de destination, sans reprendre les coordonnées de déconnexion de la carte d'origine.
- Délai anti-server-hopping entre deux serveurs officiels : configurable par l'opérateur, 90 secondes dans les tests initiaux.
- Aucun transfert entre officiel et communautaire. Les personnages communautaires restent sur leur serveur respectif.
- À la déconnexion, le GameMode sauvegarde puis supprime l'acteur survivant répliqué du monde ; sa position et son inventaire doivent rester sauvegardés.

## Sécurité réelle

- Seuls des serveurs officiellement inscrits par l'opérateur, avec un secret long gardé exclusivement côté serveur, peuvent interagir avec le coordinateur.
- La perspective 1PP/3PP et l'identité du serveur ne sont jamais acceptées à partir du navigateur/client : le registre opérateur les détermine.
- Une session active exclusive interdit de charger simultanément le même personnage sur deux serveurs. Un identifiant de session périmé ne peut pas écraser un profil ultérieur.
- Les données centrales sont écrites atomiquement avant confirmation. Un redémarrage réutilise l'état durable et conserve les sessions non clôturées verrouillées plutôt que de dupliquer.
- Le contenu des inventaires est limité aux piles et compartiments d'un personnage Unreal ; pas d'objets de monde imbriqués, ni d'objets inconnus.
- L'activation nécessite une passerelle fiable Unreal Engine 5 côté serveur : admission authentifiée, sauvegarde et synchronisation de l'inventaire, heartbeat et libération confirmée du bail. Aucune RPC client de copie directe.
- La base de données ne doit avoir qu'un écrivain actif. Pour plusieurs régions/instances, utiliser une base transactionnelle partagée.

## Fichiers

- server/official-character-registry.mjs — politique de partage par perspective, cooldown, points d'apparition et fencing.
- server/official-character-service.mjs — service HTTP interne authentifié et stockage durable monoprocès.
- tests/official-character-transfer.test.mjs — règles et absence de duplication.
- tests/official-character-service.test.mjs — authentification, redémarrage et sécurité du stockage.
- .github/workflows/prigimalia-official-transfer-policy.yml — vérification automatisée.
- unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaSessionWidget.cpp — navigateur 1PP/3PP, entrée officielle bloquée tant que la liaison n'existe pas.

## Avant de rendre cela disponible

1. Configurer et déployer un seul coordinateur derrière TLS/mTLS, avec les vrais serveurs officiels, secrets d'opérateur et points de spawn approuvés.
2. Ajouter le transport sécurisé serveur-à-serveur à Unreal GameMode. Les appels d'admission et de sortie doivent être terminés avant de rendre le survivant jouable.
3. Empêcher les interactions et dégâts pendant une admission en attente, vérifier chaque item par le catalogue serveur et transférer toutes les données de survie compatibles.
4. Tester en véritable multijoueur UE5 : transfert A→B 1PP, distinction 3PP, reconnexion, crash source/destination, tentative double connexion, déconnexion en véhicule et sauvegarde du profil.
5. Retirer seulement ensuite le blocage du navigateur pour les membres vérifiés de la flotte. Pas de fausses affirmations de migration actuellement disponible.

Cette infrastructure est originale pour ANOMALIA'Z et n'utilise aucun logiciel serveur ni donnée propriétaire de DayZ.