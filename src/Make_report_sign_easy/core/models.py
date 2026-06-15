from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
import random
import re
from typing import Any, Mapping


@dataclass(frozen=True)
class RenderProfile:
    """Immutable snapshot of handwriting render settings.

    This is the Phase 1 compatibility bridge: the existing renderer still reads
    module-level config values, but callers can now pass an explicit profile.
    Later phases can move these fields directly into pure render functions.
    """

    image_size: int
    upscale_factor: int
    font_path: str
    font_router: Mapping[str, str]
    perturb: float
    perturb_jitter: float
    shear_angle: float
    shear_jitter: float
    color_base: tuple[int, int, int]
    color_variation: int
    alpha_range: tuple[int, int]
    blob_size_range: tuple[int, int]
    partial_dot_radius: tuple[float, float]
    line_width: int
    char_spacing_offset: int
    digit_scale: float
    digit_offset_y: float
    alpha_scale: float
    alpha_offset_y: float
    cjk_scale: float
    cjk_offset_y: float
    special_scale: float
    special_offset_y: float
    blur_amount: float
    partial_dot_probability: float
    special_render_overrides: Mapping[str, Mapping[str, Any]]
    session_render_overrides: Mapping[str, Any]

    @classmethod
    def from_config(cls, cfg: Any) -> "RenderProfile":
        """Create a profile from the legacy config module."""
        if hasattr(cfg, "sync_digit_overrides"):
            cfg.sync_digit_overrides()
        return cls(
            image_size=int(cfg.IMAGE_SIZE),
            upscale_factor=int(cfg.UPSCALE_FACTOR),
            font_path=str(cfg.FONT_PATH),
            font_router=deepcopy(getattr(cfg, "FONT_ROUTER", {})),
            perturb=float(cfg.PERTURB),
            perturb_jitter=float(cfg.PERTURB_JITTER),
            shear_angle=float(cfg.SHEAR_ANGLE),
            shear_jitter=float(cfg.SHEAR_JITTER),
            color_base=tuple(int(v) for v in cfg.COLOR_BASE),
            color_variation=int(cfg.COLOR_VARIATION),
            alpha_range=tuple(int(v) for v in cfg.ALPHA_RANGE),
            blob_size_range=tuple(int(v) for v in cfg.BLOB_SIZE_RANGE),
            partial_dot_radius=tuple(float(v) for v in cfg.PARTIAL_DOT_RADIUS),
            line_width=int(cfg.LINE_WIDTH),
            char_spacing_offset=int(cfg.CHAR_SPACING_OFFSET),
            digit_scale=float(cfg.DIGIT_SCALE),
            digit_offset_y=float(cfg.DIGIT_OFFSET_Y),
            alpha_scale=float(cfg.ALPHA_SCALE),
            alpha_offset_y=float(cfg.ALPHA_OFFSET_Y),
            cjk_scale=float(cfg.CJK_SCALE),
            cjk_offset_y=float(cfg.CJK_OFFSET_Y),
            special_scale=float(cfg.SPECIAL_SCALE),
            special_offset_y=float(cfg.SPECIAL_OFFSET_Y),
            blur_amount=float(cfg.BLUR_AMOUNT),
            partial_dot_probability=float(cfg.PARTIAL_DOT_PROBABILITY),
            special_render_overrides=deepcopy(
                getattr(cfg, "SPECIAL_RENDER_OVERRIDES", {})
            ),
            session_render_overrides=deepcopy(
                getattr(cfg, "SESSION_RENDER_OVERRIDES", {})
            ),
        )

    def to_config_overrides(self) -> dict[str, Any]:
        """Return legacy config overrides for the current renderer bridge."""
        return {
            "IMAGE_SIZE": self.image_size,
            "UPSCALE_FACTOR": self.upscale_factor,
            "FONT_PATH": self.font_path,
            "FONT_ROUTER": dict(self.font_router),
            "PERTURB": self.perturb,
            "PERTURB_JITTER": self.perturb_jitter,
            "SHEAR_ANGLE": self.shear_angle,
            "SHEAR_JITTER": self.shear_jitter,
            "COLOR_BASE": self.color_base,
            "COLOR_VARIATION": self.color_variation,
            "ALPHA_RANGE": self.alpha_range,
            "BLOB_SIZE_RANGE": self.blob_size_range,
            "PARTIAL_DOT_RADIUS": self.partial_dot_radius,
            "LINE_WIDTH": self.line_width,
            "CHAR_SPACING_OFFSET": self.char_spacing_offset,
            "DIGIT_SCALE": self.digit_scale,
            "DIGIT_OFFSET_Y": self.digit_offset_y,
            "ALPHA_SCALE": self.alpha_scale,
            "ALPHA_OFFSET_Y": self.alpha_offset_y,
            "CJK_SCALE": self.cjk_scale,
            "CJK_OFFSET_Y": self.cjk_offset_y,
            "SPECIAL_SCALE": self.special_scale,
            "SPECIAL_OFFSET_Y": self.special_offset_y,
            "BLUR_AMOUNT": self.blur_amount,
            "PARTIAL_DOT_PROBABILITY": self.partial_dot_probability,
            "SPECIAL_RENDER_OVERRIDES": deepcopy(
                self.special_render_overrides
            ),
            "SESSION_RENDER_OVERRIDES": deepcopy(
                self.session_render_overrides
            ),
        }

    def jittered(
        self,
        seed: int | None = None,
        random_per: float = 10,
        param_info: Mapping[str, tuple[str, str]] | None = None,
    ) -> "RenderProfile":
        """Return a new profile with bounded legacy-style parameter jitter."""
        rng = random.Random(seed)
        info = param_info or {}
        updates = {}
        for config_key, attr_name in _JITTERABLE_CONFIG_TO_ATTR.items():
            range_text = (info.get(config_key) or ("", ""))[1]
            bounds = _parse_range(range_text)
            if bounds is None:
                continue
            current = getattr(self, attr_name)
            updates[attr_name] = _jitter_value(
                current,
                low=bounds[0],
                high=bounds[1],
                random_per=random_per,
                rng=rng,
            )
        return replace(self, **updates)


_JITTERABLE_CONFIG_TO_ATTR = {
    "IMAGE_SIZE": "image_size",
    "UPSCALE_FACTOR": "upscale_factor",
    "PERTURB": "perturb",
    "PERTURB_JITTER": "perturb_jitter",
    "SHEAR_ANGLE": "shear_angle",
    "SHEAR_JITTER": "shear_jitter",
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
}


def _parse_range(range_text: str) -> tuple[float, float] | None:
    numbers = re.findall(r"-?\d+\.?\d*", range_text)
    if len(numbers) < 2:
        return None
    low, high = map(float, numbers[:2])
    if low > high:
        low, high = high, low
    return low, high


def _jitter_value(
    value: Any,
    *,
    low: float,
    high: float,
    random_per: float,
    rng: random.Random,
) -> Any:
    delta = (high - low) * (random_per / 100)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return int(round(max(low, min(high, value + rng.uniform(-delta, delta)))))
    if isinstance(value, float):
        return max(low, min(high, value + rng.uniform(-delta, delta)))
    if isinstance(value, tuple) and len(value) == 2:
        return tuple(
            _jitter_value(
                item,
                low=low,
                high=high,
                random_per=random_per,
                rng=rng,
            )
            for item in value
        )
    return value
