import os
import sys
import random
from PIL import Image

# Prefer src-layout during development
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_SRC = os.path.join(_REPO_ROOT, 'src')
if os.path.isdir(_SRC):
    sys.path.insert(0, _SRC)

import Make_report_sign_easy.builder as builder  # noqa: E402
import Make_report_sign_easy.config as config  # noqa: E402


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
