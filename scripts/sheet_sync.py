"""Sync the biology spreadsheet with ``data/config.json``.

The biology parameters (diseases, allele frequencies, names, fun facts) are
edited in a spreadsheet so nobody has to touch JSON or the repo.

Usage
-----
Create the spreadsheet template from the current config::

    python scripts/sheet_sync.py export --xlsx bloodline_data.xlsx

Upload that file to Google Sheets (File > Import), edit it, share it as
"Anyone with the link: Viewer" and import it back::

    python scripts/sheet_sync.py import --sheet-id <ID from the sheet URL>

or import a local Excel file::

    python scripts/sheet_sync.py import --xlsx bloodline_data.xlsx

The import validates everything before overwriting ``data/config.json``.
Then commit the new JSON so the app and the notebook use it.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bloodline.config import DEFAULT_CONFIG_PATH, config_from_dict  # noqa: E402

TABS = ("game", "genes", "skin_tones", "names", "fun_facts")


# ---------------------------------------------------------------- export
def to_frames(raw: dict) -> dict[str, pd.DataFrame]:
    game = dict(raw["game"])
    lo, hi = game.pop("siblings_range")
    game["siblings_min"], game["siblings_max"] = lo, hi
    genes = [
        {
            "id": g["id"],
            "kind": g["kind"],
            "name_es": g["name"].get("es", ""),
            "name_en": g["name"].get("en", ""),
            "recessive_freq": g["recessive_freq"],
            "trait": g.get("trait") or "",
            "dominant": "" if g.get("dominant") is None else g["dominant"],
            "recessive": "" if g.get("recessive") is None else g["recessive"],
        }
        for g in raw["genes"]
    ]
    names = raw["names"]
    return {
        "game": pd.DataFrame({"key": list(game), "value": list(game.values())}),
        "genes": pd.DataFrame(genes),
        "skin_tones": pd.DataFrame({"tone": list(raw["skin_tones"]), "probability": list(raw["skin_tones"].values())}),
        "names": pd.concat(
            [pd.Series(names["F"], name="female"), pd.Series(names["M"], name="male"), pd.Series(names["surnames"], name="surname")],
            axis=1,
        ),
        "fun_facts": pd.DataFrame(raw.get("fun_facts", []), columns=["es", "en"]),
    }


def export_xlsx(config_path: Path, out: Path) -> None:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    with pd.ExcelWriter(out) as writer:
        for tab, df in to_frames(raw).items():
            df.to_excel(writer, sheet_name=tab, index=False)
    print(f"Template written to {out}")


# ---------------------------------------------------------------- import
def _value(v):
    """Spreadsheet cell -> JSON value (numbers, booleans, text)."""
    if isinstance(v, str):
        s = v.strip()
        if s.lower() in ("true", "verdadero"):
            return True
        if s.lower() in ("false", "falso"):
            return False
        try:
            f = float(s.replace(",", "."))
            return int(f) if f.is_integer() else f
        except ValueError:
            return s
    if hasattr(v, "item"):  # numpy scalar
        v = v.item()
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _clean(series: pd.Series) -> list:
    return [str(x).strip() for x in series.dropna() if str(x).strip()]


def from_frames(frames: dict[str, pd.DataFrame]) -> dict:
    game = {str(k).strip(): _value(v) for k, v in zip(frames["game"]["key"], frames["game"]["value"]) if pd.notna(k)}
    game["siblings_range"] = [game.pop("siblings_min"), game.pop("siblings_max")]
    genes = []
    for row in frames["genes"].to_dict("records"):
        if pd.isna(row.get("id")) or not str(row["id"]).strip():
            continue
        gene = {
            "id": str(row["id"]).strip(),
            "kind": str(row["kind"]).strip(),
            "recessive_freq": float(_value(row["recessive_freq"])),
            "name": {"es": str(row.get("name_es") or "").strip(), "en": str(row.get("name_en") or "").strip()},
        }
        if gene["kind"] == "cosmetic":
            gene["trait"] = str(row["trait"]).strip()
            gene["dominant"] = _value(row["dominant"])
            gene["recessive"] = _value(row["recessive"])
        genes.append(gene)
    skins = frames["skin_tones"].dropna()
    names = frames["names"]
    facts = frames["fun_facts"].fillna("")
    return {
        "version": 1,
        "game": game,
        "genes": genes,
        "skin_tones": {str(t).strip(): float(_value(p)) for t, p in zip(skins["tone"], skins["probability"])},
        "names": {"F": _clean(names["female"]), "M": _clean(names["male"]), "surnames": _clean(names["surname"])},
        "fun_facts": [
            {"es": str(r["es"]).strip(), "en": str(r["en"]).strip() or str(r["es"]).strip()}
            for r in facts.to_dict("records")
            if str(r["es"]).strip()
        ],
    }


def read_google_sheet(sheet_id: str) -> dict[str, pd.DataFrame]:
    """Read every tab of a sheet shared as 'anyone with the link can view'."""
    base = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet="
    return {tab: pd.read_csv(base + urllib.parse.quote(tab), dtype=str) for tab in TABS}


def read_xlsx(path: Path) -> dict[str, pd.DataFrame]:
    return {tab: pd.read_excel(path, sheet_name=tab, dtype=str) for tab in TABS}


def import_config(frames: dict[str, pd.DataFrame], out: Path) -> None:
    raw = from_frames(frames)
    config_from_dict(raw)  # raises with a clear message if something is wrong
    out.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {len(raw['genes'])} genes, {len(raw['fun_facts'])} fun facts -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    exp = sub.add_parser("export", help="config.json -> Excel template")
    exp.add_argument("--xlsx", type=Path, default=ROOT / "bloodline_data.xlsx")
    imp = sub.add_parser("import", help="spreadsheet -> config.json")
    src = imp.add_mutually_exclusive_group(required=True)
    src.add_argument("--sheet-id", help="Google Sheet id (shared as 'anyone with the link')")
    src.add_argument("--xlsx", type=Path, help="local Excel file")
    for p in (exp, imp):
        p.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()

    if args.command == "export":
        export_xlsx(args.config, args.xlsx)
    else:
        frames = read_google_sheet(args.sheet_id) if args.sheet_id else read_xlsx(args.xlsx)
        import_config(frames, args.config)


if __name__ == "__main__":
    main()
