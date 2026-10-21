# PR #6 — intervention et état réel

Corrections effectuées : rejet des réglages temporels non finis, bornage avant conversion des champs numériques serveur, fichiers temporaires de sauvegarde distincts, rejet des chemins de mapping avec lecteur Windows, protocole, encodage ou caractères de contrôle. Les données et clés de configuration existantes sont conservées. Un test natif vérifie le rejet de NaN/infini sans écraser la configuration valide.

Validation locale : 72 tests JavaScript réussis et 11 contrôles de contrats Unreal réussis. Il s’agit des tests du prototype JavaScript pour le gameplay correspondant, pas d’une validation des dinosaures ou du loot dans Unreal. La compilation et le nouveau test natif sont lancés séparément sur l’hôte Unreal via la branche d’intégration.

| Domaine | Présent dans les fichiers | Implémenté dans Unreal | Interface Unreal | Testé fonctionnel dans Unreal |
| --- | --- | --- | --- | --- |
| Configurations et isolation des sauvegardes | Oui | Base existante, correction P0 ajoutée | Pas de panneau complet | Nouveau test P0 en attente |
| Loot, 232 entrées et cinq tiers | Oui | Nouveau catalogue non raccordé | Non | Non |
| Radiation de 900 secondes | Oui | Non | Non | Non |
| 142 espèces, 104 variantes, 13 références Moro | Oui | Modèles/IA/apprivoisement non raccordés | Non | Non |
| 57 références de croquettes | Oui | Recettes complètes et crafting non raccordés | Non | Non |
| Administration et mode créatif | Configuration seulement | Système complet absent | Non | Non |
| Editor / Mods / Tools | Références et prototype JavaScript | Environnement complet absent | Non | Non |
| Serveurs dédiés et CMD Hosting | Références de configuration | Intégration complète non validée | Non | Non |

La branche reste en brouillon. Aucun jeu Windows autonome, serveur officiel déployé ou test multi-utilisateurs complet n’est annoncé. Les anciennes fonctionnalités, branches et sauvegardes sont conservées.
