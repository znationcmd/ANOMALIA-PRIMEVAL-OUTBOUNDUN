# UE5.8.3 native build evidence — 20 October 2026

Source commit: 30a04b010645e03c8330ba80e828458d96af39cf.
Run: https://github.com/znationcmd/ANOMALIA-PRIMEVAL-OUTBOUNDUN/actions/runs/39464868024
Artifact: ue5-native-build-evidence (12285067607).

The retained compiler logs and report.json show AnomaliaZPrigimaliaEditor and AnomaliaZPrigimalia both returning exit code 0 under installed Unreal Engine 5.8.3 on Win64. Status for that source revision: COMPILES.

The real Unreal automation report index.json records Anomalia.Native.ProfileIsolation as Success and Anomalia.Native.VehicleCatalog as Fail. The latter expected 27 definitions but the catalogue contains 28, including farm_tractor. This commit updates that expectation and explicitly checks that the tractor remains a ground vehicle. Existing uniqueness, speed, lookup and invalid-ID checks are retained.

This correction requires a fresh native run; the prior result does not validate the changed test. No playable map, rendered gameplay, furniture, vehicle physics, multiplayer or packaged Windows game is proven by this run. Automation used NullRHI.
