# ANOMALIA — cibles PC, consoles et mobiles

État du lot du 22 octobre 2026. Une cible graphique ou une commande manette ne constitue pas une version console/mobile jouable.

| Cible | Présent dans les sources | Validation disponible | Blocage restant |
|---|---|---|---|
| Windows | Jeu et Editor C++, clavier/souris/manette, sauvegardes, HUD et inventaire | Lot précédent d65a968 : compilation UE 5.8.3, 9 tests natifs, PIE, GPU et réouverture de la copie installée réussis | Ce nouveau lot doit repasser le workflow ; exécutable autonome à empaqueter/tester |
| Xbox Series X et S | Axes/boutons génériques Unreal, profils graphiques distincts | Aucun build Xbox ni essai matériel | Accès développeur constructeur, moteur source et SDK autorisés, matériel de test, intégration comptes/sauvegardes/suspension et certification |
| PlayStation 5 | Axes/boutons génériques Unreal, profil graphique cible | Aucun build PS5 ni essai matériel | Accès développeur constructeur, moteur source et SDK autorisés, matériel de test, fonctions plateforme et certification |
| Android ARM64 | Joysticks virtuels Unreal, 5 boutons tactiles, zones de sécurité, configuration de rendu mobile | Relais tactile testable dans le PIE Windows ; aucune preuve sur téléphone | Installer le SDK/NDK requis, compiler/cuire APK/AAB, tester GPU/mémoire/chauffe et optimisation de la carte |
| iPhone | Même interface tactile, zones de sécurité et configuration mobile iOS | Aucune compilation iOS ni essai sur iPhone | Hôte macOS/Xcode compatible, signature/provisioning Apple, compilation et tests sur appareil |

## Raccordement du lot

Le personnage utilise le stick gauche pour marcher, le droit pour regarder, le bouton inférieur pour sauter, le bouton de menu droit pour l’inventaire, le clic du stick gauche pour courir et la croix bas pour se reposer. Le bouton gauche interagit. Les commandes des véhicules existantes restent conservées ; leur ergonomie mobile reste à terminer.

Sur Android/iOS, le HUD affiche Interagir, Inventaire, Repos, Sauter et Courir. Les deux derniers utilisent des événements appui/relâchement. Ces boutons passent par les mêmes entrées locales et vérifications RPC serveur que le clavier. Le joystick virtuel Unreal fournit déplacement et regard. L’inventaire a un bouton Fermer/Retour, un focus initial de navigation et un retour par bouton droit de manette ou Échap ; sa fermeture rétablit déplacement et regard.

Le HUD et l’inventaire sont enveloppés dans USafeZone. Cela permet à Unreal de respecter les marges du périphérique ; il reste à mesurer les chevauchements et la lisibilité en portrait/paysage, avec encoches et différents écrans. Ce lot ne finalise pas tous les menus du jeu ni les plateformes de connexion.

Les presets Android_Mobile_Target et IOS_Mobile_Target visent 30 images/s et XboxSeriesS_Target 60 ; aucun débit n’est garanti. ApplyGraphicsPreset reste accessible en Blueprint et écrit seulement GameUserSettings.ini local. Les presets ne sont pas encore sélectionnés par un menu natif complet. Les réglages de rendu Android/IOS désactivent Nanite, GI/reflets dynamiques et ombres virtuelles uniquement pour ces plateformes. Les assets doivent encore fournir des LOD, matériaux et collisions adaptés au rendu mobile, et la grande carte doit être optimisée.

Le PIE étend le scénario existant : ramassage par le vrai bouton tactile, ouverture par la liaison manette, existence des racines SafeZone, fermeture par le bouton de l’inventaire et restauration des entrées. Ces injections logicielles ne valident ni un écran tactile réel ni une manette physique. Les tests Python contrôlent les bornes/configurations, sans remplacer Unreal.

## Conditions de livraison

Aucun SDK privé, inscription payante ou déploiement n’est engagé. Les accès constructeurs doivent être fournis légalement. La synchronisation des mods, les sauvegardes de plateforme, le réseau entre plateformes et les règles des boutiques nécessitent des lots séparés ; le cross-play n’est pas annoncé fonctionnel.

Références officielles : [consoles Unreal](https://dev.epicgames.com/documentation/unreal-engine/consoles-development-in-unreal-engine?lang=en-US), [packaging](https://dev.epicgames.com/documentation/unreal-engine/packaging-your-project), [Android](https://dev.epicgames.com/documentation/unreal-engine/android-development-requirements-for-unreal-engine?lang=en-US), [iOS](https://dev.epicgames.com/documentation/unreal-engine/setting-up-an-unreal-engine-project-for-ios), [Safe Zones](https://dev.epicgames.com/documentation/unreal-engine/umg-safe-zones-in-unreal-engine?lang=en-US).
