# Installateur Windows unique de la suite ANOMALIA

Cette commande produit **un seul fichier .exe** qui installe automatiquement, sur le PC Windows de l'utilisateur qui le lance, les trois logiciels EXISTANTS :

- CMD Studio 0.1.1 (version personnelle)
- ANOMALIA Editor 0.1.1
- ANOMALIA Tools 0.1.1

L'installeur principal contient les exécutables officiels issus des trois compilations GitHub Actions réussies. Chaque programme garde son dossier, ses projets et sa configuration indépendants. Aucun fichier des autres utilisateurs Windows n'est modifié. Les programmes ne sont pas copiés dans le dépôt ; seule leur récupération GitHub Actions à la compilation est configurée.

## Installation sur le PC

1. Dans les artefacts du workflow `ANOMALIA - Installateur unique Windows`, télécharger le ZIP nommé `Installateur-ANOMALIA-3-Applications`.
2. Décompresser le ZIP sur Windows.
3. Double-cliquer sur `Installer-ANOMALIA-3-applications.exe` puis choisir **Installer**. Les trois installateurs seront lancés l'un après l'autre, avec l'option silencieuse `/S`. L'utilisateur n'a pas à saisir de commandes PowerShell ni à télécharger les trois programmes séparément.
4. Les trois logiciels apparaîtront dans le menu Démarrer, et, selon les préférences Windows, sur le Bureau, avec leurs icônes respectives.

Aucune session de ChatGPT ne peut prendre la main sur l'ordinateur et exécuter ce fichier à distance. Le lancement initial doit être effectué volontairement sur le PC. Windows SmartScreen peut afficher un avertissement puisque les installateurs ne sont pas signés commercialement ; ne pas contourner les protections Windows automatiquement.

## Limites et confidentialité

- Le bundle est un **installateur**, pas une fonction de mise à jour automatique en arrière-plan. Les versions embarquées sont celles vérifiées dans le workflow.
- Les projets et sauvegardes existants ne sont pas supprimés par ce bundle. Ne pas confondre avec une garantie de restauration ; effectuer des sauvegardes avant une mise à jour.
- Le bundle n'inclut pas Unreal Engine ni Blender. Il ne modifie pas les dépôts de développement des trois applications.
- Le dépôt GitHub est actuellement **public**. L'artefact de compilation peut donc être accessible à d'autres utilisateurs connectés à GitHub ; cette solution ne garantit pas l'exclusivité de distribution de CMD Studio. Pour vraiment restreindre CMD Studio à une seule personne, il faut une distribution privée, à traiter séparément.

Pour refaire l'installateur, modifier les identifiants de workflow et les noms de fichiers dans `.github/workflows/anomalia-suite-installer.yml` et `installer/windows/suite.nsi` puis relancer le workflow sur la branche dédiée.


## Mise à niveau unique depuis les trois versions 0.1.1

Cet installateur a été mis à jour pour **recouvrir les installations existantes**
sans les désinstaller manuellement :

- CMD Studio : de 0.1.1 vers **0.2.1** (client de mise à jour privé intégré)
- ANOMALIA Editor : de 0.1.1 vers **0.3.0** (client de mise à jour public intégré)
- ANOMALIA Tools : de 0.1.1 vers **0.2.0** (client de mise à jour public intégré)

Il embarque les trois vrais installateurs NSIS construits séparément dans
GitHub Actions. Le programme exécute successivement chaque Setup via `/S`
et arrête la séquence en cas d'erreur. **Fermer les trois applications avant
de l'exécuter.** Il préserve les répertoires de données des logiciels : ce
n'est pas une garantie absolue de conservation, il faut exporter les projets
importants avant toute grosse mise à niveau.

**Différence importante :** 0.1.1 n'intègre aucun client de mise à jour, donc
on ne peut pas lui envoyer de mises à jour à distance depuis GitHub. Cette
première mise à niveau nécessite forcément l'exécution locale d'un programme,
soit volontairement par double-clic, soit par Work local sous le contrôle
et l'autorisation de l'utilisateur.

Pour les mises à jour **suivantes**, les clients embarqués vérifieront
automatiquement les versions. Mais les canaux de publication ne sont pas
encore tous actifs : GitHub Releases `anomalia-editor-latest` et
`anomalia-tools-latest` ont encore besoin d'une première publication ;
CMD Studio doit disposer de son serveur privé, de jetons et de clés de
publication. La seule présence du client sur le PC ne suffit pas.

**Confidentialité** : cet artefact combiné est construit dans un dépôt
GitHub public et inclut CMD Studio personnel. Il n'assure pas une
distribution privée de CMD Studio. Pour une distribution strictement privée,
la génération d'un bundle doit se faire dans un espace de publication privé.
Aucune application ne doit envoyer les fichiers utilisateurs à GitHub.
