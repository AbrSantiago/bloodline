"""Game configuration: genes, game rules and flavour data.

All biological parameters live in ``data/config.json`` (exported from the
shared Google Sheet with ``scripts/sheet_sync.py``), so the code never
hard-codes disease names or allele frequencies.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "config.json"

GENE_KINDS = ("disease", "cosmetic")
TEST_SCOPES = ("single_disease", "all")


@dataclass(frozen=True)
class Gene:
    """A single gene with two alleles: dominant and recessive.

    ``recessive_freq`` is q, the population frequency of the recessive
    allele (for diseases, the disease allele). p = 1 - q.
    """

    id: str
    kind: str
    recessive_freq: float
    name: dict[str, str]
    trait: str | None = None  # avatar attribute (cosmetic genes only)
    dominant: Any = None  # phenotype value when at least one dominant allele
    recessive: Any = None  # phenotype value when homozygous recessive

    def label(self, lang: str) -> str:
        return self.name.get(lang) or self.name.get("es") or self.id


@dataclass(frozen=True)
class GameRules:
    generations: int = 3
    candidates_per_sex: int = 10
    tests_per_game: int = 4
    test_scope: str = "single_disease"
    siblings_range: tuple[int, int] = (2, 5)
    fun_fact_probability: float = 0.35
    ranking_min_games: int = 3


@dataclass(frozen=True)
class GameConfig:
    rules: GameRules
    genes: tuple[Gene, ...]
    skin_tones: dict[str, float]
    names: dict[str, list[str]]
    fun_facts: list[dict[str, str]] = field(default_factory=list)

    @property
    def diseases(self) -> tuple[Gene, ...]:
        return tuple(g for g in self.genes if g.kind == "disease")

    @property
    def cosmetics(self) -> tuple[Gene, ...]:
        return tuple(g for g in self.genes if g.kind == "cosmetic")

    def gene(self, gene_id: str) -> Gene:
        for g in self.genes:
            if g.id == gene_id:
                return g
        raise KeyError(gene_id)


def _validate(cfg: GameConfig) -> None:
    ids = [g.id for g in cfg.genes]
    if len(ids) != len(set(ids)):
        raise ValueError("gene ids must be unique")
    for g in cfg.genes:
        if g.kind not in GENE_KINDS:
            raise ValueError(f"gene {g.id}: kind must be one of {GENE_KINDS}")
        if not 0.0 <= g.recessive_freq <= 1.0:
            raise ValueError(f"gene {g.id}: recessive_freq must be in [0, 1]")
        if g.kind == "cosmetic" and not g.trait:
            raise ValueError(f"gene {g.id}: cosmetic genes need a 'trait'")
    if not cfg.diseases:
        raise ValueError("at least one disease gene is required")
    r = cfg.rules
    if r.test_scope not in TEST_SCOPES:
        raise ValueError(f"test_scope must be one of {TEST_SCOPES}")
    if not 1 <= r.generations <= 3:
        raise ValueError("generations must be 1, 2 or 3")
    founders_per_sex = 2 ** r.generations // 2
    if r.candidates_per_sex < founders_per_sex:
        raise ValueError(f"candidates_per_sex must be at least {founders_per_sex}")
    for sex in ("F", "M"):
        if len(set(cfg.names.get(sex, []))) < r.candidates_per_sex:
            raise ValueError(f"need at least {r.candidates_per_sex} distinct names for sex {sex}")
    if abs(sum(cfg.skin_tones.values()) - 1.0) > 1e-6:
        raise ValueError("skin_tones probabilities must add up to 1")


def config_from_dict(raw: dict[str, Any]) -> GameConfig:
    game = dict(raw.get("game", {}))
    if "siblings_range" in game:
        game["siblings_range"] = tuple(game["siblings_range"])
    cfg = GameConfig(
        rules=GameRules(**game),
        genes=tuple(Gene(**g) for g in raw["genes"]),
        skin_tones=dict(raw["skin_tones"]),
        names={k: list(v) for k, v in raw["names"].items()},
        fun_facts=list(raw.get("fun_facts", [])),
    )
    _validate(cfg)
    return cfg


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> GameConfig:
    with open(path, encoding="utf-8") as f:
        return config_from_dict(json.load(f))
