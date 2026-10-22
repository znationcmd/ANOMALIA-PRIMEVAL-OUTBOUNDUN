# PR #6 — intervention et état réel

**Contrôle des indicateurs (22 octobre) :** les ajouts de santé/sang/soif/faim,
fatigue, température et états temporaires étaient dans le prototype JavaScript.
La restauration recharge maintenant fatigue, dette de sommeil et sang sans
réutiliser les horodatages d’un ancien processus. Les conditions explicitement
guéries cessent d’afficher leurs alertes. Les durées de sommeil (30 s), malaise
lié au sang bas (10 s, nouvelle vérification après 5 s éveillé) et KO (23 s) sont
testées dans la logique du prototype ; les coups ne sont pas encore reliés au KO.
75 tests JavaScript passent, dont trois nouveaux tests de ces comportements.

Un HUD UMG natif est ajouté pour les six valeurs réellement existantes dans Unreal :
santé, soif, faim, endurance, fatigue et température en °C. Il lit les valeurs
répliquées et retire les alertes de fatigue et de température lors du rétablissement.
Le repos au lit conserve ses contrôles serveur et se termine désormais après 30 s
de simulation avec récupération de fatigue et d’endurance. Les compilations Editor
et Game, les neuf tests natifs et l’essai PIE étendu réussissent dans le run
[39745990341](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39745990341)
sur la source `938940f83232a372e898e2da0698ce703fbf1260`. Le test vérifie les six
libellés natifs, la fatigue réelle, les degrés Celsius, l’alerte d’hypothermie puis
son effacement, et le sommeil déclenché par la touche R avec réveil reposé. Cet
essai utilise NullRHI : le rendu graphique final du HUD reste à examiner.
Aucun affichage de sang, fracture,
humidité, infection ou drogue n’est prétendu natif : leurs systèmes restent à relier.

Le run 39738850387 confirme **36 modèles de voitures importés**, chemins Windows
corrigés, sources préservées et présentation reliée au catalogue natif. Sa capture
GPU avait dépassé 900 s pendant la préparation des textures et shaders. Le run
39742361237 (source `6497cfb373743416a00547cd166c9b240fc1c88f`) réussit ensuite
l’import ET les 36 captures GPU, puis la réouverture graphique de l’archipel avec
sortie de processus 0. Le rapport confirme le déchargement du monde avant fermeture,
sans sauvegarde du monde temporaire. Trois vues représentatives ont été examinées
(BMW E34, archipel et plage) ; cela ne valide pas l’apparence de chaque modèle,
leurs proportions, leur placement, leur conduite ou le réalisme final du paysage.

Le workflow du lot réutilise maintenant l’installateur PC existant après réussite
des tests natifs/PIE, des voitures et d’une preuve GPU fraîche du même commit.
L’installateur conserve les versions précédentes et vérifie les sauvegardes.
Son nouveau passage reste à confirmer ; il installe un projet Editor, pas un jeu autonome.

**Validation du 22 octobre :** compilation Editor et Game réussie sur Unreal 5.8.3,
neuf tests natifs réussis, puis essai PIE solo du ramassage, de l’inventaire, de la
sauvegarde et des boutons de dépôt/retrait réussi. Preuve : étapes 3 et 4 du
[run 39738850387](https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39738850387),
source `e7cfd93ac671a7b973bf1c853eefb719305026f2`. L’import des voitures est traité
séparément. Ces résultats ne valident pas le multijoueur, les modèles définitifs,
la carte entière ou un exécutable Windows autonome.

Corrections effectuées : rejet des réglages temporels non finis, bornage avant conversion des champs numériques serveur, fichiers temporaires de sauvegarde distincts, rejet des chemins de mapping avec lecteur Windows, protocole, encodage ou caractères de contrôle. Les données et clés de configuration existantes sont conservées. Un test natif vérifie le rejet de NaN/infini sans écraser la configuration valide.

Validation locale : 72 tests JavaScript réussis et 11 contrôles de contrats Unreal réussis. Il s’agit des tests du prototype JavaScript pour le gameplay correspondant, pas d’une validation des dinosaures ou du loot dans Unreal. La compilation et le nouveau test natif sont lancés séparément sur l’hôte Unreal via la branche d’intégration.

| Domaine | Présent dans les fichiers | Implémenté dans Unreal | Interface Unreal | Testé fonctionnel dans Unreal |
| --- | --- | --- | --- | --- |
| Configurations et isolation des sauvegardes | Oui | Base existante, correction P0 ajoutée | Pas de panneau complet | Test natif P0 réussi |
| Loot, 232 entrées existantes + 28 objets RP et cinq tiers | Oui | Raccordement natif ajouté : apparitions, ramassage, inventaire, journal de sauvegarde | Interaction et inventaire existants ; visuels provisoires | Tests natifs et PIE solo réussis |
| Banque RP | Billets et configuration ajoutés | Dépôts, retraits, transferts, journal et séquences anti-rejeu ajoutés | Boutons dans l’inventaire près du terminal | Tests natifs et PIE solo réussis |
| Radiation de 900 secondes | Oui | Non | Non | Non |
| 142 espèces, 104 variantes, 13 références Moro | Oui | Modèles/IA/apprivoisement non raccordés | Non | Non |
| 57 références de croquettes | Oui | Recettes complètes et crafting non raccordés | Non | Non |
| Administration et mode créatif | Configuration seulement | Système complet absent | Non | Non |
| Editor / Mods / Tools | Références et prototype JavaScript | Environnement complet absent | Non | Non |
| Serveurs dédiés et CMD Hosting | Références de configuration | Intégration complète non validée | Non | Non |

La branche reste en brouillon. Aucun jeu Windows autonome, serveur officiel déployé ou test multi-utilisateurs complet n’est annoncé. Les anciennes fonctionnalités, branches et sauvegardes sont conservées.


## Native loot connection — native and solo PIE tests passed

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
and both Editor/Game compilations. All nine native tests and both compilations passed
in run 39738850387; the solo PIE interaction/UI test also passed after the button-name fix. Multiplayer clients, full-map loot distribution, dedicated server
builds and packaged Windows gameplay remain unverified. Other catalogue systems
(radiation, creatures, recipes, administration and Workshop) retain their previous
incomplete status and are not completed by this loot lot.


A separate `Anomalia.Loot.PIE` test and `run-loot-playtest.py` now create/open the
actual review map, inject E/I into the player controller, check collection and saved
inventory, and open/close the native UMG inventory. It requires a unique process-only
automation save scope; it refuses to interact if the GameMode uses any other scope.
This test passed in run 39738850387 and does not establish rendered appearance or multiplayer.


## RP banking connection — native and solo PIE tests passed

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
reports from run 39738850387 confirm the native transaction test and the solo PIE test passed.

The additional mission remains in scope: trading/NPC shops, containers/safes/registers,
production banks, configurable fictional substance effects and medical treatment,
seven infected animal types and their AI/animations/models, virtual DNA/gene labs,
dinosaur/crafting systems, special events and administration. These are not completed
by this banking lot. Substance recipes and genetic laboratories will use fictional
game materials/processes; no real illicit-drug manufacturing, consumption instructions
or biological engineering protocols are included. A global substance catalogue will
be extensible and cannot honestly be described as an exhaustive list of every drug.

Validation locale du lot RP : **81 contrôles de sources/staging et 11 contrôles de contrats réussis**. Ces résultats ne constituent pas une compilation Unreal ni une validation multijoueur.


## 22 octobre — reprise des blocages constatés

Le premier build natif du lot loot/banque a échoué à la compilation. Les fonctions
utilitaires de deux fichiers se heurtaient dans le build Unity d’Unreal ; elles ont
maintenant des noms distincts. Les clés JSON `UE::FSharedString` d’UE 5.8 sont
converties explicitement avant validation. Ces corrections sont publiées et la
compilation, les neuf tests natifs et l’essai PIE solo sont maintenant réussis. Le
premier essai PIE se bloquait sur l’identité des boutons reconstruits ; des noms
stables corrigent ce problème, vérifié par les clics réels de dépôt et retrait.

La branche d’intégration du 21 octobre est réconciliée dans cette branche sans
suppression : extension militaire, préparateur Python Windows, convertisseur de
textures, suivi complet des véhicules et carte métro v2 sont conservés.

Le run 39671151992 a effectivement importé et capturé les 7 + 3 références militaires
et les deux modèles de métro, et créé le circuit métro v2. Cela ne valide ni leur
réalisme final, ni leur conduite ni le multijoueur. Il a échoué sur la capture globale
(retour 0xC0000005 après capture) et sur l’import des 36 voitures : les chemins
Interchange dépassaient la limite Windows et les écritures de textures échouaient.

L’import utilise maintenant des copies GLB aux noms courts, avec conservation du
binaire de géométrie, des références par index et des crédits. Les originaux ne sont
pas modifiés. Les voitures sont réimportées vers `NamedVehicles2` et une carte de
revue v2 ; les imports partiels v1 sont préservés. Des tests locaux vérifient le GLB,
les droits d’écriture exclusifs, les crédits et le maintien des sources. Une étape
native réessaiera les 36 modèles si leur cache existe sur l’hôte. La validation des
nouveaux imports reste en attente ; le crash de fermeture de la capture globale reste
à corriger et aucun nouvel installateur autonome n’est annoncé.
