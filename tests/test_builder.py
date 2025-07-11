import os
import sys
import random
from PIL import Image

# Ensure the package root is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import Make_report_sign_easy.builder as builder
import Make_report_sign_easy.config as config


def test_generate_text_image_basic():
    random.seed(0)
    img = builder.generate_text_image('abc', font_path=config.FONT_PATH)
    assert isinstance(img, Image.Image)
    assert img.width > 0 and img.height > 0
