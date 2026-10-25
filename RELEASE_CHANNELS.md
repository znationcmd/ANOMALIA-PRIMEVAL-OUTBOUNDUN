# ANOMALIA — branches de référence et mises à jour Windows

Ce document fixe la source officielle de chaque application et évite les modifications qui restent isolées sur des branches non publiées.

| Application installée | Branche de livraison | Version publiée au 25/10/2026 | Canal de mise à jour |
|---|---|---|---|
| ANOMALIA PRIMEVAL OUTBOUNDUN (jeu) | `main` | `0.7.2` | `anomalia-game-latest` |
| ANOMALIA Editor | `feature/anomalia-editor-actual-world-bridge-20261023` | `0.5.4` | `anomalia-editor-latest` |
| ANOMALIA Tools | `feature/anomalia-tools-premium-updates-20261023` | `0.2.6` | `anomalia-tools-latest` |

## Règles obligatoires

1. **Ne jamais considérer une Pull Request ou une compilation de test comme une mise à jour de l'application installée.** Une modification n'arrive sur les PC des utilisateurs qu'après fusion dans la branche source du canal approprié, création d'une version strictement supérieure, compilation, tests et publication d'un installateur accompagné du manifeste `latest.yml` et de son `sha512`.
2. Le jeu est publié automatiquement par `.github/workflows/anomalia-game-workshop-release.yml` lors des changements de code pertinents sur `main`. Le menu **WorkForge** est dans le jeu Windows à partir de 0.7.2 ; ses favoris locaux persistent, les mods provenant d'ANOMALIA Tools sont listés s'ils existent, mais cela ne signifie pas qu'un plugin UE5 est chargé dans le monde.
3. Editor et Tools sont publiés par `.github/workflows/anomalia-windows-auto-release.yml`. Le workflow récupère **les branches de référence ci-dessus**, pas automatiquement n'importe quelle branche de test. La publication est vérifiée à intervalle régulier et peut être déclenchée par une modification du workflow de livraison.
4. Pour une correction, créer une branche de travail courte **à partir de sa branche de livraison**, la tester, puis y fusionner la PR. Éviter les chaînes de branches feature/feature/feature ; ne pas ouvrir une deuxième branche pour poursuivre une correction déjà en cours.
5. Les mises à jour Windows sont téléchargées depuis les canaux existants. Le remplacement NSIS n'est effectif qu'au moment de l'installation automatique, généralement à la fermeture/redémarrage de l'application. Aucun utilisateur ne doit être invité à retélécharger manuellement tant que la mise à jour intégrée est disponible et saine.
6. Les profils, mondes, projets privés, mods et sauvegardes utilisateur doivent être préservés. **Aucune suppression de branche, réécriture d'historique, force-push, suppression de stockage utilisateur, dépense ou copie d'assets propriétaires** sans instruction expresse.
7. Pour le rapport de chaque correction indiquer séparément : **code modifié**, **tests réussis**, **fusion**, **version Windows publiée**, **manifestes disponibles**, **installation sur le PC de l'utilisateur non vérifiable à distance**.

## Diagnostic d'une modification absente sur Windows

Vérifier dans cet ordre : numéro de version visible dans l'application, `package.json` de la branche de livraison, statut des Actions du canal, version déclarée dans le `latest.yml` de la Release, événement de téléchargement et fermeture/relance du programme. Une version différente dans les captures peut signifier que la mise à jour a été publiée mais n'a pas encore été appliquée sur le PC.

Les branches historiques restent disponibles pour conserver les travaux en cours et les PR non fusionnées.
