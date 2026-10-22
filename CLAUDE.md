# CLAUDE.md

Working notes for AI assistants (and humans) picking up this project. The
README covers setup, commands, structure and the model; this file holds the
context that is **not** visible from reading the code: decisions, conventions,
gotchas and what is pending. Keep it current: when a decision changes or a task
is done, update this file in the same change.

## What this is

Bloodline is a university TP at UNQ (class 4, "Funciones de distribución":
an educational game that simulates a probability distribution). It is an educational web game: the player picks 8
great-grandparents (4 man + woman couples) out of 20 candidates; grandparents,
parents and "Yo" are born at random; the goal is for Yo to be born without the
3 recessive hereditary diseases.

- Team of two. Santiago does **all** the programming and the deploy; his
  partner fills in the biology through a spreadsheet (`scripts/sheet_sync.py`,
  guide in `docs/planilla.md`).
- Grading rubric: distribution justification 20%, Python implementation with
  `default_rng` and a seed 20%, validation 25% (QQ-plot, moments, goodness of
  fit), playability 5%, presentation 20%, validation report 10%.
- Deliverables: notebook (`notebooks/validation.ipynb`), 1-page rules
  (`docs/reglas.md`), 5-minute presentation, validation report.
- Public repo: github.com/AbrSantiago/bloodline (GPL-3.0).

## Game and model decisions (and why)

- **Model**: Mendelian, genotype = number of recessive alleles (0/1/2).
  Founders ~ Multinomial(1; p², 2pq, q²) (Hardy-Weinberg); each child gets one
  gamete from each parent (transmission matrix T = [[1,0],[.5,.5],[0,1]]).
  The exact risk is propagated through the pedigree and shown at the end.
  The genetics live behind an `InheritanceModel` interface so a V2 model can be
  added without touching the game.
- **Outcomes**: perfect win (no disease, no copies), win (healthy carrier),
  loss (at least one disease).
- **Disease frequencies** q = 0.70 / 0.15 / 0.10 (toy names: Tos de Quilmes,
  Fiebre del Bandoneón, Síndrome del Mate Frío). Tuned so a random tree loses
  ~50% and a hint-aware player ~41%; perfect wins are 5.3% random / 8.2% smart.
  Raising perfect wins without making losses rarer is a real trade-off,
  documented in `docs/planilla.md`; do not "fix" it by just lowering q.
- **Hints** on every card are always true (simulated parents/siblings).
  Disease status is hidden until tested. 4 free tests per game, each reveals
  one disease of one person (`test_scope` in `data/config.json`).
- **Determinism**: candidates use `default_rng([seed, 0])`, births
  `default_rng([seed, 1, *founder_numbers])`. Same code + same choices = same
  game. The seed is the shareable game code (`?seed=` link = challenge).
- **Ranking**: wins, win %, average risk. Only the first play of each seed per
  nick counts; win % and risk need `ranking_min_games` games.
- **Avatars** (`bloodline/avatar.py`) are SVG drawn at runtime, nothing
  pregenerated. Genes decide eyes/hair/freckles, generation decides the era
  (frame, clothes, hairstyles, hats), `avatar_seed` decides everything else.
  Moods: neutral; result screen Yo is `happy` (perfect), `smile` (win),
  `sick` (loss: sad face + thermometer).
- Skin tone is simplified: inherited from a random parent (not polygenic).

## Conventions

- Code, identifiers, comments, README: **English**. UI: Spanish by default with
  an ES/EN switch (`bloodline/i18n/es.json`, `en.json`; add every key to both).
  Partner-facing docs (`docs/planilla.md`, `docs/reglas.md`): Spanish.
- No emoji in the UI; icons are CSS masks (`bloodline/ui/icons.py`) or
  Streamlit `:material/...:` icons.
- Colours are CSS variables on `.stApp` defined with `light-dark()`; light and
  dark themes must both work.
- Must work on phone (≈390 px) and desktop. Check 1280, 1000, 700 and 390 px
  widths plus dark mode after UI changes.
- Dependencies with uv; after changing them re-export `requirements.txt`
  (`uv export --no-dev --no-hashes --no-emit-project -o requirements.txt`).
- Run `uv run pytest` after changes.

## Working agreements with Santiago

- **Never commit or push**; Santiago reviews and commits himself.
- **Never commit secrets.** `.env` and `.streamlit/secrets.toml` are
  gitignored; secrets go in the deploy service's Secrets box (production) and
  in `.env` locally. Every key must also appear, empty, in `.env.example`.
- Do not overwrite `docs/screenshot.png` (his own capture).
- He prefers a short plan and grouped UI requests; explain in Spanish.

## Streamlit gotchas already solved

- Streamlit 1.66. Restart the server after editing modules under
  `bloodline/`; it does not always reload them. Free the port with
  `fuser -k 8501/tcp` (never `pkill -f streamlit`, it can kill the shell).
- `st.dialog` content is rendered outside `.stApp`, so CSS variables do not
  reach it; use `color: inherit` there.
- `st.html` strips inline SVG inside buttons → use CSS-mask icons.
- A `<style>` inside an inline SVG is global → scope it with the SVG's id.
  Every rendered SVG needs unique clip-path ids (see `_ids` in `avatar.py`).
- Markdown containers have `margin-bottom: -1rem`; reset to 0 inside cards.
- Flag emojis do not render on Windows → the language switch uses SVG
  data-URI images.
- Keys on containers become `st-key-<key>` CSS classes; most layout CSS in
  `app.py` hangs off them.
- Widget values are lost when the screen changes; keep them in session state.

## Pending

1. Deploy on Streamlit Community Cloud (set `BLOODLINE_PUBLIC_URL` so QR and
   share links point to the public URL).
2. Google Sheets for results: create the service account, share the sheet,
   test `GSheetsStore` with real credentials (`BLOODLINE_STORAGE=gsheets`).
3. Validation report and the 5-minute presentation (based on the notebook).
4. Partner's biology data: import with `scripts/sheet_sync.py`, re-run the
   notebook, recheck the outcome balance.

## V2 roadmap (documented, not planned for the TP)

Complex-disease mode with a multivariate Normal, real-time PvP, incomplete
penetrance, dominant and X-linked diseases, polygenic skin tone.
