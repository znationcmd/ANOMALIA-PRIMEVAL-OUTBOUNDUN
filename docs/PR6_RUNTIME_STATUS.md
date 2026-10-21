# PR #6 — intervention et état réel

Corrections effectuées : rejet des réglages temporels non finis, bornage avant conversion des champs numériques serveur, fichiers temporaires de sauvegarde distincts, rejet des chemins de mapping avec lecteur Windows, protocole, encodage ou caractères de contrôle. Les données et clés de configuration existantes sont conservées. Un test natif vérifie le rejet de NaN/infini sans écraser la configuration valide.

Validation locale : 72 tests JavaScript réussis et 11 contrôles de contrats Unreal réussis. Il s’agit des tests du prototype JavaScript pour le gameplay correspondant, pas d’une validation des dinosaures ou du loot dans Unreal. La compilation et le nouveau test natif sont lancés séparément sur l’hôte Unreal via la branche d’intégration.

| Domaine | Présent dans les fichiers | Implémenté dans Unreal | Interface Unreal | Testé fonctionnel dans Unreal |
| --- | --- | --- | --- | --- |
| Configurations et isolation des sauvegardes | Oui | Base existante, correction P0 ajoutée | Pas de panneau complet | Nouveau test P0 en attente |
| Loot, 232 entrées existantes + 28 objets RP et cinq tiers | Oui | Raccordement natif ajouté : apparitions, ramassage, inventaire, journal de sauvegarde | Interaction et inventaire existants ; visuels provisoires | Compilation et trois tests natifs en attente |
| Banque RP | Billets et configuration ajoutés | Dépôts, retraits, transferts, journal et séquences anti-rejeu ajoutés | Boutons dans l’inventaire près du terminal | Compilation, tests natifs et PIE en attente |
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
every unique catalogue ID entering and leaving inventory, range/capacity rejection, replay rejection, saving,
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


## RP banking connection — implementation added, native execution pending

The original 232 catalogue entries remain unchanged. An additive `rp_items_catalog.json`
adds 28 original game objects: seven euro-denominated RP tokens (5/10/20/50/100/200/500),
a wallet and non-convertible sealed bundle, jewellery/watch, six gold bar masses,
gold ore/nugget, silver/platinum and seven gemstone entries. Banknote mass is a
provisional 1 g gameplay value; gold bar masses match their labels. No real currency
artwork, market pricing, proprietary assets or real-money service is introduced.
All 259 unique IDs use the native inventory and loot loader. The unchanged original
232 rows include one `car_battery` listed under two categories. The loader now merges
those categories into one physical item; conflicting duplicates still stop loading. Tier category adapters retain
the five original tiers and add the RP groups; a cash review spawn is authored.

`UAnomaliaEconomySubsystem` keeps integer-cent balances in the server's own
`Saved/Servers/<id>/World/rp-economy.json`, independently of the map. Accounts start
at zero. Depositing consumes one actual inventory banknote; withdrawing adds one
only if capacity and funds permit. Transfers move balances in one atomic ledger
write, require an existing other account, and reject zero/negative/overdrawn amounts.
A persisted monotonic sequence rejects replayed requests, including after restart.
Balances and account metadata replicate only to the owning player. The client never
supplies its own account identity or a note's monetary value. The owning inventory
RPC resolves authenticated identity on the server and limits requests to five per
second. Terminal registration, proximity, visibility, health, sleeping and persistence
locks are checked again on the server.

The real native UMG inventory has deposit buttons, seven withdrawal buttons, account
balance, recipient and decimal EUR amount entry. Transactions are enabled near a
server-created terminal. An original generic labelled terminal is placed in the
separate review map; production bank buildings and ATM models still need authoring.
The terminal is functional code with a provisional mesh, not a final bank environment.

Cash exchanges journal the resulting inventory snapshot and ledger before commitment.
Failed writes retain the transaction and lock the inventory until recovery. Loot and
bank recovery both block profile autosaves and player inventory mutations while a
profile is awaiting recovery. Invalid saved inventory now remains locked instead of
being overwritten by an empty live inventory. Known profile extensions remain intact.
Single-process server ownership of each save directory is required; cross-process
sharing and power-loss durability remain unverified.

Native `Anomalia.Native.RPBankTransactions` covers deposits, withdrawals, transfers,
replay/negative/unknown-recipient/overdraft/range/capacity rejection, restart and an
interrupted deposit replayed twice without duplication. The real PIE input/UI test
also picks up a note and clicks native deposit and withdrawal buttons. Fresh engine
reports are required before marking any of these tests successful.

The additional mission remains in scope: trading/NPC shops, containers/safes/registers,
production banks, configurable fictional substance effects and medical treatment,
seven infected animal types and their AI/animations/models, virtual DNA/gene labs,
dinosaur/crafting systems, special events and administration. These are not completed
by this banking lot. Substance recipes and genetic laboratories will use fictional
game materials/processes; no real illicit-drug manufacturing, consumption instructions
or biological engineering protocols are included. A global substance catalogue will
be extensible and cannot honestly be described as an exhaustive list of every drug.

Validation locale du lot RP : **81 contrôles de sources/staging et 11 contrôles de contrats réussis**. Ces résultats ne constituent pas une compilation Unreal ni une validation multijoueur.
