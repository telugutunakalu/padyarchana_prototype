# -*- coding: utf-8 -*-
"""
Dwipada Analyser
================

A self-contained Telugu Dwipada (ద్విపద) prosody analyser with a command-line
interface. It validates whether a 2-line couplet conforms to the classical
Dwipada chandassu and reports a percentage match score. It can also be run
over a consolidated dataset to produce comprehensive statistics across
the corpus. Two input shapes are supported:
  - data/consolidated_dwipada.json — `source` is a dict with a `work` key
  - datasets/dwipada_consolidated.json — `source` is a plain string

What is Dwipada?
----------------
Dwipada (ద్విపద — "two-footed") is a Telugu poetic meter consisting of
2 lines. Each line must contain four prosodic feet (ganas):
    3 Indra ganas  +  1 Surya gana

Four rules govern Dwipada validity:

  1. Gana sequence    — each line partitions into 3 Indra + 1 Surya ganas,
                        where each gana is a known U/I (Guru/Laghu) pattern.
  2. Prasa  (ప్రాస)   — the 2nd syllable's base consonant must match between
                        line 1 and line 2 (rhyme).
  3. Yati   (యతి)     — within each line, the first letter of the 1st gana
                        must match (or be phonetically related to) the first
                        letter of the 3rd gana (alliteration).
  4. Syllable length  — each line's syllable count must lie in
                        [MIN_LINE_SYLLABLES, MAX_LINE_SYLLABLES] (11-15),
                        the bounds implied by the 3-Indra + 1-Surya inventory.

Scoring (0-100 %):
    Gana            — weight 1/4 (25 % per valid gana, averaged across 2 lines)
    Prasa           — weight 1/4 (binary: 100 % match, 0 % mismatch)
    Yati            — weight 1/4 (binary, averaged across 2 lines)
    Syllable length — weight 1/4 (binary per line, averaged across 2 lines)

Public Python API:
    analyze_dwipada(poem)         → full structured analysis (dict)
    format_analysis_report(d)     → human-readable text report
    analyze_pada(line)            → analyse one line
    analyze_single_line(line)     → text report for one line
    run_dataset_stats(json_path)  → aggregate stats over a poem-list JSON

Command-line usage:
    # Analyse a single poem
    python dwipada_analyser.py analyze "<line1>\\n<line2>"
    python dwipada_analyser.py analyze --file poem.txt
    python dwipada_analyser.py analyze --json --file poem.txt

    # Run statistics over the consolidated dataset
    python dwipada_analyser.py stats
    python dwipada_analyser.py stats --input path/to/file.json
    python dwipada_analyser.py stats --output stats.json
    python dwipada_analyser.py stats --no-by-source

Exit codes: 0 on success, 1 on input/parse error.

Based on Aksharanusarika v0.0.7a logic.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

###############################################################################
# § 1  TELUGU PROSODY GLOSSARY (ఛందస్సు పదకోశం)
###############################################################################
#
# BASIC TERMS:
#   - Aksharam  (అక్షరము): Syllable — the fundamental unit of Telugu writing.
#   - Gana      (గణము):    Prosodic foot — group of syllables with a pattern.
#   - Pada      (పాదము):   Line/verse — one line of poetry.
#   - Chandassu (ఛందస్సు): Meter/prosody — the rhythmic system.
#
# SYLLABLE WEIGHT:
#   - Guru (గురువు, U): Heavy/long syllable.
#   - Laghu (లఘువు, I): Light/short syllable.
#
# GANA TYPES IN DWIPADA:
#   - Indra ganas (ఇంద్ర గణములు, 3-4 syllables):
#         Nala (నల)   IIII   |  Naga (నగ)   IIIU
#         Sala (సల)   IIUI   |  Bha  (భ)    UII
#         Ra   (ర)    UIU    |  Ta   (త)    UUI
#   - Surya ganas (సూర్య గణములు, 2-3 syllables):
#         Na   (న)    III    |  Ha/Gala (హ/గల)  UI
#
# RULE TERMS:
#   - Prasa       (ప్రాస):       Rhyme — 2nd-syllable consonant matches across lines.
#   - Yati        (యతి):        Alliteration — 1st-letter match between gana 1 and gana 3.
#   - Yati Maitri (యతి మైత్రి):  Phonetic equivalence groups for yati.
#
# SPECIAL TERMS:
#   - Pollu hallu (పొల్లు హల్లు): Consonant + halant that cannot stand alone;
#                                merges with the previous syllable.
#   - Varga       (వర్గము):     Consonant class by place of articulation.
#   - Halant      (హలంతు, ్):    Vowel-killer mark.
#   - Anusvara    (అనుస్వారం, ం): Nasal sound marker.
#   - Visarga     (విసర్గ, ః):    Breath sound marker.
#
###############################################################################


###############################################################################
# § 2  LINGUISTIC CONSTANTS — Telugu character sets, vargas, equivalence groups
###############################################################################

# Map dependent-vowel signs to their independent vowel forms.
# Used by Svara Yati checking to compare vowel families regardless of consonant.
dependent_to_independent = {
    "ా": "ఆ", "ి": "ఇ", "ీ": "ఈ", "ు": "ఉ", "ూ": "ఊ", "ృ": "ఋ",
    "ౄ": "ౠ", "ె": "ఎ", "ే": "ఏ", "ై": "ఐ", "ొ": "ఒ", "ో": "ఓ", "ౌ": "ఔ",
}

# Halant (vowel-killer) marker.
halant = "్"

# All 35 standard Telugu consonants.
telugu_consonants = {
    "క", "ఖ", "గ", "ఘ", "ఙ", "చ", "ఛ", "జ", "ఝ", "ఞ",
    "ట", "ఠ", "డ", "ఢ", "ణ", "త", "థ", "ద", "ధ", "న",
    "ప", "ఫ", "బ", "భ", "మ", "య", "ర", "ల", "వ", "శ",
    "ష", "స", "హ", "ళ", "ఱ",
}

# Vowel classification sets.
long_vowels = {"ా", "ీ", "ూ", "ే", "ో", "ౌ", "ౄ"}
independent_vowels = {
    "అ", "ఆ", "ఇ", "ఈ", "ఉ", "ఊ", "ఋ", "ౠ",
    "ఎ", "ఏ", "ఐ", "ఒ", "ఓ", "ఔ",
}
independent_long_vowels = {"ఆ", "ఈ", "ఊ", "ౠ", "ఏ", "ఓ"}
diacritics = {"ం", "ః"}                                    # anusvara, visarga
dependent_vowels = set(dependent_to_independent.keys())

# Characters skipped during syllable splitting (whitespace, ZWNJ, stray punctuation, etc.).
ignorable_chars = {' ', '\n', 'ఁ', '​', '‌', ',', '-', ')', '1', '4'}

# -----------------------------------------------------------------------------
# YATI MAITRI GROUPS (యతి మైత్రి)
# -----------------------------------------------------------------------------
# Letters in the same group are treated as phonetically equivalent for Yati
# matching. E.g., 'క' and 'గ' satisfy yati because both lie in group #3.
YATI_MAITRI_GROUPS = [
    {"అ", "ఆ", "ఐ", "ఔ", "హ", "య", "అం", "అః"},
    {"ఇ", "ఈ", "ఎ", "ఏ", "ఋ"},
    {"ఉ", "ఊ", "ఒ", "ఓ"},
    {"క", "ఖ", "గ", "ఘ", "క్ష"},
    {"చ", "ఛ", "జ", "ఝ", "శ", "ష", "స"},
    {"ట", "ఠ", "డ", "ఢ"},
    {"త", "థ", "ద", "ధ"},
    {"ప", "ఫ", "బ", "భ", "వ"},
    {"ర", "ల", "ఱ", "ళ"},
    {"న", "ణ"},
    {"మ", "పు", "ఫు", "బు", "భు", "ము"},
]

# -----------------------------------------------------------------------------
# SVARA YATI GROUPS (స్వర యతి) — vowel-family harmony
# -----------------------------------------------------------------------------
# Used as a fallback yati: consonants ignored, vowels compared.
SVARA_YATI_GROUPS = [
    {"అ", "ఆ", "ఐ", "ఔ"},
    {"ఇ", "ఈ", "ఎ", "ఏ", "ఋ", "ౠ"},
    {"ఉ", "ఊ", "ఒ", "ఓ"},
]

# -----------------------------------------------------------------------------
# BINDU YATI (బిందు యతి) — anusvara to varga-nasal mapping
# -----------------------------------------------------------------------------
# A syllable carrying 'ం' can satisfy yati against the nasal of the same varga.
VARGA_NASALS = {
    "క": "ఙ", "ఖ": "ఙ", "గ": "ఙ", "ఘ": "ఙ",
    "చ": "ఞ", "ఛ": "ఞ", "జ": "ఞ", "ఝ": "ఞ",
    "ట": "ణ", "ఠ": "ణ", "డ": "ణ", "ఢ": "ణ",
    "త": "న", "థ": "న", "ద": "న", "ధ": "న",
    "ప": "మ", "ఫ": "మ", "బ": "మ", "భ": "మ",
}
NASAL_TO_VARGA = {
    "ఙ": {"క", "ఖ", "గ", "ఘ"},
    "ఞ": {"చ", "ఛ", "జ", "ఝ"},
    "ణ": {"ట", "ఠ", "డ", "ఢ"},
    "న": {"త", "థ", "ద", "ధ"},
    "మ": {"ప", "ఫ", "బ", "భ"},
}

# -----------------------------------------------------------------------------
# PRASA EQUIVALENTS (ప్రాస సమానాక్షరములు)
# -----------------------------------------------------------------------------
# Consonant pairs traditionally treated as equivalent for prasa.
PRASA_EQUIVALENTS = [
    {"ల", "ళ"},
    {"శ", "స"},
    {"ఱ", "ర"},
]

# -----------------------------------------------------------------------------
# CONSONANT VARGAS — grouping by place of articulation
# -----------------------------------------------------------------------------
# Used for prasa mismatch diagnostics and yati explanations.
CONSONANT_VARGAS = {
    "క-వర్గము (Velar)":       ["క", "ఖ", "గ", "ఘ", "ఙ"],
    "చ-వర్గము (Palatal)":     ["చ", "ఛ", "జ", "ఝ", "ఞ", "శ", "ష", "స"],
    "ట-వర్గము (Retroflex)":   ["ట", "ఠ", "డ", "ఢ", "ణ"],
    "త-వర్గము (Dental)":      ["త", "థ", "ద", "ధ", "న"],
    "ప-వర్గము (Labial)":      ["ప", "ఫ", "బ", "భ", "మ"],
    "య-వర్గము (Approximant)": ["య", "ర", "ల", "వ", "ళ", "ఱ"],
    "హ-వర్గము (Aspirate)":    ["హ"],
}

# -----------------------------------------------------------------------------
# SCORING CONSTANTS
# -----------------------------------------------------------------------------
EXPECTED_GANAS_PER_LINE = 4           # 3 Indra + 1 Surya per line.
SCORE_PER_VALID_GANA = 25.0           # 4 ganas × 25 % = 100 %.

YATI_EXACT_MATCH_SCORE = 100.0        # Same letter (e.g., స ↔ స).
YATI_VARGA_MATCH_SCORE = 100.0        # Same varga (e.g., క ↔ గ) — full credit.
YATI_NO_MATCH_SCORE = 0.0

PRASA_MATCH_SCORE = 100.0
PRASA_NO_MATCH_SCORE = 0.0

# Weights for the overall percentage score.
# Equal weights — each of the four rules contributes one quarter.
SCORE_WEIGHTS = {
    "gana": 1 / 4,
    "prasa": 1 / 4,
    "yati": 1 / 4,
    "syllable_length": 1 / 4,
}

# -----------------------------------------------------------------------------
# GANA PATTERNS — exhaustive U/I sequences for Indra and Surya ganas
# -----------------------------------------------------------------------------
INDRA_GANAS = {
    "IIII": "Nala (నల)",
    "IIIU": "Naga (నగ)",
    "IIUI": "Sala (సల)",
    "UII":  "Bha (భ)",
    "UIU":  "Ra (ర)",
    "UUI":  "Ta (త)",
}

SURYA_GANAS = {
    "III": "Na (న)",
    "UI":  "Ha/Gala (హ/గల)",
}

# Per-line syllable bounds derived from the gana inventory: each line is
# 3 Indra ganas (3-4 syllables each) + 1 Surya gana (2-3 syllables), so
# a valid Dwipada line carries between 11 and 15 syllables.
_INDRA_LENS = [len(p) for p in INDRA_GANAS]
_SURYA_LENS = [len(p) for p in SURYA_GANAS]
MIN_LINE_SYLLABLES = 3 * min(_INDRA_LENS) + min(_SURYA_LENS)  # 3*3 + 2 = 11
MAX_LINE_SYLLABLES = 3 * max(_INDRA_LENS) + max(_SURYA_LENS)  # 3*4 + 3 = 15

SYLLABLE_LENGTH_MATCH_SCORE = 100.0
SYLLABLE_LENGTH_NO_MATCH_SCORE = 0.0


###############################################################################
# § 3  LETTER CLASSIFICATION — varga lookup, full letter info
###############################################################################

def get_consonant_varga(consonant: str) -> Optional[str]:
    """Return the varga name for a Telugu consonant, or None if not a consonant.

    Vargas group consonants by place of articulation (ఉచ్చారణ స్థానం); the
    name is used in diagnostics ("ఆ-వర్గము (Velar)" etc.).
    """
    if not consonant:
        return None
    for varga_name, consonants in CONSONANT_VARGAS.items():
        if consonant in consonants:
            return varga_name
    return None


def get_letter_info(letter: str) -> Dict:
    """Return a complete classification dict for a Telugu letter.

    Fields:
      - letter:             The input letter.
      - type:               "vowel" | "consonant" | "unknown".
      - varga:              Varga name (only for consonants).
      - yati_groups:        Indices of YATI_MAITRI_GROUPS containing the letter.
      - yati_group_members: Flattened, deduplicated members from those groups.
    """
    result = {
        "letter": letter,
        "type": "unknown",
        "varga": None,
        "yati_groups": [],
        "yati_group_members": [],
    }
    if not letter:
        return result

    # Vowel vs consonant classification.
    if letter in independent_vowels or letter in dependent_vowels:
        result["type"] = "vowel"
    elif letter in telugu_consonants:
        result["type"] = "consonant"
        result["varga"] = get_consonant_varga(letter)

    # Yati Maitri group membership.
    for idx, group in enumerate(YATI_MAITRI_GROUPS):
        if letter in group:
            result["yati_groups"].append(idx)
            result["yati_group_members"].extend(list(group))

    # Deduplicate while preserving order.
    seen: Set[str] = set()
    unique_members = []
    for m in result["yati_group_members"]:
        if m not in seen:
            seen.add(m)
            unique_members.append(m)
    result["yati_group_members"] = unique_members
    return result


###############################################################################
# § 4  SCORING — per-component score helpers and weighted overall score
###############################################################################

def calculate_gana_score(partition_result: Optional[Dict]) -> Dict:
    """Calculate the gana score (0-100) from a partition result.

    Each valid gana contributes 25 % (4 ganas × 25 % = 100 %). A gana
    counts as valid only when the partition flagged it as `valid` —
    i.e. the U/I pattern is in the inventory AND the pattern is the
    expected type for its slot (Indra in 1-3, Surya in 4). A
    recognized-but-misplaced pattern (e.g. an Indra in the Surya slot)
    scores 0 for that gana.
    """
    result = {
        "score": 0.0,
        "ganas_matched": 0,
        "ganas_total": 4,
        "details": [],
    }
    if not partition_result or "ganas" not in partition_result:
        return result

    ganas = partition_result["ganas"]
    valid_count = 0
    for i, gana in enumerate(ganas, 1):
        is_valid = bool(gana.get("valid", False))
        if is_valid:
            valid_count += 1
        result["details"].append({
            "position": i,
            "type": gana.get("type", "Unknown"),
            "pattern": gana.get("pattern", ""),
            "name": gana.get("name"),
            "valid": is_valid,
            "aksharalu": gana.get("aksharalu", []),
        })

    result["ganas_matched"] = valid_count
    result["score"] = valid_count * SCORE_PER_VALID_GANA
    return result


def calculate_prasa_score(prasa_result: Optional[Dict]) -> Dict:
    """Calculate the prasa score (binary 0 or 100) with mismatch diagnostics."""
    result = {
        "score": 0.0,
        "match": False,
        "mismatch_details": None,
    }
    if not prasa_result:
        return result

    is_match = prasa_result.get("match", False)
    result["match"] = is_match
    result["score"] = PRASA_MATCH_SCORE if is_match else PRASA_NO_MATCH_SCORE

    if not is_match:
        cons1 = prasa_result.get("line1_consonant")
        cons2 = prasa_result.get("line2_consonant")
        varga1 = get_consonant_varga(cons1) if cons1 else None
        varga2 = get_consonant_varga(cons2) if cons2 else None
        result["mismatch_details"] = {
            "line1_full_breakdown": {
                "aksharam": prasa_result.get("line1_second_aksharam"),
                "consonant": cons1,
                "consonant_varga": varga1,
            },
            "line2_full_breakdown": {
                "aksharam": prasa_result.get("line2_second_aksharam"),
                "consonant": cons2,
                "consonant_varga": varga2,
            },
            "why_mismatch": _generate_prasa_mismatch_explanation(cons1, cons2, varga1, varga2),
            "suggestion": _generate_prasa_suggestion(cons1),
        }
    return result


def _generate_prasa_mismatch_explanation(cons1: str, cons2: str,
                                         varga1: Optional[str],
                                         varga2: Optional[str]) -> str:
    """Build a human-readable explanation of a prasa mismatch."""
    if not cons1 or not cons2:
        return "One or both lines don't have a valid consonant in 2nd position"
    if varga1 and varga2:
        if varga1 == varga2:
            return (f"Consonants '{cons1}' and '{cons2}' are from same varga "
                    f"({varga1}) but prasa requires exact match")
        return (f"Consonants '{cons1}' ({varga1}) and '{cons2}' ({varga2}) "
                f"are from different vargas")
    return (f"Consonants '{cons1}' and '{cons2}' do not match - prasa requires "
            f"identical consonants")


def _generate_prasa_suggestion(consonant: str) -> str:
    """Suggest a few example syllables that would satisfy prasa."""
    if not consonant:
        return "Unable to generate suggestion - no valid consonant found"
    vowels = ["", "ా", "ి", "ీ", "ు", "ూ", "ె", "ే", "ో"]
    examples = [consonant + v for v in vowels[:5]]
    return (f"Line 2 needs 2nd syllable with '{consonant}' consonant "
            f"(e.g., {', '.join(examples)}...)")


def calculate_yati_score(yati_result: Optional[Dict]) -> Dict:
    """Calculate the yati score (0 or 100) with letter-info diagnostics."""
    result = {
        "score": 0.0,
        "quality": "no_match",
        "mismatch_details": None,
    }
    if not yati_result:
        return result

    letter1 = yati_result.get("first_gana_letter")
    letter2 = yati_result.get("third_gana_letter")
    is_match = yati_result.get("match", False)

    info1 = get_letter_info(letter1) if letter1 else None
    info2 = get_letter_info(letter2) if letter2 else None

    if is_match:
        if letter1 == letter2:
            result["score"] = YATI_EXACT_MATCH_SCORE
            result["quality"] = "exact"
        else:
            result["score"] = YATI_VARGA_MATCH_SCORE
            result["quality"] = "varga_match"
    else:
        result["score"] = YATI_NO_MATCH_SCORE
        result["quality"] = "no_match"

    result["mismatch_details"] = {
        "letter1_info": info1,
        "letter2_info": info2,
        "why_result": _generate_yati_explanation(letter1, letter2, is_match, info1, info2),
        "suggestion": _generate_yati_suggestion(letter1, info1) if not is_match else None,
    }
    return result


def _generate_yati_explanation(letter1: str, letter2: str, is_match: bool,
                               info1: Optional[Dict], info2: Optional[Dict]) -> str:
    """Build a human-readable explanation of a yati result."""
    if not letter1 or not letter2:
        return "Unable to determine yati - missing letter information"
    if letter1 == letter2:
        return f"Exact match: both positions have '{letter1}' → MATCH (100%)"
    if is_match:
        groups1 = info1.get("yati_group_members", []) if info1 else []
        return (f"'{letter1}' and '{letter2}' belong to same Yati Maitri "
                f"group {groups1} → MATCH (70%)")
    varga1 = info1.get("varga") if info1 else None
    varga2 = info2.get("varga") if info2 else None
    if varga1 and varga2:
        return f"'{letter1}' is in {varga1}, '{letter2}' is in {varga2} → NO MATCH"
    return f"'{letter1}' and '{letter2}' are not in the same Yati Maitri group → NO MATCH"


def _generate_yati_suggestion(letter: str, info: Optional[Dict]) -> str:
    """Suggest letters that would satisfy yati for the given starting letter."""
    if not letter or not info:
        return "Unable to generate suggestion"
    group_members = info.get("yati_group_members", [])
    if group_members:
        return f"1st syllable of 3rd gana should start with: {', '.join(group_members)}"
    return f"1st syllable of 3rd gana should start with '{letter}' or related letters"


def calculate_syllable_length_score(pada: Dict) -> Dict:
    """Score a single line on whether its syllable count is in [MIN, MAX].

    A valid Dwipada line is 3 Indra ganas + 1 Surya gana, which bounds the
    syllable count to [MIN_LINE_SYLLABLES, MAX_LINE_SYLLABLES] (11-15).
    Score is binary: 100 if in range, 0 otherwise.
    """
    aksharalu = pada.get("aksharalu") or []
    n = len(aksharalu)
    in_range = MIN_LINE_SYLLABLES <= n <= MAX_LINE_SYLLABLES
    return {
        "score": SYLLABLE_LENGTH_MATCH_SCORE if in_range else SYLLABLE_LENGTH_NO_MATCH_SCORE,
        "match": in_range,
        "syllable_count": n,
        "min_allowed": MIN_LINE_SYLLABLES,
        "max_allowed": MAX_LINE_SYLLABLES,
    }


def calculate_overall_score(gana_score1: Dict, gana_score2: Dict,
                            prasa_score: Dict,
                            yati_score1: Dict, yati_score2: Dict,
                            syllable_score1: Dict, syllable_score2: Dict) -> Dict:
    """Combine per-component scores into a single weighted percentage.

    Gana, yati, and syllable_length are averaged across the two lines;
    prasa is per-couplet. Weights come from SCORE_WEIGHTS — equal 1/4
    across all four rules.
    """
    gana1 = gana_score1.get("score", 0.0)
    gana2 = gana_score2.get("score", 0.0)
    prasa = prasa_score.get("score", 0.0)
    yati1 = yati_score1.get("score", 0.0)
    yati2 = yati_score2.get("score", 0.0)
    syl1 = syllable_score1.get("score", 0.0)
    syl2 = syllable_score2.get("score", 0.0)

    avg_gana = (gana1 + gana2) / 2
    avg_yati = (yati1 + yati2) / 2
    avg_syllable = (syl1 + syl2) / 2

    overall = (
        avg_gana * SCORE_WEIGHTS["gana"]
        + prasa * SCORE_WEIGHTS["prasa"]
        + avg_yati * SCORE_WEIGHTS["yati"]
        + avg_syllable * SCORE_WEIGHTS["syllable_length"]
    )

    return {
        "overall": round(overall, 1),
        "breakdown": {
            "gana_line1": gana1,
            "gana_line2": gana2,
            "gana_average": round(avg_gana, 1),
            "prasa": prasa,
            "yati_line1": yati1,
            "yati_line2": yati2,
            "yati_average": round(avg_yati, 1),
            "syllable_length_line1": syl1,
            "syllable_length_line2": syl2,
            "syllable_length_average": round(avg_syllable, 1),
        },
        "weights": SCORE_WEIGHTS.copy(),
    }


###############################################################################
# § 5  SYLLABIFICATION — categorise, split, and U/I-mark Telugu text
###############################################################################

def categorize_aksharam(aksharam: str) -> List[str]:
    """Return linguistic tags applicable to a single syllable.

    Tags (Telugu):
      అచ్చు          — vowel (vowel-initial or pure diacritic).
      హల్లు          — consonant (contains any consonant).
      దీర్ఘ          — long vowel marker present.
      విసర్గ అక్షరం  — contains visarga (ః).
      అనుస్వారం       — contains anusvara (ం).
      సంయుక్తాక్షరం   — conjunct (different consonants joined by halant).
      ద్విత్వాక్షరం   — doubled (same consonant joined to itself by halant).
    """
    categories: Set[str] = set()

    # Vowel head (independent vowel or pure diacritic).
    if aksharam[0] in independent_vowels:
        categories.add("అచ్చు")
    elif aksharam in diacritics:
        categories.add("అచ్చు")

    # Any consonant present.
    if any(c in telugu_consonants for c in aksharam):
        categories.add("హల్లు")

    # Long vowel.
    if any(dv in aksharam for dv in long_vowels) or aksharam in independent_long_vowels:
        categories.add("దీర్ఘ")

    # Visarga / anusvara.
    if "ః" in aksharam:
        categories.add("విసర్గ అక్షరం")
    if "ం" in aksharam:
        categories.add("అనుస్వారం")

    # Conjunct / doubled consonant clusters (C ్ C).
    found_conjunct = found_double = False
    for i in range(len(aksharam) - 2):
        if (aksharam[i] in telugu_consonants
                and aksharam[i + 1] == halant
                and aksharam[i + 2] in telugu_consonants):
            if aksharam[i] == aksharam[i + 2]:
                found_double = True
            else:
                found_conjunct = True
    if found_conjunct:
        categories.add("సంయుక్తాక్షరం")
    if found_double:
        categories.add("ద్విత్వాక్షరం")

    return sorted(categories)


def split_aksharalu(word: str) -> List[str]:
    """Split a Telugu string into syllables (aksharalu).

    Two-pass algorithm:
      Pass 1 — coarse split at consonant/vowel boundaries; conjunct chains
               (C ్ C ...) and trailing dependent vowels stay attached.
      Pass 2 — merge "pollu hallu" (consonant + halant only, no vowel) into
               the previous syllable.

    Examples:
        split_aksharalu("తెలుగు")  → ['తె', 'లు', 'గు']
        split_aksharalu("సత్యము")  → ['స', 'త్య', 'ము']
        split_aksharalu("గౌరవం")   → ['గౌ', 'ర', 'వం']
    """
    # ── Pass 1 ─────────────────────────────────────────────────────────────
    coarse_split: List[str] = []
    i, n = 0, len(word)
    while i < n:
        if word[i] in ignorable_chars:
            coarse_split.append(word[i])
            i += 1
            continue

        current: List[str] = []
        if word[i] in telugu_consonants:
            # Consonant head; absorb any halant-linked consonant cluster.
            current.append(word[i])
            i += 1
            while i < n and word[i] == halant:
                current.append(word[i])
                i += 1
                if i < n and word[i] in telugu_consonants:
                    current.append(word[i])
                    i += 1
                else:
                    break  # Trailing halant — pollu hallu case.
            # Append dependent vowels and diacritics.
            while i < n and (word[i] in dependent_vowels or word[i] in diacritics):
                current.append(word[i])
                i += 1
        else:
            # Vowel head (independent vowel like అ, ఆ, ఇ).
            char = word[i]
            current.append(char)
            i += 1
            if char in independent_vowels and i < n and word[i] in diacritics:
                current.append(word[i])
                i += 1
        coarse_split.append("".join(current))

    if not coarse_split:
        return []

    # ── Pass 2 — merge pollu hallu (C+halant) with previous syllable. ─────
    final_aksharalu: List[str] = []
    for chunk in coarse_split:
        is_pollu_hallu = (
            len(chunk) == 2
            and chunk[0] in telugu_consonants
            and chunk[1] == halant
        )
        if (is_pollu_hallu
                and final_aksharalu
                and final_aksharalu[-1] not in ignorable_chars):
            final_aksharalu[-1] += chunk
        else:
            final_aksharalu.append(chunk)

    return [ak for ak in final_aksharalu if ak]


def akshara_ganavibhajana(aksharalu_list: List[str]) -> List[str]:
    """Mark each syllable as Guru ('U'), Laghu ('I'), or '' for ignorable.

    Guru rules — a syllable is heavy if ANY of these hold:
      1. Contains a long vowel (దీర్ఘ).
      2. Is/contains a diphthong: ఐ, ఔ, ై, ౌ.
      3. Carries anusvara (ం) or visarga (ః).
      4. Ends with halant (incomplete syllable).
      5. The NEXT in-word syllable starts with a conjunct/doubled cluster
         (sandhi rule — does not cross word boundaries).

    Laghu — none of the above; default for a short open syllable.
    """
    if not aksharalu_list:
        return []

    ganam_markers: List[Optional[str]] = [None] * len(aksharalu_list)

    # ── Pass 1: per-syllable rules 1–4 ────────────────────────────────────
    for i, aksharam in enumerate(aksharalu_list):
        if aksharam in ignorable_chars:
            ganam_markers[i] = ""
            continue

        ganam_markers[i] = "I"  # Default: Laghu.
        tags = set(categorize_aksharam(aksharam))

        is_guru = False
        if 'దీర్ఘ' in tags:                                     # Rule 1
            is_guru = True
        if ('ఐ' in aksharam or 'ఔ' in aksharam                  # Rule 2
                or 'ై' in aksharam or 'ౌ' in aksharam):
            is_guru = True
        if 'అనుస్వారం' in tags or 'విసర్గ అక్షరం' in tags:        # Rule 3
            is_guru = True
        if aksharam.endswith(halant):                            # Rule 4
            is_guru = True

        if is_guru:
            ganam_markers[i] = "U"

    # ── Pass 2: rule 5 (conjunct lookahead, stops at word boundary). ──────
    for i in range(len(aksharalu_list)):
        if ganam_markers[i] == "":
            continue
        next_idx = -1
        for j in range(i + 1, len(aksharalu_list)):
            if aksharalu_list[j] == ' ':
                break  # Word boundary — sandhi doesn't cross words.
            if aksharalu_list[j] not in ignorable_chars:
                next_idx = j
                break
        if next_idx != -1:
            next_tags = set(categorize_aksharam(aksharalu_list[next_idx]))
            if 'సంయుక్తాక్షరం' in next_tags or 'ద్విత్వాక్షరం' in next_tags:
                ganam_markers[i] = "U"

    return ganam_markers


###############################################################################
# § 6  SYLLABLE-LEVEL ACCESSORS — extract consonants, vowels, first letter
###############################################################################

def get_base_consonant(aksharam: str) -> Optional[str]:
    """Return the first consonant of a syllable (used for Prasa matching).

    For "క్ష", returns "క"; for vowel-initial syllables ("అ"), returns None.
    """
    if not aksharam:
        return None
    if aksharam[0] in telugu_consonants:
        return aksharam[0]
    return None


def get_first_letter(aksharam: str) -> Optional[str]:
    """Return the first character of a syllable (used for Yati matching)."""
    if not aksharam:
        return None
    return aksharam[0]


def get_independent_vowel(aksharam: str) -> Optional[str]:
    """Return the syllable's vowel as its independent form, for Svara Yati.

    Dependent vowel signs are mapped via dependent_to_independent. A bare
    consonant with no vowel marker carries the inherent 'అ' sound.
    """
    if not aksharam:
        return None
    for dv in dependent_vowels:
        if dv in aksharam:
            return dependent_to_independent[dv]
    if aksharam[0] in independent_vowels:
        return aksharam[0]
    return "అ"


def get_all_consonants(aksharam: str) -> List[str]:
    """Return every consonant in a syllable (used for Samyukta Yati).

    For "ప్ర" → ["ప", "ర"]; for "క్షా" → ["క", "ష"]; for "అ" → [].
    """
    return [ch for ch in aksharam if ch in telugu_consonants]


###############################################################################
# § 7  YATI CHECKING — primary (maitri) + svara/samyukta/bindu fallbacks
###############################################################################

def check_svara_yati(aksharam1: str, aksharam2: str) -> bool:
    """Svara Yati (స్వర యతి) — vowel-family match between two syllables."""
    v1 = get_independent_vowel(aksharam1)
    v2 = get_independent_vowel(aksharam2)
    if not v1 or not v2:
        return False
    if v1 == v2:
        return True
    for group in SVARA_YATI_GROUPS:
        if v1 in group and v2 in group:
            return True
    return False


def check_samyukta_yati(aksharam1: str, aksharam2: str) -> bool:
    """Samyukta Yati (సంయుక్త యతి) — any consonant in a conjunct may match."""
    cons1 = get_all_consonants(aksharam1)
    cons2 = get_all_consonants(aksharam2)
    if not cons1 or not cons2:
        return False
    for c1 in cons1:
        for c2 in cons2:
            if c1 == c2:
                return True
            for group in YATI_MAITRI_GROUPS:
                if c1 in group and c2 in group:
                    return True
    return False


def check_bindu_yati(aksharam1: str, aksharam2: str) -> bool:
    """Bindu Yati (బిందు యతి) — anusvara matches its varga's nasal."""
    anusvara = "ం"
    for a_with, a_other in [(aksharam1, aksharam2), (aksharam2, aksharam1)]:
        if anusvara not in a_with:
            continue
        base = get_base_consonant(a_with)
        if not base or base not in VARGA_NASALS:
            continue
        other_consonant = get_base_consonant(a_other)
        if not other_consonant:
            # Other side starts with a vowel — check if it equals the nasal.
            if a_other and a_other[0] == VARGA_NASALS[base]:
                return True
            continue
        varga_nasal = VARGA_NASALS[base]
        if other_consonant == varga_nasal:
            return True
        if other_consonant in NASAL_TO_VARGA:
            if base in NASAL_TO_VARGA[other_consonant]:
                return True
    return False


def check_yati_maitri(letter1: str, letter2: str) -> Tuple[bool, Optional[int], Dict]:
    """Primary yati check — exact match, then YATI_MAITRI_GROUPS membership.

    Returns (is_match, group_index, details). ``group_index`` is -1 for an
    exact match, the YATI_MAITRI_GROUPS index for a varga match, or None
    when there's no match.
    """
    details = {
        "letter1": letter1,
        "letter2": letter2,
        "quality_score": YATI_NO_MATCH_SCORE,
        "match_type": "no_match",
        "letter1_info": None,
        "letter2_info": None,
        "matching_group_members": None,
    }

    if not letter1 or not letter2:
        return False, None, details

    details["letter1_info"] = get_letter_info(letter1)
    details["letter2_info"] = get_letter_info(letter2)

    # Exact match (highest quality).
    if letter1 == letter2:
        details["quality_score"] = YATI_EXACT_MATCH_SCORE
        details["match_type"] = "exact"
        return True, -1, details

    # Varga (yati maitri) match.
    for idx, group in enumerate(YATI_MAITRI_GROUPS):
        if letter1 in group and letter2 in group:
            details["quality_score"] = YATI_VARGA_MATCH_SCORE
            details["match_type"] = "varga_match"
            details["matching_group_members"] = list(group)
            return True, idx, details

    return False, None, details


def check_yati_maitri_simple(letter1: str, letter2: str) -> Tuple[bool, Optional[int]]:
    """Backwards-compatible variant of check_yati_maitri returning only the pair."""
    is_match, group_idx, _ = check_yati_maitri(letter1, letter2)
    return is_match, group_idx


###############################################################################
# § 8  PRASA CHECKING — base-consonant comparison with diagnostics
###############################################################################

def are_prasa_equivalent(c1: str, c2: str) -> bool:
    """Return True if c1 and c2 are identical or share a PRASA_EQUIVALENTS group."""
    if c1 == c2:
        return True
    for group in PRASA_EQUIVALENTS:
        if c1 in group and c2 in group:
            return True
    return False


def check_prasa(line1: str, line2: str) -> Tuple[bool, Dict]:
    """Check Prasa — the 2nd syllable's base consonant must match between lines.

    Returns (is_match, details). On mismatch, details["mismatch_details"]
    contains the consonant breakdown, the varga of each, an explanation,
    and a fix suggestion.
    """
    aksharalu1 = split_aksharalu(line1)
    aksharalu2 = split_aksharalu(line2)
    pure1 = [ak for ak in aksharalu1 if ak not in ignorable_chars]
    pure2 = [ak for ak in aksharalu2 if ak not in ignorable_chars]

    if len(pure1) < 2 or len(pure2) < 2:
        return False, {"error": "Lines too short - need at least 2 aksharalu each"}

    second_ak1 = pure1[1]
    second_ak2 = pure2[1]
    consonant1 = get_base_consonant(second_ak1)
    consonant2 = get_base_consonant(second_ak2)

    is_match = (
        are_prasa_equivalent(consonant1, consonant2)
        if consonant1 and consonant2 else False
    )

    result = {
        "line1_second_aksharam": second_ak1,
        "line1_consonant": consonant1,
        "line2_second_aksharam": second_ak2,
        "line2_consonant": consonant2,
        "match": is_match,
        "mismatch_details": None,
    }

    if not is_match:
        varga1 = get_consonant_varga(consonant1) if consonant1 else None
        varga2 = get_consonant_varga(consonant2) if consonant2 else None
        result["mismatch_details"] = {
            "line1_full_breakdown": {
                "aksharam": second_ak1,
                "consonant": consonant1,
                "vowel": _extract_vowel_from_aksharam(second_ak1),
                "consonant_varga": varga1,
            },
            "line2_full_breakdown": {
                "aksharam": second_ak2,
                "consonant": consonant2,
                "vowel": _extract_vowel_from_aksharam(second_ak2),
                "consonant_varga": varga2,
            },
            "why_mismatch": _generate_prasa_mismatch_explanation(
                consonant1, consonant2, varga1, varga2
            ),
            "suggestion": _generate_prasa_suggestion(consonant1),
        }

    return is_match, result


def _extract_vowel_from_aksharam(aksharam: str) -> str:
    """Return the vowel portion of a syllable; '<vowel> (implicit)' if inherent అ."""
    if not aksharam:
        return ""
    for dv in dependent_vowels:
        if dv in aksharam:
            return dv
    if aksharam[0] in independent_vowels:
        return aksharam[0]
    return "అ (implicit)"


def check_prasa_aksharalu(aksharam1: str, aksharam2: str) -> Tuple[bool, Dict]:
    """Direct prasa check between two aksharalu (without line context)."""
    consonant1 = get_base_consonant(aksharam1)
    consonant2 = get_base_consonant(aksharam2)
    is_match = (
        are_prasa_equivalent(consonant1, consonant2)
        if consonant1 and consonant2 else False
    )
    return is_match, {
        "aksharam1": aksharam1,
        "consonant1": consonant1,
        "aksharam2": aksharam2,
        "consonant2": consonant2,
        "match": is_match,
    }


###############################################################################
# § 9  GANA PARTITIONING — search for valid 3-Indra + 1-Surya layout
###############################################################################

def identify_gana(pattern: str) -> Tuple[Optional[str], str]:
    """Map a U/I pattern to its (gana_name, gana_type) — Indra, Surya, or Unknown."""
    if pattern in INDRA_GANAS:
        return INDRA_GANAS[pattern], "Indra"
    if pattern in SURYA_GANAS:
        return SURYA_GANAS[pattern], "Surya"
    return None, "Unknown"


def find_dwipada_gana_partition(gana_markers: List[str],
                                aksharalu: List[str]) -> Optional[Dict]:
    """Search for the best Dwipada partition (3 Indra + 1 Surya) of the line.

    Tries the 16 length combinations (Indra ∈ {3, 4} × 3 positions, Surya
    ∈ {2, 3}) and selects the first fully-valid partition; otherwise the
    partition with the most matching ganas. Returns None if the line has
    fewer than 4 marker symbols.
    """
    pure_ganas = [g for g in gana_markers if g]
    pure_aksharalu = [ak for ak in aksharalu if ak not in ignorable_chars]

    if len(pure_ganas) < 4:
        return None

    pattern_str = "".join(pure_ganas)
    valid_partitions: List[Dict] = []
    all_partitions: List[Dict] = []
    partitions_tried = 0

    for i1_len in (3, 4):
        for i2_len in (3, 4):
            for i3_len in (3, 4):
                for s_len in (2, 3):
                    total_len = i1_len + i2_len + i3_len + s_len
                    if total_len != len(pure_ganas):
                        continue
                    partitions_tried += 1

                    # Slice the U/I pattern for each gana position.
                    pos = 0
                    i1_pattern = pattern_str[pos:pos + i1_len]; pos += i1_len
                    i2_pattern = pattern_str[pos:pos + i2_len]; pos += i2_len
                    i3_pattern = pattern_str[pos:pos + i3_len]; pos += i3_len
                    s_pattern  = pattern_str[pos:pos + s_len]

                    i1_name, i1_type = identify_gana(i1_pattern)
                    i2_name, i2_type = identify_gana(i2_pattern)
                    i3_name, i3_type = identify_gana(i3_pattern)
                    s_name,  s_type  = identify_gana(s_pattern)

                    # Slice the syllables matching each gana.
                    pos = 0
                    i1_aks = pure_aksharalu[pos:pos + i1_len]; pos += i1_len
                    i2_aks = pure_aksharalu[pos:pos + i2_len]; pos += i2_len
                    i3_aks = pure_aksharalu[pos:pos + i3_len]; pos += i3_len
                    s_aks  = pure_aksharalu[pos:pos + s_len]

                    g1_valid = i1_type == "Indra"
                    g2_valid = i2_type == "Indra"
                    g3_valid = i3_type == "Indra"
                    g4_valid = s_type == "Surya"
                    valid_count = sum([g1_valid, g2_valid, g3_valid, g4_valid])
                    is_fully_valid = valid_count == EXPECTED_GANAS_PER_LINE

                    partition_data = {
                        "ganas": [
                            _gana_entry(1, i1_name, i1_pattern, i1_aks, "Indra", g1_valid),
                            _gana_entry(2, i2_name, i2_pattern, i2_aks, "Indra", g2_valid),
                            _gana_entry(3, i3_name, i3_pattern, i3_aks, "Indra", g3_valid),
                            _gana_entry(4, s_name,  s_pattern,  s_aks,  "Surya", g4_valid),
                        ],
                        "total_syllables": len(pure_ganas),
                        "ganas_matched": valid_count,
                        "is_fully_valid": is_fully_valid,
                        "partition_lengths": [i1_len, i2_len, i3_len, s_len],
                    }

                    all_partitions.append(partition_data)
                    if is_fully_valid:
                        valid_partitions.append(partition_data)

    if partitions_tried == 0:
        return None

    # Prefer first fully-valid partition; otherwise the closest partial match.
    if valid_partitions:
        best = valid_partitions[0]
    else:
        best = max(all_partitions, key=lambda p: p["ganas_matched"])

    best["all_partitions_tried"] = partitions_tried
    best["valid_partitions_found"] = len(valid_partitions)
    return best


def _gana_entry(position: int, name: Optional[str], pattern: str,
                aksharalu: List[str], expected_type: str, valid: bool) -> Dict:
    """Build a single gana entry with a friendly error message when invalid."""
    return {
        "position": position,
        "name": name,
        "pattern": pattern,
        "aksharalu": aksharalu,
        "type": expected_type,
        "expected_type": expected_type,
        "valid": valid,
        "error": (None if valid
                  else f"Pattern '{pattern}' is not a valid {expected_type} gana"),
    }


###############################################################################
# § 10  TOP-LEVEL ANALYSIS API — analyze a line, analyze a couplet
###############################################################################

def analyze_pada(line: str) -> Dict:
    """Analyse a single line (pada). Returns syllables, U/I markers, partition,
    and key markers used for prasa/yati checks."""
    line = line.strip()
    aksharalu = split_aksharalu(line)
    pure_aksharalu = [ak for ak in aksharalu if ak not in ignorable_chars]
    gana_markers = akshara_ganavibhajana(aksharalu)
    pure_ganas = [g for g in gana_markers if g]
    partition = find_dwipada_gana_partition(gana_markers, aksharalu)

    first_aksharam = pure_aksharalu[0] if len(pure_aksharalu) > 0 else None
    second_aksharam = pure_aksharalu[1] if len(pure_aksharalu) > 1 else None

    third_gana_first_letter = None
    third_gana_first_aksharam = None
    if partition and len(partition["ganas"]) >= 3:
        third_gana_aksharalu = partition["ganas"][2]["aksharalu"]
        if third_gana_aksharalu:
            third_gana_first_letter = get_first_letter(third_gana_aksharalu[0])
            third_gana_first_aksharam = third_gana_aksharalu[0]

    return {
        "line": line,
        "aksharalu": pure_aksharalu,
        "gana_markers": pure_ganas,
        "gana_string": "".join(pure_ganas),
        "partition": partition,
        "first_aksharam": first_aksharam,
        "second_aksharam": second_aksharam,
        "first_letter": get_first_letter(first_aksharam) if first_aksharam else None,
        "second_consonant": get_base_consonant(second_aksharam) if second_aksharam else None,
        "third_gana_first_letter": third_gana_first_letter,
        "third_gana_first_aksharam": third_gana_first_aksharam,
        "is_valid_gana_sequence": (
            partition is not None and partition.get("is_fully_valid", False)
        ),
    }


def analyze_dwipada(poem: str) -> Dict:
    """Analyse a Dwipada couplet (two lines, newline-separated).

    Performs:
      - Per-line analysis (analyze_pada).
      - Prasa check (check_prasa) with diagnostics.
      - Yati check per line — primary maitri, with svara/samyukta/bindu fallbacks.
      - Per-component scoring + weighted overall percentage.
      - Boolean is_valid_dwipada (all rules satisfied).

    Raises:
        ValueError if the input does not contain at least 2 non-empty lines.
    """
    lines = [l.strip() for l in poem.strip().split('\n') if l.strip()]
    if len(lines) < 2:
        raise ValueError("Dwipada must have 2 lines separated by newline")
    line1, line2 = lines[0], lines[1]

    pada1 = analyze_pada(line1)
    pada2 = analyze_pada(line2)

    prasa_match, prasa_details = check_prasa(line1, line2)

    yati_line1 = _resolve_yati_for_line(pada1)
    yati_line2 = _resolve_yati_for_line(pada2)

    # Per-component scores.
    gana_score1 = calculate_gana_score(pada1.get("partition"))
    gana_score2 = calculate_gana_score(pada2.get("partition"))
    prasa_score_result = calculate_prasa_score(prasa_details)
    yati_score1 = calculate_yati_score(yati_line1)
    yati_score2 = calculate_yati_score(yati_line2)
    syllable_score1 = calculate_syllable_length_score(pada1)
    syllable_score2 = calculate_syllable_length_score(pada2)

    match_score = calculate_overall_score(
        gana_score1, gana_score2,
        prasa_score_result,
        yati_score1, yati_score2,
        syllable_score1, syllable_score2,
    )
    match_score["component_scores"] = {
        "gana_line1": gana_score1,
        "gana_line2": gana_score2,
        "prasa": prasa_score_result,
        "yati_line1": yati_score1,
        "yati_line2": yati_score2,
        "syllable_length_line1": syllable_score1,
        "syllable_length_line2": syllable_score2,
    }

    # Strict validity — all rules must pass.
    is_valid = (
        pada1["is_valid_gana_sequence"]
        and pada2["is_valid_gana_sequence"]
        and prasa_match
        and (yati_line1 is None or yati_line1["match"])
        and (yati_line2 is None or yati_line2["match"])
        and syllable_score1["match"]
        and syllable_score2["match"]
    )

    return {
        "pada1": pada1,
        "pada2": pada2,
        "prasa": prasa_details,
        "yati_line1": yati_line1,
        "yati_line2": yati_line2,
        "is_valid_dwipada": is_valid,
        "match_score": match_score,
        "validation_summary": {
            "gana_sequence_line1": pada1["is_valid_gana_sequence"],
            "gana_sequence_line2": pada2["is_valid_gana_sequence"],
            "prasa_match": prasa_match,
            "yati_line1_match": yati_line1["match"] if yati_line1 else None,
            "yati_line2_match": yati_line2["match"] if yati_line2 else None,
            "syllable_length_line1_in_range": syllable_score1["match"],
            "syllable_length_line2_in_range": syllable_score2["match"],
            "syllable_count_line1": syllable_score1["syllable_count"],
            "syllable_count_line2": syllable_score2["syllable_count"],
        },
    }


def _resolve_yati_for_line(pada: Dict) -> Optional[Dict]:
    """Run primary yati maitri, then svara/samyukta/bindu yati as fallbacks.

    Returns None if the line lacks a determinable 1st-or-3rd-gana letter.
    """
    if not (pada["first_letter"] and pada["third_gana_first_letter"]):
        return None

    match, group_idx, details = check_yati_maitri(
        pada["first_letter"],
        pada["third_gana_first_letter"],
    )
    match_type = details.get("match_type", "no_match")

    aksharam1 = pada["first_aksharam"]
    aksharam3 = pada["third_gana_first_aksharam"]
    if not match and aksharam1 and aksharam3:
        if check_svara_yati(aksharam1, aksharam3):
            match, match_type = True, "svara_yati"
        elif check_samyukta_yati(aksharam1, aksharam3):
            match, match_type = True, "samyukta_yati"
        elif check_bindu_yati(aksharam1, aksharam3):
            match, match_type = True, "bindu_yati"

    return {
        "first_gana_letter": pada["first_letter"],
        "third_gana_letter": pada["third_gana_first_letter"],
        "match": match,
        "group_index": group_idx,
        "quality_score": YATI_EXACT_MATCH_SCORE if match else YATI_NO_MATCH_SCORE,
        "match_type": match_type,
        "mismatch_details": details,
    }


###############################################################################
# § 11  REPORT FORMATTING — pretty text reports for humans
###############################################################################

def format_analysis_report(analysis: Dict) -> str:
    """Format a full analyze_dwipada result as a multi-section text report."""
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append("DWIPADA CHANDASSU ANALYSIS REPORT")
    lines.append("=" * 70)

    if "match_score" in analysis:
        overall = analysis["match_score"].get("overall", 0)
        lines.append(f"\n📊 OVERALL MATCH SCORE: {overall:.1f}%")
        lines.append("-" * 35)

    lines.extend(_format_pada_section("LINE 1 (పాదము 1)", analysis["pada1"]))
    lines.extend(_format_pada_section("LINE 2 (పాదము 2)", analysis["pada2"]))

    # Prasa.
    lines.append("\n--- PRASA (ప్రాస) ANALYSIS ---")
    if analysis["prasa"]:
        prasa = analysis["prasa"]
        status = "✓ MATCH" if prasa["match"] else "✗ NO MATCH"
        lines.append(f"Line 1 - 2nd Aksharam: '{prasa['line1_second_aksharam']}' "
                     f"(Consonant: {prasa['line1_consonant']})")
        lines.append(f"Line 2 - 2nd Aksharam: '{prasa['line2_second_aksharam']}' "
                     f"(Consonant: {prasa['line2_consonant']})")
        lines.append(f"Prasa Status: {status}")
        if not prasa["match"] and prasa.get("mismatch_details"):
            lines.extend(_format_prasa_mismatch(prasa["mismatch_details"]))
    else:
        lines.append("Could not determine Prasa")

    # Yati.
    lines.append("\n--- YATI (యతి) ANALYSIS ---")
    lines.extend(_format_yati_line(1, analysis["yati_line1"]))
    lines.extend(_format_yati_line(2, analysis["yati_line2"]))

    # Score breakdown.
    if "match_score" in analysis:
        lines.append("\n--- SCORE BREAKDOWN ---")
        score = analysis["match_score"]
        breakdown = score.get("breakdown", {})
        weights = score.get("weights", {})
        lines.append(f"  Gana (weight {weights.get('gana', 1/4) * 100:.0f}%):")
        lines.append(f"    Line 1: {breakdown.get('gana_line1', 0):.1f}%")
        lines.append(f"    Line 2: {breakdown.get('gana_line2', 0):.1f}%")
        lines.append(f"    Average: {breakdown.get('gana_average', 0):.1f}%")
        lines.append(f"  Prasa (weight {weights.get('prasa', 1/4) * 100:.0f}%): "
                     f"{breakdown.get('prasa', 0):.1f}%")
        lines.append(f"  Yati (weight {weights.get('yati', 1/4) * 100:.0f}%):")
        lines.append(f"    Line 1: {breakdown.get('yati_line1', 0):.1f}%")
        lines.append(f"    Line 2: {breakdown.get('yati_line2', 0):.1f}%")
        lines.append(f"    Average: {breakdown.get('yati_average', 0):.1f}%")
        lines.append(f"  Syllable Length (weight "
                     f"{weights.get('syllable_length', 1/4) * 100:.0f}%):")
        lines.append(f"    Line 1: {breakdown.get('syllable_length_line1', 0):.1f}%")
        lines.append(f"    Line 2: {breakdown.get('syllable_length_line2', 0):.1f}%")
        lines.append(f"    Average: {breakdown.get('syllable_length_average', 0):.1f}%")

    # Validation summary.
    lines.append("\n" + "=" * 70)
    lines.append("VALIDATION SUMMARY")
    lines.append("=" * 70)
    s = analysis["validation_summary"]
    lines.append(f"Gana Sequence Line 1: {'✓ Valid' if s['gana_sequence_line1'] else '✗ Invalid'}")
    lines.append(f"Gana Sequence Line 2: {'✓ Valid' if s['gana_sequence_line2'] else '✗ Invalid'}")
    lines.append(f"Prasa Match: {'✓ Yes' if s['prasa_match'] else '✗ No'}")
    lines.append(f"Yati Line 1: "
                 f"{'✓ Match' if s['yati_line1_match'] else '✗ No Match' if s['yati_line1_match'] is False else 'N/A'}")
    lines.append(f"Yati Line 2: "
                 f"{'✓ Match' if s['yati_line2_match'] else '✗ No Match' if s['yati_line2_match'] is False else 'N/A'}")
    n1 = s.get("syllable_count_line1")
    n2 = s.get("syllable_count_line2")
    range_str = f"[{MIN_LINE_SYLLABLES}-{MAX_LINE_SYLLABLES}]"
    lines.append(f"Syllable Length Line 1: "
                 f"{'✓' if s.get('syllable_length_line1_in_range') else '✗'} "
                 f"{n1} syllables (allowed {range_str})")
    lines.append(f"Syllable Length Line 2: "
                 f"{'✓' if s.get('syllable_length_line2_in_range') else '✗'} "
                 f"{n2} syllables (allowed {range_str})")
    lines.append("")

    if "match_score" in analysis:
        overall = analysis["match_score"].get("overall", 0)
        verdict = "✓ VALID DWIPADA" if analysis['is_valid_dwipada'] else "✗ INVALID DWIPADA"
        lines.append(f"OVERALL: {verdict} ({overall:.1f}% match)")
    else:
        verdict = "✓ VALID DWIPADA" if analysis['is_valid_dwipada'] else "✗ INVALID DWIPADA"
        lines.append(f"OVERALL: {verdict}")
    lines.append("=" * 70)

    return "\n".join(lines)


def _format_pada_section(label: str, pada: Dict) -> List[str]:
    """Render the per-line section (text, syllables, markers, gana breakdown)."""
    out = [f"\n--- {label} ---",
           f"Text: {pada['line']}",
           f"Aksharalu: {' | '.join(pada['aksharalu'])}",
           f"Gana Markers: {' '.join(pada['gana_markers'])}"]
    partition = pada.get("partition")
    if partition:
        ganas_matched = partition.get("ganas_matched", 4)
        out.append(f"\nGana Breakdown ({ganas_matched}/4 valid):")
        for gana in partition["ganas"]:
            label_text = "ఇంద్ర గణము" if gana["type"] == "Indra" else "సూర్య గణము"
            mark = "✓" if gana.get("valid", True) else "✗"
            name = gana['name'] if gana['name'] else "[Invalid]"
            out.append(
                f"  {mark} Gana {gana.get('position', '?')}: "
                f"{''.join(gana['aksharalu'])} = {gana['pattern']} = {name} ({label_text})"
            )
            if not gana.get("valid", True) and gana.get("error"):
                out.append(f"      ↳ {gana['error']}")
    else:
        out.append("\n[WARNING] Could not find valid 3 Indra + 1 Surya Gana partition")
    return out


def _format_prasa_mismatch(details: Dict) -> List[str]:
    """Render the prasa-mismatch diagnostic block."""
    out = ["\n  📋 Mismatch Details:"]
    if details.get("line1_full_breakdown"):
        bd = details["line1_full_breakdown"]
        out.append(f"    Line 1: '{bd.get('aksharam')}' → consonant "
                   f"'{bd.get('consonant')}' ({bd.get('consonant_varga', 'unknown')})")
    if details.get("line2_full_breakdown"):
        bd = details["line2_full_breakdown"]
        out.append(f"    Line 2: '{bd.get('aksharam')}' → consonant "
                   f"'{bd.get('consonant')}' ({bd.get('consonant_varga', 'unknown')})")
    if details.get("why_mismatch"):
        out.append(f"    Why: {details['why_mismatch']}")
    if details.get("suggestion"):
        out.append(f"    💡 Suggestion: {details['suggestion']}")
    return out


def _format_yati_line(line_num: int, yati: Optional[Dict]) -> List[str]:
    """Render the yati block for a single line."""
    if not yati:
        return [f"Line {line_num}: Could not determine Yati"]
    match_type = yati.get("match_type", "unknown")
    quality = yati.get("quality_score", 0)
    status = (f"✓ MATCH ({match_type}, {quality:.0f}%)"
              if yati["match"] else "✗ NO MATCH")
    out = [f"Line {line_num}: '{yati['first_gana_letter']}' (1st gana) ↔ "
           f"'{yati['third_gana_letter']}' (3rd gana) - {status}"]
    if not yati["match"] or match_type == "varga_match":
        details = yati.get("mismatch_details", {})
        info1 = details.get("letter1_info", {}) if details else {}
        if info1:
            out.append(f"    '{yati['first_gana_letter']}' groups: "
                       f"{info1.get('yati_group_members', [])}")
        if details and details.get("matching_group_members"):
            out.append(f"    Matching group: {details['matching_group_members']}")
    return out


def analyze_single_line(line: str) -> str:
    """Quick text report for a single line (when only one pada is on hand)."""
    pada = analyze_pada(line)
    out = ["=" * 60, "SINGLE LINE ANALYSIS", "=" * 60,
           f"Text: {pada['line']}",
           f"Aksharalu: {' | '.join(pada['aksharalu'])}",
           f"Gana Markers: {' '.join(pada['gana_markers'])}",
           f"Gana String: {pada['gana_string']}"]
    partition = pada.get("partition")
    if partition:
        out.append("\nGana Breakdown (3 Indra + 1 Surya):")
        for i, gana in enumerate(partition["ganas"], 1):
            label = "ఇంద్ర" if gana["type"] == "Indra" else "సూర్య"
            aksharalu_str = "".join(gana['aksharalu'])
            out.append(f"  {i}. {aksharalu_str} = {gana['pattern']} = "
                       f"{gana['name']} ({label})")
        out.append("\n✓ Valid Dwipada line structure")
    else:
        out.append("\n✗ Could not find valid 3 Indra + 1 Surya partition")
    out.append("=" * 60)
    return "\n".join(out)


###############################################################################
# § 12  DATASET STATISTICS — aggregate analyse over consolidated_dwipada.json
###############################################################################
#
# The consolidated dataset is a flat JSON list. Each entry has the shape:
#     {
#         "poem":   "<line1>\n<line2>",
#         "line1":  "<line1>",
#         "line2":  "<line2>",
#         "source": {"work": "ranganatha_ramayanam", ...},
#     }
#
# run_dataset_stats() runs analyze_dwipada() over every entry, accumulates
# pass/fail counters, per-rule breakdowns, score histograms, and a sample of
# failures for inspection. format_dataset_stats_report() renders the result
# as a multi-section text report; the dict is also JSON-serialisable for
# downstream pipelines.

# Score histogram bucket boundaries. Each value is the upper bound (exclusive
# above the previous bound, inclusive at 100 for the final bucket).
SCORE_HISTOGRAM_EDGES = (25.0, 50.0, 75.0, 100.0)

# How many failing poems to retain as samples in the report.
DEFAULT_FAILURE_SAMPLES = 10


def _empty_accumulator() -> Dict:
    """Build a fresh accumulator dict for one scope (global or per-source)."""
    return {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "valid_count": 0,
        "partially_valid_count": 0,
        "gana_line1_valid": 0,
        "gana_line2_valid": 0,
        "gana_both_valid": 0,
        "prasa_match": 0,
        "yati_line1_match": 0,
        "yati_line2_match": 0,
        "yati_both_match": 0,
        "syllable_line1_in_range": 0,
        "syllable_line2_in_range": 0,
        "syllable_both_in_range": 0,
        "syllable_count_sum_line1": 0,
        "syllable_count_sum_line2": 0,
        "score_sum": 0.0,
        "score_histogram": Counter(),
    }


def _bucket_for_score(score: float) -> str:
    """Map a 0-100 score to a histogram bucket label like '50-75'."""
    prev = 0.0
    for edge in SCORE_HISTOGRAM_EDGES:
        if score < edge or (edge == 100.0 and score <= 100.0):
            return f"{int(prev)}-{int(edge)}"
        prev = edge
    # Defensive fallback — shouldn't trigger for well-formed scores.
    return f"{int(SCORE_HISTOGRAM_EDGES[-1])}+"


def _ingest(acc: Dict, analysis: Dict) -> None:
    """Update an accumulator with one poem's analysis result."""
    acc["total"] += 1

    summary = analysis.get("validation_summary", {})
    is_valid = analysis.get("is_valid_dwipada", False)
    if is_valid:
        acc["passed"] += 1
    else:
        acc["failed"] += 1

    gana1 = bool(summary.get("gana_sequence_line1"))
    gana2 = bool(summary.get("gana_sequence_line2"))
    if gana1: acc["gana_line1_valid"] += 1
    if gana2: acc["gana_line2_valid"] += 1
    if gana1 and gana2: acc["gana_both_valid"] += 1

    if summary.get("prasa_match"):
        acc["prasa_match"] += 1

    yati1 = summary.get("yati_line1_match")
    yati2 = summary.get("yati_line2_match")
    if yati1: acc["yati_line1_match"] += 1
    if yati2: acc["yati_line2_match"] += 1
    if yati1 and yati2: acc["yati_both_match"] += 1

    syl1 = bool(summary.get("syllable_length_line1_in_range"))
    syl2 = bool(summary.get("syllable_length_line2_in_range"))
    if syl1: acc["syllable_line1_in_range"] += 1
    if syl2: acc["syllable_line2_in_range"] += 1
    if syl1 and syl2: acc["syllable_both_in_range"] += 1
    acc["syllable_count_sum_line1"] += int(summary.get("syllable_count_line1") or 0)
    acc["syllable_count_sum_line2"] += int(summary.get("syllable_count_line2") or 0)

    score = analysis.get("match_score", {}).get("overall", 0.0) or 0.0
    score = float(score)
    acc["score_sum"] += score
    acc["score_histogram"][_bucket_for_score(score)] += 1
    # A poem is "valid" only when the overall score is a perfect 100 %.
    # Anything less is "partially valid". This is independent of the
    # boolean `passed` check — score == 100 and the boolean check can
    # disagree in both directions (see README for details).
    if score >= 100.0:
        acc["valid_count"] += 1
    else:
        acc["partially_valid_count"] += 1


def _finalise(acc: Dict) -> Dict:
    """Convert raw counters into a report-ready dict with percentages.

    Counter is converted to a plain dict so the result is JSON-serialisable.
    """
    total = acc["total"] or 1  # Guard against div-by-zero on empty scopes.
    return {
        "total": acc["total"],
        "passed": acc["passed"],
        "failed": acc["failed"],
        "passed_pct": round(100.0 * acc["passed"] / total, 2),
        "failed_pct": round(100.0 * acc["failed"] / total, 2),
        "valid_count": acc["valid_count"],
        "valid_pct": round(100.0 * acc["valid_count"] / total, 2),
        "partially_valid_count": acc["partially_valid_count"],
        "partially_valid_pct": round(100.0 * acc["partially_valid_count"] / total, 2),
        "gana_line1_valid": acc["gana_line1_valid"],
        "gana_line1_valid_pct": round(100.0 * acc["gana_line1_valid"] / total, 2),
        "gana_line2_valid": acc["gana_line2_valid"],
        "gana_line2_valid_pct": round(100.0 * acc["gana_line2_valid"] / total, 2),
        "gana_both_valid": acc["gana_both_valid"],
        "gana_both_valid_pct": round(100.0 * acc["gana_both_valid"] / total, 2),
        "prasa_match": acc["prasa_match"],
        "prasa_match_pct": round(100.0 * acc["prasa_match"] / total, 2),
        "yati_line1_match": acc["yati_line1_match"],
        "yati_line1_match_pct": round(100.0 * acc["yati_line1_match"] / total, 2),
        "yati_line2_match": acc["yati_line2_match"],
        "yati_line2_match_pct": round(100.0 * acc["yati_line2_match"] / total, 2),
        "yati_both_match": acc["yati_both_match"],
        "yati_both_match_pct": round(100.0 * acc["yati_both_match"] / total, 2),
        "syllable_line1_in_range": acc["syllable_line1_in_range"],
        "syllable_line1_in_range_pct": round(100.0 * acc["syllable_line1_in_range"] / total, 2),
        "syllable_line2_in_range": acc["syllable_line2_in_range"],
        "syllable_line2_in_range_pct": round(100.0 * acc["syllable_line2_in_range"] / total, 2),
        "syllable_both_in_range": acc["syllable_both_in_range"],
        "syllable_both_in_range_pct": round(100.0 * acc["syllable_both_in_range"] / total, 2),
        "syllable_mean_count_line1": round(acc["syllable_count_sum_line1"] / total, 2),
        "syllable_mean_count_line2": round(acc["syllable_count_sum_line2"] / total, 2),
        "syllable_bounds": [MIN_LINE_SYLLABLES, MAX_LINE_SYLLABLES],
        "mean_overall_score": round(acc["score_sum"] / total, 2),
        "score_histogram": dict(acc["score_histogram"]),
    }


def _failed_rules(analysis: Dict) -> List[str]:
    """List the rule names a poem failed (for sample-failure rendering)."""
    s = analysis.get("validation_summary", {})
    failed = []
    if not s.get("gana_sequence_line1"): failed.append("gana_line1")
    if not s.get("gana_sequence_line2"): failed.append("gana_line2")
    if not s.get("prasa_match"):         failed.append("prasa")
    if s.get("yati_line1_match") is False: failed.append("yati_line1")
    if s.get("yati_line2_match") is False: failed.append("yati_line2")
    if s.get("syllable_length_line1_in_range") is False: failed.append("syllable_length_line1")
    if s.get("syllable_length_line2_in_range") is False: failed.append("syllable_length_line2")
    return failed


def _extract_source_work(entry: Dict) -> Optional[str]:
    """Return the work name for an entry's `source` field.

    Accepts both shapes:
      - dict with a `work` key (data/consolidated_dwipada.json)
      - plain string (datasets/dwipada_consolidated.json)
    Returns None when the field is missing or empty.
    """
    src = entry.get("source")
    if isinstance(src, dict):
        return src.get("work") or None
    if isinstance(src, str):
        return src or None
    return None


def run_dataset_stats(
    json_path: Path,
    by_source: bool = True,
    max_failure_samples: int = DEFAULT_FAILURE_SAMPLES,
    progress_every: int = 2000,
) -> Dict:
    """Run analyze_dwipada over every entry and aggregate statistics.

    Args:
        json_path:           Path to a flat JSON list of poem entries with
                             at least a "poem" field; "source.work" is used
                             for the per-source breakdown when present.
        by_source:           If True, also compute per-source-work breakdowns.
        max_failure_samples: How many failing poems to retain as samples.
        progress_every:      Emit a progress line on stderr every N entries.

    Returns:
        Dict with keys:
            - input:           Path to the JSON file (string).
            - total:           Number of entries scanned.
            - parse_errors:    Entries that raised ValueError (too short, etc.).
            - other_errors:    Entries that raised any other exception.
            - global:          Finalised accumulator for the whole corpus.
            - by_source:       Dict[source -> finalised accumulator] (or None).
            - sample_failures: First N failing poems with their failed rules.
    """
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"Dataset not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(
            f"Expected a JSON list of poem entries; got {type(data).__name__}"
        )

    print(f"Loaded {len(data):,} entries from {json_path}", file=sys.stderr)

    # Accumulators.
    global_acc = _empty_accumulator()
    per_source_acc: Dict[str, Dict] = {} if by_source else {}
    sample_failures: List[Dict] = []
    parse_errors = 0
    other_errors = 0

    # Main loop.
    for i, entry in enumerate(data, start=1):
        poem = entry.get("poem") if isinstance(entry, dict) else None
        if not poem:
            parse_errors += 1
            continue

        try:
            analysis = analyze_dwipada(poem)
        except ValueError:
            parse_errors += 1
            continue
        except Exception:
            # Unexpected — keep counting but don't crash the run.
            other_errors += 1
            continue

        _ingest(global_acc, analysis)

        if by_source:
            source_work = _extract_source_work(entry) or "unknown"
            if source_work not in per_source_acc:
                per_source_acc[source_work] = _empty_accumulator()
            _ingest(per_source_acc[source_work], analysis)

        # Collect sample failures (deterministic — first N).
        if (not analysis.get("is_valid_dwipada")
                and len(sample_failures) < max_failure_samples):
            sample_failures.append({
                "poem": poem,
                "source": _extract_source_work(entry),
                "score": analysis.get("match_score", {}).get("overall", 0.0),
                "failed_rules": _failed_rules(analysis),
                "validation_summary": analysis.get("validation_summary", {}),
            })

        if progress_every and i % progress_every == 0:
            print(f"  ...processed {i:,}/{len(data):,}", file=sys.stderr)

    print(f"Done. Scanned {global_acc['total']:,} valid entries; "
          f"{parse_errors:,} parse errors, {other_errors:,} other errors.",
          file=sys.stderr)

    return {
        "input": str(json_path),
        "total": len(data),
        "parse_errors": parse_errors,
        "other_errors": other_errors,
        "global": _finalise(global_acc),
        "by_source": (
            {src: _finalise(acc) for src, acc in per_source_acc.items()}
            if by_source else None
        ),
        "sample_failures": sample_failures,
    }


def format_dataset_stats_report(stats: Dict) -> str:
    """Render run_dataset_stats output as a multi-section text report."""
    out: List[str] = []
    out.append("=" * 78)
    out.append("DWIPADA DATASET STATISTICS")
    out.append("=" * 78)
    out.append(f"Input: {stats['input']}")
    out.append(f"Total entries: {stats['total']:,}")
    out.append(f"Parse errors:  {stats['parse_errors']:,} (skipped — poem missing or < 2 lines)")
    if stats.get("other_errors"):
        out.append(f"Other errors:  {stats['other_errors']:,}")

    # Global summary.
    out.append("")
    out.append("─" * 78)
    out.append("GLOBAL SUMMARY")
    out.append("─" * 78)
    out.extend(_format_scope_block(stats["global"]))

    # Score histogram.
    out.append("")
    out.append("─" * 78)
    out.append("SCORE HISTOGRAM (overall % match)")
    out.append("─" * 78)
    out.extend(_format_histogram(stats["global"]))

    # Per-source breakdown.
    if stats.get("by_source"):
        out.append("")
        out.append("─" * 78)
        out.append("PER-SOURCE BREAKDOWN")
        out.append("─" * 78)
        out.extend(_format_per_source_table(stats["by_source"]))

    # Sample failures.
    if stats.get("sample_failures"):
        out.append("")
        out.append("─" * 78)
        out.append(f"SAMPLE FAILURES (first {len(stats['sample_failures'])})")
        out.append("─" * 78)
        for i, fail in enumerate(stats["sample_failures"], 1):
            out.extend(_format_sample_failure(i, fail))

    out.append("")
    out.append("=" * 78)
    return "\n".join(out)


def _format_scope_block(scope: Dict) -> List[str]:
    """Render one finalised accumulator (global or per-source) as text."""
    out = []
    out.append(f"  Total analysed:           {scope['total']:>8,}")
    out.append(f"  Valid (score = 100 %):    {scope['valid_count']:>8,}  "
               f"({scope['valid_pct']:>5.2f} %)")
    out.append(f"  Partially valid (< 100):  {scope['partially_valid_count']:>8,}  "
               f"({scope['partially_valid_pct']:>5.2f} %)")
    out.append(f"  Passed boolean rule check:{scope['passed']:>8,}  "
               f"({scope['passed_pct']:>5.2f} %)")
    out.append(f"  Failed boolean rule check:{scope['failed']:>8,}  "
               f"({scope['failed_pct']:>5.2f} %)")
    out.append(f"  Mean overall score:       {scope['mean_overall_score']:>8.2f} %")
    out.append("")
    out.append("  Per-rule pass counts:")
    out.append(f"    Gana — line 1 valid:  {scope['gana_line1_valid']:>8,} "
               f"({scope['gana_line1_valid_pct']:>5.2f} %)")
    out.append(f"    Gana — line 2 valid:  {scope['gana_line2_valid']:>8,} "
               f"({scope['gana_line2_valid_pct']:>5.2f} %)")
    out.append(f"    Gana — both valid:    {scope['gana_both_valid']:>8,} "
               f"({scope['gana_both_valid_pct']:>5.2f} %)")
    out.append(f"    Prasa match:          {scope['prasa_match']:>8,} "
               f"({scope['prasa_match_pct']:>5.2f} %)")
    out.append(f"    Yati — line 1 match:  {scope['yati_line1_match']:>8,} "
               f"({scope['yati_line1_match_pct']:>5.2f} %)")
    out.append(f"    Yati — line 2 match:  {scope['yati_line2_match']:>8,} "
               f"({scope['yati_line2_match_pct']:>5.2f} %)")
    out.append(f"    Yati — both match:    {scope['yati_both_match']:>8,} "
               f"({scope['yati_both_match_pct']:>5.2f} %)")
    bounds = scope.get("syllable_bounds") or [MIN_LINE_SYLLABLES, MAX_LINE_SYLLABLES]
    out.append(f"    Syllable len line 1 in [{bounds[0]}-{bounds[1]}]: "
               f"{scope['syllable_line1_in_range']:>8,} "
               f"({scope['syllable_line1_in_range_pct']:>5.2f} %)")
    out.append(f"    Syllable len line 2 in [{bounds[0]}-{bounds[1]}]: "
               f"{scope['syllable_line2_in_range']:>8,} "
               f"({scope['syllable_line2_in_range_pct']:>5.2f} %)")
    out.append(f"    Syllable len both in range:   "
               f"{scope['syllable_both_in_range']:>8,} "
               f"({scope['syllable_both_in_range_pct']:>5.2f} %)")
    out.append(f"    Mean syllables/line: "
               f"line1={scope['syllable_mean_count_line1']:.2f}, "
               f"line2={scope['syllable_mean_count_line2']:.2f}")
    return out


def _format_histogram(scope: Dict) -> List[str]:
    """Render the bucketed score histogram with a simple ASCII bar chart."""
    hist = scope.get("score_histogram", {})
    total = scope.get("total", 0) or 1
    # Iterate buckets in fixed order so the report is deterministic.
    bucket_order = []
    prev = 0.0
    for edge in SCORE_HISTOGRAM_EDGES:
        bucket_order.append(f"{int(prev)}-{int(edge)}")
        prev = edge
    out = []
    bar_max = 50
    for bucket in bucket_order:
        count = hist.get(bucket, 0)
        pct = 100.0 * count / total
        bar_len = int(round(bar_max * count / max(hist.values()))) if hist else 0
        bar = "█" * bar_len
        out.append(f"  {bucket:>7}  {count:>8,}  ({pct:>5.2f} %)  {bar}")
    return out


def _format_per_source_table(by_source: Dict[str, Dict]) -> List[str]:
    """Render the per-source breakdown as an aligned text table."""
    if not by_source:
        return ["  (no per-source data)"]
    sources = sorted(by_source.keys(),
                     key=lambda s: -by_source[s]["total"])
    name_w = max(len(s) for s in sources)
    out = []
    header = (f"  {'source':<{name_w}}  {'total':>8}  {'pass':>8}  {'pass %':>7}  "
              f"{'mean %':>7}  {'gana/2':>7}  {'prasa':>7}  {'yati/2':>7}")
    out.append(header)
    out.append("  " + "-" * (len(header) - 2))
    for src in sources:
        s = by_source[src]
        out.append(
            f"  {src:<{name_w}}  "
            f"{s['total']:>8,}  "
            f"{s['passed']:>8,}  "
            f"{s['passed_pct']:>6.2f}%  "
            f"{s['mean_overall_score']:>6.2f}%  "
            f"{s['gana_both_valid_pct']:>6.2f}%  "
            f"{s['prasa_match_pct']:>6.2f}%  "
            f"{s['yati_both_match_pct']:>6.2f}%"
        )
    out.append("")
    out.append("  Legend: gana/2 = both lines have valid gana sequence; "
               "yati/2 = both lines satisfy yati.")
    return out


def _format_sample_failure(idx: int, fail: Dict) -> List[str]:
    """Render one sample-failure entry compactly."""
    out = [f"\n  [{idx}] source={fail.get('source')}  "
           f"score={fail.get('score', 0):.1f}%  "
           f"failed={fail.get('failed_rules')}"]
    poem = fail.get("poem", "")
    for line in poem.split("\n"):
        out.append(f"      | {line}")
    return out


###############################################################################
# § 13  COMMAND-LINE INTERFACE
###############################################################################

def _build_argument_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser for `analyze` and `stats` subcommands."""
    parser = argparse.ArgumentParser(
        prog="dwipada_analyser",
        description="Telugu Dwipada (ద్విపద) prosody analyser — "
                    "validate poems and compute corpus statistics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python dwipada_analyser.py analyze 'line1\\nline2'\n"
            "  python dwipada_analyser.py analyze --file poem.txt --json\n"
            "  python dwipada_analyser.py stats\n"
            "  python dwipada_analyser.py stats --output stats.json\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True,
                                metavar="{analyze,stats}")

    # `analyze` — single-poem analysis.
    a = sub.add_parser("analyze",
                       help="Analyse a single Dwipada couplet.")
    a.add_argument("poem", nargs="?", default=None,
                   help="Poem text. Use \\n between the two lines, or omit "
                        "this argument and pass --file, or omit both for "
                        "interactive stdin entry.")
    a.add_argument("--file", "-f", default=None,
                   help="Path to a UTF-8 file containing the 2-line poem.")
    a.add_argument("--json", action="store_true",
                   help="Emit the raw analysis dict as JSON instead of a "
                        "formatted text report.")

    # `stats` — corpus-wide statistics.
    s = sub.add_parser("stats",
                       help="Compute statistics over a poem-list JSON file.")
    s.add_argument("--input", "-i", default=None,
                   help="Path to a JSON list of poem entries. Defaults to "
                        "data/consolidated_dwipada.json relative to the "
                        "script. datasets/dwipada_consolidated.json is also "
                        "supported (its `source` field is a plain string "
                        "rather than a dict, and Schema-B records have no "
                        "`source` field at all — both shapes are handled).")
    s.add_argument("--no-by-source", action="store_true",
                   help="Skip the per-source-work breakdown.")
    s.add_argument("--output", "-o", default=None,
                   help="Optional path to write the stats dict as JSON.")
    s.add_argument("--samples", type=int, default=DEFAULT_FAILURE_SAMPLES,
                   help=f"How many sample failures to record "
                        f"(default {DEFAULT_FAILURE_SAMPLES}).")
    return parser


def _read_poem_from_args(poem_arg: Optional[str], file_arg: Optional[str]) -> str:
    """Resolve the poem text from --file, positional argument, or stdin prompt.

    Mirrors the behaviour of the original CLI so existing usage continues to
    work: a positional --poem may use the literal escape '\\n' for the line
    separator (argparse doesn't unescape it), which we convert here.
    """
    if file_arg:
        return Path(file_arg).read_text(encoding="utf-8").strip()
    if poem_arg:
        return poem_arg.replace("\\n", "\n")
    # Interactive — read until a blank line.
    print("Enter poem (2 lines, press Enter twice to finish):", file=sys.stderr)
    lines: List[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line:
            break
        lines.append(line)
    return "\n".join(lines)


def cmd_analyze(args: argparse.Namespace) -> int:
    """Handle the `analyze` subcommand. Returns process exit code."""
    poem = _read_poem_from_args(args.poem, args.file)
    if not poem.strip():
        print("Error: empty poem.", file=sys.stderr)
        return 1
    try:
        analysis = analyze_dwipada(poem)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(analysis, ensure_ascii=False, indent=2,
                         default=_json_default))
    else:
        print(format_analysis_report(analysis))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Handle the `stats` subcommand. Returns process exit code."""
    if args.input:
        json_path = Path(args.input)
    else:
        # Default: data/consolidated_dwipada.json next to this script.
        json_path = Path(__file__).resolve().parent / "data" / "consolidated_dwipada.json"

    try:
        stats = run_dataset_stats(
            json_path,
            by_source=not args.no_by_source,
            max_failure_samples=args.samples,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(format_dataset_stats_report(stats))

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )
        print(f"\nWrote JSON stats to {out_path}", file=sys.stderr)

    return 0


def _json_default(obj):
    """Fallback JSON encoder for sets and other non-default types."""
    if isinstance(obj, set):
        return sorted(obj)
    if isinstance(obj, Counter):
        return dict(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON-serialisable")


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point. Returns the process exit code."""
    parser = _build_argument_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        return cmd_analyze(args)
    if args.command == "stats":
        return cmd_stats(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
