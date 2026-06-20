"""
Migration: collapse meter and poet variants into the canonical names we
settled on this session.

The corpus JSON files in `padyalu_json_data/` use a variety of spellings
for the same chandassu (e.g. క, కంద, కందము, కందం, కం., క. all mean the
same meter). The importer takes them at face value and creates a row per
distinct string, which is correct for a faithful first pass but leaves
the meters table cluttered.

Running this migration after the import normalises everything to one
canonical set:

  • Kandam variants                  → కందము
  • Aataveladi / Utpalamala / etc.  abbreviations → full canonical names
  • Sees + tetagiti compound forms  → "సీసము + తేటగీతి"
  • Trailing-period names (వ., గద్య., …) → bare form
  • Single-poem nāyikā categories  → కందము (per the session decisions)
  • కీర్తన meter                    → Unknown (it's a literary form,
                                       not a chandassu)
  • Poet "vemana" (English)         → "వేమన" (Telugu)
  • All జడ శతకము poems              → కందము
  • క్రీడాభిరామం's గీతము           → తేటగీతి (per author intent;
                                       the గీతము row is kept alive
                                       for any future imports that
                                       genuinely want it)

The migration is idempotent — running twice does nothing on the second
pass because there's no source row to merge from.

Called automatically from `app.bootstrap.auto_bootstrap_if_empty` after
the corpus import and before the FTS5 setup; running it before FTS5
exists avoids firing the per-row sync triggers thousands of times.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


# (source_names → target_name). Each source row is dropped after its
# poems are repointed.
_METER_MERGES: list[tuple[list[str], str]] = [
    # All kandam variants → కందము.
    (["కంద", "కందం", "కందపద్యం", "కందపద్యము", "క.", "కం.", "కం", "కం ."], "కందము"),
    # Aataveladi abbreviation.
    (["ఆ."], "ఆటవెలది"),
    # Utpalamala.
    (["ఉ.", "ఉ"], "ఉత్పలమాల"),
    # Champakamala.
    (["చ.", "చ"], "చంపకమాల"),
    # Shardulam.
    (["శార్దూలవిక్రీడితం", "శార్దూలము", "శా."], "శార్దూలవిక్రీడితము"),
    # Matthebham.
    (["మత్తేభవిక్రీడితం", "మత్తేభము", "మ."], "మత్తేభవిక్రీడితము"),
    # Sees.
    (["సీసపద్యము", "సీసపద్యం", "సీ."], "సీసము"),
    # Tetagiti — గీ. is also an abbreviation for tetagiti.
    (["తే.", "గీ."], "తేటగీతి"),
    # Sees + tetagiti compound forms (note: "సీసము, తేటగీति" has a
    # Devanagari 'ति' typo in some source files; matched here so it
    # also collapses).
    (
        [
            "సీసము + గీతము",
            "సీసము, తేటగీతి",
            "సీసము, తేటగీति",
            "సీసపద్యము, తేటగీతి",
            "సీసం/తేటగీతి",
            "సీసం + తేటగీతి",
        ],
        "సీసము + తేటగీతి",
    ),
    # సీసము2 + … duplicates of the canonical compound forms.
    (["సీసము2 + ఆటవెలది"], "సీసము + ఆటవెలది"),
    (["సీసము2 + తేటగీతి"], "సీసము + తేటగీతి"),
    # Sees + atavelaadi compound (the importer creates 'సీసం + ఆటవెలది'
    # variant too from some sources).
    (["సీసం + ఆటవెలది"], "సీసము + ఆటవెలది"),
    # Kīrtana is a literary form, not a meter — drop these poems into Unknown.
    (["కీర్తన"], "Unknown"),
]

# Trailing-period chandassu names — drop the period.
# If a target row with the bare name already exists, merge into it.
_METER_RENAMES: list[tuple[str, str]] = [
    ("వ.", "వచనము"),
    ("గద్య.", "గద్యము"),
    ("లయవిభాతి.", "లయవిభాతి"),
    ("మాలిని.", "మాలిని"),
]

# Nāyikā categories that mistakenly got entered as chandassu in the
# source for జడ శతకము. All of those poems are actually కందము.
_NAYIKA_NAMES: list[str] = [
    "అభిసారిక",
    "కలహాంతరిత",
    "ఖండిత",
    "ప్రోషితభర్తృక",
    "విప్రలబ్ద",
    "విరహోత్కంఠిత",
    "వాసకసజ్జిక",
    "స్వాధీన పతిక",
]


def _row_id(cur: sqlite3.Cursor, table: str, name: str) -> int | None:
    r = cur.execute(f"SELECT id FROM {table} WHERE name = ?", (name,)).fetchone()
    return r[0] if r else None


def _merge_meter(cur: sqlite3.Cursor, src_name: str, target_id: int) -> int:
    """Repoint poems from `src_name` to `target_id`, then drop the source
    row. Returns rowcount of repointed poems (0 if src didn't exist)."""
    src_id = _row_id(cur, "meters", src_name)
    if src_id is None or src_id == target_id:
        return 0
    cur.execute("UPDATE poems SET meter_id = ? WHERE meter_id = ?", (target_id, src_id))
    n = cur.rowcount
    cur.execute("DELETE FROM meters WHERE id = ?", (src_id,))
    return n


def apply(db_path: str | Path) -> dict:
    """Apply all meter + poet consolidations. Returns a small dict of
    counts for the bootstrap log."""
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = OFF")  # we manage referential integrity ourselves
    cur = con.cursor()
    repointed = 0
    rows_dropped = 0

    try:
        # 1. Meter merges.
        for sources, target in _METER_MERGES:
            target_id = _row_id(cur, "meters", target)
            if target_id is None:
                # Target doesn't exist — create it so we have somewhere
                # to send the orphans.
                cur.execute("INSERT INTO meters (name) VALUES (?)", (target,))
                target_id = cur.lastrowid
            for src_name in sources:
                n = _merge_meter(cur, src_name, target_id)
                if n:
                    repointed += n
                    rows_dropped += 1

        # 2. Trailing-period renames.
        for old, new in _METER_RENAMES:
            old_id = _row_id(cur, "meters", old)
            if old_id is None:
                continue
            new_id = _row_id(cur, "meters", new)
            if new_id is None:
                cur.execute("UPDATE meters SET name = ? WHERE id = ?", (new, old_id))
            else:
                cur.execute(
                    "UPDATE poems SET meter_id = ? WHERE meter_id = ?", (new_id, old_id)
                )
                repointed += cur.rowcount
                cur.execute("DELETE FROM meters WHERE id = ?", (old_id,))
                rows_dropped += 1

        # 3. All జడ శతకము poems → కందము (the source has nāyikā categories
        # mis-tagged as chandassu).
        kandam_id = _row_id(cur, "meters", "కందము")
        if kandam_id:
            cur.execute(
                "UPDATE poems SET meter_id = ? "
                "WHERE source = ? AND meter_id != ?",
                (kandam_id, "జడ శతకము", kandam_id),
            )
            repointed += cur.rowcount

            # Then collapse those nāyikā meter rows (now empty if they
            # were only used by జడ శతకము).
            for name in _NAYIKA_NAMES:
                n = _merge_meter(cur, name, kandam_id)
                if n:
                    repointed += n
                    rows_dropped += 1

        # 4. క్రీడాభిరామం's గీతము rows → తేటగీతి. Per the author's
        # intent, all 'గీతము' under that work is actually tetagiti. We
        # do NOT drop the గీతము meter row — it stays available in case
        # a later import genuinely uses it.
        tetagiti_id = _row_id(cur, "meters", "తేటగీతి")
        gita_id = _row_id(cur, "meters", "గీతము")
        if tetagiti_id and gita_id and tetagiti_id != gita_id:
            cur.execute(
                "UPDATE poems SET meter_id = ? "
                "WHERE source = ? AND meter_id = ?",
                (tetagiti_id, "క్రీడాభిరామం", gita_id),
            )
            repointed += cur.rowcount

        # 5. Poet "vemana" (English) → "వేమన" (Telugu).
        old = cur.execute("SELECT id FROM poets WHERE name = ?", ("vemana",)).fetchone()
        new = cur.execute("SELECT id FROM poets WHERE name = ?", ("వేమన",)).fetchone()
        if old:
            if new:
                cur.execute(
                    "UPDATE poems SET poet_id = ? WHERE poet_id = ?", (new[0], old[0])
                )
                repointed += cur.rowcount
                cur.execute("DELETE FROM poets WHERE id = ?", (old[0],))
                rows_dropped += 1
            else:
                cur.execute("UPDATE poets SET name = ? WHERE id = ?", ("వేమన", old[0]))

        con.commit()
    finally:
        con.close()

    return {"poems_repointed": repointed, "rows_dropped": rows_dropped}


if __name__ == "__main__":
    db = Path(__file__).parent.parent.parent / "padyarchana.db"
    if not db.exists():
        raise SystemExit(f"DB not found: {db}")
    stats = apply(db)
    print(f"poems repointed: {stats['poems_repointed']:,}")
    print(f"meter / poet rows dropped: {stats['rows_dropped']}")
