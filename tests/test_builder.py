import os
import sys
import random
from dataclasses import replace
import hashlib
from PIL import Image

# Prefer src-layout during development
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_SRC = os.path.join(_REPO_ROOT, 'src')
if os.path.isdir(_SRC):
    sys.path.insert(0, _SRC)

import Make_report_sign_easy.builder as builder  # noqa: E402
import Make_report_sign_easy.config as config  # noqa: E402
from Make_report_sign_easy.core import RenderProfile  # noqa: E402


def _image_hash(img):
    return hashlib.sha256(img.tobytes()).hexdigest()


def test_generate_text_image_basic():
    random.seed(0)
    img = builder.generate_text_image('abc', font_path=config.FONT_PATH)
    assert isinstance(img, Image.Image)
    assert img.width > 0 and img.height > 0


def test_generate_text_image_random_option():
    random.seed(0)
    img = builder.generate_text_image(
        'abc', font_path=config.FONT_PATH, random=True
    )
    assert isinstance(img, Image.Image)
    assert img.width > 0 and img.height > 0


def test_generate_text_image_random_per():
    random.seed(0)
    img = builder.generate_text_image(
        'abc', font_path=config.FONT_PATH, random=True, random_per=20
    )
    assert isinstance(img, Image.Image)
    assert img.width > 0 and img.height > 0


def test_render_profile_matches_legacy_config_output():
    profile = RenderProfile.from_config(config)

    random.seed(0)
    legacy_img = builder.generate_text_image('abc', font_path=config.FONT_PATH)

    random.seed(0)
    profile_img = builder.generate_text_image('abc', profile=profile)

    assert isinstance(profile_img, Image.Image)
    assert profile_img.size == legacy_img.size
    assert _image_hash(profile_img) == _image_hash(legacy_img)


def test_render_profile_overrides_restore_legacy_config():
    original_line_width = config.LINE_WIDTH
    profile = replace(
        RenderProfile.from_config(config),
        line_width=original_line_width + 1,
    )

    random.seed(0)
    img = builder.generate_text_image('abc', profile=profile)

    assert isinstance(img, Image.Image)
    assert config.LINE_WIDTH == original_line_width


def test_render_profile_jittered_is_reproducible():
    profile = RenderProfile.from_config(config)

    jittered_a = profile.jittered(seed=42, param_info=config.PARAM_INFO)
    jittered_b = profile.jittered(seed=42, param_info=config.PARAM_INFO)

    assert jittered_a == jittered_b
    assert jittered_a is not profile
