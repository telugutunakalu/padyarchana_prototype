export const meta = {
  name: 'verify-shatakashityam',
  description: 'Verify each parsed śatakam JSON faithfully matches its raw blog body',
  phases: [
    { title: 'Verify', detail: 'one auditor per śatakam — fidelity, meter, author, boundaries' },
    { title: 'Synthesize', detail: 'aggregate, list śatakams needing fixes' },
  ],
}

const COUNT = (typeof args === 'string' ? JSON.parse(args) : args)?.count || 46

const SCHEMA = {
  type: 'object',
  required: ['idx', 'faithful', 'verdict', 'issues'],
  properties: {
    idx: { type: 'integer' },
    padyalu_count: { type: 'integer' },
    faithful: { type: 'boolean', description: 'true if the parsed verse lines copy the raw body verbatim with no loss/corruption/merge/split errors' },
    meter_ok: { type: 'boolean', description: 'per-padyam Chandassu matches the raw meter labels / header-declared meter, or correctly "unknown" when absent' },
    author_ok: { type: 'boolean', description: 'author_telugu correctly reflects the post title/labels (or "unknown")' },
    header_leak: { type: 'boolean', description: 'true if title/author/genre header lines leaked into a padyam' },
    verdict: { type: 'string', enum: ['good', 'minor-issues', 'needs-fix'] },
    issues: { type: 'array', items: { type: 'string' } },
  },
}

phase('Verify')
const idxs = Array.from({ length: COUNT }, (_, i) => i)
const reviews = await parallel(idxs.map((i) => () =>
  agent(
    `Audit one parsed Telugu śatakam against its raw blog source.

1. Read crawlers/shatakashityam_pairs.json — it's an array; take element index ${i}. It has {json, raw, title, author, n}.
2. Read BOTH files: the "raw" file (has body_text — the original blog post) and the "json" file (the parsed output with poems[]).
3. Verify, strictly:
   - FIDELITY: do the parsed poems[].lines_telugu copy the verse text from body_text VERBATIM? Watch for: dropped padyalu, dropped/duplicated lines within a padyam, two padyalu merged into one, one padyam split into two, the title/author/genre header lines captured as a "padyam", a padyam-number or meter-abbrev ("1.", "శా.") left stuck in the text.
   - COUNT: a śatakam should be ~100 padyalu (give or take). Flag if far off (e.g. <60 or a wildly wrong count).
   - METER: the blog marks meter as "N. శా." (per-padyam) OR declares one meter in a header like "(కందపద్య శతకము)" OR gives none. Check Chandassu is the correctly-expanded meter (శా→శార్దూలవిక్రీడితము, మ→మత్తేభవిక్రీడితము, క→కందము, చ→చంపకమాల, ఉ→ఉత్పలమాల, తే→తేటగీతి, ఆ→ఆటవెలది, సీ→సీసము) or "unknown" when the source has no meter info.
   - AUTHOR: author_telugu should match the author in the title (after the dash) or labels; "unknown" only when the source says రచయిత తెలియదు or gives none.
   - HEADER LEAK: confirm the first padyam is a real verse, not the title/author/"(కందపద్య శతకము)" line.
4. Be concrete — quote any bad padyam id/line you find. Set faithful=false if ANY fidelity problem exists.

Return the structured verdict with idx=${i}.`,
    { label: `verify:${i}`, phase: 'Verify', schema: SCHEMA }
  ).then((v) => v || { idx: i, faithful: false, verdict: 'needs-fix', issues: ['agent returned null'] })
))

const ok = reviews.filter(Boolean)
phase('Synthesize')
const bad = ok.filter((r) => r.verdict !== 'good')
const summary = await agent(
  `${ok.length} parsed śatakams were audited against their raw blog bodies.
Verdicts: ${JSON.stringify({ good: ok.filter(r=>r.verdict==='good').length, minor: ok.filter(r=>r.verdict==='minor-issues').length, needsfix: ok.filter(r=>r.verdict==='needs-fix').length })}.
Counts: faithful=${ok.filter(r=>r.faithful).length}/${ok.length}, meter_ok=${ok.filter(r=>r.meter_ok).length}, author_ok=${ok.filter(r=>r.author_ok).length}, header_leak=${ok.filter(r=>r.header_leak).length}.
Non-good items: ${JSON.stringify(bad, null, 1)}.

Write a tight engineering summary: overall fidelity, the recurring failure patterns (with the underlying cause in the parser, e.g. boundary/meter/author/header-leak), concrete parser fixes for the top issues, and a clear list of which śatakams (by idx/title) need a fix vs are clean.`,
  { label: 'synthesize', phase: 'Synthesize' }
)
return { reviews: ok, summary }
