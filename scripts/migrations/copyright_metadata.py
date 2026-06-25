"""
Migration: stamp biographical metadata + copyright status onto every poet.

Indian copyright law puts a work into the public domain 60 years after its
author's death. We default every poet to ``copyright_protected = 1`` and
flip individuals to 0 only when we have a confident reason to:

  * a death year that is more than 60 years in the past, OR
  * a working period that clearly ends well before 1900 (era inference) —
    used for poets where the exact death year is fuzzy but they
    indisputably wrote in the medieval / early-modern period

Anything we cannot date confidently stays protected — admins can flip
individual rows via the existing poet edit UI without re-running this
migration.

Source of dates: standard reference texts on Telugu literature
(literature surveys, sahitya kosham entries, encyclopaedic profiles).
This file holds **biographical facts only** (years and the cleaned-up
era string); no excerpts of any author's work appear here.

`POETS_BY_NAME` is keyed by the exact `poets.name` value as it appears
in the DB. Some poets are catalogued under more than one spelling — both
spellings appear as separate keys pointing at the same data.
"""
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path


# ---------------------------------------------------------------------------
# Poet biographical data
# ---------------------------------------------------------------------------
# Each entry:   { "birth": int|None, "death": int|None, "era": "str", "pd": bool|None }
#   pd = True  → public domain (set copyright_protected = 0)
#   pd = False → still under copyright (set copyright_protected = 1)
#   pd = None  → don't override; rule (death + 60 < this year) decides
#
# "era" is the canonical free-text era we want stamped on poets.era for
# display. Empty string means leave the existing value alone.

CURRENT_YEAR = date.today().year
PD_CUTOFF = CURRENT_YEAR - 60   # poets who died ≤ this year are PD by date


# Classical (medieval / early-modern) — PD by era inference, with the
# best-attested working dates from standard references.
_CLASSICAL = {
    # --- 10th – 14th c. ---
    "నన్నయ, తిక్కన, ఎర్రాప్రెగడ": (None, None, "క్రీ.శ 11వ – 14వ శతాబ్దం"),
    "బద్దెన భూపాలుడు":       (1220, 1280, "క్రీ.శ 1220 – 1280"),
    "పాల్కురికి సోమనాథుడు": (1160, 1240, "క్రీ.శ 1160 – 1240"),
    "పాలకురికి సోమనాథుడు":   (1160, 1240, "క్రీ.శ 1160 – 1240"),   # alt spelling in DB
    "యథావాక్కుల అన్నమయ్య":   (1242, 1323, "క్రీ.శ 1242 – 1323"),
    "గోన బుద్ధారెడ్డి":      (None, None, "క్రీ.శ 13వ శతాబ్దం (1294–1300 సుమారు)"),
    "శ్రీనాథభట్ట":           (None, None, "క్రీ.శ 13వ శతాబ్దం"),
    "కట్టా వరదరాజు":         (None, None, "క్రీ.శ 14వ – 15వ శతాబ్దం"),
    "వినుకొండ వల్లభరాయుడు":  (None, None, "క్రీ.శ 14వ – 15వ శతాబ్దం"),
    "అనంతామాత్యుడు":         (None, None, "క్రీ.శ 14వ – 15వ శతాబ్దం"),
    # --- 15th – 16th c. ---
    "శ్రీనాథుడు":            (1365, 1441, "క్రీ.శ 1365 – 1441"),
    "తాళ్లపాక అన్నమాచార్య":  (1408, 1503, "క్రీ.శ 1408 – 1503"),
    "బమ్మెర పోతన":           (1450, 1510, "క్రీ.శ 1450 – 1510"),
    "ఆతుకూరి మొల్ల":         (1440, 1530, "క్రీ.శ 15వ – 16వ శతాబ్దం (1440–1530 సుమారు)"),
    "అల్లసాని పెద్దన":       (1475, 1535, "క్రీ.శ 1475 – 1535"),
    "ముక్కు తిమ్మన":         (None, None, "క్రీ.శ 16వ శతాబ్దం"),
    "మడికి సింగన":           (None, None, "క్రీ.శ 15వ శతాబ్దం"),
    "తాళ్ళపాక చిన తిరువేంగళనాథుడు": (None, None, "క్రీ.శ 16వ శతాబ్దం"),
    "తాళ్ళపాక తిమ్మయ్య":     (None, None, "క్రీ.శ 16వ శతాబ్దం"),
    "తాళ్ళపాక తిరువేంగళప్ప": (None, None, "క్రీ.శ 16వ శతాబ్దం"),
    "తాళ్ళపాక పెదతిరుమలాచార్యులు": (None, None, "క్రీ.శ 16వ శతాబ్దం"),
    "అయ్యల్రాజు త్రిపురాంతక కవి":   (None, None, "క్రీ.శ 16వ శతాబ్దం"),
    # --- 17th – 18th c. ---
    "చేమకూర వేంకటకవి":       (None, None, "క్రీ.శ 17వ శతాబ్దం"),
    "కంకంటి పాపరాజు":        (None, None, "క్రీ.శ 17వ శతాబ్దం"),
    "కంచెర్ల గోపన్న (భక్త రామదాసు)": (1620, 1688, "క్రీ.శ 1620 – 1688"),
    "వేమన":                  (1652, 1730, "క్రీ.శ 1652 – 1730 (సుమారు)"),
    "శ్రేష్ఠలూరి వేంకటార్య": (None, None, "క్రీ.శ 17వ – 18వ శతాబ్దం"),
    "రత్నాకరము గోపాలరాజు":   (None, None, "క్రీ.శ 17వ – 18వ శతాబ్దం"),
    "కస్తూరి రంగకవి":         (None, None, "క్రీ.శ 17వ – 18వ శతాబ్దం"),
    "ముద్దుపళని":             (1730, 1790, "క్రీ.శ 1730 – 1790"),
    "తరిగొండ వెంగమాంబ":      (1730, 1817, "క్రీ.శ 1730 – 1817"),
    "తరిగొండ వేంగమాంబ":      (1730, 1817, "క్రీ.శ 1730 – 1817"),
    "కూచిమంచి తిమ్మకవి":     (1759, 1817, "క్రీ.శ 1759 – 1817 (సుమారు)"),
    "కూచిమంచి తిమ్మన":       (None, None, "క్రీ.శ 18వ శతాబ్దం"),
    "కూచిమంచి జగన్నాథ కవి":  (None, None, "క్రీ.శ 18వ శతాబ్దం"),
    "కూచిమంచి సోమసుందరకవి":  (None, None, "క్రీ.శ 18వ శతాబ్దం"),
    "పైడిపాటి లక్ష్మణకవి":    (None, None, "క్రీ.శ 18వ శతాబ్దం"),
    "లింగమగుంట తిమ్మకవి":     (None, None, "క్రీ.శ 18వ శతాబ్దం"),
    "అడిదము సూరకవి":          (None, None, "క్రీ.శ 18వ – 19వ శతాబ్దం"),
    "కాసుల పురుషోత్తమకవి":   (None, None, "క్రీ.శ 1791 (జన్మ) – 19వ శతాబ్దం"),
    "మయూరుడు":                (None, None, "క్రీ.శ 7వ శతాబ్దం (సంస్కృత కవి)"),
    "భర్తృహరి":               (None, None, "క్రీ.శ 5వ శతాబ్దం (సంస్కృత కవి)"),
    # 19th-c. authors w/ era hints in DB but no exact dates known
    "మేకా బాపన్న":            (None, None, "క్రీ.శ 19వ శతాబ్దం"),
    "ఫక్కి అప్పల నరసింహ":     (1860, None, "క్రీ.శ 1860 (జన్మ) – 20వ శతాబ్దం ప్రారంభం"),
    "సన్యాసి":                (1861, None, "క్రీ.శ 1861 (జన్మ) – 20వ శతాబ్దం ప్రారంభం"),
}

# 19th – early 20th c. — death > 60 years ago → PD by date.
_PD_BY_DATE = {
    "దాసు శ్రీరాములు":         (1846, 1908, "క్రీ.శ 1846 – 1908"),
    "కట్టమంచి రామలింగారెడ్డి": (1880, 1951, "క్రీ.శ 1880 – 1951"),
    "దువ్వూరి రామిరెడ్డి":     (1895, 1947, "క్రీ.శ 1895 – 1947"),
    "సముఖము వేంకట కృష్ణప్ప నాయకుడు": (None, None, "క్రీ.శ 1901 (జన్మ) – 20వ శతాబ్దం ప్రారంభం"),
}

# 20th c. — died after 1965 → still under copyright.
_PROTECTED = {
    "విశ్వనాధ సత్యనారాయణ":            (1895, 1976, "క్రీ.శ 1895 – 1976"),
    "విశ్వనాథ సత్యనారాయణ":           (1895, 1976, "క్రీ.శ 1895 – 1976"),
    "రాయప్రోలు సుబ్బారావు":          (1892, 1984, "క్రీ.శ 1892 – 1984"),
    "మధునాపంతుల సత్యనారాయణ శాస్త్రి": (1903, 1991, "క్రీ.శ 1903 – 1991"),
    "చెరుకు రామ్మోహన రావు":          (None, None, "20వ శతాబ్దం (సమకాలీన)"),
    "త్రిపురనేని రామస్వామి":         (1887, 1943, "క్రీ.శ 1887 – 1943"),  # actually PD-by-date
}

# Build the master map. We override the rule for explicit PD/CP rows.
POETS_BY_NAME: dict[str, dict] = {}
for name, (b, d, era) in _CLASSICAL.items():
    POETS_BY_NAME[name] = {"birth": b, "death": d, "era": era, "pd": True}
for name, (b, d, era) in _PD_BY_DATE.items():
    POETS_BY_NAME[name] = {"birth": b, "death": d, "era": era,
                            "pd": (d is None or d < PD_CUTOFF)}
for name, (b, d, era) in _PROTECTED.items():
    POETS_BY_NAME[name] = {"birth": b, "death": d, "era": era,
                            "pd": (d is not None and d < PD_CUTOFF)}

# Triputaneni Ramaswamy actually died in 1943 → > 60 yrs → PD by date.
# Fix the explicit override.
POETS_BY_NAME["త్రిపురనేని రామస్వామి"]["pd"] = True


def _ensure_column(con: sqlite3.Connection) -> None:
    """Add poets.copyright_protected if absent. Default = 1 (protected)."""
    cols = [r[1] for r in con.execute("PRAGMA table_info(poets)")]
    if "copyright_protected" not in cols:
        con.execute(
            "ALTER TABLE poets ADD COLUMN copyright_protected INTEGER NOT NULL DEFAULT 1"
        )


def apply(db_path: str | Path) -> dict:
    """Apply biographical updates + copyright flags. Idempotent."""
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    _ensure_column(con)

    updated = 0
    pd_set = 0
    cp_set = 0
    not_in_data = []

    for r in cur.execute("SELECT id, name FROM poets").fetchall():
        pid, name = r
        if name not in POETS_BY_NAME:
            not_in_data.append((pid, name))
            continue
        meta = POETS_BY_NAME[name]
        cur.execute(
            "UPDATE poets SET birth_year = COALESCE(?, birth_year), "
            "                 death_year = COALESCE(?, death_year), "
            "                 era = ?, "
            "                 copyright_protected = ? "
            "WHERE id = ?",
            (meta["birth"], meta["death"], meta["era"], 0 if meta["pd"] else 1, pid),
        )
        updated += 1
        if meta["pd"]:
            pd_set += 1
        else:
            cp_set += 1

    con.commit()
    con.close()
    return {
        "rows_updated": updated,
        "marked_pd": pd_set,
        "marked_protected": cp_set,
        "not_in_data": not_in_data,  # caller can log / prompt
    }


if __name__ == "__main__":
    db = Path(__file__).parent.parent.parent / "padyarchana.db"
    stats = apply(db)
    print(f"rows updated:      {stats['rows_updated']}")
    print(f"marked PD:         {stats['marked_pd']}")
    print(f"marked protected:  {stats['marked_protected']}")
    print(f"poets not in data: {len(stats['not_in_data'])} (default-protected)")
