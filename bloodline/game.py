"""One game of Bloodline, independent of any user interface.

Pedigree layout
---------------
Levels are numbered from the bottom: level 0 is "me", level 1 the parents,
level 2 the grandparents and level 3 the great-grandparents (founders).
Inside a level, person ``i`` is the child of the couple ``(2i, 2i + 1)`` of
the level above, where the even slot is always the man and the odd slot the
woman. With 3 generations the founders' couples are (0,1), (2,3), (4,5),
(6,7); (0..3) is the father's side and (4..7) the mother's side.

Randomness
----------
Everything comes from ``numpy.random.default_rng`` seeded with the game
seed, so a seed reproduces the exact same game:

* ``default_rng([seed, 0])`` creates the candidates.
* ``default_rng([seed, 1, *founder_numbers])`` is used for the births, so two
  players who build the same pedigree in the same game get the same child.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from .config import GameConfig
from .genetics import InheritanceModel, MendelianModel, RiskReport
from .people import Person, generate_candidates

SEED_MAX = 999_999
OUTCOMES = ("perfect", "win", "loss")


def random_seed() -> int:
    return int(np.random.default_rng().integers(1, SEED_MAX + 1))


def slot_sex(index: int) -> str:
    return "M" if index % 2 == 0 else "F"


@dataclass
class Result:
    levels: dict[int, list[Person]]  # level -> people, founders at max level
    risk: RiskReport
    outcome: str  # one of OUTCOMES
    affected: frozenset[str]
    carrier: frozenset[str]

    @property
    def me(self) -> Person:
        return self.levels[0][0]


class Game:
    def __init__(self, config: GameConfig, seed: int | None = None, model: InheritanceModel | None = None):
        self.config = config
        self.seed = int(seed) if seed is not None else random_seed()
        self.model = model or MendelianModel(config)
        self.generations = config.rules.generations
        self.candidates: list[Person] = generate_candidates(
            config, self.model, np.random.default_rng([self.seed, 0])
        )
        self._by_id = {c.id: c for c in self.candidates}
        self.slots: list[str | None] = [None] * (2**self.generations)
        self.tests: dict[str, dict[str, str]] = {}  # candidate id -> gene id -> result
        self.tests_used = 0
        self.result: Result | None = None

    # ------------------------------------------------------------ candidates
    def candidate(self, cid: str) -> Person:
        return self._by_id[cid]

    def candidates_of(self, sex: str) -> list[Person]:
        return [c for c in self.candidates if c.sex == sex]

    def slot_of(self, cid: str) -> int | None:
        return self.slots.index(cid) if cid in self.slots else None

    # ------------------------------------------------------------ building
    def assign(self, slot: int, cid: str | None) -> None:
        """Place a candidate in a founder slot (``None`` empties it).

        A candidate already placed elsewhere moves to the new slot.
        """
        self._ensure_open()
        if cid is not None:
            if self.candidate(cid).sex != slot_sex(slot):
                raise ValueError(f"slot {slot} needs sex {slot_sex(slot)}")
            previous = self.slot_of(cid)
            if previous is not None:
                self.slots[previous] = None
        self.slots[slot] = cid

    def clear(self) -> None:
        self._ensure_open()
        self.slots = [None] * len(self.slots)

    @property
    def is_complete(self) -> bool:
        return all(s is not None for s in self.slots)

    # ------------------------------------------------------------ genetic tests
    @property
    def tests_left(self) -> int:
        return self.config.rules.tests_per_game - self.tests_used

    def test_results(self, cid: str) -> dict[str, str]:
        return self.tests.get(cid, {})

    def can_test(self, cid: str, gene_id: str | None = None) -> bool:
        if self.result is not None or self.tests_left <= 0:
            return False
        done = self.test_results(cid)
        if self.config.rules.test_scope == "all":
            return not done
        return gene_id is not None and gene_id not in done

    def run_test(self, cid: str, gene_id: str | None = None) -> dict[str, str]:
        """Spend one test. Scope 'single_disease' reveals one disease,
        scope 'all' reveals every disease of that candidate."""
        if not self.can_test(cid, gene_id):
            raise ValueError("test not available")
        genome = self.candidate(cid).genome
        if self.config.rules.test_scope == "all":
            genes = [d.id for d in self.config.diseases]
        else:
            genes = [gene_id]
        found = {g: self.model.test(genome, g) for g in genes}
        self.tests.setdefault(cid, {}).update(found)
        self.tests_used += 1
        return found

    # ------------------------------------------------------------ birth
    def founders(self) -> list[Person]:
        if not self.is_complete:
            raise ValueError("pedigree is not complete")
        return [self.candidate(cid) for cid in self.slots]  # type: ignore[arg-type]

    def risk(self) -> RiskReport:
        """Exact risk of the chosen pedigree (computed, not simulated)."""
        return self.model.descendant_risk([p.genome for p in self.founders()])

    def resolve(self) -> Result:
        """Simulate the births down to "me". Idempotent."""
        if self.result is not None:
            return self.result
        founders = self.founders()
        numbers = [int(cid[1:]) + (100 if cid[0] == "F" else 0) for cid in self.slots]  # type: ignore[index]
        rng = np.random.default_rng([self.seed, 1, *numbers])
        top = self.generations
        levels: dict[int, list[Person]] = {top: []}
        for i, f in enumerate(founders):
            f.index = i
            levels[top].append(f)
        for level in range(top - 1, -1, -1):
            above = levels[level + 1]
            current = []
            for i in range(len(above) // 2):
                father, mother = above[2 * i], above[2 * i + 1]
                genome = self.model.child_genome(mother.genome, father.genome, rng)
                sex = slot_sex(i) if level > 0 else str(rng.choice(["F", "M"]))
                skin = (father if rng.random() < 0.5 else mother).skin
                current.append(
                    Person(
                        id=f"L{level}-{i}",
                        sex=sex,
                        level=level,
                        index=i,
                        genome=genome,
                        skin=skin,
                        avatar_seed=int(rng.integers(1, 2**31)),
                    )
                )
            levels[level] = current
        me = levels[0][0]
        pheno = self.model.phenotype(me.genome)
        if pheno.affected:
            outcome = "loss"
        elif pheno.carrier:
            outcome = "win"
        else:
            outcome = "perfect"
        self.result = Result(levels, self.risk(), outcome, pheno.affected, pheno.carrier)
        return self.result

    def _ensure_open(self) -> None:
        if self.result is not None:
            raise ValueError("game already finished")

    # ------------------------------------------------------------ records
    def record(self, nick: str, lang: str, version: str) -> dict:
        """Flat row for the results store / ranking."""
        if self.result is None:
            raise ValueError("game not finished")
        r = self.result
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "nick": nick,
            "seed": self.seed,
            "outcome": r.outcome,
            "risk": round(r.risk.p_loss, 6),
            "p_perfect": round(r.risk.p_perfect, 6),
            "tests_used": self.tests_used,
            "founders": " ".join(self.slots),  # type: ignore[arg-type]
            "lang": lang,
            "version": version,
        }
