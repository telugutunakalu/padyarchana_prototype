"""
Repair the handful of padyalu_json_data/*.json files that have malformed
JSON. Two patterns are fixed:

  1. Bare backslashes before non-escape characters (e.g. '\\\\न' from
     transliteration artifacts) — these are stripped. JSON only allows
     backslash before " / \\ b f n r t u.
  2. Trailing commas before ] or } — JSON forbids them.

The fixes are idempotent: running on already-clean JSON is a no-op.

Run once locally; the cleaned files are committed.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
TARGETS = [
    "padyalu_json_data/agha_vinasha_satakam.json",
    "padyalu_json_data/narayana_satakam.json",
    "padyalu_json_data/sampangimanna_satakam.json",
    "padyalu_json_data/vemana_201_299.json",
    "padyalu_json_data/vemana_301_467.json",
]

# Match ONE OR MORE backslashes immediately before a non-JSON-escape
# character (e.g. a Telugu code point). Handles both '\न' and '\\न'
# variants of the same transliteration artifact.
_BARE_BACKSLASH = re.compile(r'\\+(?=[^"/\\bfnrtu])')

# Trailing comma before ] or } (with optional whitespace).
_TRAILING_COMMA = re.compile(r",(\s*[\]\}])")


def fix(text: str) -> str:
    text = _BARE_BACKSLASH.sub("", text)
    text = _TRAILING_COMMA.sub(r"\1", text)
    return text


def main():
    rc = 0
    for rel in TARGETS:
        path = ROOT / rel
        if not path.exists():
            print(f"  {rel}: SKIP (missing)")
            continue
        original = path.read_text(encoding="utf-8")
        fixed = fix(original)
        if fixed == original:
            # Still confirm it parses
            try:
                json.loads(original)
                print(f"  {rel}: already clean")
            except json.JSONDecodeError as e:
                print(f"  {rel}: WARN — still fails to parse ({e})")
                rc = 1
            continue
        # Verify the fix actually parses before writing.
        try:
            json.loads(fixed)
        except json.JSONDecodeError as e:
            print(f"  {rel}: ABORT — fix didn't make it parse ({e})")
            rc = 1
            continue
        path.write_text(fixed, encoding="utf-8")
        delta = len(original) - len(fixed)
        print(f"  {rel}: fixed, {delta:+} bytes")
    return rc


if __name__ == "__main__":
    sys.exit(main())
