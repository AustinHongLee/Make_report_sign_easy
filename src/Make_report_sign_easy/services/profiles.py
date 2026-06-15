from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any, Mapping
import json

from Make_report_sign_easy.core import RenderProfile


_TUPLE_FIELDS = {
    "color_base",
    "alpha_range",
    "blob_size_range",
    "partial_dot_radius",
}

_LEGACY_KEY_TO_ATTR = {
    "IMAGE_SIZE": "image_size",
    "UPSCALE_FACTOR": "upscale_factor",
    "FONT_PATH": "font_path",
    "FONT_ROUTER": "font_router",
    "PERTURB": "perturb",
    "PERTURB_JITTER": "perturb_jitter",
    "SHEAR_ANGLE": "shear_angle",
    "SHEAR_JITTER": "shear_jitter",
    "COLOR_BASE": "color_base",
    "COLOR_VARIATION": "color_variation",
    "ALPHA_RANGE": "alpha_range",
    "BLOB_SIZE_RANGE": "blob_size_range",
    "PARTIAL_DOT_RADIUS": "partial_dot_radius",
    "LINE_WIDTH": "line_width",
    "CHAR_SPACING_OFFSET": "char_spacing_offset",
    "DIGIT_SCALE": "digit_scale",
    "DIGIT_OFFSET_Y": "digit_offset_y",
    "ALPHA_SCALE": "alpha_scale",
    "ALPHA_OFFSET_Y": "alpha_offset_y",
    "CJK_SCALE": "cjk_scale",
    "CJK_OFFSET_Y": "cjk_offset_y",
    "SPECIAL_SCALE": "special_scale",
    "SPECIAL_OFFSET_Y": "special_offset_y",
    "BLUR_AMOUNT": "blur_amount",
    "PARTIAL_DOT_PROBABILITY": "partial_dot_probability",
    "SPECIAL_RENDER_OVERRIDES": "special_render_overrides",
    "SESSION_RENDER_OVERRIDES": "session_render_overrides",
}


class ProfileService:
    """Load, save, and normalize handwriting render profiles."""

    def default_profile(self) -> RenderProfile:
        import Make_report_sign_easy.config as config

        return RenderProfile.from_config(config)

    def from_dict(
        self,
        data: Mapping[str, Any],
        *,
        base: RenderProfile | None = None,
    ) -> RenderProfile:
        payload = self.to_dict(base or self.default_profile())
        valid_fields = {field.name for field in fields(RenderProfile)}

        for key, value in data.items():
            if key == "config_version":
                continue
            attr = _LEGACY_KEY_TO_ATTR.get(key, key)
            if attr in valid_fields:
                payload[attr] = value

        for key in _TUPLE_FIELDS:
            payload[key] = tuple(payload[key])
        payload["font_router"] = dict(payload["font_router"])
        payload["special_render_overrides"] = dict(payload["special_render_overrides"])
        payload["session_render_overrides"] = dict(payload["session_render_overrides"])

        return RenderProfile(**payload)

    def to_dict(self, profile: RenderProfile) -> dict[str, Any]:
        return {
            field.name: _jsonable(getattr(profile, field.name))
            for field in fields(RenderProfile)
        }

    def to_legacy_dict(self, profile: RenderProfile) -> dict[str, Any]:
        return {
            key: _jsonable(value)
            for key, value in profile.to_config_overrides().items()
        }

    def load_json(
        self,
        path: str | Path,
        *,
        base: RenderProfile | None = None,
    ) -> RenderProfile:
        profile_path = Path(path)
        if not profile_path.exists():
            raise FileNotFoundError(profile_path)
        with profile_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("profile JSON must be an object")
        return self.from_dict(data, base=base)

    def save_json(self, profile: RenderProfile, path: str | Path) -> None:
        profile_path = Path(path)
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(
            json.dumps(self.to_dict(profile), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value
