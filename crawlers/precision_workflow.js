export const meta = {
  name: 'verify-online-padyalu-precision',
  description: 'Judge a stratified sample of extracted blog padyalu to measure extraction precision',
  phases: [
    { title: 'Judge', detail: 'one judge per batch of ~20 padyalu' },
    { title: 'Synthesize', detail: 'precision estimate + leak patterns' },
  ],
}

const COUNT = (typeof args === 'string' ? JSON.parse(args) : args)?.count || 178
const BATCH = 20
const ranges = []
for (let i = 0; i < COUNT; i += BATCH) ranges.push([i, Math.min(i + BATCH, COUNT)])

const SCHEMA = {
  type: 'object',
  required: ['verdicts'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['i', 'real_padyam', 'verdict'],
        properties: {
          i: { type: 'integer', description: 'the item index given' },
          real_padyam: { type: 'boolean', description: 'true only if lines form a clean, complete, coherent Telugu padyam' },
          verdict: {
            type: 'string',
            enum: ['clean', 'truncated', 'prose-leak', 'merged-multi', 'missing-lines', 'garbage', 'samasya-only'],
            description: 'clean = perfect; truncated = a padam or more lost; prose-leak = discussion/praise/prose captured as verse; merged-multi = 2+ padyalu mashed together; missing-lines = padyam but some lines dropped; samasya-only = only the given problem line, no actual pūraṇa; garbage = not verse',
          },
          note: { type: 'string' },
        },
      },
    },
  },
}

phase('Judge')
const results = await parallel(ranges.map(([start, end], bi) => () =>
  agent(
    `You are auditing the PRECISION of an automated extractor that pulled Telugu padyalu (classical verse) out of blog comments on a సమస్యాపూరణం/అవధానం blog. The user wants PRECISION-FIRST output — so be strict.

Read the JSON file crawlers/precision_sample.json (an array). Judge ONLY the items with array index from ${start} to ${end - 1} inclusive (each item has an "i" field = its index).

For EACH of those items judge whether "lines" is a CLEAN, COMPLETE, COHERENT Telugu padyam (a real verse a poet submitted), correctly isolated. Problems to catch:
- prose-leak: the lines are actually prose/discussion/praise/feedback, not metrical verse.
- truncated / missing-lines: a real padyam but one or more పాదాలు are cut off or dropped (e.g. a kanda should be 4 short+long lines; a vrutta 4 padams; tetagiti/ataveladi 4; sisa 6-8). If it ends mid-word or is obviously incomplete, mark truncated.
- merged-multi: two or more separate padyalu mashed into one entry.
- samasya-only: only the GIVEN problem line(s) with no actual completion.
- garbage: not Telugu verse at all.
- clean: a complete, coherent padyam with no leak/truncation.

Set real_padyam=true ONLY for verdict "clean" (a complete coherent padyam). Everything else is real_padyam=false. Telugu padyam lines are short metrical పాదాలు; the given సమస్య line woven into the verse is fine and expected.

Return a verdict for every item in your index range ${start}–${end - 1}.`,
    { label: `judge:${start}-${end - 1}`, phase: 'Judge', schema: SCHEMA }
  ).then((r) => (r && r.verdicts) || [])
))

const all = results.filter(Boolean).flat()
phase('Synthesize')
const n = all.length
const clean = all.filter((v) => v.real_padyam).length
const byVerdict = {}
for (const v of all) byVerdict[v.verdict] = (byVerdict[v.verdict] || 0) + 1
const bad = all.filter((v) => !v.real_padyam)

const summary = await agent(
  `An extractor pulled ~161,827 Telugu padyalu from a blog. We judged a stratified sample of ${n}.
Precision (clean/total): ${clean}/${n} = ${(100 * clean / n).toFixed(1)}%.
Verdict breakdown: ${JSON.stringify(byVerdict)}.
The non-clean items (verdict + note): ${JSON.stringify(bad.slice(0, 60), null, 1)}.

Write a tight engineering assessment:
- State the measured precision and whether it is acceptable for a precision-first onboard.
- Group the failure modes (truncated / prose-leak / merged / samasya-only / garbage) by frequency and describe the PATTERN behind each (what kind of comment causes it) so the extractor can be tuned.
- Give concrete, specific tuning recommendations (regex/heuristic changes) for the top 2-3 failure modes.
- Estimate, if those fixes were applied, the likely precision.`,
  { label: 'synthesize', phase: 'Synthesize' }
)

return { sampled: n, clean, precision_pct: +(100 * clean / n).toFixed(1), byVerdict, bad, summary }
