"""Generate reviewable PCG and starter mobility configurations, never live spawns.

No changes to any server's Saved/Servers files. A server operator must verify
real vehicle rigs, art assets, road surfaces, collision, starter locations and
approved enemy classes before applying these rules.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from chernaskaluxria_fauna_progression import review_manifest as fauna_review_manifest
from chernaskaluxria_gameplay_pcg import (
    BIOME_RULES, CELL_SIZE_M, WORLD_ID, WORLD_PACKAGE,
    starter_mobility_hubs, server_vehicle_template, plan_population_cell,
)

def export(output:Path):
    if output.exists():
        raise FileExistsError("No overwrite of existing review package")
    output.mkdir(parents=True)
    # No hidden changes to gameplay in the main project.
    mapping={
      "world-map-policy.json":{
        "schemaVersion":1,
        "mapId":WORLD_ID,"unrealPackage":WORLD_PACKAGE,
        "pcgPluginEnabled":True,"cellSizeMeters":CELL_SIZE_M,
        "staticPopulation":{"requiresLicensedMeshes":True,
             "mustUseWorldPartitionStreaming":True,
             "mustUseHISMForRepetitiveMeshes":True},
        "dangerZones":{"radiationWarningsBeforeDamage":True,
             "requiresServerAuthority":True,
             "unknownAIClassesAreRejected":True,
             "maxPerPlayerConcurrentAI":10,
             "neverSpawnBeyondActiveRadiusMeters":600},
        "regions":BIOME_RULES,
        "status":"VALIDATED_RULE_SOURCE_NOT_EXECUTING_ASSETS"
      },
      "starter-hubs.review.json":{
        "mapId":WORLD_ID,"hubs":starter_mobility_hubs(),
        "flyingMountsOnlyAfterNativeCreatureValidation":True,
        "realVehicleMeshesMustBeInstalled":True,
        "status":"REVIEW_CANDIDATES_NOT_DEPLOYED"
      },
      "vehicles.review.json":server_vehicle_template(),
      "fauna-encounters.review.json":fauna_review_manifest(),
      "preview-population.review.json":{
        "worldId":WORLD_ID,
        "sampleCells":[
          plan_population_cell(0,0,"asphalt",100,True),
          plan_population_cell(32000,8000,"sand",100,True),
          plan_population_cell(25000,-27000,"ash",100,True),
          plan_population_cell(-9000,-27000,"soil",None,False)],
        "status":"SOURCE_PREVIEW_NOT_PCG_GRAPH"
      }
    }
    for file,data in mapping.items():
        with (output/file).open("x",encoding="utf-8") as writer:
            json.dump(data,writer,indent=2,ensure_ascii=False)
            writer.write("\n")
    return {"mapId":WORLD_ID,"files":list(mapping),
            "changesAppliedToServer":False,"worldImported":False}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(export(args.output),indent=2))
