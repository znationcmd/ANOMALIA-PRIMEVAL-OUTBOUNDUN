# ANOMALIA Suite — installation Windows des trois logiciels

## Un seul EXE, trois logiciels

Le programme `Installer-ANOMALIA-Trois-Applications-AutoMAJ.exe` réunit :

| Programme | Version | Mise à jour après installation |
| --- | --- | --- |
| CMD Studio | 0.2.1 | Mécanisme installé, mais **source HTTPS privée + jeton requis** |
| ANOMALIA Editor | 0.5.1 | Oui, via Release `anomalia-editor-latest` |
| ANOMALIA Tools | 0.2.2 | Oui, via Release `anomalia-tools-latest` |

Il installe les trois applications successivement via les installateurs NSIS
existants et leurs options silencieuses `/S`, dans le **profil Windows courant**.
Aucun nettoyage des profils, projets, catalogues 3D ou sauvegardes n'est effectué.
Le programme refuse de poursuivre si une des installations retourne une erreur ;
les applications déjà traitées restent alors installées, et le bouton Reprendre
n'est pas disponible. Fermer les trois applications avant de lancer le setup.

**Important :** il s'agit d'une mise à niveau de transition, pas d'un service
Windows administrateur ni d'un gestionnaire de lancement permanent. Il ne
fusionne pas les trois logiciels en une application unique. Les raccourcis restent
distincts. Les fonctionnalités de synchronisation entre appareils nécessitent
encore leur infrastructure propre.

## Pourquoi CMD Studio ne se met pas encore à jour tout seul

Le code du Studio contient déjà `electron-updater`, mais l'accès aux
mises à jour est intentionnellement **privé**. La source doit fournir
`latest.yml`, l'installateur et les blockmaps derrière une adresse HTTPS
authentifiée, et CMD Studio exige une clé d'accès chiffrée avec le mécanisme
Windows. Aucun flux public (GitHub Releases public) ne doit être utilisé pour
CMD Studio sans permission expresse : le logiciel personnel n'est donc **pas
publié** en Release dans ce dépôt public. Ce setup ne crée pas cette source.
Le menu de mise à jour du Studio doit être configuré une fois.

Pour Editor et Tools, les URLs de mise à jour officielles sont déjà intégrées
dans les versions installées. L'application contrôle les versions au démarrage,
puis régulièrement, télécharge une version plus récente et l'installe à la
fermeture lorsque le téléchargement a réussi. GitHub Actions publie les
versions officielles après les tests. Les applications plus anciennes, comme
0.1.1, ne savaient pas forcément effectuer ces mises à jour.

## Production et contrôle

Workflow : `.github/workflows/anomalia-suite-installer.yml`

1. Utilise l'installateur CMD Studio 0.2.1 **compilé antérieurement**, conservé
   comme artefact GitHub Actions de la branche du Studio.
2. Récupère `latest.yml` pour ANOMALIA Editor et ANOMALIA Tools depuis
   leurs Releases officielles et vérifie la version exacte ainsi que le
   `SHA-512` du fichier EXE téléchargé avant de l'intégrer.
3. Assemble tous les fichiers en un seul EXE avec NSIS sous Windows et publie
   l'artefact `ANOMALIA-Installeur-Unique-3-Logiciels-AutoMAJ`.
4. Ce processus ne vérifie pas **à lui seul** les mises à niveau sur le vrai
   PC de l'utilisateur : tester sur une machine Windows avant toute promesse
   de compatibilité avec des chemins d'installation personnalisés.

Ne jamais utiliser cet outil pour désinstaller les trois logiciels ou effacer
les dossiers de projets. Le setup agrège des exécutables, mais ne possède pas
les droits d'accéder à l'ordinateur du propriétaire sans que celui-ci lance
explicitement l'installation.
