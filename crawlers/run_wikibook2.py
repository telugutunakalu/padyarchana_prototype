import sys, json
from pathlib import Path
sys.path.insert(0, "crawlers")
import wikibook_crawler as wb
wb.OUT = Path("crawlers/wikibook2_json")          # stage, don't auto-mix with corpus
m = json.load(open("crawlers/wikibook2_manifest.json"))
results = []
for rec in m:
    if rec.get("status") != "ok":
        continue
    print(f"\n## {rec['work']} ({rec.get('author')})", flush=True)
    results.append(wb.crawl_book(rec))
print(f"\n=== TOTAL: {sum(r['padyalu'] for r in results)} padyalu across {len(results)} works ===")
json.dump(results, open("crawlers/wikibook2_results.json", "w"), ensure_ascii=False, indent=1)
