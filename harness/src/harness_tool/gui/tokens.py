"""Design tokens: the single source for GUI colours, type, spacing. No Qt imports on purpose.

The clickable prototype (tools/build_prototype.py) and the real GUI both read these values.
Colour is never the only carrier of meaning: signal categories also differ by label, icon and
line weight; redundancy is a dashed line. Category colours were chosen to stay apart under
simulated colour blindness. Contrast and separation are verified in tests/test_tokens.py.
"""

from typing import Final

LIGHT: Final[dict[str, str]] = {
    "bg": "#FFFFFF",
    "surface": "#F4F6F8",
    "surface-2": "#E6EAEE",
    "border": "#6B7686",
    "text": "#1B1F24",
    "text-muted": "#4A5565",
    "primary": "#0B5CAD",
    "on-primary": "#FFFFFF",
    "focus": "#6A2FD8",
    "error": "#B3261E",
    "warning": "#8A5200",
    "success": "#1B6E3C",
    "info": "#0B5CAD",
    "auto-fill": "#7A5C00",
    "locked": "#4A5565",
    "released": "#1B6E3C",
    "cat-power": "#B83014",
    "cat-data": "#000080",
    "cat-analog": "#235C53",
    "cat-rf": "#9933CC",
    "cat-pyro": "#5C0000",
    "cat-discrete": "#5500FF",
    "cat-ground": "#3A0953",
}

DARK: Final[dict[str, str]] = {
    "bg": "#12161B",
    "surface": "#1B2129",
    "surface-2": "#26303B",
    "border": "#8793A3",
    "text": "#ECEFF3",
    "text-muted": "#B4BDC9",
    "primary": "#6DB3F2",
    "on-primary": "#0A1A2B",
    "focus": "#B79BFF",
    "error": "#FF8A80",
    "warning": "#F2B04A",
    "success": "#6FD39A",
    "info": "#6DB3F2",
    "auto-fill": "#E6C34D",
    "locked": "#B4BDC9",
    "released": "#6FD39A",
    "cat-power": "#DDFF33",
    "cat-data": "#33FFFF",
    "cat-analog": "#9EF075",
    "cat-rf": "#E566FF",
    "cat-pyro": "#F07575",
    "cat-discrete": "#B89C14",
    "cat-ground": "#46A6B9",
}

CATEGORIES: Final[dict[str, dict[str, str]]] = {
    # name -> label, icon glyph (also drawn on the line), line weight in px
    "power": {"label": "Power", "icon": "P", "weight": "3.5"},
    "data": {"label": "Data", "icon": "D", "weight": "2"},
    "analog": {"label": "Analog", "icon": "A", "weight": "1.5"},
    "rf": {"label": "RF", "icon": "R", "weight": "2.5"},
    "pyro": {"label": "Pyro", "icon": "!", "weight": "4"},
    "discrete": {"label": "Discrete", "icon": "d", "weight": "1.5"},
    "ground": {"label": "Ground", "icon": "G", "weight": "1"},
}

# Model categories without their own design-system colour share one with a related category.
CATEGORY_ALIAS: Final[dict[str, str]] = {"thermal": "analog", "other": "ground"}


def style_category(category: str) -> str:
    """The design-system category used to draw an interface-type category."""
    key = CATEGORY_ALIAS.get(category, category)
    return key if key in CATEGORIES else "data"


FONT_UI: Final[str] = "Inter, 'Segoe UI', system-ui, sans-serif"  # Inter bundled in the release
FONT_MONO: Final[str] = "'JetBrains Mono', Consolas, monospace"
# Type scale in px (base 14, ratio ~1.2) and spacing on a 4/8 px grid.
TYPE_SCALE: Final[dict[str, int]] = {"xs": 11, "sm": 12, "base": 14, "md": 16, "lg": 20, "xl": 24}
SPACING: Final[tuple[int, ...]] = (4, 8, 12, 16, 24, 32, 48)


def _lin(c: int) -> float:
    s = c / 255
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4


def luminance(hex_colour: str) -> float:
    r, g, b = (int(hex_colour[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a: str, b: str) -> float:
    """WCAG 2.x contrast ratio between two #RRGGBB colours."""
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)
