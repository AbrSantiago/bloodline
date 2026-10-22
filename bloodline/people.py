"""People in the game: candidates (founders) and their descendants."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .config import GameConfig
from .genetics import InheritanceModel

GENERATION_NAMES = {0: "self", 1: "parent", 2: "grandparent", 3: "great_grandparent"}


@dataclass(frozen=True)
class Hint:
    """A clue printed on a candidate's card.

    kinds: ``parent_affected`` (params: gene, relative), ``sibling_affected``
    (gene, n, total), ``healthy_family`` (total) and ``fun_fact`` (index).
    Family clues are always true: they come from simulating the candidate's
    own parents and siblings with the same inheritance model.
    """

    kind: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Person:
    id: str
    sex: str  # "F" or "M"
    level: int  # 0 = me, 1 = parents, 2 = grandparents, 3 = great-grandparents
    index: int  # position inside its level (see pedigree.py)
    genome: Any
    skin: str
    avatar_seed: int
    name: str | None = None
    hint: Hint | None = None

    @property
    def generation(self) -> str:
        return GENERATION_NAMES.get(self.level, "great_grandparent")


def _family_hint(
    model: InheritanceModel,
    config: GameConfig,
    mother: Any,
    father: Any,
    siblings: list[Any],
    rng: np.random.Generator,
) -> Hint:
    facts: list[Hint] = []
    for relative, genome in (("father", father), ("mother", mother)):
        for d in sorted(model.phenotype(genome).affected):
            facts.append(Hint("parent_affected", {"gene": d, "relative": relative}))
    for d in config.diseases:
        n = sum(d.id in model.phenotype(s).affected for s in siblings)
        if n:
            facts.append(Hint("sibling_affected", {"gene": d.id, "n": n, "total": len(siblings)}))
    if facts:
        return facts[int(rng.integers(len(facts)))]
    return Hint("healthy_family", {"total": len(siblings)})


def generate_candidates(
    config: GameConfig, model: InheritanceModel, rng: np.random.Generator
) -> list[Person]:
    """Create the pool of candidate founders for one game.

    Each candidate is born from two random parents of the previous
    generation (drawn at Hardy-Weinberg equilibrium) together with a few
    siblings. Only the candidate enters the game; parents and siblings are
    used to write a truthful family clue.
    """
    rules = config.rules
    n = rules.candidates_per_sex
    skins = list(config.skin_tones)
    skin_p = np.array([config.skin_tones[s] for s in skins])
    surnames = config.names["surnames"]
    lo, hi = rules.siblings_range
    people: list[Person] = []
    for sex in ("M", "F"):
        first_names = rng.choice(config.names[sex], size=n, replace=False)
        for i in range(n):
            father = model.random_genome(rng)
            mother = model.random_genome(rng)
            genome = model.child_genome(mother, father, rng)
            siblings = [
                model.child_genome(mother, father, rng)
                for _ in range(int(rng.integers(lo, hi + 1)))
            ]
            if config.fun_facts and rng.random() < rules.fun_fact_probability:
                hint = Hint("fun_fact", {"index": int(rng.integers(len(config.fun_facts)))})
            else:
                hint = _family_hint(model, config, mother, father, siblings, rng)
            people.append(
                Person(
                    id=f"{sex}{i + 1:02d}",
                    sex=sex,
                    level=rules.generations,
                    index=-1,
                    genome=genome,
                    skin=str(rng.choice(skins, p=skin_p)),
                    avatar_seed=int(rng.integers(1, 2**31)),
                    name=f"{first_names[i]} {rng.choice(surnames)}",
                    hint=hint,
                )
            )
    return people
