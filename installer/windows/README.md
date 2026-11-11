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
