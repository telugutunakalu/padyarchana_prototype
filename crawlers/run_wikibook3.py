import json, sys
from pathlib import Path
sys.path.insert(0, "crawlers")
import wikibook_crawler as wb
wb.OUT = Path("crawlers/wikibook3_json")
wb.MANIFEST = json.load(open("crawlers/wikibook3_manifest.json"))
results = []
for rec in wb.MANIFEST:
    if rec.get("status") != "ok":
        continue
    print(f"\n## {rec['work']} ({rec.get('author')})", flush=True)
    try:
        results.append(wb.crawl_book(rec))
    except Exception as e:
        print(f"  !! ERROR {rec['slug']}: {e}", flush=True)
print(f"\n=== TOTAL: {sum(r['padyalu'] for r in results)} padyalu across {len(results)} books ===")
json.dump(results, open("crawlers/wikibook3_results.json", "w"), ensure_ascii=False, indent=1)
