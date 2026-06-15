import os
import sys
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if os.path.isdir(SRC):
    sys.path.insert(0, str(SRC))

import Make_report_sign_easy.config as config  # noqa: E402
from Make_report_sign_easy.core import RenderProfile  # noqa: E402
from Make_report_sign_easy.services import ProfileService  # noqa: E402


BASELINE_PRESET = (
    REPO_ROOT
    / "src"
    / "Make_report_sign_easy"
    / "configs"
    / "presets"
    / "baseline.json"
)


def test_profile_service_loads_default_profile():
    profile = ProfileService().default_profile()

    assert isinstance(profile, RenderProfile)
    assert profile.image_size == config.IMAGE_SIZE
    assert profile.color_base == config.COLOR_BASE


def test_profile_service_round_trips_json(tmp_path):
    service = ProfileService()
    profile = replace(service.default_profile(), line_width=config.LINE_WIDTH + 1)
    path = tmp_path / "profile.json"

    service.save_json(profile, path)
    loaded = service.load_json(path)

    assert loaded == profile


def test_profile_service_loads_legacy_baseline_preset():
    profile = ProfileService().load_json(BASELINE_PRESET)

    assert profile.image_size == 512
    assert profile.color_base == (65, 105, 225)
    assert profile.alpha_range == (160, 255)


def test_profile_service_applies_partial_override():
    service = ProfileService()
    base = service.default_profile()

    profile = service.from_dict({"line_width": base.line_width + 2}, base=base)

    assert profile.line_width == base.line_width + 2
    assert profile.image_size == base.image_size
