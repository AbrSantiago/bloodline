"""Small single-color icons drawn with CSS masks (no emoji, no image files).

``icon("trophy")`` returns a span; ``ICONS_CSS`` defines one class per icon.
The icon takes the current text color, or a color passed explicitly.
"""

from __future__ import annotations

import urllib.parse

_SVG = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>{}</svg>"

PATHS = {
    "trophy": "<path d='M7 3h10v2h3v3a4 4 0 0 1-4 4h-.3A5 5 0 0 1 13 14.9V18h3v3H8v-3h3v-3.1A5 5 0 0 1 8.3 12H8a4 4 0 0 1-4-4V5h3V3zm-1 4v1a2 2 0 0 0 2 2V7H6zm12 0h-2v3a2 2 0 0 0 2-2V7z'/>",
    "check": "<path fill-rule='evenodd' d='M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20zm-1.2 14.2 7-7-1.4-1.4-5.6 5.6-2.6-2.6-1.4 1.4 4 4z'/>",
    "skull": "<path fill-rule='evenodd' d='M12 2c5 0 8.5 3.6 8.5 8.2 0 2.6-1.1 4.4-2.5 5.6V19a1 1 0 0 1-1 1h-1.5v-2H14v2h-4v-2H8.5v2H7a1 1 0 0 1-1-1v-3.2c-1.4-1.2-2.5-3-2.5-5.6C3.5 5.6 7 2 12 2zM8.5 9a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm7 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM12 13.5 10.7 16h2.6L12 13.5z'/>",
    "swords": "<path d='M4 4l10.5 10.5M20 4 9.5 14.5M6.5 17.5 3.5 20.5M17.5 17.5l3 3M5 14.5l4.5 4.5M19 14.5 14.5 19' stroke='black' stroke-width='2.3' stroke-linecap='round' fill='none'/>",
    "dna": "<path d='M7 3c0 6 10 6 10 12s-10 6-10 6M17 3c0 6-10 6-10 12s10 6 10 6M8 7h8M8 17h8M9.5 12h5' stroke='black' stroke-width='2' stroke-linecap='round' fill='none'/>",
    "dice": "<path fill-rule='evenodd' d='M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm3 3.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm8 8a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm-4-4a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z'/>",
}


def _uri(name: str) -> str:
    return "data:image/svg+xml," + urllib.parse.quote(_SVG.format(PATHS[name]))


ICONS_CSS = (
    ".ic {display: inline-block; width: 1em; height: 1em; vertical-align: -.14em; background: currentColor;"
    " flex: 0 0 auto;}\n"
    + "\n".join(
        f'.ic-{n} {{-webkit-mask: url("{_uri(n)}") center / contain no-repeat;'
        f' mask: url("{_uri(n)}") center / contain no-repeat;}}'
        for n in PATHS
    )
)


def icon(name: str, color: str | None = None, cls: str = "") -> str:
    style = f' style="background:{color}"' if color else ""
    return f'<span class="ic ic-{name} {cls}"{style} aria-hidden="true"></span>'


def rank_badge(rank: int) -> str:
    """Round badge: gold, silver and bronze medals for the podium."""
    colors = {1: ("#f3cf5a", "#9a7417"), 2: ("#d9dde2", "#7b838c"), 3: ("#e3a26b", "#8a5428")}
    if rank in colors:
        fill, edge = colors[rank]
        return (
            '<svg class="rank" viewBox="0 0 28 28" width="26" height="26" aria-label="' + str(rank) + '">'
            f'<path d="M8 1h4l2 6-4 1zM20 1h-4l-2 6 4 1z" fill="{edge}"/>'
            f'<circle cx="14" cy="16" r="10" fill="{fill}" stroke="{edge}" stroke-width="2"/>'
            f'<text x="14" y="20.5" text-anchor="middle" font-size="12" font-weight="700" '
            f'font-family="system-ui,sans-serif" fill="{edge}">{rank}</text></svg>'
        )
    return f'<span class="rank-n">{rank}</span>'
