#!/usr/bin/env python3
"""Cloud-only source validation for ANOMALIA'Z PRIGIMALIA 35s intro.

No network, no Epic credentials, no game asset mutations.
This is NOT an Unreal Engine compile or runtime media acceptance test.
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys
from datetime import datetime, timezone


MOVIE = "ANOMALIAZ_PRIGIMALIA_GENERIQUE_35s_ALERTE_ROUGE.mp4"
EXPECTED_MOVIE_SHA256 = "29e4f8c5f00a08877e49fa856707755e0cd257eead26d4c411a38e1960403ccf"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    root = pathlib.Path(args.root).resolve()
    cpp_file = root / "unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaIntroWidget.cpp"
    header_file = root / "unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaIntroWidget.h"
    game_mode_file = root / "unreal/Source/AnomaliaZPrigimalia/AnomaliaZPrigimaliaGameMode.cpp"
    project_file = root / "unreal/AnomaliaZPrigimalia.uproject"
    required = [cpp_file, header_file, game_mode_file, project_file]
    checks = {}
    hashes = {}
    missing = [str(p.relative_to(root)) for p in required if not p.is_file()]
    checks["all_sources_checked_out"] = not missing
    if not missing:
        cpp = cpp_file.read_text(encoding="utf-8-sig")
        hdr = header_file.read_text(encoding="utf-8-sig")
        gm = game_mode_file.read_text(encoding="utf-8-sig")
        project = json.loads(project_file.read_text(encoding="utf-8-sig"))
        module_names = {m.get("Name") for m in project.get("Modules", [])}
        checks["real_anomalia_game_module"] = "AnomaliaZPrigimalia" in module_names
        checks["uses_single_35s_mp4"] = (
            MOVIE in cpp
            and "UnifiedMoviePath()" in cpp
            and "ClickBloodMoviePath" not in cpp
            and "SW_IntroTitle_Original_v5" not in cpp
        )
        checks["actual_pause_at_click"] = (
            "PauseAtClick()" in cpp
            and "GetTime().GetTotalSeconds() >= 23.95" in cpp
            and "void PauseAtClick();" in hdr
            and "VideoPlayer->Pause()" in cpp
        )
        checks["resumes_same_media_when_clicked"] = (
            "OnContinueClicked()" in cpp
            and "VideoPlayer->Play()" in cpp
            and "bAwaitingClick = false" in cpp
        )
        checks["has_skip_button_and_no_lost_player"] = (
            "OnSkipClicked()" in cpp
            and "VideoPlayer->Seek(" in cpp
            and "PRIGIMALIA_UNIFIED_35S_END_CALLBACK_TIMEOUT" in cpp
        )
        checks["returns_to_real_game_menu"] = (
            "FinishToMainMenu()" in cpp
            and "UAnomaliaZPrigimaliaSessionWidget::Open(PC, true)" in cpp
            and "UAnomaliaZPrigimaliaIntroWidget::Open(PC)" in gm
            and "UAnomaliaZPrigimaliaSessionWidget::Open(PC,true)" in gm
        )
        checks["legacy_c2181_pattern_absent"] = not re.search(
            r"else\s+bBloodFinished\s*=\s*false\s*;", cpp
        )
        for p in required:
            hashes[str(p.relative_to(root))] = sha256(p)
    result = {
        "project": "ANOMALIA'Z PRIGIMALIA",
        "run_type": "cloud_source_check_without_engine",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "intro_file": MOVIE,
        "movie_sha256_expected_for_future_cloud_asset_sync": EXPECTED_MOVIE_SHA256,
        "movie_bytes_verified_in_this_job": False,
        "engine_compile_performed": False,
        "in_game_visual_test_performed": False,
        "missing_files": missing,
        "checks": checks,
        "source_sha256": hashes,
        "passed": all(checks.values()),
    }
    path = pathlib.Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for name, passed in checks.items():
        print(("PASS" if passed else "FAIL") + ": " + name, flush=True)
    print("CLOUD_SOURCE_VALIDATION_PASSED=" + str(result["passed"]).lower(), flush=True)
    print("NO_UNREAL_BUILD_NO_LOCAL_PC_ACCESS=true", flush=True)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
