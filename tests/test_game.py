import xml.etree.ElementTree as ET

import pytest

from bloodline.avatar import EYES, HAIR, SKIN, Look, render_avatar, render_unknown
from bloodline.config import load_config
from bloodline.game import Game, slot_sex
from bloodline.i18n import LANGUAGES, strings
from bloodline.ranking import build_ranking

CFG = load_config()


def fill(game: Game) -> None:
    for i in range(len(game.slots)):
        game.assign(i, game.candidates_of(slot_sex(i))[i // 2].id)


def test_same_seed_same_game():
    a, b = Game(CFG, seed=123), Game(CFG, seed=123)
    assert [(c.name, c.genome, c.hint) for c in a.candidates] == [(c.name, c.genome, c.hint) for c in b.candidates]
    fill(a)
    fill(b)
    assert a.resolve().me.genome == b.resolve().me.genome


def test_different_seeds_differ():
    assert [c.genome for c in Game(CFG, seed=1).candidates] != [c.genome for c in Game(CFG, seed=2).candidates]


def test_pool_has_both_sexes():
    g = Game(CFG, seed=5)
    n = CFG.rules.candidates_per_sex
    assert len(g.candidates_of("M")) == n and len(g.candidates_of("F")) == n
    assert len({c.name for c in g.candidates}) == 2 * n


def test_slot_sex_is_enforced():
    g = Game(CFG, seed=7)
    with pytest.raises(ValueError):
        g.assign(0, g.candidates_of("F")[0].id)


def test_assign_moves_candidate():
    g = Game(CFG, seed=7)
    cid = g.candidates_of("M")[0].id
    g.assign(0, cid)
    g.assign(2, cid)
    assert g.slots[0] is None and g.slots[2] == cid


def test_assign_swaps_occupied_slots():
    g = Game(CFG, seed=7)
    a, b = (c.id for c in g.candidates_of("M")[:2])
    g.assign(0, a)
    g.assign(2, b)
    g.assign(0, b)
    assert g.slots[0] == b and g.slots[2] == a


def test_test_budget():
    g = Game(CFG, seed=9)
    disease = CFG.diseases[0].id
    for c in g.candidates[: CFG.rules.tests_per_game]:
        g.run_test(c.id, disease)
    assert g.tests_left == 0
    with pytest.raises(ValueError):
        g.run_test(g.candidates[-1].id, disease)


def test_outcome_matches_phenotype():
    for seed in range(1, 40):
        g = Game(CFG, seed=seed)
        fill(g)
        r = g.resolve()
        pheno = g.model.phenotype(r.me.genome)
        expected = "loss" if pheno.affected else "win" if pheno.carrier else "perfect"
        assert r.outcome == expected
        assert g.resolve() is r  # idempotent
        assert len(r.levels[0]) == 1 and len(r.levels[CFG.rules.generations]) == 8


def test_i18n_languages_have_same_keys():
    keys = [set(strings(lang)) for lang in LANGUAGES]
    assert all(k == keys[0] for k in keys)


def test_avatars_are_valid_svg():
    for gen in ("great_grandparent", "grandparent", "parent", "self"):
        ET.fromstring(render_unknown(gen))
        for sex in "FM":
            for eyes in EYES:
                for hair in HAIR:
                    for skin in SKIN:
                        ET.fromstring(render_avatar(Look(sex, eyes, hair, True, skin), gen, seed=1, sick=True))


def test_ranking_counts_first_play_per_seed_only():
    rows = [
        {"timestamp": "1", "nick": "Ana", "seed": 10, "outcome": "loss", "risk": 0.5},
        {"timestamp": "2", "nick": "ana", "seed": 10, "outcome": "perfect", "risk": 0.0},  # replay
        {"timestamp": "3", "nick": "Ana", "seed": 11, "outcome": "win", "risk": 0.1},
    ]
    table = build_ranking(rows)
    row = table.iloc[0]
    assert row["games"] == 2 and row["wins"] == 1
    assert row["avg_risk"] == pytest.approx(0.3)
