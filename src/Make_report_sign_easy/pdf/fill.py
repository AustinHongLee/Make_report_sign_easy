from __future__ import annotations

from pathlib import Path
import random as random_module
from typing import Mapping
import io

import fitz

from Make_report_sign_easy.builder import generate_text_image
from Make_report_sign_easy.core import RenderProfile

from .models import FillResult
from .template import extract_freetext_positions


def paste_image_centered(page, rect, pil_image):
    """Scale a PIL image into a PDF rect and insert it centered."""
    img_w, img_h = pil_image.size
    rect_w = rect.width
    rect_h = rect.height
    if img_w == 0 or img_h == 0:
        return
    scale = min(rect_w / img_w, rect_h / img_h)
    w = max(1, int(img_w * scale))
    h = max(1, int(img_h * scale))
    x0 = rect.x0 + (rect_w - w) / 2
    y0 = rect.y0 + (rect_h - h) / 2
    x1 = x0 + w
    y1 = y0 + h
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    page.insert_image(fitz.Rect(x0, y0, x1, y1), stream=buf.getvalue())


def fill_pdf(
    *,
    template_path: str | Path,
    values: Mapping[str, object],
    output_path: str | Path,
    clear_annots: bool = False,
    random: bool = False,
    seed: int | None = None,
    profile: RenderProfile | None = None,
    page_index: int = 0,
) -> FillResult:
    """Fill one PDF page using FreeText annotation keys and value mapping."""
    if seed is not None:
        random_module.seed(seed)

    template_path = Path(template_path)
    output_path = Path(output_path)

    if not template_path.exists():
        raise FileNotFoundError(template_path)

    pos_map = extract_freetext_positions(template_path, page_index=page_index)

    doc = fitz.open(template_path)
    try:
        page = doc[page_index]

        if clear_annots:
            for annot in list(page.annots() or []):
                page.delete_annot(annot)

        filled = []
        missing = []
        for key, text in values.items():
            rect = pos_map.get(key)
            if rect is None:
                missing.append(key)
                continue
            img = generate_text_image(
                str(text),
                random=random,
                profile=profile,
            )
            if img:
                paste_image_centered(page, rect, img)
                filled.append(key)

        doc.save(output_path, garbage=4, deflate=True)
    finally:
        doc.close()

    return FillResult(
        output_path=output_path,
        filled_fields=tuple(filled),
        missing_fields=tuple(missing),
    )
