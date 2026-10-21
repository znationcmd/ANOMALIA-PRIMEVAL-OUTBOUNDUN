# PR #6 — intervention et état réel

Corrections effectuées : rejet des réglages temporels non finis, bornage avant conversion des champs numériques serveur, fichiers temporaires de sauvegarde distincts, rejet des chemins de mapping avec lecteur Windows, protocole, encodage ou caractères de contrôle. Les données et clés de configuration existantes sont conservées. Un test natif vérifie le rejet de NaN/infini sans écraser la configuration valide.

Validation locale : 72 tests JavaScript réussis et 11 contrôles de contrats Unreal réussis. Il s’agit des tests du prototype JavaScript pour le gameplay correspondant, pas d’une validation des dinosaures ou du loot dans Unreal. La compilation et le nouveau test natif sont lancés séparément sur l’hôte Unreal via la branche d’intégration.

| Domaine | Présent dans les fichiers | Implémenté dans Unreal | Interface Unreal | Testé fonctionnel dans Unreal |
| --- | --- | --- | --- | --- |
| Configurations et isolation des sauvegardes | Oui | Base existante, correction P0 ajoutée | Pas de panneau complet | Nouveau test P0 en attente |
| Loot, 232 entrées et cinq tiers | Oui | Raccordement natif ajouté : apparitions, ramassage, inventaire, journal de sauvegarde | Interaction et inventaire existants ; visuels provisoires | Compilation et trois tests natifs en attente |
| Radiation de 900 secondes | Oui | Non | Non | Non |
| 142 espèces, 104 variantes, 13 références Moro | Oui | Modèles/IA/apprivoisement non raccordés | Non | Non |
| 57 références de croquettes | Oui | Recettes complètes et crafting non raccordés | Non | Non |
| Administration et mode créatif | Configuration seulement | Système complet absent | Non | Non |
| Editor / Mods / Tools | Références et prototype JavaScript | Environnement complet absent | Non | Non |
| Serveurs dédiés et CMD Hosting | Références de configuration | Intégration complète non validée | Non | Non |

La branche reste en brouillon. Aucun jeu Windows autonome, serveur officiel déployé ou test multi-utilisateurs complet n’est annoncé. Les anciennes fonctionnalités, branches et sauvegardes sont conservées.


## Native loot connection — implementation added, engine verification pending

The branch now connects `loot_items_catalog.json` (232 entries) and `loot_tiers.json`
to `UAnomaliaLootSubsystem`, the existing native inventory, the existing Interact
input (including its current controller binding), and the inventory UMG screen.
The server chooses the nearest registered pickup; clients send neither an item ID,
quantity, position nor player identity. Collection checks distance, visibility,
health, sleep state, generation identity and inventory capacity. Unknown IDs fail.
Pickups replicate their item identity, count and label. Their small generic box is
explicitly provisional; firearms, medicine effects and individual production meshes
are not implemented by this connection.

Defaults are staged from `public/config` into packaged `Content/Anomalia/Data` by
`stage-runtime-data.py`. The staging manifest refuses to replace manually edited or
unowned data and never writes `Saved`. Server overrides are independently read from
`Saved/Servers/<server-id>/loot_items_catalog.json`, `loot_tiers.json` and
`loot_spawns.json`; a malformed override stops loot rather than falling back silently.
The default standalone scope is `solo-local`, with stable local-owner persistence;
explicit server IDs and existing files remain untouched.

The three beach supply points target the real `ANOMALIA_Archipelago_v2` map relative
to its unique PlayerStart, projected onto actual ground collision. Maps with multiple
starts require exactly one `AnomaliaLootAnchor` tag. Five further points target a
separate review map created by `unreal/Scripts/create_loot_review.py`.
Hospital, garage, bunker and other building classes resolve to configured tiers;
placements for every building across the 48 km world still need authoring. Tier
category groups map explicitly to catalogue categories. Rarity governs appearance
chance per restock attempt; quantity, lifetime, restock and nominal caps are applied
per map. Eligible items below their configured `min` receive priority over other
candidates; the number of authored compatible points and rarity still bound achievable
population. Quality rolls are not yet implemented.

World state is map- and server-scoped. A write-ahead journal records the consumed
point together with the complete resulting player profile before either is exposed
as committed. Recovery replays that exact snapshot idempotently. If disk writes fail,
the point and affected inventory stay locked; profile autosaves cannot overwrite the
pending result. A reconnect waiting on recovery reloads its saved profile before it
can be autosaved. Malformed existing state is retained and stops loot. This covers
process interruption; power-loss durability and concurrent independent server
processes sharing the same save directory are not verified/supported.

Legacy item storage rules are preserved. Catalogue IDs without physical metadata use
provisional 1 kg / 1x1 / stack-20 storage rules; the optional `weightKg`, `maxStack`,
`inventoryWidth` and `inventoryHeight` fields configure new IDs. No physical realism
is claimed for those defaults.

`Anomalia.Native.LootCatalog`, `LootTransactions` and `LootJournalRecovery` test
all 232 catalogue IDs entering and leaving inventory, range/capacity rejection, replay rejection, saving,
restart cooldown, isolated server scopes and interrupted-journal replay in actual
Unreal test worlds. The dedicated trusted-branch workflow requires all three tests
and both Editor/Game compilations. They are **not passed until its fresh report
confirms success**. Multiplayer clients, full-map loot distribution, dedicated server
builds and packaged Windows gameplay remain unverified. Other catalogue systems
(radiation, creatures, recipes, administration and Workshop) retain their previous
incomplete status and are not completed by this loot lot.


A separate `Anomalia.Loot.PIE` test and `run-loot-playtest.py` now create/open the
actual review map, inject E/I into the player controller, check collection and saved
inventory, and open/close the native UMG inventory. It requires a unique process-only
automation save scope; it refuses to interact if the GameMode uses any other scope.
This test is pending execution, and does not establish rendered appearance or multiplayer.
