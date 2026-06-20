"""
Batch import all JSON files from padyalu_json_data/ into padyarchana.db.
Reuses import_poems_from_json() from import_json.py.

Usage:
    python scripts/batch_import_json.py              # Import all eligible files
    python scripts/batch_import_json.py --dry-run    # List files without importing
"""
import asyncio
import argparse
import json
import re
import sys
import traceback
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from app.database import engine, Base, AsyncSessionLocal
from app.models import Poet, Meter, Poem
from scripts.import_json import import_poems_from_json, ensure_tables_exist

# ── Files to skip (duplicates and Vemana subsets) ──────────────────────────
SKIP_FILES = {
    # Vemana partial/subset files — vemana_master.json is the comprehensive source
    "vemana_100.json",
    "vemana_200.json",
    "vemana_1_150.json",
    "vemana_1_279.json",
    "vemana_150_300.json",
    "vemana_201_299.json",
    "vemana_301_467.json",
    "vemana_satakam_300_400.json",
    "vemana_satakam_401_418.json",
    # Explicit duplicate
    "bhakta_mandara_satakam_duplicate.json",
}

# ── Literary form overrides for non-shatakam works ─────────────────────────
LITERARY_FORM_OVERRIDES = {
    "narayana_dwipada.json": "ద్విపద",
    "kuchelopakyanam.json": "కావ్యం",
    "krishivaludu.json": "ఖండకావ్యం",
    "trunakankanam.json": "ఖండకావ్యం",
    "rammohana_ramyasukthi.json": "రమ్య సూక్తి",
    "bhatruhari_1.json": "శతకం",
    "bhatruhari_2.json": "శతకం",
    "bhatruhari_3.json": "శతకం",
}


def load_json_with_repair(file_path: str) -> dict:
    """Load JSON, attempting repair for common encoding issues."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fix trailing commas before ] or }
        repaired = re.sub(r',\s*(\])', r'\1', content)
        repaired = re.sub(r',\s*(\})', r'\1', repaired)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            # Remove stray backslashes before non-JSON-escape characters
            # (common data error: \న instead of న in Telugu text)
            # Step 1: Protect valid \\ pairs with placeholder
            repaired = repaired.replace('\\\\', '\x00DBL_BS\x00')
            # Step 2: Remove lone backslashes before invalid escape chars
            repaired = re.sub(r'\\(?!["\\/bfnrtu])', '', repaired)
            # Step 3: Restore double backslashes
            repaired = repaired.replace('\x00DBL_BS\x00', '\\\\')
            return json.loads(repaired)


def print_summary(results, errors, skipped_files):
    """Print a comprehensive summary report."""
    total_imported = sum(r["imported"] for r in results)
    total_skipped_dup = sum(r["skipped"] for r in results)
    total_files_ok = len(results)
    total_files_err = len(errors)

    print(f"\n{'='*70}")
    print(f"  పద్యార్చన - BATCH IMPORT SUMMARY")
    print(f"{'='*70}")
    print(f"  Files processed successfully : {total_files_ok}")
    print(f"  Files with errors            : {total_files_err}")
    print(f"  Files skipped (exclusion)    : {len(skipped_files)}")
    print(f"  Total poems imported         : {total_imported}")
    print(f"  Total poems skipped (dups)   : {total_skipped_dup}")

    print(f"\n  {'─'*64}")
    print(f"  Per-file breakdown:")
    print(f"  {'─'*64}")
    for r in results:
        fname = Path(r["file"]).name
        print(f"    {fname:45s} +{r['imported']:4d}  skip={r['skipped']}")

    if errors:
        print(f"\n  {'─'*64}")
        print(f"  ERRORS:")
        print(f"  {'─'*64}")
        for e in errors:
            print(f"    {e['file']}: {e['error']}")

    print(f"{'='*70}\n")


async def verify_import():
    """Print DB stats after import."""
    async with AsyncSessionLocal() as db:
        total_poems = (await db.execute(select(func.count(Poem.id)))).scalar()
        total_poets = (await db.execute(select(func.count(Poet.id)))).scalar()
        total_meters = (await db.execute(select(func.count(Meter.id)))).scalar()

        print(f"  Database totals:")
        print(f"    Poems  : {total_poems}")
        print(f"    Poets  : {total_poets}")
        print(f"    Meters : {total_meters}")

        # Poems by literary form
        rows = (await db.execute(
            select(Poem.literary_form, func.count(Poem.id))
            .group_by(Poem.literary_form)
        )).all()
        print(f"\n  Poems by literary form:")
        for form, count in rows:
            print(f"    {form or 'NULL':20s}: {count}")

        # Top 10 sources
        rows = (await db.execute(
            select(Poem.source, func.count(Poem.id))
            .group_by(Poem.source)
            .order_by(func.count(Poem.id).desc())
            .limit(10)
        )).all()
        print(f"\n  Top 10 sources:")
        for source, count in rows:
            print(f"    {source:40s}: {count}")


async def batch_import(data_dir: str, dry_run: bool = False):
    """Process all JSON files in data_dir."""
    data_path = Path(data_dir)
    all_files = sorted(data_path.glob("*.json"))

    # Partition into eligible and skipped
    skipped_files = []
    eligible_files = []
    for f in all_files:
        if f.name in SKIP_FILES:
            skipped_files.append(f)
        else:
            eligible_files.append(f)

    print(f"\n{'='*70}")
    print(f"  పద్యార్చన (Padyarchana) - Batch JSON Importer")
    print(f"{'='*70}")
    print(f"  Total JSON files found : {len(all_files)}")
    print(f"  Files to skip          : {len(skipped_files)}")
    print(f"  Files to import        : {len(eligible_files)}")

    if dry_run:
        print(f"\n  DRY RUN — no changes will be made.\n")
        for f in eligible_files:
            literary_form = LITERARY_FORM_OVERRIDES.get(f.name, "శతకం")
            print(f"    {f.name:45s} [{literary_form}]")
        print(f"\n  Skipped files:")
        for f in skipped_files:
            print(f"    {f.name}")
        return

    # Ensure tables exist
    await ensure_tables_exist()

    results = []
    errors = []

    async with AsyncSessionLocal() as db:
        for i, f in enumerate(eligible_files, 1):
            print(f"\n[{i}/{len(eligible_files)}] {f.name}")
            try:
                # Load and repair JSON
                data = load_json_with_repair(str(f))

                # Determine literary form
                literary_form = LITERARY_FORM_OVERRIDES.get(f.name, "శతకం")

                result = await import_poems_from_json(
                    db,
                    str(f),
                    default_meter_name="Unknown",
                    literary_form=literary_form,
                    data=data,
                )
                results.append(result)

            except Exception as e:
                error_info = {
                    "file": f.name,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
                errors.append(error_info)
                print(f"  ERROR: {e}")
                await db.rollback()

    # Summary
    print_summary(results, errors, skipped_files)
    await verify_import()
    await engine.dispose()


async def main():
    parser = argparse.ArgumentParser(description="Batch import JSON poems into padyarchana.db")
    parser.add_argument("--dry-run", action="store_true", help="List files without importing")
    parser.add_argument("--data-dir", default="padyalu_json_data", help="Path to JSON data folder")
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / args.data_dir
    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    await batch_import(str(data_dir), dry_run=args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
