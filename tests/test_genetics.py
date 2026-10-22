import numpy as np
import pytest
from scipy import stats

from bloodline.config import load_config
from bloodline.genetics import MendelianModel, hardy_weinberg, offspring_distribution
from bloodline.genetics.mendelian import one_hot

CFG = load_config()


def test_hardy_weinberg_sums_to_one():
    for q in (0.0, 0.1, 0.5, 0.93, 1.0):
        hw = hardy_weinberg(q)
        assert hw.sum() == pytest.approx(1.0)
        assert hw[2] == pytest.approx(q * q)


@pytest.mark.parametrize(
    "mother, father, expected",
    [
        (1, 1, [0.25, 0.5, 0.25]),  # Aa x Aa: Mendel's 1:2:1
        (0, 2, [0.0, 1.0, 0.0]),  # AA x aa: every child is a carrier
        (1, 2, [0.0, 0.5, 0.5]),
        (0, 0, [1.0, 0.0, 0.0]),
    ],
)
def test_punnett_squares(mother, father, expected):
    got = offspring_distribution(one_hot(mother), one_hot(father))
    np.testing.assert_allclose(got, expected)


def test_random_founders_follow_hardy_weinberg():
    model = MendelianModel(CFG)
    rng = np.random.default_rng(1)
    gene = CFG.diseases[0]
    counts = np.bincount([model.random_genome(rng)[gene.id] for _ in range(20_000)], minlength=3)
    expected = 20_000 * hardy_weinberg(gene.recessive_freq)
    assert stats.chisquare(counts, expected).pvalue > 0.001


def test_simulated_children_match_exact_distribution():
    model = MendelianModel(CFG)
    rng = np.random.default_rng(2)
    founders = [model.random_genome(rng) for _ in range(8)]
    gid = CFG.diseases[0].id
    exact = model.descendant_distribution(founders, gid)
    n = 20_000
    counts = np.zeros(3)
    for _ in range(n):
        level = founders
        while len(level) > 1:
            level = [model.child_genome(level[2 * i + 1], level[2 * i], rng) for i in range(len(level) // 2)]
        counts[level[0][gid]] += 1
    mask = exact > 0
    assert counts[~mask].sum() == 0  # impossible genotypes never appear
    if mask.sum() > 1:
        assert stats.chisquare(counts[mask], n * exact[mask]).pvalue > 0.001


def test_risk_report_is_consistent():
    model = MendelianModel(CFG)
    rng = np.random.default_rng(3)
    report = model.descendant_risk([model.random_genome(rng) for _ in range(8)])
    assert report.p_loss + report.p_perfect + report.p_win_carrier == pytest.approx(1.0)
    for d in report.per_disease:
        assert d.p_clear + d.p_carrier + d.p_affected == pytest.approx(1.0)


def test_two_clear_lines_give_zero_risk():
    model = MendelianModel(CFG)
    founders = [{g.id: 0 for g in CFG.genes} for _ in range(8)]
    founders[0] = {**founders[0], CFG.diseases[0].id: 2}  # one sick founder, everyone else clear
    report = model.descendant_risk(founders)
    assert report.p_loss == 0.0
