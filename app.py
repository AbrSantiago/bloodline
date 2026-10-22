"""Bloodline: Streamlit user interface.

Run locally with ``streamlit run app.py``. All game logic lives in the
``bloodline`` package; this file only draws screens and reacts to clicks.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

from bloodline import __version__, settings
from bloodline.config import load_config
from bloodline.game import SEED_MAX, Game, random_seed, slot_sex
from bloodline.i18n import DEFAULT_LANGUAGE, LANGUAGES, translate
from bloodline.ranking import build_ranking, by_avg_risk, by_win_rate, by_wins
from bloodline.storage import get_store
from bloodline.ui import components as ui
from bloodline.ui.tree import STATUS_COLORS

ASSETS = Path(__file__).resolve().parent / "assets"
LOGO_SVG = (ASSETS / "logo.svg").read_text(encoding="utf-8")
SEX_MD = {"M": ":blue[**♂**]", "F": ":violet[**♀**]"}

st.set_page_config(page_title="Bloodline", page_icon=str(ASSETS / "icon.png"), layout="wide")

CSS = """
<style>
.block-container {max-width: 1120px; padding-top: 3.6rem;}
h1, h2, h3, h4 {font-family: Georgia, 'Times New Roman', serif !important;}
.stButton button[kind="primary"] {font-weight: 700; letter-spacing: .03em;}
.st-key-play button {min-height: 3.4rem; font-size: 1.3rem; letter-spacing: .18em;
                     box-shadow: 0 6px 0 #5e1d26, 0 10px 18px rgba(90, 30, 40, .3);}
.st-key-play button p {font-size: 1.3rem;}
.st-key-birth button {min-height: 3rem; letter-spacing: .12em;}
.st-key-birth button p {font-size: 1.15rem;}
/* menu */
.hero {position: relative; overflow: hidden; margin-top: 12px; border-radius: 22px; padding: 26px 12px 24px; text-align: center;
       background: radial-gradient(120% 90% at 50% 0%, #7a2a36 0%, #3b1a20 60%, #24100f 100%); color: #f6e7c8;
       box-shadow: inset 0 0 0 5px #b8892f, inset 0 0 0 8px #6e4a17, 0 10px 24px rgba(60, 20, 20, .25);}
.hero-gallery {display: flex; justify-content: center; gap: 12px; margin: 4px 0 10px;}
.hero-pic {flex: 0 0 auto; width: 92px; transform: rotate(var(--r));
           filter: drop-shadow(0 6px 8px rgba(0, 0, 0, .45));}
.hero-pic:nth-child(4) {width: 112px; margin-top: -6px;}
.hero-title {font-family: Georgia, serif; font-weight: 700; font-size: 3.6rem; line-height: 1.05; letter-spacing: .12em;
             color: #f3d27a; text-shadow: 0 3px 0 #6e4a17, 0 6px 18px rgba(0, 0, 0, .5); margin-top: 6px;}
.hero-tag {font-family: Georgia, serif; font-style: italic; font-size: 1.3rem; margin-top: 2px;}
.hero-intro {max-width: 620px; margin: 10px auto 0; font-size: .98rem; color: #ead9b8;}
.section-title {font-family: Georgia, serif; font-size: 1.45rem; font-weight: 700; margin: 1.2rem 0 .2rem;}
.challenge {text-align: center; font-weight: 700; color: #8c2f39;}
/* cards */
.portrait {max-width: 150px; margin: 0 auto;}
.portrait-big {max-width: 230px; margin: 0 auto;}
.card-name {text-align: center; font-weight: 700; margin: .35rem 0 .15rem; font-size: 1rem; overflow-wrap: anywhere;}
.card-hint {font-style: italic; color: #5d5349; font-size: .88rem; text-align: center; overflow-wrap: anywhere;}
.chip {display: inline-block; max-width: 100%; border: 1px solid; border-radius: 999px; padding: .05rem .55rem;
       font-size: .78rem; margin: .1rem .1rem; white-space: normal; overflow-wrap: anywhere; line-height: 1.35;}
.chips {text-align: center; margin: .2rem 0;}
.tests {margin-top: .35rem;}
[class*="st-key-card-"] {gap: .45rem;}
[class*="st-key-card-"] [data-testid="stMarkdownContainer"] {margin-bottom: 0;}
.card-hint {margin-bottom: .1rem;}
.test-line {font-size: .8rem; line-height: 1.35; text-align: center; overflow-wrap: anywhere;}
.test-line .dot {margin: 0 .3rem 0 0; width: .6rem; height: .6rem;}
/* tree */
.couple-title {font-weight: 700; text-align: center; font-size: .9rem;}
.slot-pic {width: 80px; margin: 0 auto; transition: transform .12s ease, filter .12s ease;}
.slot-name {font-size: .8rem; font-weight: 700; text-align: center; white-space: nowrap; overflow: hidden;
             text-overflow: ellipsis; max-width: 88px; min-height: 1.2rem; margin-top: 2px;}
[class*="st-key-slot-"]:not([class*="st-key-slot-btn"]) {position: relative; cursor: pointer; min-height: 126px;}
[class*="st-key-slot-"]:not([class*="st-key-slot-btn"]):hover .slot-pic {transform: translateY(-3px) scale(1.04);
    filter: drop-shadow(0 6px 8px rgba(60, 20, 20, .35));}
[class*="st-key-slot-btn"] {position: absolute !important; inset: 0; z-index: 2; margin: 0 !important;}
[class*="st-key-slot-btn"] .stButton, [class*="st-key-slot-btn"] button {width: 100% !important; height: 100% !important;}
[class*="st-key-slot-btn"] button {opacity: 0; cursor: pointer;}
[class*="st-key-cbox-"] {container-type: inline-size;}
@container (max-width: 190px) {
  [class*="st-key-couple-"] {flex-direction: column !important;}
  [class*="st-key-couple-"] .heart {margin: -8px 0 8px !important;}
}
.st-key-tree-btn button {min-height: 3rem; border: 2px solid #8c2f39; font-weight: 700;}
.st-key-tree-btn button p {font-size: 1.05rem;}
@media (min-width: 641px) {
  [data-testid="stHorizontalBlock"]:has([class*="st-key-card-"]) {align-items: stretch;}
  [data-testid="stColumn"]:has(> div > [class*="st-key-card-"]) > div,
  [data-testid="stColumn"]:has([class*="st-key-card-"]) > [data-testid="stVerticalBlock"],
  [data-testid="stLayoutWrapper"]:has(> [class*="st-key-card-"]) {height: 100%;}
  [class*="st-key-card-"] {height: 100%; justify-content: flex-start;}
  [class*="st-key-card-"] > div:first-child {flex: 1 0 auto;}
}
.heart {color: #8c2f39; font-size: 1rem; margin: 0 4px 18px;}
.tree-wrap {overflow-x: auto; -webkit-overflow-scrolling: touch;}
.tree-wrap svg {min-width: 620px;}
.tree-wrap.lower {margin-top: -14px;}
/* result */
.banner {border-radius: 14px; padding: 1rem 1.2rem; margin: .4rem 0 1rem; text-align: center;}
.banner h2 {margin: 0; padding: 0;}
.banner p {margin: .3rem 0 0;}
.legend {font-size: .85rem; text-align: center; margin-top: .4rem; color: #6b6158;}
.brand {display: flex; align-items: center; gap: .55rem; font-family: Georgia, serif; font-weight: 700;
        font-size: 2rem; color: #2b2420;}
.brand-logo svg {width: 2.3rem; height: 2.3rem; display: block;}
.hero-logo svg {width: .82em; height: .82em; vertical-align: -0.08em; margin-right: .18em;
                filter: drop-shadow(0 3px 6px rgba(0, 0, 0, .45));}
.dot {display: inline-block; width: .7rem; height: .7rem; border-radius: 50%; margin: 0 .25rem 0 .7rem;
      vertical-align: middle;}
.qr {max-width: 200px;}
.seed {font-family: ui-monospace, monospace; font-weight: 700;}
@media (max-width: 640px) {
  .portrait {max-width: 110px;}
  .portrait-big {max-width: 170px;}
  .qr {max-width: 150px;}
  .hero-title {font-size: 2.5rem; letter-spacing: .08em;}
  .hero-pic {width: 70px;}
  .hero-pic:nth-child(4) {width: 86px;}
  .tree-wrap.lower {margin-top: 0;}
}
</style>
"""

OUTCOME_STYLE = {
    "perfect": ("🏆", "#3f9d5a"),
    "win": ("✅", "#5a8fbf"),
    "loss": ("💀", "#d83a3a"),
}


# ---------------------------------------------------------------- shared state
@st.cache_resource
def get_config():
    return load_config()


@st.cache_resource
def store():
    return get_store()


@st.cache_data(ttl=20, show_spinner=False)
def load_records() -> list[dict]:
    return store().load()


def init_state() -> None:
    ss = st.session_state
    ss.setdefault("lang", DEFAULT_LANGUAGE)
    ss.setdefault("screen", "menu")
    ss.setdefault("player", "")  # widget keys are dropped when a screen hides them
    ss.setdefault("nick", ss.player)
    ss.setdefault("game", None)
    ss.setdefault("show_tree", False)
    if not ss.get("booted"):  # first run of this browser session: read ?seed=
        ss.booted = True
        ss.seed_input = str(st.query_params.get("seed", ""))
        if ss.seed_input:
            st.toast(translate(ss.lang, "menu.challenge_loaded", seed=ss.seed_input), icon="⚔️")
    ss.setdefault("seed_input", "")


def t(key: str, **params) -> str:
    return translate(st.session_state.lang, key, **params)


def go(screen: str) -> None:
    st.session_state.screen = screen


def fmt_pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def public_url() -> str:
    return settings.get("BLOODLINE_PUBLIC_URL").rstrip("/")


# ---------------------------------------------------------------- header
def header(show_title: bool) -> None:
    left, right = st.columns([5, 1], vertical_alignment="center")
    if show_title:
        left.markdown(f'<div class="brand"><span class="brand-logo">{LOGO_SVG}</span>Bloodline</div>',
                      unsafe_allow_html=True)
    with right:
        choice = st.segmented_control(
            "lang",
            LANGUAGES,
            default=st.session_state.lang,
            format_func=str.upper,
            label_visibility="collapsed",
            key="lang_select",
            required=True,
        )
        if choice and choice != st.session_state.lang:
            st.session_state.lang = choice
            st.rerun()


# ---------------------------------------------------------------- menu
def start_game(seed: int | None) -> None:
    st.session_state.game = Game(get_config(), seed=seed)
    st.session_state.show_tree = False
    st.session_state.saved = False
    go("build")


def try_start() -> None:
    nick = st.session_state.nick.strip()
    raw = st.session_state.seed_input.strip().lstrip("#")
    if not nick:
        st.session_state.menu_error = t("menu.need_nick")
    elif raw and (not raw.isdigit() or not 1 <= int(raw) <= SEED_MAX):
        st.session_state.menu_error = t("menu.bad_seed", max=SEED_MAX)
    else:
        st.session_state.menu_error = ""
        st.session_state.player = nick
        start_game(int(raw) if raw else None)


def screen_menu() -> None:
    ss = st.session_state
    ss.setdefault("hero_seed", random_seed())
    st.markdown(
        '<div class="hero">'
        f"{ui.hero_gallery(ss.hero_seed)}"
        f'<div class="hero-title"><span class="hero-logo">{LOGO_SVG}</span>BLOODLINE</div>'
        f'<div class="hero-tag">{t("menu.tagline")}</div>'
        f'<div class="hero-intro">{t("menu.intro")}</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.write("")
        if not ss.get("nick"):
            ss.nick = ss.player
        st.text_input(t("menu.nick"), key="nick", max_chars=20, placeholder=t("menu.nick_placeholder"))
        if ss.seed_input:
            st.markdown(f'<div class="challenge">⚔️ {t("menu.challenge", seed=ss.seed_input)}</div>',
                        unsafe_allow_html=True)
        st.button(t("menu.play"), key="play", type="primary", icon="🎲", width="stretch", on_click=try_start)
        if ss.get("menu_error"):
            st.error(ss.menu_error)
        with st.expander(t("menu.have_code"), icon="🎟️", expanded=False):
            st.text_input(t("menu.seed"), key="seed_input", max_chars=6, help=t("menu.seed_help"))
        c1, c2 = st.columns(2)
        with c1.popover(t("rules.title"), icon="📜", width="stretch"):
            st.markdown(t("rules.body"))
        with c2.popover(t("menu.share"), icon="📱", width="stretch"):
            st.markdown(f'<div class="qr">{ui.qr_svg(public_url())}</div>', unsafe_allow_html=True)
            st.code(public_url(), language=None)

    st.markdown(f'<div class="section-title">🏅 {t("ranking.hall")}</div>', unsafe_allow_html=True)
    ranking_tables(height=320)
    st.caption(t("menu.footer", version=__version__))


# ---------------------------------------------------------------- building
def on_test(cid: str, gene_id: str | None) -> None:
    st.session_state.game.run_test(cid, gene_id)


def on_birth() -> None:
    game: Game = st.session_state.game
    game.resolve()
    if not st.session_state.get("saved"):
        try:
            store().save(game.record(st.session_state.player, st.session_state.lang, __version__))
            load_records.clear()
        except Exception as exc:  # the game must go on even if the sheet fails
            st.session_state.save_error = str(exc)
        st.session_state.saved = True
    go("result")


def card_body(game: Game, cid: str) -> str:
    """Portrait, name, status chips, clue and test results of a candidate."""
    cfg, lang = game.config, st.session_state.lang
    c = game.candidate(cid)
    chips = []  # disease status stays hidden until a test reveals it
    slot = game.slot_of(cid)
    if slot is not None:
        chips.append(ui.chip(t("card.placed", n=slot // 2 + 1), "#8c2f39"))
    tests = "".join(
        f'<div class="test-line"><span class="dot" style="background:{STATUS_COLORS[res]}"></span>'
        f"{escape(ui.disease_name(cfg, gid, lang))}: <b>{escape(ui.test_label(t, res, c.sex))}</b></div>"
        for gid, res in game.test_results(cid).items()
    )
    return (
        f'<div class="portrait">{ui.portrait(c, game.model)}</div>'
        f'<div class="card-name">{escape(c.name)}</div>'
        f'<div class="chips">{"".join(chips)}</div>'
        f'<div class="card-hint">“{escape(ui.hint_text(t, c, cfg, lang))}”</div>'
        f'<div class="tests">{tests}</div>'
    )


def test_controls(game: Game, cid: str, prefix: str) -> None:
    cfg, lang = game.config, st.session_state.lang
    if cfg.rules.test_scope == "all":
        st.button(
            t("card.test_all"),
            key=f"{prefix}test-{cid}",
            icon="🧪",
            width="stretch",
            disabled=not game.can_test(cid),
            on_click=on_test,
            args=(cid, None),
        )
        return
    pending = [d for d in cfg.diseases if game.can_test(cid, d.id)]
    with st.popover(t("card.test"), icon="🧪", width="stretch", disabled=not pending, key=f"{prefix}pop-{cid}"):
        st.caption(t("card.test_pick", left=game.tests_left))
        for d in pending:
            st.button(d.label(lang), key=f"{prefix}test-{cid}-{d.id}", width="stretch", on_click=on_test, args=(cid, d.id))


def candidate_card(game: Game, cid: str) -> None:
    with st.container(border=True, key=f"card-g-{cid}"):
        st.markdown(card_body(game, cid), unsafe_allow_html=True)
        test_controls(game, cid, "g-")


def pick_dialog(slot: int) -> None:
    """Modal opened by tapping a slot of the tree: choose who goes there."""
    game: Game = st.session_state.game
    sex = slot_sex(slot)
    current = game.slots[slot]
    st.caption(t("pick.help", left=game.tests_left))
    if current is not None and st.button(t("pick.clear"), icon="🗑️"):
        game.assign(slot, None)
        st.rerun()
    people = game.candidates_of(sex)
    per_row = 5
    for start in range(0, len(people), per_row):
        cols = st.columns(per_row)
        for col, c in zip(cols, people[start : start + per_row]):
            with col, st.container(border=True, key=f"card-d-{c.id}"):
                st.markdown(card_body(game, c.id), unsafe_allow_html=True)
                if c.id == current:
                    st.button(t("pick.here"), key=f"pick-{c.id}", icon="✅", width="stretch", disabled=True)
                elif st.button(t("pick.choose"), key=f"pick-{c.id}", type="primary", width="stretch"):
                    game.assign(slot, c.id)
                    st.rerun()
                test_controls(game, c.id, "d-")


def open_picker(slot: int) -> None:
    sex = slot_sex(slot)
    title = t(f"pick.title.{sex}", n=slot // 2 + 1)
    st.dialog(title, width="large", on_dismiss="rerun")(pick_dialog)(slot)


def founder_slot(game: Game, slot: int) -> None:
    """A frame of the tree. The whole frame is a (transparent) button."""
    cid = game.slots[slot]
    level, sex = game.generations, slot_sex(slot)
    with st.container(key=f"slot-{slot}", width=88, gap=None, horizontal_alignment="center"):
        if cid is None:
            pic, name = ui.empty_slot(level, sex), ""
        else:
            c = game.candidate(cid)
            pic, name = ui.portrait(c, game.model), c.name.split()[0]
        st.markdown(
            f'<div class="slot-pic">{pic}</div><div class="slot-name">{escape(name) or "&nbsp;"}</div>',
            unsafe_allow_html=True,
        )
        if st.button(t(f"build.pick.{sex}"), key=f"slot-btn-{slot}"):
            open_picker(slot)


def screen_build() -> None:
    game: Game = st.session_state.game
    cfg = game.config
    top = st.columns([3, 2, 2], vertical_alignment="center")
    top[0].markdown(f'{t("build.game")} <span class="seed">#{game.seed:06d}</span>', unsafe_allow_html=True)
    top[1].markdown(t("build.tests_left", left=game.tests_left, total=cfg.rules.tests_per_game))
    top[2].button(t("build.menu"), icon="🏠", width="stretch", on_click=go, args=("menu",))

    st.markdown(f"### {t('build.title')}")
    st.caption(t("build.help"))

    n_couples = len(game.slots) // 2
    cols = st.columns(n_couples, gap="small")
    for k in range(n_couples):
        with cols[k].container(border=True, horizontal_alignment="center", key=f"cbox-{k}"):
            st.markdown(f'<div class="couple-title">{t("build.couple", n=k + 1)}</div>', unsafe_allow_html=True)
            with st.container(
                horizontal=True, horizontal_alignment="center", vertical_alignment="center", gap=None, key=f"couple-{k}"
            ):
                founder_slot(game, 2 * k)
                st.markdown('<div class="heart">❤</div>', unsafe_allow_html=True)
                founder_slot(game, 2 * k + 1)
    st.markdown(f'<div class="tree-wrap lower">{ui.lower_tree(game, t)}</div>', unsafe_allow_html=True)

    ready = game.is_complete
    with st.container(horizontal_alignment="center"):
        st.button(t("build.birth"), key="birth", type="primary", width=300, disabled=not ready, on_click=on_birth)
    if not ready:
        st.caption(t("build.birth_help"))

    st.markdown(f"#### {t('build.candidates')}")
    st.caption(t("build.candidates_help"))
    tabs = st.tabs([f"{SEX_MD['M']} {t('build.tab.M')}", f"{SEX_MD['F']} {t('build.tab.F')}"])
    for tab, sex in zip(tabs, ("M", "F")):
        with tab:
            people = game.candidates_of(sex)
            per_row = 5
            for start in range(0, len(people), per_row):
                cols = st.columns(per_row)
                for col, c in zip(cols, people[start : start + per_row]):
                    with col:
                        candidate_card(game, c.id)


# ---------------------------------------------------------------- result
def new_game_same_nick() -> None:
    st.session_state.seed_input = ""
    start_game(None)


def outcome_text_key(outcome: str, sex: str) -> str:
    return f"result.{outcome}.text.{sex}" if outcome == "win" else f"result.{outcome}.text"


def screen_result() -> None:
    game: Game = st.session_state.game
    result = game.resolve()
    cfg, lang = game.config, st.session_state.lang
    risk = result.risk
    emoji, color = OUTCOME_STYLE[result.outcome]

    st.markdown(
        f'<div class="banner" style="background:{color}1f;border:2px solid {color}">'
        f"<h2>{emoji} {t(f'result.{result.outcome}.title')}</h2>"
        f"<p>{t(outcome_text_key(result.outcome, result.me.sex))}</p></div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([2, 3], gap="large")
    me = result.me
    with left:
        st.markdown(
            f'<div class="portrait-big">{ui.portrait(me, game.model, sick=bool(result.affected))}</div>'
            f'<div class="card-name">{t("role.me")}</div>',
            unsafe_allow_html=True,
        )
        chips = [
            ui.chip(f"{ui.disease_name(cfg, d.id, lang)}: {ui.test_label(t, game.model.test(me.genome, d.id), me.sex)}",
                    STATUS_COLORS[game.model.test(me.genome, d.id)])
            for d in cfg.diseases
        ]
        st.markdown(f'<div class="chips">{"".join(chips)}</div>', unsafe_allow_html=True)
    with right:
        st.markdown(f"### {t('result.risk_title', risk=fmt_pct(risk.p_loss))}")
        st.caption(t("result.risk_help"))
        m = st.columns(3)
        m[0].metric(t("result.p_perfect"), fmt_pct(risk.p_perfect))
        m[1].metric(t("result.p_win"), fmt_pct(risk.p_win_carrier))
        m[2].metric(t("result.p_loss"), fmt_pct(risk.p_loss))
        for d in cfg.diseases:
            r = risk.disease(d.id)
            carriers = [
                p.name.split()[0]
                for p in result.levels[game.generations]
                if game.model.test(p.genome, d.id) != "clear"
            ]
            st.progress(min(1.0, r.p_affected), text=f"**{d.label(lang)}**: {fmt_pct(r.p_affected)}")
            st.caption(
                t("result.carriers", names=", ".join(carriers)) if carriers else t("result.no_carriers")
            )
        if result.outcome == "loss" and risk.p_loss < 0.25:
            st.info(t("result.bad_luck"), icon="🎲")
        elif result.outcome != "loss" and risk.p_loss > 0.55:
            st.info(t("result.good_luck"), icon="🍀")

    with st.container(horizontal_alignment="center"):
        shown = st.session_state.show_tree
        st.button(
            t("result.hide_tree") if shown else t("result.show_tree"),
            key="tree-btn",
            icon="🌳",
            type="secondary",
            width=340,
            on_click=lambda: st.session_state.update(show_tree=not st.session_state.show_tree),
        )
    if st.session_state.show_tree:
        st.markdown(f'<div class="legend">👆 {t("result.tree_hint")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="tree-wrap">{ui.full_tree(game, result, t, lang)}</div>', unsafe_allow_html=True)

    if st.session_state.get("save_error"):
        st.warning(t("result.save_error"), icon="⚠️")

    st.markdown(f"#### {t('result.challenge_title')}")
    link = f"{public_url()}/?seed={game.seed}"
    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(t("result.challenge_text", seed=f"{game.seed:06d}"))
        st.code(link, language=None)
    with c2:
        st.markdown(f'<div class="qr">{ui.qr_svg(link)}</div>', unsafe_allow_html=True)

    b = st.columns(3)
    b[0].button(t("result.again"), type="primary", icon="🎲", width="stretch", on_click=new_game_same_nick)
    b[1].button(t("menu.ranking"), icon="🏅", width="stretch", on_click=go, args=("ranking",))
    b[2].button(t("build.menu"), icon="🏠", width="stretch", on_click=go, args=("menu",))


# ---------------------------------------------------------------- ranking
def ranking_tables(height: int | str = "auto") -> None:
    try:
        table = build_ranking(load_records())
    except Exception:
        st.error(t("ranking.error"))
        return
    min_games = get_config().rules.ranking_min_games
    if table.empty:
        st.info(t("ranking.empty"), icon="🪦")
        return
    cols = {
        "nick": t("ranking.col.nick"),
        "games": t("ranking.col.games"),
        "wins": t("ranking.col.wins"),
        "perfect": t("ranking.col.perfect"),
        "win_rate": t("ranking.col.win_rate"),
        "avg_risk": t("ranking.col.avg_risk"),
    }
    tabs = st.tabs([t("ranking.tab.wins"), t("ranking.tab.win_rate"), t("ranking.tab.risk")])
    views = (
        (by_wins(table), "ranking.help.wins"),
        (by_win_rate(table, min_games), "ranking.help.win_rate"),
        (by_avg_risk(table, min_games), "ranking.help.risk"),
    )
    for tab, (view, help_key) in zip(tabs, views):
        with tab:
            st.caption(t(help_key, min=min_games))
            shown = view.copy()
            medals = ["🥇", "🥈", "🥉"]
            shown.insert(0, "#", [medals[i] if i < 3 else str(i + 1) for i in range(len(shown))])
            shown["win_rate"] = (100 * shown["win_rate"]).round(1)
            shown["avg_risk"] = (100 * shown["avg_risk"]).round(1)
            rows_h = 38 + 35 * len(shown)
            st.dataframe(
                shown.rename(columns=cols),
                hide_index=True,
                width="stretch",
                height=min(height, rows_h) if isinstance(height, int) else height,
                column_config={
                    cols["win_rate"]: st.column_config.NumberColumn(format="%.1f%%"),
                    cols["avg_risk"]: st.column_config.NumberColumn(format="%.1f%%"),
                },
            )


def screen_ranking() -> None:
    st.markdown(f"### 🏅 {t('ranking.title')}")
    ranking_tables()
    c1, c2 = st.columns(2)
    c1.button(t("ranking.refresh"), icon="🔄", width="stretch", on_click=load_records.clear)
    c2.button(t("build.menu"), icon="🏠", width="stretch", on_click=go, args=("menu",))


# ---------------------------------------------------------------- main
def main() -> None:
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    screen = st.session_state.screen
    if screen in ("build", "result") and st.session_state.game is None:
        screen = "menu"
    header(show_title=screen != "menu")
    {"menu": screen_menu, "build": screen_build, "result": screen_result, "ranking": screen_ranking}[screen]()


main()
