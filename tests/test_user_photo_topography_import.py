"""Source contract for the exact user-supplied image-driven Unreal .r16 imports."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class UserCompositeTopoImportTests(unittest.TestCase):
    def test_exact_image_sources_and_import_metadata(self):
        data=json.loads((ROOT/"public/config/photo-derived-topographic-source-audit.json").read_text())
        w={v["name"]:v for v in data["worlds"]}
        assert len(w)==5
        assert w["VORGRAD"]["photo"]==3 and w["VORGRAD"]["vertices"]==3025
        assert w["NEXAVARKHOS"]["photo"]==4 and w["NEXAVARKHOS"]["vertices"]==1009
        assert w["SOLYNACALYRA"]["photo"]==2 and w["SOLYNACALYRA"]["vertices"]==1513
        assert w["DRAKHEIM"]["photo"]==1 and w["DRAKHEIM"]["vertices"]==2017
        assert w["CHERNASKALUXRIA"]["photo"]==[5,6,7,8,9]
        assert w["CHERNASKALUXRIA"]["realTileCount"]==400
        assert w["CHERNASKALUXRIA"]["sharedEdgesVerified"]==760
        for item in data["worlds"]:
            assert item["expectedBytes"]==2*item["vertices"]**2
        assert sum(1 for z in w["CHERNASKALUXRIA"]["photo"])==5
        assert not data["nativeUEImportVerified"]
        assert not data["productionLevelCreated"]
        assert w["CHERNASKALUXRIA"]["geographyTargetPassed"] is False

    def test_four_world_native_cpp_source_guard_opt_in(self):
        cpp=(ROOT/"unreal/Source/AnomaliaZPrigimalia/World/AnomaliaZPrigimaliaWorldImportLibrary.cpp").read_text()
        assert 'TEXT("ANOMALIAUseUserTopoR16")' in cpp
        assert 'TEXT("TerrainSource"),MapIdentifier,MapIdentifier+TEXT(".r16")' in cpp
        assert 'if(!FFileHelper::LoadFileToArray(SourceBytes,*Source)' in cpp
        assert 'return nullptr; // Do not substitute unrelated procedural terrain!' in cpp
        assert 'if(bUsePhotoR16)' in cpp
        assert 'int64(Size)*int64(Size)*int64(sizeof(uint16))' in cpp
        assert 'CreateChernaskaluxriaLandscapeTile(int32 Col,int32 Row)' in cpp

    def test_python_native_dry_spawn_reads_same_image_based_source(self):
        script=(ROOT/"unreal/Scripts/create_four_additional_maps.py").read_text()
        assert 'PRIGIMALIA_USE_IMAGE_TOPO_R16' in script
        assert 'def photo_height(e,n)' in script
        assert 'photo_height(e+dx,n+dy)' in script
        assert 'struct.unpack_from("<H",imageTopoData' in script
        assert 'if len(imageTopoData)!=spec["samples"]**2*2:' in script
        assert 'terrainSource="USER_PHOTO_R16"' in script

    def test_preserve_nine_independent_worlds_and_saves(self):
        rows=json.loads((ROOT/"public/config/anomalia-map-catalog.json").read_text())["maps"]
        assert len(rows)==9
        assert len({i["id"] for i in rows})==9
        assert len({i["saveNamespace"] for i in rows})==9
        assert all(i["originalUnrealPackage"].startswith("/Game/Maps/") for i in rows)
        assert not next(i for i in rows if i["id"]=="chernaskaluxria-v1")["serverSelectable"]

if __name__=="__main__":unittest.main()
