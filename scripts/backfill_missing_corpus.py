"""
Backfill missing corpus from the live DB into `padyalu_json_data/*.json`.

Context
-------
Some poem-source/poet combinations exist in `padyarchana.db` but have no
corresponding json file under `padyalu_json_data/`. The first-run
bootstrap (`app.bootstrap.auto_bootstrap_if_empty`) reads only that
folder, so a from-scratch checkout silently loses those rows.

This script dumps each (source, poet) pair listed in `TARGETS` to its
own json file in the standard schema so a fresh bootstrap reproduces
the live state exactly.

Reproducibility strategy
------------------------
For each poem we record:
  * lines_telugu — `text` split on `\n`
  * Chandassu    — meter name (joined from meters table)
  * kanda        — preserved verbatim
  * bhavam       — preserved verbatim
  * prathipadartham — preserved verbatim
  * id           — derived from the live title's `c<N>` / `<N>` trailing
                   segment when possible; falls back to a sequential index
  * chapter      — extracted from titles like
                   `{source} - {chapter} - c{id}` when present
  * title        — set explicitly only when the live title can't be
                   reconstructed from id/kanda/chapter (e.g. శతకాలు that
                   use the first line as title). Honored by the patched
                   `scripts/import_json.py`.

Run with:
    ./venv/bin/python scripts/backfill_missing_corpus.py
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "padyarchana.db"
OUT_DIR = ROOT / "padyalu_json_data"

# (source_in_db, poet_id, output_filename_stem, [optional metadata overrides])
TARGETS = [
    # ── poet 91 గోపీనాథము వేంకటకవి (3 works) ───────────────────────────
    ("గోపీనాథ రామాయణము", 91, "gopinatha_ramayanamu_gopinathamu_venkatakavi", "కావ్యము"),
    ("శిశుపాలవధ మహాకావ్యము", 91, "shishupalavadha_mahakavyam_gopinathamu_venkatakavi", "మహాకావ్యము"),
    ("మారుతి శతకము", 91, "maaruti_satakam_gopinathamu_venkatakavi", "శతకం"),

    # ── single-poet works ──────────────────────────────────────────────
    ("తాలాంకనందినీపరిణయము", 97, "talankanandiniparinayamu_asuri_maringanti", "కావ్యము"),
    ("శ్రీ ప్రబంధరాజ వేంకటేశ్వర విజయ విలాసము", 92, "prabandharaja_venkateswara_vijaya_vilasamu_ganapavarapu", "కావ్యము"),
    ("చంద్రికా పరిణయము", 89, "chandrika_parinayamu_surabhi_madhava_rayalu", "కావ్యము"),
    ("ధనుర్విద్యావిలాసము", 90, "dhanurvidyavilasamu_krishnamacharyudu", "కావ్యము"),
    ("రాధికాసాంత్వనము", 93, "radhikasantvanamu_muddupalani", "కావ్యము"),
    ("అహల్యాసంక్రందనము", 88, "ahalyasankrandanamu_samukham_venkata_krishnappa", "కావ్యము"),

    # ── శతకాలు (first-line is the live title — use explicit `title`) ──
    ("సుమతీ శతకము", 3, "sumati_satakam_baddena", "శతకం"),
    ("మంచి మాట వినర మానవుండ! శతకం", 100, "manchi_mata_satakam_kameshwaramma", "శతకం"),
    ("ఆంధ్రనాయక శతకము", 99, "andhra_nayaka_satakam_kasula_purushottama", "శతకం"),
    ("తరికొండ నృసింహశతకము", 98, "tarikonda_nrusimha_satakam", "శతకం"),
    ("శృంగారామరుకావ్యము", 95, "srungaramaruka_kavyam_pina_tiruvengalappa", "కావ్యము"),
    ("శృంగార వృత్తపద్యాల శతకము", 96, "srungara_vrutta_padyalu_pedatirumalayya", "శతకం"),

    # ── special: ౦కుచేలోపాఖ్యానము is a sub-work attributed to పోతన ──────
    ("కుచేలోపాఖ్యానము", 85, "kuchelopakhyanamu_pothana", "కావ్యము"),
]


# Match the trailing `... - c<NN>` (multi-chapter) or `... - <NN>` (single)
_TRAIL_RE = re.compile(r"^(?P<prefix>.+?) - (?P<sep>c)?(?P<id>\d+)$")
# Match `{source} - {chapter} - c{id}` to extract chapter explicitly
_CHAPTER_RE = re.compile(r"^(?P<src>.+?) - (?P<chapter>[^-]+?) - c(?P<id>\d+)$")


def _row_to_poem(idx: int, source: str, row: sqlite3.Row) -> dict:
    """Convert one DB row to a poem dict in the importer's expected schema."""
    title = row["title"] or ""
    text = row["text"] or ""
    meter = row["meter_name"] or "Unknown"
    kanda = row["kanda"]

    # Try to recover the per-source id + chapter from the title.
    chapter = None
    poem_id = idx + 1
    use_explicit_title = False

    m = _CHAPTER_RE.match(title)
    if m and m.group("src").strip() == source.strip():
        chapter = m.group("chapter").strip()
        poem_id = int(m.group("id"))
    else:
        m2 = _TRAIL_RE.match(title)
        if m2 and m2.group("prefix").strip() == source.strip():
            poem_id = int(m2.group("id"))
        else:
            # Title doesn't follow the standard pattern (e.g. śatakams whose
            # title is the first line of the verse). Record it explicitly so
            # the importer round-trips it.
            use_explicit_title = True

    poem: dict = {
        "id": poem_id,
        "lines_telugu": text.split("\n") if text else [],
        "Chandassu": meter,
    }
    if chapter:
        poem["chapter"] = chapter
    if kanda:
        poem["kanda"] = kanda
    if row["bhavam"]:
        poem["bhavam"] = row["bhavam"]
    if row["prathipadartham"]:
        try:
            poem["prathipadartham"] = json.loads(row["prathipadartham"])
        except json.JSONDecodeError:
            # Stored value was already a JSON string — pass through.
            poem["prathipadartham"] = row["prathipadartham"]
    if use_explicit_title:
        poem["title"] = title
    return poem


def _dump_source(con: sqlite3.Connection, source: str, poet_id: int,
                 out_stem: str, literary_form: str) -> tuple[Path, int, bool]:
    con.row_factory = sqlite3.Row
    poet_row = con.execute(
        "SELECT id, name FROM poets WHERE id = ?", (poet_id,)
    ).fetchone()
    if not poet_row:
        raise ValueError(f"poet id {poet_id} not found")

    rows = con.execute(
        """
        SELECT p.id, p.title, p.text, p.kanda, p.bhavam, p.prathipadartham,
               m.name AS meter_name
        FROM poems p
        LEFT JOIN meters m ON m.id = p.meter_id
        WHERE p.source = ? AND p.poet_id = ?
        ORDER BY p.id
        """,
        (source, poet_id),
    ).fetchall()

    poems = [_row_to_poem(i, source, r) for i, r in enumerate(rows)]
    used_explicit = any("title" in p for p in poems)

    data = {
        "shatakam_title_telugu": source,
        "author_telugu": poet_row["name"],
        "year": None,
        "literary_form_telugu": literary_form,
        "source_url": None,
        "poems": poems,
    }

    out_path = OUT_DIR / f"{out_stem}.json"
    out_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out_path, len(poems), used_explicit


def main() -> None:
    con = sqlite3.connect(str(DB))
    print(f"backfilling from {DB}\n")
    total_poems = 0
    for source, poet_id, out_stem, literary_form in TARGETS:
        path, n, explicit = _dump_source(con, source, poet_id, out_stem, literary_form)
        flag = "  (explicit titles)" if explicit else ""
        print(f"  {path.name:<70} {n:>5} poems{flag}")
        total_poems += n
    con.close()
    print(f"\nwrote {len(TARGETS)} files · {total_poems:,} poems total")


if __name__ == "__main__":
    main()
