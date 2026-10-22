"""Mendelian inheritance with Multinomial genotypes.

Representation
--------------
For every gene a genotype is the number of recessive alleles a person
carries: 0 (AA), 1 (Aa) or 2 (aa). For disease genes the recessive allele is
the disease allele, so 0 = clear, 1 = healthy carrier, 2 = affected.

Why the Multinomial
-------------------
* A founder drawn from a population in Hardy-Weinberg equilibrium has
  genotype counts ~ Multinomial(1; p², 2pq, q²).
* A child's genotype given its parents is also Multinomial: each parent
  passes one of its two copies at random (a fair coin for heterozygotes),
  so the child's genotype probabilities are the outer product of the two
  "gamete" vectors, collapsed into (AA, Aa, aa).

The same matrix algebra gives the *exact* probability for the descendant at
the bottom of the pedigree, which the game shows as the player's risk and
which the validation notebook compares against Monte Carlo simulations.
"""

from __future__ import annotations

import numpy as np

from ..config import GameConfig, Gene
from .base import DiseaseRisk, InheritanceModel, Phenotype, RiskReport

Genome = dict[str, int]

TEST_RESULTS = ("clear", "carrier", "affected")


def hardy_weinberg(q: float) -> np.ndarray:
    """Genotype probabilities (AA, Aa, aa) for recessive allele frequency q."""
    p = 1.0 - q
    return np.array([p * p, 2 * p * q, q * q])


def transmission_matrix(het_transmission: float = 0.5) -> np.ndarray:
    """T[k, a] = P(parent with k recessive copies passes allele a).

    Column 0 is the dominant allele, column 1 the recessive one.
    ``het_transmission`` is the chance a heterozygote passes the recessive
    allele: 0.5 under Mendel's law. Other values model segregation
    distortion and are used in the notebook to show the tests detect it.
    """
    h = het_transmission
    return np.array([[1.0, 0.0], [1.0 - h, h], [0.0, 1.0]])


def gamete_distribution(genotype_dist: np.ndarray, het_transmission: float = 0.5) -> np.ndarray:
    """Vector (P(passes dominant), P(passes recessive)) for a parent."""
    return genotype_dist @ transmission_matrix(het_transmission)


def offspring_distribution(
    mother: np.ndarray, father: np.ndarray, het_transmission: float = 0.5
) -> np.ndarray:
    """Child genotype probabilities (AA, Aa, aa) from both parents' distributions.

    The outer product ``M[i, j] = P(mother passes i) * P(father passes j)``
    is the classic Punnett square; summing its anti-diagonals collapses it
    into the number of recessive alleles the child receives.
    Assumes both parents are independent (no shared ancestors), which holds
    in the game because every founder slot holds a different person.
    """
    punnett = np.outer(
        gamete_distribution(mother, het_transmission),
        gamete_distribution(father, het_transmission),
    )
    return np.array([punnett[0, 0], punnett[0, 1] + punnett[1, 0], punnett[1, 1]])


def one_hot(count: int) -> np.ndarray:
    v = np.zeros(3)
    v[count] = 1.0
    return v


class MendelianModel(InheritanceModel):
    """Independent single-gene recessive traits (diseases and cosmetics)."""

    def __init__(self, config: GameConfig, het_transmission: float = 0.5):
        self.config = config
        self.genes: tuple[Gene, ...] = config.genes
        self.het_transmission = het_transmission
        self._T = transmission_matrix(het_transmission)

    # ------------------------------------------------------------ sampling
    def random_genome(self, rng: np.random.Generator) -> Genome:
        """Founder genotype: one Multinomial(1; p², 2pq, q²) draw per gene."""
        return {
            g.id: int(rng.choice(3, p=hardy_weinberg(g.recessive_freq)))
            for g in self.genes
        }

    def gamete(self, genome: Genome, rng: np.random.Generator) -> dict[str, int]:
        """Alleles passed on by one parent: 1 means the recessive allele."""
        return {gid: int(rng.random() < self._T[k, 1]) for gid, k in genome.items()}

    def child_genome(self, mother: Genome, father: Genome, rng: np.random.Generator) -> Genome:
        from_mother = self.gamete(mother, rng)
        from_father = self.gamete(father, rng)
        return {gid: from_mother[gid] + from_father[gid] for gid in mother}

    # ------------------------------------------------------------ reading
    def phenotype(self, genome: Genome) -> Phenotype:
        affected, carrier, traits = set(), set(), {}
        for g in self.genes:
            k = genome[g.id]
            if g.kind == "disease":
                if k == 2:
                    affected.add(g.id)
                elif k == 1:
                    carrier.add(g.id)
            else:
                traits[g.trait] = g.recessive if k == 2 else g.dominant
        return Phenotype(frozenset(affected), frozenset(carrier), traits)

    def test(self, genome: Genome, gene_id: str) -> str:
        return TEST_RESULTS[genome[gene_id]]

    # ------------------------------------------------------------ exact maths
    def pedigree_distributions(self, founders: list[Genome], gene_id: str) -> list[list[np.ndarray]]:
        """Exact genotype distribution of every person in the pedigree.

        Returns levels from the founders (index 0) down to the single
        descendant (last). Inside each level, person i comes from the couple
        (2i = father, 2i + 1 = mother) of the level above.
        """
        level = [one_hot(f[gene_id]) for f in founders]
        levels = [level]
        while len(level) > 1:
            level = [
                offspring_distribution(level[2 * i + 1], level[2 * i], self.het_transmission)
                for i in range(len(level) // 2)
            ]
            levels.append(level)
        return levels

    def descendant_distribution(self, founders: list[Genome], gene_id: str) -> np.ndarray:
        return self.pedigree_distributions(founders, gene_id)[-1][0]

    def descendant_risk(self, founders: list[Genome]) -> RiskReport:
        risks = []
        for g in self.config.diseases:
            clear, carrier, affected = self.descendant_distribution(founders, g.id)
            risks.append(DiseaseRisk(g.id, float(clear), float(carrier), float(affected)))
        return RiskReport(tuple(risks))
