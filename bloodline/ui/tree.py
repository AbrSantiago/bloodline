"""Pedigree diagram as a single SVG (portraits + couple lines)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html import escape

PORTRAIT_W = 100
PORTRAIT_H = 125
SPOUSE_GAP = 20
COUPLE_GAP = 30
MARGIN = 16
LABEL_H = 34
ROW_GAP = 46

STATUS_COLORS = {"clear": "#3f9d5a", "carrier": "#e2a72e", "affected": "#d83a3a", "unknown": "#c9c2b6"}


@dataclass
class NodeView:
    svg: str  # portrait from bloodline.avatar
    label: str = ""
    dots: list[str] = field(default_factory=list)  # status names per disease
    highlight: bool = False


def _place(svg: str, x: float, y: float, w: float) -> str:
    """Turn a standalone avatar SVG into a positioned nested <svg>."""
    head, rest = svg.split(">", 1)
    head = re.sub(r'\s(width|height)="[^"]*"', "", head)
    head = head.replace("<svg ", f'<svg x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{w * 1.25:.1f}" ', 1)
    return head + ">" + rest


def pedigree_svg(
    nodes: dict[tuple[int, int], NodeView],
    generations: int,
    spread_width: float | None = None,
    max_width: int = 820,
) -> str:
    """Draw the pedigree. ``nodes`` maps (level, index) to what to show;
    level ``generations`` holds the top row and level 0 is "me".

    With ``spread_width`` the top row is spread evenly over that width and
    gets short lines going up, so the drawing continues a row of couples
    rendered above it (the interactive founders while building)."""
    n_top = 2**generations
    couple_w = 2 * PORTRAIT_W + SPOUSE_GAP
    row_h = PORTRAIT_H + LABEL_H + ROW_GAP
    top_pad = 30 if spread_width else 0
    if spread_width:
        width = spread_width
        tops = [MARGIN + (width - 2 * MARGIN) * (i + 0.5) / n_top for i in range(n_top)]
    else:
        width = 2 * MARGIN + (n_top // 2) * couple_w + (n_top // 2 - 1) * COUPLE_GAP
        tops = []
        for c in range(n_top // 2):
            x0 = MARGIN + c * (couple_w + COUPLE_GAP)
            tops += [x0 + PORTRAIT_W / 2, x0 + PORTRAIT_W + SPOUSE_GAP + PORTRAIT_W / 2]
    height = 2 * MARGIN + top_pad + (generations + 1) * row_h - ROW_GAP

    # x centre of every person: top row first, then midpoints of each couple
    centers: dict[int, list[float]] = {generations: tops}
    for level in range(generations - 1, -1, -1):
        above = centers[level + 1]
        centers[level] = [(above[2 * i] + above[2 * i + 1]) / 2 for i in range(len(above) // 2)]

    def top(level: int) -> float:
        return MARGIN + top_pad + (generations - level) * row_h

    lines, portraits = [], []
    if spread_width:
        for x in tops:
            lines.append(f'<path d="M{x:.1f},0 V{top(generations) - 4:.1f}"/>')
    for level in range(generations, 0, -1):
        y_mid = top(level) + PORTRAIT_H * 0.55
        for i in range(len(centers[level]) // 2):
            xa, xb = centers[level][2 * i], centers[level][2 * i + 1]
            xm = (xa + xb) / 2
            lines.append(f'<path d="M{xa + PORTRAIT_W / 2 - 4:.1f},{y_mid:.1f} H{xb - PORTRAIT_W / 2 + 4:.1f}"/>')
            lines.append(
                f'<path d="M{xm:.1f},{y_mid:.1f} V{top(level) + PORTRAIT_H + LABEL_H + 2:.1f} '
                f'M{xm:.1f},{top(level) + PORTRAIT_H + LABEL_H + 2:.1f} V{top(level - 1) - 4:.1f}"/>'
            )

    for (level, index), node in nodes.items():
        cx = centers[level][index]
        x, y = cx - PORTRAIT_W / 2, top(level)
        if node.highlight:
            portraits.append(
                f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="{PORTRAIT_W + 10}" height="{PORTRAIT_H + 10}" '
                'rx="10" fill="none" stroke="#8c2f39" stroke-width="3" stroke-dasharray="6 4"/>'
            )
        portraits.append(_place(node.svg, x, y, PORTRAIT_W))
        label_y = y + PORTRAIT_H + (20 if node.highlight else 14)
        if node.label:
            portraits.append(
                f'<text x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle" class="lbl">{escape(node.label)}</text>'
            )
        if node.dots:
            n = len(node.dots)
            for j, status in enumerate(node.dots):
                dx = cx + (j - (n - 1) / 2) * 14
                portraits.append(
                    f'<circle cx="{dx:.1f}" cy="{label_y + 13:.1f}" r="5" fill="{STATUS_COLORS[status]}" '
                    'stroke="#ffffff" stroke-width="1.2"/>'
                )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'style="width:100%;max-width:{max_width}px;height:auto;display:block;margin:0 auto" role="img">'
        "<style>.lbl{font:600 13px system-ui,sans-serif;fill:#2b2420}"
        ".ln path{stroke:#8a7f73;stroke-width:2.5;fill:none;stroke-linecap:round}</style>"
        f'<g class="ln">{"".join(lines)}</g>{"".join(portraits)}</svg>'
    )
