"""Caricature avatars rendered as SVG from a person's visible traits.

Everything is drawn in code at runtime: no AI, no image files.

* The **genes** decide eye colour, hair colour, freckles (and skin tone).
* The **generation** decides the era: frame, background, clothes, hairstyles
  and hats that fit ~1900, ~1955, ~1985 or today.
* A per-person **seed** picks everything else (face shape, nose, brows,
  hairstyle, outfit and colours, hat, beard, glasses, earrings...), so two
  people with the same genes still look like different people, and the same
  person always looks the same.
* An optional **mood** changes the expression of "me" on the result screen.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np

_ids = itertools.count()

# ---------------------------------------------------------------- palettes
HAIR = {
    "black": "#2b2220",
    "brown": "#6b4226",
    "blond": "#e2b85c",
    "red": "#c4532d",
}
EYES = {
    "brown": "#6b3e1f",
    "blue": "#3d8fd6",
    "green": "#4f9a4a",
}
SKIN = {
    "light": "#f6d2b8",
    "medium": "#e3ad86",
    "tan": "#c68a5e",
    "dark": "#8d5a3b",
}

GENERATIONS = ("great_grandparent", "grandparent", "parent", "self")
MOODS = ("neutral", "smile", "happy", "sad", "sick")

# per-era background tints, outfit colours and accent colours
BACKGROUNDS = {
    "great_grandparent": ["#55654a", "#5b4f3f", "#4a5a63", "#61504f"],
    "grandparent": ["#a9b9c9", "#b9c4a9", "#c9b8a9", "#b3abc4"],
    "parent": ["#f6c6c6", "#c6e3f6", "#f6e7a9", "#d4c6f6"],
    "self": ["#dcebe4", "#e4e0f2", "#f2e6d8", "#dbe8f2"],
}
OUTFIT = {
    "great_grandparent": ["#2c2f3a", "#4a3528", "#3b3b3b", "#2f3d33", "#5e3550", "#3d2f4f"],
    "grandparent": ["#5a6474", "#3f8a8b", "#8a5a44", "#6e7a4f", "#a2465a", "#465a8a"],
    "parent": ["#3fb6c2", "#7d4cdb", "#ea5a9a", "#f2a541", "#2fa36b", "#3b6fd6"],
    "self": ["#3a7d5c", "#f2a541", "#3b5bdb", "#e0525e", "#2b2b33", "#8a6fd6"],
}


@dataclass(frozen=True)
class Look:
    """Visible traits of a person (the phenotype, not the genotype)."""

    sex: str  # "F" or "M"
    eyes: str = "brown"
    hair: str = "brown"
    freckles: bool = False
    skin: str = "light"


@dataclass(frozen=True)
class Head:
    rx: float  # half width
    ry: float  # half height
    jaw: float  # jaw half width near the chin (smaller = pointier chin)
    cy: float = 108.0

    @property
    def top(self) -> float:
        return self.cy - self.ry

    @property
    def chin(self) -> float:
        return self.cy + self.ry


# ---------------------------------------------------------------- helpers
def _shade(hex_color: str, factor: float) -> str:
    """Darken (factor < 1) or lighten (factor > 1) a hex colour."""
    h = hex_color.lstrip("#")
    rgb = [int(h[i : i + 2], 16) for i in (0, 2, 4)]
    if factor < 1:
        rgb = [round(c * factor) for c in rgb]
    else:
        rgb = [round(c + (255 - c) * (factor - 1)) for c in rgb]
    return "#" + "".join(f"{min(255, max(0, c)):02x}" for c in rgb)


def _pick(rng: np.random.Generator, options, p=None):
    return options[int(rng.choice(len(options), p=p))]


# ---------------------------------------------------------------- frames
def _frame(gen: str, bg_color: str | None = None) -> tuple[str, str]:
    """Return (background, frame) SVG for the generation's era."""
    if gen == "great_grandparent":  # ~1900: ornate gold frame
        bg = f'<rect x="18" y="18" width="164" height="214" fill="{bg_color or "#55654a"}"/>'
        corners = "".join(
            f'<circle cx="{x}" cy="{y}" r="9" fill="#e9c86f" stroke="#8a6420" stroke-width="2"/>'
            for x, y in ((14, 14), (186, 14), (14, 236), (186, 236))
        )
        frame = (
            '<rect x="7" y="7" width="186" height="236" rx="4" fill="none" stroke="#b8892f" stroke-width="14"/>'
            '<rect x="16" y="16" width="168" height="218" fill="none" stroke="#e9c86f" stroke-width="3"/>'
            '<rect x="1" y="1" width="198" height="248" rx="6" fill="none" stroke="#7a5518" stroke-width="2"/>'
            + corners
        )
    elif gen == "grandparent":  # ~1955: plain wooden frame
        bg = f'<rect x="16" y="16" width="168" height="218" fill="{bg_color or "#a9b9c9"}"/>'
        frame = (
            '<rect x="6" y="6" width="188" height="238" fill="none" stroke="#7a5232" stroke-width="12"/>'
            '<rect x="14" y="14" width="172" height="222" fill="none" stroke="#a47148" stroke-width="3"/>'
        )
    elif gen == "parent":  # ~1985: instant photo
        bg = f'<rect x="14" y="14" width="172" height="192" fill="{bg_color or "#f6c6c6"}"/>'
        frame = (
            '<path d="M0,0 H200 V250 H0 Z M14,14 V206 H186 V14 Z" fill="#fbfaf5" fill-rule="evenodd"/>'
            '<rect x="0.5" y="0.5" width="199" height="249" fill="none" stroke="#d8d4c8"/>'
        )
    else:  # today: rounded "profile picture"
        bg = f'<rect x="8" y="8" width="184" height="234" rx="22" fill="{bg_color or "#dcebe4"}"/>'
        frame = '<rect x="4" y="4" width="192" height="242" rx="26" fill="none" stroke="#2f3b36" stroke-width="5"/>'
    return bg, frame


def _clip(gen: str) -> str:
    if gen == "great_grandparent":
        return '<rect x="18" y="18" width="164" height="214"/>'
    if gen == "grandparent":
        return '<rect x="16" y="16" width="168" height="218"/>'
    if gen == "parent":
        return '<rect x="14" y="14" width="172" height="192"/>'
    return '<rect x="8" y="8" width="184" height="234" rx="22"/>'


# ---------------------------------------------------------------- head
def _head_path(h: Head) -> str:
    t, b, rx, jw, cy = h.top, h.chin, h.rx, h.jaw, h.cy
    return (
        f"M100,{t:.1f} C{100 + rx * 0.62:.1f},{t:.1f} {100 + rx:.1f},{t + h.ry * 0.38:.1f} {100 + rx:.1f},{cy + 2:.1f} "
        f"C{100 + rx:.1f},{cy + h.ry * 0.5:.1f} {100 + jw:.1f},{b - 2:.1f} 100,{b:.1f} "
        f"C{100 - jw:.1f},{b - 2:.1f} {100 - rx:.1f},{cy + h.ry * 0.5:.1f} {100 - rx:.1f},{cy + 2:.1f} "
        f"C{100 - rx:.1f},{t + h.ry * 0.38:.1f} {100 - rx * 0.62:.1f},{t:.1f} 100,{t:.1f} Z"
    )


def _random_head(rng: np.random.Generator) -> Head:
    rx = float(rng.uniform(41, 48))
    ry = float(rng.uniform(49, 55))
    jaw = rx * float(rng.uniform(0.45, 0.85))
    return Head(rx, ry, jaw)


# ---------------------------------------------------------------- hair
def _cap(h: Head, color: str, vol: float = 7, hairline: float = 22, part: str = "none", sides: float = 4) -> str:
    """Hair hugging the skull: an outer arc around the top of the head and
    an inner hairline on the forehead, so it can never float."""
    t, cy, rx = h.top, h.cy, h.rx
    hy = t + hairline
    side_y = cy + sides
    outer = (
        f"M{100 - rx - 3:.1f},{side_y:.1f} "
        f"C{100 - rx - vol:.1f},{t - vol * 0.4:.1f} {100 - rx * 0.55:.1f},{t - vol:.1f} 100,{t - vol:.1f} "
        f"C{100 + rx * 0.55:.1f},{t - vol:.1f} {100 + rx + vol:.1f},{t - vol * 0.4:.1f} {100 + rx + 3:.1f},{side_y:.1f} "
    )
    if part == "left":  # sweep falling to the right
        inner = (
            f"L{100 + rx - 3:.1f},{side_y:.1f} C{100 + rx - 4:.1f},{hy + 10:.1f} {100 + rx * 0.3:.1f},{hy + 8:.1f} {100 - rx * 0.25:.1f},{hy - 6:.1f} "
            f"C{100 - rx * 0.55:.1f},{hy + 2:.1f} {100 - rx + 3:.1f},{hy + 4:.1f} {100 - rx + 3:.1f},{side_y:.1f} Z"
        )
    elif part == "right":
        inner = (
            f"L{100 + rx - 3:.1f},{side_y:.1f} C{100 + rx - 3:.1f},{hy + 4:.1f} {100 + rx * 0.55:.1f},{hy + 2:.1f} {100 + rx * 0.25:.1f},{hy - 6:.1f} "
            f"C{100 - rx * 0.3:.1f},{hy + 8:.1f} {100 - rx + 4:.1f},{hy + 10:.1f} {100 - rx + 3:.1f},{side_y:.1f} Z"
        )
    elif part == "middle":
        inner = (
            f"L{100 + rx - 3:.1f},{side_y:.1f} C{100 + rx - 2:.1f},{hy + 12:.1f} {100 + rx * 0.35:.1f},{hy + 2:.1f} 100,{hy - 8:.1f} "
            f"C{100 - rx * 0.35:.1f},{hy + 2:.1f} {100 - rx + 2:.1f},{hy + 12:.1f} {100 - rx + 3:.1f},{side_y:.1f} Z"
        )
    elif part == "bangs":
        inner = (
            f"L{100 + rx - 3:.1f},{side_y:.1f} C{100 + rx - 3:.1f},{hy + 14:.1f} {100 + rx * 0.5:.1f},{hy + 12:.1f} {100 + rx * 0.3:.1f},{hy + 9:.1f} "
            f"L{100 + rx * 0.15:.1f},{hy + 13:.1f} L100,{hy + 9:.1f} L{100 - rx * 0.15:.1f},{hy + 13:.1f} "
            f"L{100 - rx * 0.3:.1f},{hy + 9:.1f} C{100 - rx * 0.5:.1f},{hy + 12:.1f} {100 - rx + 3:.1f},{hy + 14:.1f} {100 - rx + 3:.1f},{side_y:.1f} Z"
        )
    else:
        inner = (
            f"L{100 + rx - 3:.1f},{side_y:.1f} C{100 + rx - 3:.1f},{hy + 8:.1f} {100 + rx * 0.4:.1f},{hy:.1f} 100,{hy:.1f} "
            f"C{100 - rx * 0.4:.1f},{hy:.1f} {100 - rx + 3:.1f},{hy + 8:.1f} {100 - rx + 3:.1f},{side_y:.1f} Z"
        )
    return f'<path d="{outer}{inner}" fill="{color}"/>'


def _curls_ring(h: Head, color: str, dark: str, r: float, n: int, spread: float = 6, y_from: float = 0) -> str:
    out = []
    for a in np.linspace(-0.15, np.pi + 0.15, n):
        x = 100 + (h.rx + spread) * np.cos(a)
        y = h.cy - 6 - (h.ry + spread) * np.sin(a) + y_from
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" stroke="{dark}" stroke-width="1"/>')
    return "".join(out)


def _hair(h: Head, gen: str, sex: str, color: str, rng: np.random.Generator) -> tuple[str, str, str]:
    """Return (back_layer, front_layer, style_name)."""
    d = _shade(color, 0.72)
    lt = _shade(color, 1.35)
    t, cy, rx = h.top, h.cy, h.rx
    styles_m = {
        "great_grandparent": ["side_part", "slick", "receding", "short", "curly_short"],
        "grandparent": ["side_part", "pompadour", "short", "slick", "receding"],
        "parent": ["mullet", "curly_short", "side_part", "spiky", "short"],
        "self": ["messy", "spiky", "short", "curly_short", "buzz", "side_part"],
    }
    styles_f = {
        "great_grandparent": ["bun", "low_bun", "updo_curls", "middle_bun"],
        "grandparent": ["updo_curls", "bob", "rolls", "bun"],
        "parent": ["big_curly", "long_straight", "ponytail", "bob", "wavy_long"],
        "self": ["long_straight", "ponytail", "pixie", "wavy_long", "bob", "bun_top"],
    }
    style = _pick(rng, (styles_m if sex == "M" else styles_f)[gen])
    back, front = "", ""
    shine = f'<path d="M{100 - rx * 0.45:.1f},{t + 2:.1f} Q{100 - rx * 0.1:.1f},{t - 6:.1f} {100 + rx * 0.2:.1f},{t - 3:.1f}" stroke="{lt}" stroke-width="2.5" fill="none" stroke-linecap="round" opacity=".55"/>'

    if style == "side_part":
        front = _cap(h, color, vol=8, hairline=20, part="left") + f'<path d="M{100 - rx * 0.28:.1f},{t - 5:.1f} Q{100 - rx * 0.3:.1f},{t + 6:.1f} {100 - rx * 0.25:.1f},{t + 14:.1f}" stroke="{d}" stroke-width="2" fill="none"/>' + shine
    elif style == "slick":
        front = _cap(h, color, vol=4, hairline=16) + shine + f'<path d="M{100 - rx * 0.6:.1f},{t + 8:.1f} Q100,{t - 2:.1f} {100 + rx * 0.6:.1f},{t + 8:.1f}" stroke="{d}" stroke-width="1.6" fill="none" opacity=".7"/>'
    elif style == "receding":
        # hair only around the sides; the caller paints the bald crown on top
        front = _cap(h, color, vol=3, hairline=6, sides=6) + "<!--crown-->"
    elif style == "short":
        front = _cap(h, color, vol=6, hairline=22)
    elif style == "buzz":
        front = f'<g opacity=".85">{_cap(h, color, vol=2, hairline=18)}</g>'
    elif style == "curly_short":
        front = _cap(h, color, vol=8, hairline=20) + _curls_ring(h, color, d, 8, 11, spread=3, y_from=4)
    elif style == "pompadour":
        front = _cap(h, color, vol=7, hairline=18) + (
            f'<path d="M{100 - rx * 0.75:.1f},{t + 10:.1f} C{100 - rx * 0.7:.1f},{t - 24:.1f} {100 + rx * 0.5:.1f},{t - 26:.1f} {100 + rx * 0.7:.1f},{t + 2:.1f} '
            f'C{100 + rx * 0.3:.1f},{t - 6:.1f} {100 - rx * 0.3:.1f},{t - 4:.1f} {100 - rx * 0.75:.1f},{t + 10:.1f} Z" fill="{color}"/>'
            f'<path d="M{100 - rx * 0.5:.1f},{t - 4:.1f} Q{100:.1f},{t - 20:.1f} {100 + rx * 0.5:.1f},{t - 8:.1f}" stroke="{lt}" stroke-width="2" fill="none" opacity=".6"/>'
        )
    elif style == "mullet":
        back = f'<path d="M{100 - rx - 2:.1f},{cy:.1f} C{100 - rx - 6:.1f},{cy + 50:.1f} {100 - rx + 6:.1f},{cy + 66:.1f} {100 - rx + 18:.1f},{cy + 70:.1f} L{100 + rx - 18:.1f},{cy + 70:.1f} C{100 + rx - 6:.1f},{cy + 66:.1f} {100 + rx + 6:.1f},{cy + 50:.1f} {100 + rx + 2:.1f},{cy:.1f} Z" fill="{color}"/>'
        front = _cap(h, color, vol=12, hairline=24, part="bangs")
    elif style == "spiky":
        spikes = "".join(
            f'<path d="M{x - 9:.1f},{t + 4:.1f} L{x + 2:.1f},{t - 20 - (i % 2) * 6:.1f} L{x + 10:.1f},{t + 4:.1f} Z" fill="{color}"/>'
            for i, x in enumerate(np.linspace(100 - rx * 0.7, 100 + rx * 0.6, 6))
        )
        front = spikes + _cap(h, color, vol=8, hairline=20)
    elif style == "messy":
        front = _cap(h, color, vol=10, hairline=24, part="bangs") + "".join(
            f'<path d="M{x:.1f},{t - 6:.1f} q{6 * s:.1f},-14 {14 * s:.1f},-8" stroke="{color}" stroke-width="6" fill="none" stroke-linecap="round"/>'
            for x, s in ((100 - rx * 0.4, 1), (100 + rx * 0.1, 1), (100 + rx * 0.4, -1))
        )
    elif style in ("bun", "middle_bun", "bun_top"):
        y = t - 14 if style != "middle_bun" else t - 8
        back = f'<circle cx="100" cy="{y:.1f}" r="17" fill="{color}"/><circle cx="100" cy="{y:.1f}" r="17" fill="none" stroke="{d}" stroke-width="2" stroke-dasharray="5 6"/>'
        front = _cap(h, color, vol=7, hairline=20, part="middle") + shine
    elif style == "low_bun":
        back = f'<ellipse cx="{100 + rx * 0.75:.1f}" cy="{cy + 22:.1f}" rx="15" ry="17" fill="{color}"/>'
        front = _cap(h, color, vol=8, hairline=18, part="middle", sides=14)
    elif style == "updo_curls":
        front = _curls_ring(h, color, d, 14, 11, spread=5) + _cap(h, color, vol=9, hairline=20) + "".join(
            f'<circle cx="{x:.1f}" cy="{t + 10 + abs(x - 100) * 0.15:.1f}" r="8.5" fill="{color}" stroke="{d}" stroke-width="1.2"/>'
            for x in np.linspace(100 - rx * 0.55, 100 + rx * 0.55, 4)
        )
    elif style == "rolls":  # 1950s victory rolls
        front = _cap(h, color, vol=8, hairline=18, part="middle", sides=16) + "".join(
            f'<ellipse cx="{x:.1f}" cy="{t + 6:.1f}" rx="15" ry="11" fill="{color}" stroke="{d}" stroke-width="1.5"/>'
            for x in (100 - rx * 0.45, 100 + rx * 0.45)
        )
        back = f'<path d="M{100 - rx - 4:.1f},{cy:.1f} Q{100 - rx - 10:.1f},{cy + 50:.1f} {100 - rx + 10:.1f},{cy + 56:.1f} L{100 + rx - 10:.1f},{cy + 56:.1f} Q{100 + rx + 10:.1f},{cy + 50:.1f} {100 + rx + 4:.1f},{cy:.1f} Z" fill="{color}"/>'
    elif style == "bob":
        back = f'<path d="M{100 - rx - 6:.1f},{cy - 10:.1f} C{100 - rx - 10:.1f},{cy + 30:.1f} {100 - rx - 4:.1f},{cy + 46:.1f} {100 - rx + 8:.1f},{cy + 48:.1f} L{100 + rx - 8:.1f},{cy + 48:.1f} C{100 + rx + 4:.1f},{cy + 46:.1f} {100 + rx + 10:.1f},{cy + 30:.1f} {100 + rx + 6:.1f},{cy - 10:.1f} Z" fill="{color}"/>'
        front = _cap(h, color, vol=10, hairline=24, part=_pick(rng, ["bangs", "left", "right"]), sides=18)
    elif style in ("long_straight", "wavy_long"):
        if style == "wavy_long":
            back = f'<path d="M{100 - rx - 6:.1f},{cy - 10:.1f} C{100 - rx - 22:.1f},{cy + 30:.1f} {100 - rx + 4:.1f},{cy + 60:.1f} {100 - rx - 14:.1f},{cy + 110:.1f} L{100 + rx + 14:.1f},{cy + 110:.1f} C{100 + rx - 4:.1f},{cy + 60:.1f} {100 + rx + 22:.1f},{cy + 30:.1f} {100 + rx + 6:.1f},{cy - 10:.1f} Z" fill="{color}"/>'
        else:
            back = f'<path d="M{100 - rx - 5:.1f},{cy - 12:.1f} C{100 - rx - 9:.1f},{cy + 40:.1f} {100 - rx - 10:.1f},{cy + 90:.1f} {100 - rx - 8:.1f},{cy + 115:.1f} L{100 + rx + 8:.1f},{cy + 115:.1f} C{100 + rx + 10:.1f},{cy + 90:.1f} {100 + rx + 9:.1f},{cy + 40:.1f} {100 + rx + 5:.1f},{cy - 12:.1f} Z" fill="{color}"/>'
        front = _cap(h, color, vol=8, hairline=22, part=_pick(rng, ["middle", "left", "right"]), sides=22) + shine
    elif style == "ponytail":
        back = f'<path d="M{100 + rx * 0.6:.1f},{t + 6:.1f} C{100 + rx + 30:.1f},{t + 10:.1f} {100 + rx + 18:.1f},{cy + 50:.1f} {100 + rx + 26:.1f},{cy + 70:.1f} C{100 + rx + 4:.1f},{cy + 50:.1f} {100 + rx + 6:.1f},{t + 34:.1f} {100 + rx * 0.4:.1f},{t + 16:.1f} Z" fill="{color}"/>'
        front = _cap(h, color, vol=6, hairline=18, part="left") + shine + f'<circle cx="{100 + rx * 0.82:.1f}" cy="{t + 10:.1f}" r="4" fill="{_pick(rng, ["#e0525e", "#3b5bdb", "#f2a541"])}"/>'
    elif style == "big_curly":
        back = f'<circle cx="100" cy="{cy - 4:.1f}" r="{rx + 30:.1f}" fill="{color}"/>' + _curls_ring(h, color, d, 13, 14, spread=24, y_from=8)
        front = _cap(h, color, vol=10, hairline=22) + "".join(
            f'<circle cx="{x:.1f}" cy="{t + 8 + abs(x - 100) * 0.2:.1f}" r="9" fill="{color}" stroke="{d}" stroke-width="1.2"/>'
            for x in np.linspace(100 - rx * 0.65, 100 + rx * 0.65, 5)
        )
    elif style == "pixie":
        front = _cap(h, color, vol=7, hairline=24, part="left", sides=8) + shine
    else:
        front = _cap(h, color)
    return back, front, style


# ---------------------------------------------------------------- hats
COVERING_HATS = {"top_hat", "bowler", "flat_cap", "fedora", "beret", "headscarf", "pillbox", "flower_hat", "cap", "beanie"}
TALL_HAIR = {"spiky", "pompadour", "bun", "bun_top", "middle_bun", "big_curly", "updo_curls", "messy", "rolls"}

def _hat(h: Head, gen: str, sex: str, rng: np.random.Generator, style: str = "") -> str:
    t = h.top
    rx = h.rx
    options = {
        ("great_grandparent", "M"): [("top_hat", .14), ("bowler", .14), ("flat_cap", .12), (None, .60)],
        ("great_grandparent", "F"): [("flower_hat", .22), ("ribbon", .18), (None, .60)],
        ("grandparent", "M"): [("fedora", .2), ("beret", .14), ("flat_cap", .1), (None, .56)],
        ("grandparent", "F"): [("headscarf", .16), ("pillbox", .12), ("flower_clip", .14), (None, .58)],
        ("parent", "M"): [("headband", .15), ("cap", .12), (None, .73)],
        ("parent", "F"): [("headband", .18), ("big_bow", .16), (None, .66)],
        ("self", "M"): [("beanie", .16), ("cap", .14), (None, .70)],
        ("self", "F"): [("beanie", .14), ("hair_clip", .18), (None, .68)],
    }[(gen, sex)]
    names = [o[0] for o in options]
    kind = names[int(rng.choice(len(names), p=[o[1] for o in options]))]
    if kind in COVERING_HATS and style in TALL_HAIR:
        return ""  # a hat on top of a bun or a pompadour looks odd
    if kind is None:
        return ""
    c = _pick(rng, ["#2b2b33", "#5e3550", "#3d4f6b", "#6b4a2b", "#8c2f39", "#2f5d4a"])
    cl = _shade(c, 1.35)
    if kind == "top_hat":
        return (f'<rect x="{100 - rx * 0.6:.1f}" y="{t - 32:.1f}" width="{rx * 1.2:.1f}" height="34" rx="3" fill="{c}"/>'
                f'<rect x="{100 - rx * 0.62:.1f}" y="{t - 8:.1f}" width="{rx * 1.24:.1f}" height="7" fill="{cl}"/>'
                f'<ellipse cx="100" cy="{t + 2:.1f}" rx="{rx + 14:.1f}" ry="7" fill="{c}"/>')
    if kind == "bowler":
        return (f'<path d="M{100 - rx * 0.78:.1f},{t + 4:.1f} C{100 - rx * 0.78:.1f},{t - 36:.1f} {100 + rx * 0.78:.1f},{t - 36:.1f} {100 + rx * 0.78:.1f},{t + 4:.1f} Z" fill="{c}"/>'
                f'<rect x="{100 - rx * 0.78:.1f}" y="{t - 4:.1f}" width="{rx * 1.56:.1f}" height="6" fill="{cl}"/>'
                f'<ellipse cx="100" cy="{t + 5:.1f}" rx="{rx + 10:.1f}" ry="6" fill="{c}"/>')
    if kind == "flat_cap":
        return (f'<path d="M{100 - rx - 4:.1f},{t + 16:.1f} C{100 - rx - 6:.1f},{t - 22:.1f} {100 + rx + 6:.1f},{t - 26:.1f} {100 + rx + 10:.1f},{t + 8:.1f} '
                f'C{100 + rx + 4:.1f},{t + 16:.1f} {100:.1f},{t + 10:.1f} {100 - rx - 4:.1f},{t + 16:.1f} Z" fill="{c}"/>'
                f'<path d="M{100 - rx * 0.2:.1f},{t + 12:.1f} Q{100 + rx * 0.6:.1f},{t + 20:.1f} {100 + rx + 12:.1f},{t + 12:.1f}" stroke="{cl}" stroke-width="5" fill="none" stroke-linecap="round"/>')
    if kind == "fedora":
        return (f'<path d="M{100 - rx * 0.75:.1f},{t + 4:.1f} C{100 - rx * 0.8:.1f},{t - 30:.1f} {100 - rx * 0.2:.1f},{t - 34:.1f} 100,{t - 24:.1f} '
                f'C{100 + rx * 0.2:.1f},{t - 34:.1f} {100 + rx * 0.8:.1f},{t - 30:.1f} {100 + rx * 0.75:.1f},{t + 4:.1f} Z" fill="{c}"/>'
                f'<rect x="{100 - rx * 0.76:.1f}" y="{t - 6:.1f}" width="{rx * 1.52:.1f}" height="7" fill="#2b2220" opacity=".7"/>'
                f'<path d="M{100 - rx - 18:.1f},{t + 6:.1f} Q100,{t - 4:.1f} {100 + rx + 18:.1f},{t + 6:.1f} Q100,{t + 12:.1f} {100 - rx - 18:.1f},{t + 6:.1f} Z" fill="{c}"/>')
    if kind == "beret":
        return (f'<ellipse cx="{100 - 6:.1f}" cy="{t - 2:.1f}" rx="{rx + 8:.1f}" ry="15" fill="{c}" transform="rotate(-8 100 {t:.1f})"/>'
                f'<circle cx="{100 + 2:.1f}" cy="{t - 17:.1f}" r="3" fill="{c}"/>')
    if kind == "headscarf":
        return (f'<path d="M{100 - rx - 6:.1f},{h.cy + 10:.1f} C{100 - rx - 10:.1f},{t - 20:.1f} {100 + rx + 10:.1f},{t - 20:.1f} {100 + rx + 6:.1f},{h.cy + 10:.1f} '
                f'C{100 + rx - 2:.1f},{t + 20:.1f} {100 - rx + 2:.1f},{t + 20:.1f} {100 - rx - 6:.1f},{h.cy + 10:.1f} Z" fill="{c}"/>'
                + "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="#fbf7ee" opacity=".8"/>'
                          for x, y in ((100 - 20, t - 2), (100 + 6, t - 8), (100 + 26, t + 2), (100 - 34, t + 14), (100 + 36, t + 18)))
                + f'<path d="M{100 + rx * 0.2:.1f},{h.chin + 2:.1f} l-6,12 l12,0 Z" fill="{c}"/>')
    if kind == "pillbox":
        return f'<rect x="{100 - 22:.1f}" y="{t - 18:.1f}" width="44" height="18" rx="5" fill="{c}"/><rect x="{100 - 22:.1f}" y="{t - 4:.1f}" width="44" height="4" fill="{cl}"/>'
    if kind == "flower_hat":
        return (f'<ellipse cx="100" cy="{t - 2:.1f}" rx="{rx + 22:.1f}" ry="11" fill="{c}"/>'
                f'<path d="M{100 - rx * 0.6:.1f},{t - 4:.1f} C{100 - rx * 0.6:.1f},{t - 30:.1f} {100 + rx * 0.6:.1f},{t - 30:.1f} {100 + rx * 0.6:.1f},{t - 4:.1f} Z" fill="{c}"/>'
                + "".join(f'<circle cx="{100 + rx * 0.45 + dx:.1f}" cy="{t - 12 + dy:.1f}" r="5" fill="{fc}"/>'
                          for dx, dy, fc in ((0, 0, "#f2a541"), (8, 4, "#e0525e"), (-6, 6, "#fbf7ee")))
                + f'<circle cx="{100 + rx * 0.45 + 1:.1f}" cy="{t - 9:.1f}" r="2.5" fill="#6b4a2b"/>')
    if kind == "ribbon":
        return (f'<path d="M{100 - 14:.1f},{t - 10:.1f} l-14,-8 l0,16 Z M{100 + 14:.1f},{t - 10:.1f} l14,-8 l0,16 Z" fill="{c}"/>'
                f'<circle cx="100" cy="{t - 10:.1f}" r="5" fill="{cl}"/>')
    if kind in ("flower_clip", "hair_clip"):
        x = 100 + rx * 0.62
        if kind == "hair_clip":
            return f'<rect x="{x - 10:.1f}" y="{t + 10:.1f}" width="20" height="6" rx="3" fill="{_pick(rng, ["#f2a541", "#e0525e", "#3b5bdb"])}" transform="rotate(-25 {x:.1f} {t + 13:.1f})"/>'
        return "".join(f'<circle cx="{x + dx:.1f}" cy="{t + 12 + dy:.1f}" r="5.5" fill="#f6f1e7"/>' for dx, dy in ((0, -6), (6, 0), (0, 6), (-6, 0))) + f'<circle cx="{x:.1f}" cy="{t + 12:.1f}" r="4" fill="#f2a541"/>'
    if kind == "headband":
        return f'<path d="M{100 - rx - 1:.1f},{t + 24:.1f} Q100,{t - 2:.1f} {100 + rx + 1:.1f},{t + 24:.1f}" stroke="{_pick(rng, ["#ea5a9a", "#3fb6c2", "#f6d34a"])}" stroke-width="9" fill="none"/>'
    if kind == "big_bow":
        bc = _pick(rng, ["#ea5a9a", "#7d4cdb", "#3fb6c2"])
        return f'<path d="M100,{t - 2:.1f} l-20,-12 l0,22 Z M100,{t - 2:.1f} l20,-12 l0,22 Z" fill="{bc}"/><circle cx="100" cy="{t - 2:.1f}" r="6" fill="{_shade(bc, 0.8)}"/>'
    if kind == "cap":
        return (f'<path d="M{100 - rx - 3:.1f},{t + 18:.1f} C{100 - rx - 4:.1f},{t - 24:.1f} {100 + rx + 4:.1f},{t - 24:.1f} {100 + rx + 3:.1f},{t + 18:.1f} Z" fill="{c}"/>'
                f'<path d="M{100 - rx * 0.2:.1f},{t + 14:.1f} Q{100 + rx * 0.7:.1f},{t + 10:.1f} {100 + rx + 26:.1f},{t + 20:.1f} L{100 + rx + 22:.1f},{t + 24:.1f} Q{100 + rx * 0.6:.1f},{t + 18:.1f} {100 - rx * 0.2:.1f},{t + 20:.1f} Z" fill="{_shade(c, 0.8)}"/>'
                f'<circle cx="100" cy="{t - 12:.1f}" r="3" fill="{cl}"/>')
    if kind == "beanie":
        return (f'<path d="M{100 - rx - 4:.1f},{t + 20:.1f} C{100 - rx - 4:.1f},{t - 28:.1f} {100 + rx + 4:.1f},{t - 28:.1f} {100 + rx + 4:.1f},{t + 20:.1f} Z" fill="{c}"/>'
                f'<rect x="{100 - rx - 5:.1f}" y="{t + 10:.1f}" width="{2 * rx + 10:.1f}" height="12" rx="5" fill="{cl}"/>'
                + "".join(f'<path d="M{x:.1f},{t + 11:.1f} v10" stroke="{c}" stroke-width="1.5" opacity=".5"/>' for x in np.arange(100 - rx, 100 + rx + 1, 7))
                + f'<circle cx="100" cy="{t - 20:.1f}" r="8" fill="{cl}"/>')
    return ""


# ---------------------------------------------------------------- clothes
SHOULDERS = "M24,260 C26,198 60,178 100,176 C140,178 174,198 176,260 Z"
WIDE_SHOULDERS = "M10,260 C10,196 50,176 100,174 C150,176 190,196 190,260 Z"


def _clothes(gen: str, sex: str, rng: np.random.Generator) -> str:
    c = _pick(rng, OUTFIT[gen])
    dk, lt = _shade(c, 0.78), _shade(c, 1.3)
    acc = _pick(rng, ["#b23b3b", "#2c4f8a", "#d9a441", "#2f6a4e", "#5e3550"])
    shirt = _pick(rng, ["#f4f1e8", "#eaf0f6", "#f6eee0"])

    if gen == "great_grandparent" and sex == "M":
        style = _pick(rng, ["bowtie", "tie", "vest", "uniform"])
        base = (f'<path d="{SHOULDERS}" fill="{c}"/><path d="M80,176 L100,232 L120,176 Z" fill="{shirt}"/>'
                f'<path d="M80,176 L94,250 L60,250 L58,190 Z" fill="{lt}"/><path d="M120,176 L106,250 L140,250 L142,190 Z" fill="{lt}"/>'
                f'<rect x="84" y="158" width="32" height="22" rx="4" fill="{shirt}" stroke="#d8d2c2"/>')
        if style == "bowtie":
            return base + f'<path d="M100,186 L86,178 L86,194 Z M100,186 L114,178 L114,194 Z" fill="{_pick(rng, ["#1b1b22", acc])}"/><circle cx="100" cy="186" r="3.5" fill="#1b1b22"/>'
        if style == "tie":
            return base + f'<path d="M96,180 L104,180 L107,222 L100,232 L93,222 Z" fill="{acc}"/>'
        if style == "vest":
            return (base + f'<path d="M84,184 L100,232 L116,184 L122,250 L78,250 Z" fill="{dk}"/>'
                    + "".join(f'<circle cx="100" cy="{y}" r="2" fill="#d9b25c"/>' for y in (206, 218, 230))
                    + '<path d="M86,214 Q96,224 108,216" stroke="#d9b25c" stroke-width="1.5" fill="none"/>'
                    f'<path d="M96,180 L104,180 L102,190 L98,190 Z" fill="{acc}"/>')
        return (f'<path d="{SHOULDERS}" fill="{c}"/><rect x="84" y="160" width="32" height="24" fill="{c}"/>'
                f'<path d="M84,170 H116" stroke="#d9b25c" stroke-width="3"/>'
                + "".join(f'<circle cx="100" cy="{y}" r="3" fill="#d9b25c"/>' for y in (196, 212, 228, 244))
                + '<path d="M40,196 L64,188 M160,196 L136,188" stroke="#d9b25c" stroke-width="6" stroke-linecap="round"/>')
    if gen == "great_grandparent":
        style = _pick(rng, ["cameo", "lace", "shawl"])
        if style == "cameo":
            lace = "".join(f'<circle cx="{x}" cy="176" r="5" fill="#fbf7ee"/>' for x in range(82, 122, 6))
            return (f'<path d="{SHOULDERS}" fill="{c}"/><rect x="84" y="148" width="32" height="30" rx="6" fill="#fbf7ee"/>{lace}'
                    f'<ellipse cx="100" cy="196" rx="8" ry="10" fill="#e9c86f"/><ellipse cx="100" cy="196" rx="5" ry="7" fill="#f3e2d0"/>')
        if style == "lace":
            ruffles = "".join(f'<path d="M{60 + i * 10},{186 + abs(i - 4) * 2} q5,6 10,0" stroke="#fbf7ee" stroke-width="2" fill="none"/>' for i in range(9))
            return (f'<path d="{SHOULDERS}" fill="{c}"/><path d="M80,170 Q100,200 120,170 L120,180 Q100,212 80,180 Z" fill="#fbf7ee"/>{ruffles}'
                    f'<circle cx="100" cy="196" r="3" fill="{acc}"/>')
        return (f'<path d="{SHOULDERS}" fill="{c}"/><rect x="86" y="152" width="28" height="26" rx="6" fill="#fbf7ee"/>'
                f'<path d="M24,260 C30,200 64,182 100,206 C136,182 170,200 176,260 Z" fill="{acc}" opacity=".9"/>'
                + "".join(f'<path d="M{x},{200 + abs(x - 100) * 0.1:.0f} l0,12" stroke="{_shade(acc, 0.7)}" stroke-width="2"/>' for x in range(40, 170, 12)))

    if gen == "grandparent" and sex == "M":
        style = _pick(rng, ["suit", "sweater_vest", "cardigan", "polo"])
        if style == "suit":
            return (f'<path d="{SHOULDERS}" fill="{c}"/><path d="M82,176 L100,214 L118,176 Z" fill="{shirt}"/>'
                    f'<path d="M96,180 L104,180 L107,222 L100,232 L93,222 Z" fill="{acc}"/>'
                    f'<path d="M82,176 L98,240 L66,250 L60,190 Z" fill="{lt}"/><path d="M118,176 L102,240 L134,250 L140,190 Z" fill="{lt}"/>')
        if style == "sweater_vest":
            argyle = "".join(f'<path d="M{x},{214} l8,-10 l8,10 l-8,10 Z" fill="{lt}" opacity=".8"/>' for x in range(52, 150, 16))
            return (f'<path d="{SHOULDERS}" fill="{shirt}"/><path d="M48,260 C52,210 70,190 84,180 L100,210 L116,180 C130,190 148,210 152,260 Z" fill="{c}"/>{argyle}'
                    f'<path d="M84,176 L92,190 L100,180 L108,190 L116,176" fill="{shirt}" stroke="#d8d2c2"/>')
        if style == "cardigan":
            return (f'<path d="{SHOULDERS}" fill="{c}"/><path d="M90,176 L100,250 L110,176 Z" fill="{shirt}"/>'
                    + "".join(f'<circle cx="112" cy="{y}" r="2.6" fill="{dk}"/>' for y in (200, 216, 232, 248))
                    + f'<path d="M30,230 h40 M130,230 h40" stroke="{dk}" stroke-width="3" opacity=".5"/>')
        return (f'<path d="{SHOULDERS}" fill="{c}"/><path d="M84,176 L100,194 L116,176 L118,186 L100,204 L82,186 Z" fill="{lt}"/>'
                + "".join(f'<circle cx="100" cy="{y}" r="2" fill="{dk}"/>' for y in (206, 216)))
    if gen == "grandparent":
        style = _pick(rng, ["pearls", "collar", "polka"])
        if style == "pearls":
            pearls = "".join(f'<circle cx="{100 + 22 * np.sin(a):.1f}" cy="{176 + 12 * np.cos(a):.1f}" r="2.6" fill="#fffaf0" stroke="#d9cfbf" stroke-width="0.6"/>' for a in np.linspace(-1.3, 1.3, 11))
            return (f'<path d="{SHOULDERS}" fill="{c}"/><path d="M72,182 Q86,204 100,184 Q114,204 128,182 Q114,176 100,178 Q86,176 72,182 Z" fill="#ffffff"/>{pearls}')
        if style == "collar":
            return (f'<path d="{SHOULDERS}" fill="{c}"/><path d="M76,178 Q88,200 100,182 Q112,200 124,178 Q112,172 100,176 Q88,172 76,178 Z" fill="{shirt}"/>'
                    f'<path d="M96,184 h8 l-4,6 Z" fill="{acc}"/>')
        dots = "".join(f'<circle cx="{x}" cy="{y}" r="3" fill="#fbf7ee" opacity=".9"/>' for x in range(40, 170, 14) for y in range(194, 260, 14) if (x + y) % 28 < 14)
        return f'<path d="{SHOULDERS}" fill="{c}"/>{dots}<path d="M84,178 Q100,196 116,178" stroke="{dk}" stroke-width="4" fill="none"/>'

    if gen == "parent" and sex == "M":
        style = _pick(rng, ["zigzag", "denim", "track"])
        if style == "zigzag":
            zig = "M24,206 L44,196 L64,206 L84,196 L104,206 L124,196 L144,206 L164,196 L176,202 L176,220 L164,214 L144,224 L124,214 L104,224 L84,214 L64,224 L44,214 L24,224 Z"
            return (f'<path d="{SHOULDERS}" fill="{c}"/><path d="{zig}" fill="{acc}"/>'
                    f'<path d="M28,232 H172" stroke="#f6d34a" stroke-width="6"/><path d="M84,176 Q100,190 116,176" fill="none" stroke="{dk}" stroke-width="7"/>')
        if style == "denim":
            return (f'<path d="{SHOULDERS}" fill="#4a6fa5"/><path d="M84,176 L100,200 L116,176 Z" fill="{c}"/>'
                    '<path d="M100,200 V250" stroke="#2f4f80" stroke-width="2" stroke-dasharray="4 3"/>'
                    '<rect x="62" y="208" width="22" height="16" rx="2" fill="none" stroke="#f2c14e" stroke-width="1.5"/>'
                    '<rect x="116" y="208" width="22" height="16" rx="2" fill="none" stroke="#f2c14e" stroke-width="1.5"/>')
        return (f'<path d="{SHOULDERS}" fill="{c}"/><path d="M40,200 L64,250 M160,200 L136,250" stroke="#ffffff" stroke-width="5"/>'
                f'<path d="M100,180 V250" stroke="{dk}" stroke-width="3"/><path d="M84,174 Q100,186 116,174 L116,182 Q100,194 84,182 Z" fill="{dk}"/>')
    if gen == "parent":
        style = _pick(rng, ["blazer", "stripes", "neon"])
        if style == "blazer":
            return (f'<path d="{WIDE_SHOULDERS}" fill="{c}"/><path d="M86,176 L100,206 L114,176 Z" fill="{acc}"/>'
                    f'<path d="M86,176 L98,250 L70,250 L62,186 Z" fill="{dk}"/><path d="M114,176 L102,250 L130,250 L138,186 Z" fill="{dk}"/>')
        if style == "stripes":
            stripes = "".join(f'<path d="M20,{y} H180" stroke="{lt}" stroke-width="5"/>' for y in range(196, 260, 14))
            return f'<path d="{SHOULDERS}" fill="{c}"/>{stripes}<path d="M84,178 Q100,192 116,178" stroke="{dk}" stroke-width="5" fill="none"/>'
        return (f'<path d="{WIDE_SHOULDERS}" fill="{c}"/><path d="M60,200 L140,250 M140,200 L60,250" stroke="{lt}" stroke-width="8" opacity=".6"/>'
                f'<path d="M80,176 Q100,198 120,176" stroke="{dk}" stroke-width="5" fill="none"/>')

    style = _pick(rng, ["hoodie", "tshirt", "shirt", "sweater"])
    if style == "hoodie":
        return (f'<path d="M58,184 Q100,160 142,184 Q100,200 58,184 Z" fill="{dk}"/><path d="{SHOULDERS}" fill="{c}"/>'
                f'<path d="M82,178 Q100,194 118,178" fill="none" stroke="{dk}" stroke-width="6"/>'
                '<path d="M92,190 V214 M108,190 V214" stroke="#f2efe6" stroke-width="2.5" stroke-linecap="round"/>'
                f'<path d="M70,228 H130 V250 H70 Z" fill="{dk}" opacity=".35"/>')
    if style == "tshirt":
        logo = _pick(rng, [
            f'<circle cx="100" cy="220" r="12" fill="none" stroke="{lt}" stroke-width="4"/>',
            f'<path d="M86,228 L100,206 L114,228 Z" fill="{lt}"/>',
            f'<path d="M100,230 C80,214 90,202 100,212 C110,202 120,214 100,230 Z" fill="{lt}"/>',
        ])
        return f'<path d="{SHOULDERS}" fill="{c}"/><path d="M84,177 Q100,192 116,177" fill="none" stroke="{dk}" stroke-width="5"/>{logo}'
    if style == "shirt":
        return (f'<path d="{SHOULDERS}" fill="{c}"/><path d="M86,176 L100,196 L114,176 L118,188 L100,204 L82,188 Z" fill="{shirt}"/>'
                f'<path d="M100,204 V250" stroke="{dk}" stroke-width="2"/>'
                + "".join(f'<circle cx="104" cy="{y}" r="1.8" fill="{dk}"/>' for y in (214, 228, 242)))
    return (f'<path d="{SHOULDERS}" fill="{c}"/><path d="M84,177 Q100,192 116,177" fill="none" stroke="{dk}" stroke-width="7"/>'
            + "".join(f'<path d="M{x},200 v50" stroke="{dk}" stroke-width="2" opacity=".35"/>' for x in range(46, 160, 10)))


# ---------------------------------------------------------------- face
def _eyes(h: Head, iris: str, skin: str, mood: str, rng: np.random.Generator, spacing: float, size: float) -> str:
    y = h.cy - 2
    skin_dark = _shade(skin, 0.82)
    out = []
    for side in (-1, 1):
        ex = 100 + side * spacing
        out += [
            f'<ellipse cx="{ex:.1f}" cy="{y:.1f}" rx="{size:.1f}" ry="{size * 1.12:.1f}" fill="#ffffff" stroke="{skin_dark}" stroke-width="1"/>',
            f'<circle cx="{ex:.1f}" cy="{y + 2:.1f}" r="{size * 0.68:.1f}" fill="{iris}"/>',
            f'<circle cx="{ex:.1f}" cy="{y + 2:.1f}" r="{size * 0.31:.1f}" fill="#161616"/>',
            f'<circle cx="{ex + 2.5:.1f}" cy="{y - 1:.1f}" r="{size * 0.18:.1f}" fill="#ffffff"/>',
        ]
        if mood == "happy":  # smiling eyes: lower lid pushes up, iris still visible
            out.append(f'<path d="M{ex - size - 1:.1f},{y + size * 0.9:.1f} Q{ex:.1f},{y + size * 0.1:.1f} {ex + size + 1:.1f},{y + size * 0.9:.1f} L{ex + size + 1:.1f},{y + size * 1.3:.1f} L{ex - size - 1:.1f},{y + size * 1.3:.1f} Z" fill="{skin}"/>')
        elif mood in ("sad", "sick"):  # heavy upper lid
            out.append(f'<path d="M{ex - size - 1:.1f},{y - size * 1.3:.1f} L{ex + size + 1:.1f},{y - size * 1.3:.1f} L{ex + size + 1:.1f},{y - size * 0.15 + side * 1.5:.1f} Q{ex:.1f},{y - size * 0.6:.1f} {ex - size - 1:.1f},{y - size * 0.15 - side * 1.5:.1f} Z" fill="{skin}"/>'
                       f'<path d="M{ex - size:.1f},{y - size * 0.15 - side * 1.5:.1f} Q{ex:.1f},{y - size * 0.6:.1f} {ex + size:.1f},{y - size * 0.15 + side * 1.5:.1f}" stroke="{skin_dark}" stroke-width="1.5" fill="none"/>')
    return "".join(out)


def _brows(h: Head, color: str, mood: str, rng: np.random.Generator, spacing: float, kind: str) -> str:
    y = h.cy - 18
    width = {"thin": 2.5, "normal": 3.8, "thick": 5.5}[kind]
    out = []
    for side in (-1, 1):
        inner = 100 + side * (spacing - 11)
        outer = 100 + side * (spacing + 12)
        if mood in ("sad", "sick"):
            yi, yo, ctrl = y - 7, y + 1, y - 5
        elif mood == "happy":
            yi, yo, ctrl = y - 3, y - 2, y - 10
        else:
            tilt = float(rng.uniform(-2, 2))
            yi, yo, ctrl = y + tilt, y + 1, y - 6
        out.append(f'<path d="M{inner:.1f},{yi:.1f} Q{(inner + outer) / 2:.1f},{ctrl:.1f} {outer:.1f},{yo:.1f}" '
                   f'stroke="{color}" stroke-width="{width}" fill="none" stroke-linecap="round"/>')
    return "".join(out)


def _nose(h: Head, skin: str, kind: str) -> str:
    y = h.cy + 14
    sd = _shade(skin, 0.8)
    if kind == "button":
        return f'<ellipse cx="100" cy="{y:.1f}" rx="6" ry="5" fill="{sd}"/>'
    if kind == "round":
        return f'<ellipse cx="100" cy="{y:.1f}" rx="9" ry="7.5" fill="{sd}"/><circle cx="96" cy="{y + 3:.1f}" r="1.6" fill="{_shade(skin, 0.6)}"/><circle cx="104" cy="{y + 3:.1f}" r="1.6" fill="{_shade(skin, 0.6)}"/>'
    if kind == "long":
        return (f'<path d="M100,{y - 15:.1f} Q96,{y + 1:.1f} 91,{y + 5:.1f} Q100,{y + 11:.1f} 109,{y + 5:.1f} Q104,{y + 1:.1f} 100,{y - 15:.1f} Z" fill="{sd}"/>'
                f'<path d="M94,{y + 6:.1f} Q100,{y + 9:.1f} 106,{y + 6:.1f}" stroke="{_shade(skin, 0.62)}" stroke-width="1.6" fill="none" stroke-linecap="round"/>')
    return f'<path d="M100,{y - 10:.1f} L93,{y + 5:.1f} Q100,{y + 8:.1f} 107,{y + 5:.1f} Z" fill="{sd}"/>'


def _mouth(h: Head, mood: str, rng: np.random.Generator) -> str:
    y = h.cy + 31
    lip = "#7a3a2a"
    if mood == "happy":
        return (f'<path d="M80,{y - 3:.1f} Q100,{y + 26:.1f} 120,{y - 3:.1f} Z" fill="{lip}"/>'
                f'<path d="M84,{y - 1:.1f} Q100,{y + 5:.1f} 116,{y - 1:.1f} L116,{y - 2:.1f} L84,{y - 2:.1f} Z" fill="#ffffff"/>'
                f'<path d="M90,{y + 12:.1f} Q100,{y + 6:.1f} 110,{y + 12:.1f} Q100,{y + 20:.1f} 90,{y + 12:.1f} Z" fill="#e0525e"/>')
    if mood == "smile":
        return f'<path d="M88,{y:.1f} Q100,{y + 9:.1f} 112,{y:.1f}" stroke="{lip}" stroke-width="3" fill="none" stroke-linecap="round"/>'
    if mood == "sad":
        return f'<path d="M88,{y + 6:.1f} Q100,{y - 4:.1f} 112,{y + 6:.1f}" stroke="{lip}" stroke-width="3" fill="none" stroke-linecap="round"/>'
    if mood == "sick":
        return ""  # the thermometer sits in the mouth
    kind = _pick(rng, ["arc", "closed", "smirk", "teeth"])
    if kind == "arc":
        return f'<path d="M86,{y - 2:.1f} Q100,{y + 10:.1f} 114,{y - 2:.1f}" stroke="{lip}" stroke-width="3" fill="none" stroke-linecap="round"/>'
    if kind == "closed":
        return f'<path d="M90,{y:.1f} Q100,{y + 4:.1f} 110,{y:.1f}" stroke="{lip}" stroke-width="3" fill="none" stroke-linecap="round"/>'
    if kind == "smirk":
        return f'<path d="M89,{y + 2:.1f} Q102,{y + 5:.1f} 113,{y - 3:.1f}" stroke="{lip}" stroke-width="3" fill="none" stroke-linecap="round"/>'
    return (f'<path d="M86,{y - 1:.1f} Q100,{y + 16:.1f} 114,{y - 1:.1f} Z" fill="{lip}"/>'
            f'<path d="M89,{y:.1f} Q100,{y + 4:.1f} 111,{y:.1f}" stroke="#ffffff" stroke-width="3" fill="none"/>')


def _facial_hair(h: Head, gen: str, color: str, rng: np.random.Generator) -> str:
    p_none = {"great_grandparent": 0.3, "grandparent": 0.55, "parent": 0.55, "self": 0.65}[gen]
    if rng.random() < p_none:
        return ""
    y = h.cy + 24
    d = _shade(color, 0.9)
    kinds = {
        "great_grandparent": ["handlebar", "walrus", "full_beard", "chops"],
        "grandparent": ["pencil", "chevron", "goatee"],
        "parent": ["chevron", "walrus", "stubble", "full_beard"],
        "self": ["stubble", "goatee", "full_beard", "chevron"],
    }[gen]
    kind = _pick(rng, kinds)
    if kind == "handlebar":
        return f'<path d="M100,{y:.1f} C90,{y - 8:.1f} 76,{y - 6:.1f} 70,{y + 6:.1f} C78,{y:.1f} 88,{y + 4:.1f} 100,{y + 4:.1f} C112,{y + 4:.1f} 122,{y:.1f} 130,{y + 6:.1f} C124,{y - 6:.1f} 110,{y - 8:.1f} 100,{y:.1f} Z" fill="{d}"/>'
    if kind == "walrus":
        return f'<path d="M82,{y + 4:.1f} Q100,{y - 10:.1f} 118,{y + 4:.1f} L116,{y + 10:.1f} Q100,{y + 4:.1f} 84,{y + 10:.1f} Z" fill="{d}"/>'
    if kind == "chevron":
        return f'<path d="M86,{y + 4:.1f} Q100,{y - 6:.1f} 114,{y + 4:.1f} Q100,{y + 1:.1f} 86,{y + 4:.1f} Z" fill="{d}"/>'
    if kind == "pencil":
        return f'<path d="M88,{y + 3:.1f} Q100,{y - 1:.1f} 112,{y + 3:.1f}" stroke="{d}" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
    if kind == "goatee":
        return (f'<path d="M92,{y + 2:.1f} Q100,{y - 3:.1f} 108,{y + 2:.1f}" stroke="{d}" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
                f'<path d="M93,{h.chin - 12:.1f} Q100,{h.chin - 7:.1f} 107,{h.chin - 12:.1f} Q107,{h.chin + 3:.1f} 100,{h.chin + 4:.1f} Q93,{h.chin + 3:.1f} 93,{h.chin - 12:.1f} Z" fill="{d}"/>')
    if kind == "stubble":
        return "".join(f'<circle cx="{100 + rng.uniform(-28, 28):.1f}" cy="{h.chin - rng.uniform(4, 22):.1f}" r="1" fill="{d}" opacity=".55"/>' for _ in range(42))
    if kind == "chops":
        return "".join(f'<path d="M{100 + s * (h.rx - 3):.1f},{h.cy:.1f} L{100 + s * (h.rx - 2):.1f},{h.cy + 30:.1f} Q{100 + s * (h.rx - 14):.1f},{h.cy + 30:.1f} {100 + s * (h.rx - 16):.1f},{h.cy + 18:.1f} L{100 + s * (h.rx - 10):.1f},{h.cy:.1f} Z" fill="{d}"/>' for s in (-1, 1)) + _facial_hair_simple(y, d)
    # full beard: follows the jaw, leaves the mouth area free
    return (f'<path d="M{100 - h.rx + 2:.1f},{h.cy + 4:.1f} C{100 - h.rx:.1f},{h.cy + h.ry * 0.6:.1f} {100 - h.jaw:.1f},{h.chin + 12:.1f} 100,{h.chin + 14:.1f} '
            f'C{100 + h.jaw:.1f},{h.chin + 12:.1f} {100 + h.rx:.1f},{h.cy + h.ry * 0.6:.1f} {100 + h.rx - 2:.1f},{h.cy + 4:.1f} '
            f'C{100 + h.rx - 8:.1f},{h.cy + 24:.1f} 114,{y + 18:.1f} 100,{y + 18:.1f} C86,{y + 18:.1f} {100 - h.rx + 8:.1f},{h.cy + 24:.1f} {100 - h.rx + 2:.1f},{h.cy + 4:.1f} Z" fill="{d}"/>'
            + _facial_hair_simple(y, d))


def _facial_hair_simple(y: float, d: str) -> str:
    return f'<path d="M86,{y + 4:.1f} Q100,{y - 6:.1f} 114,{y + 4:.1f} Q100,{y + 1:.1f} 86,{y + 4:.1f} Z" fill="{d}"/>'


def _glasses(h: Head, gen: str, rng: np.random.Generator, spacing: float) -> str:
    if rng.random() > {"great_grandparent": 0.14, "grandparent": 0.22, "parent": 0.2, "self": 0.18}[gen]:
        return ""
    y = h.cy - 1
    color = _pick(rng, ["#2b2220", "#8a6420", "#5e3550", "#3d4f6b"])
    kind = "round" if gen == "great_grandparent" else _pick(rng, ["round", "square", "cat"])
    out = []
    for side in (-1, 1):
        ex = 100 + side * spacing
        if kind == "square":
            out.append(f'<rect x="{ex - 14:.1f}" y="{y - 11:.1f}" width="28" height="22" rx="5" fill="#ffffff" fill-opacity=".12" stroke="{color}" stroke-width="3"/>')
        elif kind == "cat":
            o, i = ex + side * 15, ex - side * 13  # outer corner flicks up
            out.append(f'<path d="M{i:.1f},{y - 7:.1f} Q{ex:.1f},{y - 12:.1f} {o:.1f},{y - 11:.1f} Q{ex + side * 13:.1f},{y + 11:.1f} {ex:.1f},{y + 10:.1f} Q{i:.1f},{y + 9:.1f} {i:.1f},{y - 7:.1f} Z" fill="#ffffff" fill-opacity=".12" stroke="{color}" stroke-width="3"/>')
        else:
            out.append(f'<circle cx="{ex:.1f}" cy="{y:.1f}" r="13" fill="#ffffff" fill-opacity=".12" stroke="{color}" stroke-width="2.5"/>')
        out.append(f'<path d="M{ex + side * 13:.1f},{y - 2:.1f} L{100 + side * (h.rx - 1):.1f},{y - 4:.1f}" stroke="{color}" stroke-width="2.5"/>')
    out.append(f'<path d="M{100 - spacing + 13:.1f},{y - 2:.1f} Q100,{y - 7:.1f} {100 + spacing - 13:.1f},{y - 2:.1f}" stroke="{color}" stroke-width="2.5" fill="none"/>')
    return "".join(out)


def _sick_overlay(h: Head) -> str:
    """Pale face, a drop of sweat and a thermometer: bulb in the mouth,
    glass stick pointing out and slightly down."""
    y = h.cy + 31
    return (
        f'<ellipse cx="104" cy="{y:.1f}" rx="7" ry="6" fill="#5a2a22"/>'
        f'<path d="M106,{y - 1:.1f} L152,{y + 14:.1f}" stroke="#9aa3ad" stroke-width="9" stroke-linecap="round"/>'
        f'<path d="M106,{y - 1:.1f} L152,{y + 14:.1f}" stroke="#f4f7fa" stroke-width="6" stroke-linecap="round"/>'
        f'<path d="M108,{y:.1f} L132,{y + 7.6:.1f}" stroke="#d83a3a" stroke-width="2.6" stroke-linecap="round"/>'
        + "".join(f'<path d="M{x:.1f},{y + (x - 106) * 0.326 - 4:.1f} l1.4,-3" stroke="#6b7480" stroke-width="1"/>' for x in range(124, 150, 6))
        + f'<circle cx="106" cy="{y - 1:.1f}" r="4.5" fill="#d83a3a"/>'
        f'<path d="M{100 + h.rx - 8:.1f},{h.cy - 30:.1f} C{100 + h.rx - 14:.1f},{h.cy - 20:.1f} {100 + h.rx - 15:.1f},{h.cy - 14:.1f} {100 + h.rx - 8:.1f},{h.cy - 12:.1f} '
        f'C{100 + h.rx - 1:.1f},{h.cy - 14:.1f} {100 + h.rx - 2:.1f},{h.cy - 20:.1f} {100 + h.rx - 8:.1f},{h.cy - 30:.1f} Z" fill="#7fc7f0" stroke="#3d8fd6" stroke-width="1"/>'
    )


# ---------------------------------------------------------------- public API
def render_unknown(generation: str, size: int | None = 160, label: str = "?", color: str = "#ffffff") -> str:
    """Placeholder portrait for a person not chosen or not yet revealed."""
    bg, frame = _frame(generation)
    cid = f"u{next(_ids)}"
    body = (
        f'<path d="{SHOULDERS}" fill="#000" opacity="0.18"/>'
        '<ellipse cx="100" cy="108" rx="46" ry="52" fill="#000" opacity="0.18"/>'
        f'<text x="100" y="128" text-anchor="middle" font-family="Georgia, Segoe UI Symbol, DejaVu Sans, serif" font-size="64" font-weight="700" fill="{color}" opacity="0.9">{label}</text>'
    )
    dims = f' width="{size}" height="{size * 1.25:.0f}"' if size else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 250"{dims}>'
        f'<defs><clipPath id="{cid}">{_clip(generation)}</clipPath></defs>'
        f'{bg}<g clip-path="url(#{cid})">{body}</g>{frame}</svg>'
    )


def render_avatar(
    look: Look,
    generation: str,
    seed: int = 0,
    size: int | None = 160,
    sick: bool = False,
    mood: str = "neutral",
) -> str:
    """Return an SVG string for a person.

    ``seed`` picks every non-genetic detail, so the same seed always draws
    the same person. ``mood`` is one of MOODS; ``sick=True`` is a shortcut
    for ``mood="sick"``.
    """
    if generation not in GENERATIONS:
        raise ValueError(f"unknown generation: {generation}")
    if sick:
        mood = "sick"
    if mood not in MOODS:
        raise ValueError(f"unknown mood: {mood}")
    # independent streams: changing one feature never reshuffles the others
    ss = np.random.SeedSequence(seed)
    r_face, r_hair, r_hat, r_clothes, r_extra, r_mouth = (np.random.default_rng(s) for s in ss.spawn(6))

    skin = SKIN[look.skin]
    skin_dark = _shade(skin, 0.82)
    hair_color = HAIR[look.hair]
    h = _random_head(r_face)
    spacing = float(r_face.uniform(16.5, 19.5))
    eye_size = float(r_face.uniform(9.5, 11.5))
    nose = _pick(r_face, ["button", "round", "long", "triangle"])
    brow_kind = _pick(r_face, ["thin", "normal", "thick"], p=[0.25, 0.5, 0.25] if look.sex == "M" else [0.45, 0.45, 0.10])

    bg_color = _pick(r_extra, BACKGROUNDS[generation])
    bg, frame = _frame(generation, bg_color)
    hair_back, hair_front, style = _hair(h, generation, look.sex, hair_color, r_hair)
    hat = _hat(h, generation, look.sex, r_hat, style)

    parts = [hair_back, f'<rect x="88" y="{h.chin - 22:.1f}" width="24" height="{200 - h.chin:.1f}" rx="8" fill="{skin_dark}"/>']
    parts.append(_clothes(generation, look.sex, r_clothes))
    for side in (-1, 1):  # ears
        ex = 100 + side * (h.rx - 1)
        parts.append(f'<ellipse cx="{ex:.1f}" cy="{h.cy + 6:.1f}" rx="8" ry="11" fill="{skin}"/>'
                     f'<ellipse cx="{ex + side * 1.5:.1f}" cy="{h.cy + 6:.1f}" rx="3.5" ry="6" fill="{skin_dark}" opacity=".6"/>')
    parts.append(f'<path d="{_head_path(h)}" fill="{skin}"/>')
    if mood == "sick":  # a slightly green, feverish face
        parts.append(f'<path d="{_head_path(h)}" fill="#8fd18a" opacity=".18"/>')
    blush = 0.45 if mood == "happy" else 0.26
    parts.append(f'<ellipse cx="{100 - spacing - 8:.1f}" cy="{h.cy + 20:.1f}" rx="9" ry="6" fill="#e8746a" opacity="{blush}"/>'
                 f'<ellipse cx="{100 + spacing + 8:.1f}" cy="{h.cy + 20:.1f}" rx="9" ry="6" fill="#e8746a" opacity="{blush}"/>')
    if look.freckles:
        for side in (-1, 1):
            for _ in range(8):
                fx = 100 + side * (spacing - 2 + r_extra.uniform(0, 16))
                fy = h.cy + 12 + r_extra.uniform(0, 12)
                parts.append(f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="1.6" fill="#b4663e" opacity="0.75"/>')
    if r_extra.random() < 0.15:  # beauty mark
        parts.append(f'<circle cx="{100 + r_extra.choice([-1, 1]) * r_extra.uniform(20, 30):.1f}" cy="{h.cy + 26:.1f}" r="1.8" fill="#5a3a2a"/>')
    parts.append(_eyes(h, EYES[look.eyes], skin, mood, r_face, spacing, eye_size))
    parts.append(_brows(h, _shade(hair_color, 0.8), mood, r_face, spacing, brow_kind))
    parts.append(_nose(h, skin, nose))
    if look.sex == "M":
        parts.append(_facial_hair(h, generation, hair_color, r_extra))
    parts.append(_mouth(h, mood, r_mouth))
    parts.append(hair_front)
    if style == "receding":
        scalp = f'<path d="M{100 - h.rx * 0.62:.1f},{h.top + 14:.1f} C{100 - h.rx * 0.6:.1f},{h.top - 3:.1f} {100 + h.rx * 0.6:.1f},{h.top - 3:.1f} {100 + h.rx * 0.62:.1f},{h.top + 14:.1f} Z" fill="{skin}"/>'
        parts[-1] = parts[-1].replace("<!--crown-->", scalp)
    parts.append(hat)
    parts.append(_glasses(h, generation, r_extra, spacing))
    if look.sex == "F" and r_extra.random() < 0.55:
        earring = _pick(r_extra, ["pearl", "hoop", "drop"])
        color = _pick(r_extra, ["#f2c14e", "#fffaf0", "#c0c6cc"])
        for side in (-1, 1):
            ex, ey = 100 + side * (h.rx - 1), h.cy + 18
            if earring == "hoop":
                parts.append(f'<circle cx="{ex:.1f}" cy="{ey + 4:.1f}" r="6" fill="none" stroke="{color}" stroke-width="2.5"/>')
            elif earring == "drop":
                parts.append(f'<path d="M{ex:.1f},{ey:.1f} l-3,9 l3,4 l3,-4 Z" fill="{color}"/>')
            else:
                parts.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="3.2" fill="{color}"/>')
    if mood == "sick":
        parts.append(_sick_overlay(h))
    if mood == "happy":  # a couple of sparkles
        parts.append("".join(f'<path d="M{x},{y} l2,-6 l2,6 l6,2 l-6,2 l-2,6 l-2,-6 l-6,-2 Z" fill="#f6d34a"/>'
                             for x, y in ((40, 60), (152, 74))))

    cid = f"a{next(_ids)}"
    dims = f' width="{size}" height="{size * 1.25:.0f}"' if size else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 250"{dims}>'
        f'<defs><clipPath id="{cid}">{_clip(generation)}</clipPath></defs>'
        f'{bg}<g clip-path="url(#{cid})">{"".join(p for p in parts if p)}</g>{frame}</svg>'
    )
