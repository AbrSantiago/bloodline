"""Pure helpers that turn game objects into HTML/SVG for the UI."""

from __future__ import annotations

import io
from collections.abc import Callable
from html import escape

from ..avatar import Look, render_avatar, render_unknown
from ..config import GameConfig
from ..game import Game, Result
from ..genetics import InheritanceModel
from ..people import GENERATION_NAMES, Person
from .tree import NodeView, pedigree_svg

T = Callable[..., str]


def look_of(person: Person, model: InheritanceModel) -> Look:
    traits = model.phenotype(person.genome).traits
    return Look(
        sex=person.sex,
        eyes=traits.get("eyes", "brown"),
        hair=traits.get("hair", "brown"),
        freckles=bool(traits.get("freckles", False)),
        skin=person.skin,
    )


def portrait(person: Person, model: InheritanceModel, size: int | None = None, sick: bool = False) -> str:
    return render_avatar(look_of(person, model), person.generation, seed=person.avatar_seed, size=size, sick=sick)


def role_label(t: T, level: int, index: int, generations: int) -> str:
    if level == 0:
        return t("role.me")
    if level == 1:
        return t("role.father") if index == 0 else t("role.mother")
    if level == 2 and generations >= 2:
        return t(f"role.grand.{index}")
    return ""


def disease_name(config: GameConfig, gene_id: str, lang: str) -> str:
    return config.gene(gene_id).label(lang)


def hint_text(t: T, person: Person, config: GameConfig, lang: str) -> str:
    h = person.hint
    if h is None:
        return ""
    p = h.params
    if h.kind == "fun_fact":
        fact = config.fun_facts[p["index"]]
        return fact.get(lang) or fact.get("es", "")
    if h.kind == "parent_affected":
        return t(f"hint.parent_affected.{p['relative']}", disease=disease_name(config, p["gene"], lang))
    if h.kind == "sibling_affected":
        n, total = p["n"], p["total"]
        if total == 1:
            key = "hint.sibling_affected.only"
        elif n == total:
            key = "hint.sibling_affected.both" if total == 2 else "hint.sibling_affected.all"
        else:
            key = "hint.sibling_affected.one" if n == 1 else "hint.sibling_affected.many"
        n_word = number_word(t, n)
        return t(
            key,
            n=n_word[:1].upper() + n_word[1:],
            total=number_word(t, total),
            disease=disease_name(config, p["gene"], lang),
        )
    if h.kind == "healthy_family":
        key = "hint.healthy_family.only" if p["total"] == 1 else "hint.healthy_family"
        return t(key, total=number_word(t, p["total"]))
    return ""


def number_word(t: T, n: int) -> str:
    """'dos' instead of '2' for small numbers (falls back to digits)."""
    word = t(f"num.{n}")
    return str(n) if word == f"num.{n}" else word


def test_label(t: T, result: str, sex: str) -> str:
    return t(f"test.{result}.{sex}")


def status_of(model: InheritanceModel, person: Person, gene_id: str) -> str:
    return model.test(person.genome, gene_id)


# ---------------------------------------------------------------- trees
def lower_tree(game: Game, t: T, width: float = 1300) -> str:
    """Grandparents, parents and "me", still unknown while building.

    The founders are drawn above it as interactive slots, so this drawing
    starts one level below and spreads the grandparents under each couple."""
    g = game.generations
    nodes = {
        (level, i): NodeView(
            render_unknown(GENERATION_NAMES[level], size=None),
            role_label(t, level, i, g),
            highlight=level == 0,
        )
        for level in range(g - 1, -1, -1)
        for i in range(2**level)
    }
    return pedigree_svg(nodes, g - 1, spread_width=width, max_width=100_000, row_gap=22, label_px=16)


SEX_SYMBOL = {"M": "♂", "F": "♀"}
SEX_COLOR = {"M": "#3d7fc4", "F": "#c9508a"}


def empty_slot(level: int, sex: str) -> str:
    return render_unknown(GENERATION_NAMES[level], size=None, label=SEX_SYMBOL[sex], color=SEX_COLOR[sex])


def full_tree(game: Game, result: Result, t: T, lang: str) -> str:
    """Pedigree after birth: every person, a dot per disease and a hover
    card with the status of each disease."""
    g = game.generations
    diseases = game.config.diseases
    nodes = {}
    for level, people in result.levels.items():
        for p in people:
            label = p.name.split()[0] if p.name else role_label(t, level, p.index, g)
            sick = level == 0 and bool(result.affected)
            statuses = [status_of(game.model, p, d.id) for d in diseases]
            nodes[(level, p.index)] = NodeView(
                portrait(p, game.model, sick=sick),
                label,
                dots=statuses,
                highlight=level == 0,
                tip_title=p.name or role_label(t, level, p.index, g),
                tip_lines=[
                    (st_, f"{d.label(lang)}: {test_label(t, st_, p.sex)}") for d, st_ in zip(diseases, statuses)
                ],
            )
    return pedigree_svg(nodes, g)


# ---------------------------------------------------------------- misc
def qr_svg(url: str) -> str:
    import qrcode
    import qrcode.image.svg

    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode("utf-8")
    svg = svg[svg.index("<svg") :]
    return svg.replace("<svg ", '<svg style="width:100%;height:auto;background:#fff" ', 1)


def chip(text: str, color: str) -> str:
    return (
        f'<span class="chip" style="background:{color}22;border-color:{color};color:var(--bl-text, #2b2420)">'
        f"{escape(text)}</span>"
    )


def hero_gallery(seed: int, n: int = 7) -> str:
    """Decorative row of random portraits for the main menu."""
    import numpy as np

    from ..avatar import EYES, HAIR, SKIN

    rng = np.random.default_rng(seed)
    eras = ["great_grandparent", "grandparent", "parent", "self", "parent", "grandparent", "great_grandparent"]
    tilts = [-7, 4, -3, 0, 3, -4, 6]
    items = []
    for i in range(n):
        look = Look(
            sex="MF"[i % 2],
            eyes=str(rng.choice(list(EYES))),
            hair=str(rng.choice(list(HAIR))),
            freckles=bool(rng.random() < 0.35),
            skin=str(rng.choice(list(SKIN))),
        )
        svg = render_avatar(look, eras[i % len(eras)], seed=int(rng.integers(1, 2**31)), size=None)
        items.append(f'<div class="hero-pic" style="--r:{tilts[i % len(tilts)]}deg">{svg}</div>')
    return f'<div class="hero-gallery">{"".join(items)}</div>'
