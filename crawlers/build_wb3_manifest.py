#!/usr/bin/env python3
"""Build the batch-3 crawl manifest from discovery, resolving the book-inside-book
cases and applying the user's per-work flags (śrī-prepend, ద్విపద)."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, "crawlers")
import wikibook_crawler as wb

OUT = "/tmp/claude-1000/-home-samvaran-workspace-workspace-padyarchana-prototype/db7db891-6802-4475-a6b4-3d295c90853c/scratchpad"
disc = {r["work"]: r for r in json.load(open(f"{OUT}/wb3_manifest.json"))}

# 8 already-onboarded (exact source match) → skip
SKIP = {"పరమయోగి విలాసము", "సులక్షణసారము", "పానశాల", "శృంగార వృత్తపద్యాల శతకము",
        "శ్రీ ప్రబంధరాజ వేంకటేశ్వర విజయ విలాసము", "తాలాంకనందినీపరిణయము",
        "చంద్రికా పరిణయము", "తరికొండ నృసింహశతకము"}
# subpages whose parent is also in the list (redundant) → drop
DROP = {"రసాభరణము/ప్రథమాశ్వాసము", "శృంగారశాకుంతలము (ఎమెస్కో)/అవతారిక"}
# front-matter subpage → crawl the parent work instead
REPLACE = {"శ్రీముత్తరరామాయణము/విషయసూచిక": "శ్రీమదుత్తరరామాయణము",
           "శృంగారనైషధము/విషయసూచిక": "శృంగారనైషధము",
           "ఉషాపరిణయము/విషయసూచిక": "ఉషాపరిణయము",
           "పాండురంగమాహాత్మ్యము/": "పాండురంగమాహాత్మ్యము",
           # whole work + śrī-prepend each అంశము (user note)
           "విష్ణుపురాణము (కలిదిండి భావనారాయణ)/ప్రథమాంశము": "విష్ణుపురాణము (కలిదిండి భావనారాయణ)"}
SRI = {"విష్ణుపురాణము (కలిదిండి భావనారాయణ)", "నీలాసుందరీపరిణయము"}
DWIPADA = {"నవనాథచరిత్ర", "సౌగంధికప్రసవాపహరణము", "రాజయోగసారము", "శశికళ", "శ్రీనివాసవిలాససేవధి"}

# ---- crude Telugu→ASCII romaniser (for slug only) ----
V = {"అ":"a","ఆ":"aa","ఇ":"i","ఈ":"ii","ఉ":"u","ఊ":"uu","ఋ":"ru","ఎ":"e","ఏ":"e",
     "ఐ":"ai","ఒ":"o","ఓ":"o","ఔ":"au"}
M = {"ా":"aa","ి":"i","ీ":"ii","ు":"u","ూ":"uu","ృ":"ru",
     "ె":"e","ే":"e","ై":"ai","ొ":"o","ో":"o","ౌ":"au"}
C = {"క":"k","ఖ":"kh","గ":"g","ఘ":"gh","ఙ":"n","చ":"ch","ఛ":"chh","జ":"j","ఝ":"jh",
     "ఞ":"n","ట":"t","ఠ":"th","డ":"d","ఢ":"dh","ణ":"n","త":"t","థ":"th","ద":"d","ధ":"dh",
     "న":"n","ప":"p","ఫ":"ph","బ":"b","భ":"bh","మ":"m","య":"y","ర":"r","ల":"l","వ":"v",
     "శ":"sh","ష":"sh","స":"s","హ":"h","ళ":"l","ఱ":"r","క్ష":"ksh"}
VIR = "్"; ANU = "ం"; VIS = "ః"

def romanize(s):
    out=[]; i=0
    while i < len(s):
        ch=s[i]
        if ch in C:
            out.append(C[ch])
            if i+1 < len(s) and s[i+1]==VIR: i+=2; continue
            if i+1 < len(s) and s[i+1] in M: out.append(M[s[i+1]]); i+=2; continue
            out.append("a"); i+=1; continue
        if ch in V: out.append(V[ch]); i+=1; continue
        if ch==ANU: out.append("m"); i+=1; continue
        if ch==VIS: out.append("h"); i+=1; continue
        i+=1
    return re.sub(r"[^a-z0-9]+","_","".join(out).lower()).strip("_")

def slug_for(work, author):
    base = work.split("/")[0]
    base = re.sub(r"\s*\([^)]*\)","",base)        # drop disambiguation parens
    s = romanize(base)[:40].strip("_")
    a = romanize((author or "").split()[-1]) if author and author!="unknown" else ""
    return (s + ("_"+a if a else "")).strip("_") or "work"

# ---- assemble ----
final, used = [], set()
order = [r["work"] for r in json.load(open(f"{OUT}/wb3_manifest.json"))]
for work in order:
    if work in SKIP or work in DROP: continue
    target = REPLACE.get(work, work)
    if target in {f["work"] for f in final}: continue          # already added via replace
    rec = disc.get(target)
    if not rec or rec.get("status") != "ok":
        rec = {"work": target, "author": "", "year": "", "content_subs": wb.content_chapters(target),
               "quality": "clean", "status": "ok"}
    sub = wb.content_chapters(target) if target != work else rec.get("content_subs", [])
    slug = slug_for(target, rec.get("author"))
    k = slug
    n = 2
    while k in used:
        k = f"{slug}_{n}"; n += 1
    used.add(k)
    entry = {"slug": k, "work": target, "author": rec.get("author") or "unknown",
             "year": rec.get("year") or "unknown", "content_subs": sub,
             "force_ocr": rec.get("quality") == "ocr", "status": "ok"}
    if target in SRI: entry["sri_prepend"] = True
    if target in DWIPADA: entry["dwipada"] = True
    final.append(entry)

json.dump(final, open("crawlers/wikibook3_manifest.json", "w"), ensure_ascii=False, indent=1)
npages = sum(len(e["content_subs"]) or 1 for e in final)
print(f"manifest: {len(final)} works, {npages} content pages")
print(f"  sri_prepend: {sum(1 for e in final if e.get('sri_prepend'))} | dwipada: {sum(1 for e in final if e.get('dwipada'))} | force_ocr: {sum(1 for e in final if e['force_ocr'])}")
print("\nslug collisions:", len(final) - len(used))
for e in final[:5] + final[-3:]:
    print(f"  {e['slug'][:38]:38s} <- {e['work'][:34]}")
