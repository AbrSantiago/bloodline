"""Pedigree diagram as a single SVG (portraits + couple lines)."""

from __future__ import annotations

import itertools
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

_ids = itertools.count()
TIP_W = 230
TIP_LINE = 24
TIP_PAD = 12

STATUS_COLORS = {"clear": "#3f9d5a", "carrier": "#e2a72e", "affected": "#d83a3a", "unknown": "#c9c2b6"}


@dataclass
class NodeView:
    svg: str  # portrait from bloodline.avatar
    label: str = ""
    dots: list[str] = field(default_factory=list)  # status names per disease
    highlight: bool = False
    tip_title: str = ""  # hover card: heading
    tip_lines: list[tuple[str, str]] = field(default_factory=list)  # (status, text) per disease


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
    row_gap: float = ROW_GAP,
    label_px: int = 13,
) -> str:
    """Draw the pedigree. ``nodes`` maps (level, index) to what to show;
    level ``generations`` holds the top row and level 0 is "me".

    With ``spread_width`` the top row is spread evenly over that width and
    gets short lines going up, so the drawing continues a row of couples
    rendered above it (the interactive founders while building)."""
    n_top = 2**generations
    couple_w = 2 * PORTRAIT_W + SPOUSE_GAP
    row_h = PORTRAIT_H + LABEL_H + row_gap
    top_pad = 24 if spread_width else 0
    if spread_width:
        # exactly under the centre of each of the n_top equal-width boxes above
        width = spread_width
        tops = [width * (i + 0.5) / n_top for i in range(n_top)]
    else:
        width = 2 * MARGIN + (n_top // 2) * couple_w + (n_top // 2 - 1) * COUPLE_GAP
        tops = []
        for c in range(n_top // 2):
            x0 = MARGIN + c * (couple_w + COUPLE_GAP)
            tops += [x0 + PORTRAIT_W / 2, x0 + PORTRAIT_W + SPOUSE_GAP + PORTRAIT_W / 2]
    height = 2 * MARGIN + top_pad + (generations + 1) * row_h - row_gap

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

    uid = f"pd{next(_ids)}"
    tips, rules = [], []
    for k, ((level, index), node) in enumerate(nodes.items()):
        cx = centers[level][index]
        x, y = cx - PORTRAIT_W / 2, top(level)
        group = []
        if node.highlight:
            group.append(
                f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="{PORTRAIT_W + 10}" height="{PORTRAIT_H + 10}" '
                'rx="10" fill="none" stroke-width="3" stroke-dasharray="6 4" class="hl"/>'
            )
        group.append(_place(node.svg, x, y, PORTRAIT_W))
        label_y = y + PORTRAIT_H + (20 if node.highlight else 14)
        if node.label:
            group.append(
                f'<text x="{cx:.1f}" y="{label_y:.1f}" text-anchor="middle" class="lbl">{escape(node.label)}</text>'
            )
        if node.dots:
            n = len(node.dots)
            for j, status in enumerate(node.dots):
                dx = cx + (j - (n - 1) / 2) * 14
                group.append(
                    f'<circle cx="{dx:.1f}" cy="{label_y + 13:.1f}" r="5" fill="{STATUS_COLORS[status]}" '
                    'stroke-width="1.2" class="ring"/>'
                )
        if node.tip_lines:
            nid, tid = f"{uid}n{k}", f"{uid}t{k}"
            portraits.append(f'<g id="{nid}" class="node" tabindex="0">{"".join(group)}</g>')
            tips.append(_tip(tid, node, cx, y, label_y, width, below=level > 0))
            rules.append(f"svg:has(#{nid}:hover) #{tid},svg:has(#{nid}:focus) #{tid}{{display:inline}}")
        else:
            portraits.extend(group)

    return (
        f'<svg id="{uid}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'style="width:100%;max-width:{max_width}px;height:auto;display:block;margin:0 auto" role="img">'
        f"<style>#{uid} .lbl{{font:600 {label_px}px system-ui,sans-serif;fill:var(--bl-text,#2b2420)}}"
        ".ln path{stroke:var(--bl-line,#8a7f73);stroke-width:2.5;fill:none;stroke-linecap:round}"
        ".hl{stroke:var(--bl-accent,#8c2f39)}.ring{stroke:var(--bl-ring,#fff)}"
        ".tip rect{fill:var(--bl-surface,#fffaf0);stroke:var(--bl-gold,#b8892f)}"
        ".node{cursor:help;outline:none}.tip{display:none;pointer-events:none}"
        ".tip text{font:15px system-ui,sans-serif;fill:var(--bl-text,#2b2420)}.tip .tt{font-weight:700}"
        f"{''.join(rules)}</style>"
        f'<g class="ln">{"".join(lines)}</g>{"".join(portraits)}{"".join(tips)}</svg>'
    )


def _tip(tid: str, node: NodeView, cx: float, y: float, label_y: float, width: float, below: bool) -> str:
    """Small card with the status of every disease, shown on hover/tap."""
    h = TIP_PAD * 2 + TIP_LINE * (len(node.tip_lines) + 1)
    longest = max([len(node.tip_title)] + [len(text) + 3 for _, text in node.tip_lines])
    tip_w = max(TIP_W, int(longest * 8.4) + 2 * TIP_PAD)  # ~8.4 units per character at 15px
    tx = min(max(cx - tip_w / 2, 4), width - tip_w - 4)
    ty = label_y + 26 if below else y - h - 8
    parts = [
        f'<rect x="{tx:.1f}" y="{ty:.1f}" width="{tip_w}" height="{h}" rx="10" stroke-width="2" '
        'style="filter:drop-shadow(0 4px 8px rgba(0,0,0,.3))"/>',
        f'<text class="tt" x="{tx + TIP_PAD:.1f}" y="{ty + TIP_PAD + 16:.1f}">{escape(node.tip_title)}</text>',
    ]
    for i, (status, text) in enumerate(node.tip_lines):
        ly = ty + TIP_PAD + TIP_LINE * (i + 1) + 16
        parts.append(f'<circle cx="{tx + TIP_PAD + 6:.1f}" cy="{ly - 5:.1f}" r="6" fill="{STATUS_COLORS[status]}"/>')
        parts.append(f'<text x="{tx + TIP_PAD + 20:.1f}" y="{ly:.1f}">{escape(text)}</text>')
    return f'<g id="{tid}" class="tip">{"".join(parts)}</g>'
