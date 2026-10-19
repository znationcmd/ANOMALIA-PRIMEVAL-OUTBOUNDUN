# Véhicules et circuits — ANOMALIA (prototype jouable)

Le catalogue `src/vehicles.js` contient les catégories terrestres, nautiques et aériennes. Elles apparaissent dans **ADMIN → Véhicules** : choisir un véhicule puis « Créer », s'en approcher et appuyer sur **E**. Commandes de conduite : ZQSD/WASD, **E** pour sortir, **F5** pour changer de vue, **Espace/Ctrl** pour l'altitude des avions/hélicoptères et la profondeur des sous-marins. Les modèles sont pour l'instant des maquettes procédurales, et non des véhicules photoréalistes homologués ou des simulateurs de vol.

## Circuits sur la carte 48 × 48 km

- Circuit Formule 1 Austral : **X 9000, Z 16000** (asphalte, tracé fermé)
- Monster Truck Arena : **X 15000, Z 17400** (piste tout-terrain avec bosses)
- Terrain de motocross : **X 8000, Z 11000** (tracé sinueux et bosses)
- Massif enneigé de Borée : **X -12400, Z -17100** (montagnes avec neige selon altitude)

Ces sites sont marqués sur la carte et les pistes 3D sont générées au fur et à mesure du chargement des secteurs. Ils n'ont pas encore de chronométrage de course, de championnat, d'IA concurrente ni de collisions de piste spécialisées.

## Réglage indépendant par serveur

Le fichier `vehicles.xml` (historique, racine `<navalVehicles>` conservée pour compatibilité) prend en charge **tous les identifiants de véhicules** de `src/vehicles.js`, pas seulement les navires. Exemple :

```xml
<vehicle type="monster_truck" enabled="1" nominal="3" respawn="3600">
  <pos x="15000" z="17570" yaw="0"/>
</vehicle>
```

- `enabled` : active ou désactive l'apparition automatique.
- `nominal` : nombre de véhicules (0 à 20 par entrée).
- `respawn` : délai de réapparition en secondes.
- `pos` : coordonnées et orientation de départ.

Chaque profil local dispose de sa copie de configuration ; le serveur distant doit disposer de sa propre configuration. La modification des fichiers locaux d'un joueur **n'accorde pas** le droit de modifier les paramètres du serveur multijoueur. Les modifications existantes sont préservées. Le système de réglages ne constitue pas encore un moteur de mods complet.

Le rendu final et la conduite doivent être vérifiés sur Windows après la compilation CI ; la présence du code ne garantit pas la qualité visuelle ni l'absence de bogues.
