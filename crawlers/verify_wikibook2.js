export const meta = {
  name: 'verify-wikibooks',
  description: 'Adversarial quality review of the crawled Wikisource padyalu JSONs',
  phases: [
    { title: 'Review', detail: 'one reviewer per book — coherence, metadata, structure' },
    { title: 'Synthesize', detail: 'aggregate verdicts, list books needing attention' },
  ],
}

// args = [{slug, work, author, year, count, flag}, ...]
const books = typeof args === 'string' ? JSON.parse(args) : args

const VERDICT = {
  type: 'object',
  required: ['slug', 'coherence', 'metadata_ok', 'verdict', 'issues'],
  properties: {
    slug: { type: 'string' },
    padyalu_count: { type: 'integer' },
    coherence: {
      type: 'string',
      enum: ['clean', 'mostly-clean', 'garbled-ocr', 'prose-not-verse', 'mixed'],
      description: 'Overall Telugu verse quality of the sampled padyalu',
    },
    metadata_ok: { type: 'boolean' },
    metadata_note: { type: 'string' },
    ocr_flag_present: { type: 'boolean' },
    ocr_flag_appropriate: { type: 'boolean', description: 'Is the OCR-sourced flag correctly present/absent for this quality?' },
    structural_issues: {
      type: 'array', items: { type: 'string' },
      description: 'e.g. front-matter bled into a verse, prose captured as padyam, empty/duplicate lines, broken couplet, makutam inconsistency',
    },
    issues: { type: 'array', items: { type: 'string' } },
    verdict: { type: 'string', enum: ['good', 'minor-issues', 'needs-fix', 'drop'] },
    recommendation: { type: 'string' },
  },
}

phase('Review')
const reviews = await parallel(books.map((b) => () =>
  agent(
    `You are auditing one structured-JSON output of a Telugu poetry (పద్యం) crawler before it is onboarded into a database.

File: crawlers/wikibook2_json/${b.slug}.json
Work: ${b.work} — author "${b.author}", year ${b.year}. Reported padya count: ${b.count}. File flag: ${b.flag || '(none)'}.

Do this:
1. Read the JSON file (use the Read or Bash/python tool).
2. Sample padyalu spread across the file — the FIRST 4, 4 from the MIDDLE, and the LAST 4. For each, look at "lines_telugu", "Chandassu", "chapter", "padyam_number".
3. Judge, skeptically:
   - COHERENCE: Are the lines coherent classical Telugu verse, or OCR-garbled, or actually prose (not metered verse), or mixed? Telugu padyalu lines are short metrical పాదాలు. Watch for: garbled aksharas, Latin/symbol leakage, prose sentences, front-matter/title/colophon/publisher text captured as a "padyam", a table-of-contents or glossary captured as verses, near-empty or 1-character lines, the SAME makutam line repeated (normal for śatakams) vs random repetition.
   - For ద్విపద (Chandassu="ద్విపద") works each poem should be ~2 lines (a couplet) — flag if couplets look mis-paired (a heading or half-line stuck in).
   - METADATA: Is author/year/literary_form present and plausible for this work?
   - OCR FLAG: Given the actual text quality you observed, is the file flag (${b.flag || 'none'}) appropriate? (garbled => should be OCR-sourced; clean => should NOT be flagged.)
4. Be concrete: quote the specific bad padyam ids/lines you find. Do not pass a file just because it has many poems — sample real content.

Return the structured verdict. Use verdict="good" only if the sampled padyalu are coherent verse with correct metadata; "drop" only if it is essentially not salvageable Telugu padyalu (prose/garbage).`,
    { label: `review:${b.slug}`, phase: 'Review', schema: VERDICT }
  ).then((v) => ({ ...b, ...(v || {}) }))
))

const ok = reviews.filter(Boolean)
phase('Synthesize')
const summary = await agent(
  `Here are ${ok.length} per-book audit verdicts (JSON) for a batch of crawled Telugu poetry files:\n\n` +
  JSON.stringify(ok.map((r) => ({
    slug: r.slug, work: r.work, count: r.padyalu_count ?? r.count,
    coherence: r.coherence, metadata_ok: r.metadata_ok, ocr_flag_appropriate: r.ocr_flag_appropriate,
    verdict: r.verdict, issues: r.issues, structural_issues: r.structural_issues,
    recommendation: r.recommendation,
  })), null, 1) +
  `\n\nWrite a concise engineering summary for the human:
- Group books by verdict (good / minor-issues / needs-fix / drop).
- For every book that is NOT "good", give a one-line actionable note (what's wrong + suggested fix).
- Call out any systemic patterns across books (e.g. a recurring front-matter bleed, a meter mislabel, an OCR flag that should/shouldn't be set).
- End with a clear KEEP list and DROP list.`,
  { label: 'synthesize', phase: 'Synthesize' }
)

return { reviews: ok, summary }
