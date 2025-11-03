import os
import sys
import json
import io
import argparse
import fitz  # PyMuPDF

# 允許直接以腳本執行：加入專案上層到 sys.path，改用絕對匯入
if __name__ == "__main__" and __package__ is None:
    here = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(here, "..", ".."))
    src_root = os.path.join(repo_root, "src")
    if os.path.isdir(src_root):
        sys.path.insert(0, src_root)
    sys.path.insert(0, repo_root)
try:
    # Prefer installed package-style import
    from Make_report_sign_easy import builder as _builder  # type: ignore
except Exception:  # Fallback to repo-local module import
    import builder as _builder  # type: ignore

generate_text_image = _builder.generate_text_image


def extract_freetext_positions(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    pos_map = {}
    for annot in page.annots() or []:
        if annot.type[1] == "FreeText":
            content = annot.info.get("content", "").strip()
            if content:
                pos_map[content] = fitz.Rect(annot.rect)
    doc.close()
    return pos_map


def paste_image_centered(page, rect, pil_image):
    # 將 PIL 影像等比縮放，完整落在 rect 內，並置中
    img_w, img_h = pil_image.size
    rect_w = rect.width
    rect_h = rect.height
    if img_w == 0 or img_h == 0:
        return
    scale = min(rect_w / img_w, rect_h / img_h)
    w = max(1, int(img_w * scale))
    h = max(1, int(img_h * scale))
    # 計算置中位置
    x0 = rect.x0 + (rect_w - w) / 2
    y0 = rect.y0 + (rect_h - h) / 2
    x1 = x0 + w
    y1 = y0 + h
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    page.insert_image(fitz.Rect(x0, y0, x1, y1), stream=buf.getvalue())


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Fill a PDF template using FreeText annotation keys and hand-"
            "written style text images."
        )
    )
    parser.add_argument(
        "--template", required=True, help="Path to the PDF template"
    )
    parser.add_argument(
        "--output", required=True, help="Path to save the filled PDF"
    )
    parser.add_argument(
        "--values", required=True,
        help="Path to JSON mapping: {field_key: text}"
    )
    parser.add_argument(
        "--clear-annots", action="store_true",
        help="Remove annotations after insertion"
    )
    parser.add_argument(
        "--random", action="store_true",
        help="Enable random jitter for each character"
    )
    args = parser.parse_args()

    if not os.path.exists(args.template):
        raise FileNotFoundError(args.template)
    if not os.path.exists(args.values):
        raise FileNotFoundError(args.values)

    with open(args.values, "r", encoding="utf-8") as f:
        values = json.load(f)
        if not isinstance(values, dict):
            raise ValueError(
                "values must be a JSON object mapping {field_key: text}"
            )

    pos_map = extract_freetext_positions(args.template)

    doc = fitz.open(args.template)
    page = doc[0]

    # 先清除註解（可選）
    if args.clear_annots:
        for annot in page.annots() or []:
            page.delete_annot(annot)

    missing = []
    for key, text in values.items():
        rect = pos_map.get(key)
        if rect is None:
            missing.append(key)
            continue
        img = generate_text_image(str(text), random=args.random)
        if img:
            paste_image_centered(page, rect, img)

    doc.save(args.output, garbage=4, deflate=True)
    doc.close()

    if missing:
        print("⚠️ 無對應欄位：", ", ".join(missing))
    print(f"✅ 已輸出：{args.output}")


if __name__ == "__main__":
    main()
