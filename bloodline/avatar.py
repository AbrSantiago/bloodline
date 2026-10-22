"""Caricature avatars rendered as SVG from a person's visible traits.

Everything is drawn in code: no AI, no image files. The face shows the
inherited traits (eye colour, hair colour, freckles, skin tone); the
generation only changes clothing, hairstyle, frame and background, so the
genetic traits stay readable in every portrait.
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


@dataclass(frozen=True)
class Look:
    """Visible traits of a person (the phenotype, not the genotype)."""

    sex: str  # "F" or "M"
    eyes: str = "brown"
    hair: str = "brown"
    freckles: bool = False
    skin: str = "light"


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


# ---------------------------------------------------------------- frames
def _frame(gen: str) -> tuple[str, str]:
    """Return (background, frame) SVG for the generation's era."""
    if gen == "great_grandparent":  # ~1900: ornate gold frame
        bg = '<rect x="18" y="18" width="164" height="214" fill="#55654a"/>'
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
        bg = '<rect x="16" y="16" width="168" height="218" fill="#a9b9c9"/>'
        frame = (
            '<rect x="6" y="6" width="188" height="238" fill="none" stroke="#7a5232" stroke-width="12"/>'
            '<rect x="14" y="14" width="172" height="222" fill="none" stroke="#a47148" stroke-width="3"/>'
        )
    elif gen == "parent":  # ~1985: instant photo
        bg = '<rect x="14" y="14" width="172" height="192" fill="#f6c6c6"/>'
        frame = (
            '<path d="M0,0 H200 V250 H0 Z M14,14 V206 H186 V14 Z" fill="#fbfaf5" fill-rule="evenodd"/>'
            '<rect x="0.5" y="0.5" width="199" height="249" fill="none" stroke="#d8d4c8"/>'
        )
    else:  # today: rounded "profile picture"
        bg = '<rect x="8" y="8" width="184" height="234" rx="22" fill="#dcebe4"/>'
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


# ---------------------------------------------------------------- clothing
SHOULDERS = "M24,260 C26,198 60,178 100,176 C140,178 174,198 176,260 Z"
WIDE_SHOULDERS = "M10,260 C10,196 50,176 100,174 C150,176 190,196 190,260 Z"


def _clothes(gen: str, sex: str) -> str:
    if gen == "great_grandparent":
        if sex == "M":
            return (
                f'<path d="{SHOULDERS}" fill="#2c2f3a"/>'
                '<path d="M80,176 L100,232 L120,176 Z" fill="#f4f1e8"/>'
                '<path d="M80,176 L94,250 L60,250 L58,190 Z" fill="#3a3e4c"/>'
                '<path d="M120,176 L106,250 L140,250 L142,190 Z" fill="#3a3e4c"/>'
                '<rect x="84" y="158" width="32" height="22" rx="4" fill="#fbf9f2" stroke="#d8d2c2"/>'
                '<path d="M100,186 L86,178 L86,194 Z M100,186 L114,178 L114,194 Z" fill="#1b1b22"/>'
                '<circle cx="100" cy="186" r="3.5" fill="#1b1b22"/>'
            )
        lace = "".join(f'<circle cx="{x}" cy="176" r="5" fill="#fbf7ee"/>' for x in range(82, 122, 6))
        return (
            f'<path d="{SHOULDERS}" fill="#5e3550"/>'
            '<rect x="84" y="148" width="32" height="30" rx="6" fill="#fbf7ee"/>'
            + lace
            + '<ellipse cx="100" cy="196" rx="8" ry="10" fill="#e9c86f"/>'
            '<ellipse cx="100" cy="196" rx="5" ry="7" fill="#f3e2d0"/>'
        )
    if gen == "grandparent":
        if sex == "M":
            return (
                f'<path d="{SHOULDERS}" fill="#5a6474"/>'
                '<path d="M82,176 L100,214 L118,176 Z" fill="#ffffff"/>'
                '<path d="M96,180 L104,180 L107,222 L100,232 L93,222 Z" fill="#b23b3b"/>'
                '<path d="M82,176 L98,240 L66,250 L60,190 Z" fill="#6b7686"/>'
                '<path d="M118,176 L102,240 L134,250 L140,190 Z" fill="#6b7686"/>'
            )
        pearls = "".join(f'<circle cx="{100 + 22 * np.sin(a):.1f}" cy="{176 + 12 * np.cos(a):.1f}" r="2.6" fill="#fffaf0" stroke="#d9cfbf" stroke-width="0.6"/>' for a in np.linspace(-1.3, 1.3, 11))
        return (
            f'<path d="{SHOULDERS}" fill="#3f8a8b"/>'
            '<path d="M72,182 Q86,204 100,184 Q114,204 128,182 Q114,176 100,178 Q86,176 72,182 Z" fill="#ffffff"/>'
            + pearls
        )
    if gen == "parent":
        if sex == "M":
            zig = "M24,206 L44,196 L64,206 L84,196 L104,206 L124,196 L144,206 L164,196 L176,202 L176,220 L164,214 L144,224 L124,214 L104,224 L84,214 L64,224 L44,214 L24,224 Z"
            return (
                f'<path d="{SHOULDERS}" fill="#3fb6c2"/>'
                f'<path d="{zig}" fill="#ea5a9a"/>'
                '<path d="M28,232 H172" stroke="#f6d34a" stroke-width="6"/>'
                '<path d="M84,176 Q100,190 116,176" fill="none" stroke="#2c8f99" stroke-width="7"/>'
            )
        return (
            f'<path d="{WIDE_SHOULDERS}" fill="#7d4cdb"/>'
            '<path d="M86,176 L100,206 L114,176 Z" fill="#f6d34a"/>'
            '<path d="M86,176 L98,250 L70,250 L62,186 Z" fill="#6a3cc4"/>'
            '<path d="M114,176 L102,250 L130,250 L138,186 Z" fill="#6a3cc4"/>'
        )
    # today
    if sex == "M":
        return (
            '<path d="M58,184 Q100,160 142,184 Q100,200 58,184 Z" fill="#2f6a4e"/>'
            f'<path d="{SHOULDERS}" fill="#3a7d5c"/>'
            '<path d="M82,178 Q100,194 118,178" fill="none" stroke="#2f6a4e" stroke-width="6"/>'
            '<path d="M92,190 V214 M108,190 V214" stroke="#f2efe6" stroke-width="2.5" stroke-linecap="round"/>'
        )
    return (
        f'<path d="{SHOULDERS}" fill="#f2a541"/>'
        '<path d="M84,177 Q100,192 116,177" fill="none" stroke="#d98a24" stroke-width="5"/>'
        '<path d="M88,180 Q100,196 112,180" fill="none" stroke="#c9b37a" stroke-width="1.5"/>'
        '<circle cx="100" cy="195" r="3" fill="#c9b37a"/>'
    )


# ---------------------------------------------------------------- hair
def _hair(gen: str, sex: str, color: str) -> tuple[str, str]:
    """Return (back_layer, front_layer) for the era's hairstyle."""
    c = HAIR[color]
    d = _shade(c, 0.75)
    cap = (
        "M53,114 C48,62 78,40 100,40 C122,40 152,62 147,114 "
        "C142,94 134,82 120,78 C106,84 90,83 72,80 C62,88 56,100 53,114 Z"
    )
    if gen == "great_grandparent":
        if sex == "M":  # slicked side part + handlebar moustache
            front = (
                f'<path d="M53,108 C50,60 80,44 102,44 C124,44 150,62 147,108 C142,88 132,74 112,70 C96,70 76,72 64,82 C58,90 55,98 53,108 Z" fill="{c}"/>'
                f'<path d="M84,47 C80,58 78,66 76,74" stroke="{d}" stroke-width="2.5" fill="none"/>'
                f'<path d="M100,132 C90,124 76,126 70,138 C80,132 88,136 100,136 C112,136 120,132 130,138 C124,126 110,124 100,132 Z" fill="{d}"/>'
            )
            return "", front
        back = f'<circle cx="100" cy="36" r="15" fill="{d}"/>'
        front = (
            f'<path d="M50,110 C40,50 72,30 100,32 C128,30 160,50 150,110 C146,86 138,72 122,66 C108,62 92,62 78,66 C62,72 54,86 50,110 Z" fill="{c}"/>'
            f'<path d="M76,46 C86,40 96,40 100,44 M124,46 C114,40 104,40 100,44" stroke="{d}" stroke-width="2.5" fill="none"/>'
        )
        return back, front
    if gen == "grandparent":
        if sex == "M":  # neat pompadour
            front = (
                f'<path d="{cap}" fill="{c}"/>'
                f'<path d="M60,74 C62,44 96,30 124,40 C112,42 104,50 102,62 C90,56 74,62 60,74 Z" fill="{c}"/>'
                f'<path d="M78,52 C90,44 104,42 116,42" stroke="{d}" stroke-width="2.5" fill="none"/>'
            )
            return "", front
        curls = "".join(
            f'<circle cx="{100 + 50 * np.cos(a):.1f}" cy="{102 - 52 * np.sin(a):.1f}" r="15" fill="{c}"/>'
            for a in np.linspace(-0.25, np.pi + 0.25, 11)
        )
        front = curls + f'<path d="{cap}" fill="{c}"/>' + "".join(
            f'<circle cx="{x}" cy="{y}" r="9" fill="{c}" stroke="{d}" stroke-width="1.5"/>'
            for x, y in ((74, 74), (90, 68), (108, 68), (126, 74))
        )
        return "", front
    if gen == "parent":
        if sex == "M":  # fluffy mullet
            back = f'<path d="M56,104 C54,140 60,160 76,166 L124,166 C140,160 146,140 144,104 Z" fill="{c}"/>'
            front = (
                f'<path d="{cap}" fill="{c}"/>'
                f'<path d="M58,82 C56,52 80,34 104,36 C130,34 150,56 142,84 C130,66 112,64 100,70 C88,62 70,66 58,82 Z" fill="{c}"/>'
                f'<path d="M72,60 C84,54 96,56 104,62 M106,56 C116,50 128,54 134,62" stroke="{d}" stroke-width="2.5" fill="none"/>'
            )
            return back, front
        back = f'<circle cx="100" cy="108" r="76" fill="{c}"/><circle cx="100" cy="108" r="76" fill="none" stroke="{d}" stroke-width="2" stroke-dasharray="6 10"/>'
        front = f'<path d="{cap}" fill="{c}"/>' + "".join(
            f'<circle cx="{x}" cy="{y}" r="11" fill="{c}" stroke="{d}" stroke-width="1.5"/>'
            for x, y in ((68, 72), (86, 64), (104, 62), (122, 66), (136, 76))
        )
        return back, front
    # today
    if sex == "M":  # short messy
        spikes = (
            "M53,112 C48,66 70,42 100,40 C130,40 152,62 147,112 C143,94 138,84 130,78 "
            "L134,66 L122,74 L120,60 L108,72 L102,58 L94,72 L84,60 L80,74 L68,68 L70,80 C62,88 56,100 53,112 Z"
        )
        front = f'<path d="{spikes}" fill="{c}"/>' + f'<path d="M58,70 C66,50 84,42 100,42 C118,40 138,50 144,70 C130,56 112,52 100,54 C86,52 70,58 58,70 Z" fill="{c}"/>'
        return "", front
    back = f'<path d="M50,96 C46,140 44,190 48,232 L152,232 C156,190 154,140 150,96 Z" fill="{c}"/>'
    front = (
        f'<path d="M51,118 C44,60 74,38 100,38 C126,38 156,60 149,118 C146,96 140,82 128,74 C112,88 86,92 62,88 C56,96 52,106 51,118 Z" fill="{c}"/>'
        f'<path d="M66,86 C86,86 114,80 128,74" stroke="{d}" stroke-width="2" fill="none"/>'
    )
    return back, front


# ---------------------------------------------------------------- face
def _face(look: Look, rng: np.random.Generator) -> str:
    skin = SKIN[look.skin]
    skin_dark = _shade(skin, 0.82)
    rx = 44 + rng.integers(0, 5)
    ry = 50 + rng.integers(0, 5)
    nose_r = 6 + rng.integers(0, 4)
    iris = EYES[look.eyes]
    brow = _shade(HAIR[look.hair], 0.8)
    parts = [
        f'<rect x="88" y="140" width="24" height="40" rx="8" fill="{skin_dark}"/>',
        f'<circle cx="{100 - rx + 2}" cy="114" r="10" fill="{skin}"/>',
        f'<circle cx="{100 + rx - 2}" cy="114" r="10" fill="{skin}"/>',
        f'<ellipse cx="100" cy="108" rx="{rx}" ry="{ry}" fill="{skin}"/>',
        f'<ellipse cx="72" cy="128" rx="9" ry="6" fill="#e8746a" opacity="0.28"/>',
        f'<ellipse cx="128" cy="128" rx="9" ry="6" fill="#e8746a" opacity="0.28"/>',
    ]
    if look.freckles:
        for side in (-1, 1):
            for _ in range(7):
                fx = 100 + side * (20 + rng.uniform(0, 16))
                fy = 118 + rng.uniform(0, 12)
                parts.append(f'<circle cx="{fx:.1f}" cy="{fy:.1f}" r="1.6" fill="#b4663e" opacity="0.75"/>')
    for ex in (82, 118):
        parts += [
            f'<ellipse cx="{ex}" cy="106" rx="11" ry="12.5" fill="#ffffff" stroke="{skin_dark}" stroke-width="1"/>',
            f'<circle cx="{ex}" cy="108" r="7.5" fill="{iris}"/>',
            f'<circle cx="{ex}" cy="108" r="3.4" fill="#161616"/>',
            f'<circle cx="{ex + 2.5}" cy="105" r="2" fill="#ffffff"/>',
        ]
    tilt = rng.integers(-3, 4)
    parts += [
        f'<path d="M70,{90 + tilt} Q82,{84 + tilt} 93,90" stroke="{brow}" stroke-width="4" fill="none" stroke-linecap="round"/>',
        f'<path d="M107,90 Q118,{84 + tilt} 130,{90 + tilt}" stroke="{brow}" stroke-width="4" fill="none" stroke-linecap="round"/>',
        f'<ellipse cx="100" cy="122" rx="{nose_r}" ry="{nose_r - 1}" fill="{skin_dark}"/>',
    ]
    if rng.random() < 0.5:
        parts.append('<path d="M86,138 Q100,150 114,138" stroke="#7a3a2a" stroke-width="3" fill="none" stroke-linecap="round"/>')
    else:
        parts.append('<path d="M86,137 Q100,154 114,137 Z" fill="#7a3a2a"/><path d="M90,139 Q100,143 110,139" stroke="#ffffff" stroke-width="3" fill="none"/>')
    return "".join(parts)


# ---------------------------------------------------------------- public API
def _sick_overlay() -> str:
    """Thermometer and a drop of sweat: the descendant got a disease."""
    return (
        '<path d="M120,140 L156,126" stroke="#ffffff" stroke-width="7" stroke-linecap="round"/>'
        '<path d="M120,140 L156,126" stroke="#9aa3ad" stroke-width="7" stroke-linecap="round" stroke-opacity="0.35"/>'
        '<path d="M124,138 L140,132" stroke="#d83a3a" stroke-width="3" stroke-linecap="round"/>'
        '<circle cx="121" cy="140" r="5" fill="#d83a3a"/>'
        '<path d="M146,78 C140,88 138,94 146,96 C154,94 152,88 146,78 Z" fill="#7fc7f0" stroke="#3d8fd6" stroke-width="1"/>'
    )


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


def render_avatar(look: Look, generation: str, seed: int = 0, size: int | None = 160, sick: bool = False) -> str:
    """Return an SVG string for a person.

    `seed` only varies cosmetic details (face shape, nose, smile, freckle
    pattern) so two people with the same traits don't look identical.
    """
    if generation not in GENERATIONS:
        raise ValueError(f"unknown generation: {generation}")
    rng = np.random.default_rng(seed)
    bg, frame = _frame(generation)
    hair_back, hair_front = _hair(generation, look.sex, look.hair)
    earrings = ""
    if generation == "parent" and look.sex == "F":
        earrings = '<circle cx="54" cy="128" r="7" fill="none" stroke="#f6d34a" stroke-width="3"/><circle cx="146" cy="128" r="7" fill="none" stroke="#f6d34a" stroke-width="3"/>'
    cid = f"a{next(_ids)}"
    body = hair_back + _clothes(generation, look.sex) + _face(look, rng) + hair_front + earrings
    if sick:
        body += _sick_overlay()
    dims = f' width="{size}" height="{size * 1.25:.0f}"' if size else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 250"{dims}>'
        f'<defs><clipPath id="{cid}">{_clip(generation)}</clipPath></defs>'
        f'{bg}<g clip-path="url(#{cid})">{body}</g>{frame}</svg>'
    )
