"""Inheritance model interface.

The game only talks to an ``InheritanceModel``. The V1 ships one
implementation, :class:`~bloodline.genetics.mendelian.MendelianModel`
(single-gene recessive traits, Multinomial genotypes). A future game mode
could plug in a different model (for example complex diseases with a
Multivariate Normal liability) without touching the UI or the game loop.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np

Genome = Any  # each model decides its own genome representation


@dataclass(frozen=True)
class Phenotype:
    """What can be observed (or tested) about a person."""

    affected: frozenset[str]  # disease ids the person suffers
    carrier: frozenset[str]  # disease ids carried without symptoms
    traits: dict[str, Any] = field(default_factory=dict)  # avatar attributes


@dataclass(frozen=True)
class DiseaseRisk:
    gene_id: str
    p_clear: float  # no copies of the disease allele
    p_carrier: float  # one copy, healthy
    p_affected: float  # two copies, sick


@dataclass(frozen=True)
class RiskReport:
    """Exact probabilities for the youngest descendant ("me")."""

    per_disease: tuple[DiseaseRisk, ...]

    @property
    def p_loss(self) -> float:
        """P(me is affected by at least one disease)."""
        return 1.0 - float(np.prod([1.0 - d.p_affected for d in self.per_disease]))

    @property
    def p_perfect(self) -> float:
        """P(me neither affected nor carrier of anything)."""
        return float(np.prod([d.p_clear for d in self.per_disease]))

    @property
    def p_win_carrier(self) -> float:
        """P(me healthy but carrier of at least one disease)."""
        return 1.0 - self.p_loss - self.p_perfect

    def disease(self, gene_id: str) -> DiseaseRisk:
        return next(d for d in self.per_disease if d.gene_id == gene_id)


class InheritanceModel(ABC):
    """How genomes are created, combined and read."""

    @abstractmethod
    def random_genome(self, rng: np.random.Generator) -> Genome:
        """A founder drawn from the population at equilibrium."""

    @abstractmethod
    def child_genome(self, mother: Genome, father: Genome, rng: np.random.Generator) -> Genome:
        """One random child of two parents."""

    @abstractmethod
    def phenotype(self, genome: Genome) -> Phenotype:
        """Observable traits and disease status."""

    @abstractmethod
    def test(self, genome: Genome, gene_id: str) -> str:
        """Genetic test result for one disease: 'clear', 'carrier' or 'affected'."""

    @abstractmethod
    def descendant_risk(self, founders: list[Genome]) -> RiskReport:
        """Exact risk for the single descendant of a full founder pedigree.

        ``founders`` are ordered as pedigree slots: pairs (2i, 2i+1) are
        (father, mother) couples, and each level halves until one person.
        """
