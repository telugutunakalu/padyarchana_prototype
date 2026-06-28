/*
 * chandam_headless_scan.mjs — headless chandassu scanner.
 *
 * Runs the real Chandam engine (static/chandam/chandam.te.app.min.js, the same
 * one the website uses) inside jsdom under Node, so we can metrically scan tens
 * of thousands of poems with no browser. For each poem it records the detected
 * meter ONLY when the verse scans a perfect 100% (engine `matched`), which is
 * the high-precision signal the gold pipeline reclassifies on.
 *
 * యతి: experimentalSandhi=true  ⇒  "అచ్చు ఆధారంగా సంధియుత యతి మైత్రి గుర్తింపు"
 * (vowel-based sandhi yati-maitri) is ENABLED, alongside the normal yati + prasa
 * checks. Change OPTS below to alter that.
 *
 * Usage:
 *   npm --prefix scripts install        # one-time: installs jsdom (~16 MB)
 *   node scripts/chandam_headless_scan.mjs <chunks_dir> [pairs_out_dir]
 *
 * <chunks_dir> holds chunk_*.json files of [{id, text}, ...] (see
 * gold_unknown_export.py). Output: pairs_NNN.json of [[id, meterName], ...] for
 * the 100%-matches, which scripts/gold_unknown_apply.py then applies. Resumable:
 * a chunk whose pairs file already exists is skipped.
 */
import { JSDOM, VirtualConsole } from "jsdom";
import { readFileSync, writeFileSync, readdirSync, existsSync, mkdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join, resolve } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");
const CH = join(ROOT, "static", "chandam");

const chunksDir = process.argv[2] || join(ROOT, "static", "_goldscan_unknown");
const pairsDir = process.argv[3] || join(chunksDir, "pairs");
mkdirSync(pairsDir, { recursive: true });

// --- boot the engine inside jsdom ------------------------------------------
const vc = new VirtualConsole();
vc.on("jsdomError", () => {});            // the engine's init is noisy; ignore
const dom = new JSDOM("<!DOCTYPE html><html><head></head><body></body></html>",
  { runScripts: "dangerously", virtualConsole: vc, pretendToBeVisual: true, url: "http://localhost/" });
const w = dom.window;
const inject = (code) => {
  const s = w.document.createElement("script");
  s.textContent = code;
  w.document.head.appendChild(s);
};
inject(readFileSync(join(CH, "chandam.te.app.min.js"), "utf8"));
inject(readFileSync(join(CH, "chandam-lib.js"), "utf8"));
await w.Chandam.ready();
console.log("engine ready:", w.Chandam.isReady());

const OPTS = {
  language: 0,              // telugu
  quickMatch: true,
  matchYati: true,
  matchPrasa: true,
  allowSantiPrasa: false,
  experimentalSandhi: true, // అచ్చు ఆధారంగా సంధియుత యతి మైత్రి గుర్తింపు
  includeRare: true,        // also search rare vṛttas
};

// --- scan -------------------------------------------------------------------
const chunks = readdirSync(chunksDir).filter((f) => /^chunk_\d+\.json$/.test(f)).sort();
if (!chunks.length) { console.error(`no chunk_*.json in ${chunksDir}`); process.exit(1); }

let total = 0, matched = 0, errors = 0;
const meterCounts = {};
const t0 = Date.now();
for (const cf of chunks) {
  const idx = cf.match(/(\d+)/)[1];
  const outFile = join(pairsDir, `pairs_${idx}.json`);
  const poems = JSON.parse(readFileSync(join(chunksDir, cf), "utf8"));
  if (existsSync(outFile)) {                          // resume
    const prev = JSON.parse(readFileSync(outFile, "utf8"));
    matched += prev.length; total += poems.length;
    console.log(`  ${cf}: SKIP (already ${prev.length})`);
    continue;
  }
  const pairs = [];
  for (const p of poems) {
    total++;
    let r = null;
    try { r = w.Chandam.analyze(p.text, OPTS); } catch (e) { errors++; continue; }
    if (r && r.matched && r.meter && r.meter.name) {
      pairs.push([p.id, r.meter.name]);
      matched++;
      meterCounts[r.meter.name] = (meterCounts[r.meter.name] || 0) + 1;
    }
  }
  writeFileSync(outFile, JSON.stringify(pairs));
  const el = (Date.now() - t0) / 1000;
  console.log(`  ${cf}: ${pairs.length}/${poems.length} matched | cumulative ${matched}/${total}` +
              ` | ${el.toFixed(0)}s | ${(el * 1000 / total).toFixed(1)} ms/poem`);
}

console.log(`\nDONE: ${matched}/${total} matched 100% (errors ${errors}) in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
console.log("detected-meter distribution:");
for (const [m, c] of Object.entries(meterCounts).sort((a, b) => b[1] - a[1])) {
  console.log(`  ${String(c).padStart(6)}  ${m}`);
}
process.exit(0);
