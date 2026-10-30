# Translation brief — Parenthood: The Atlas → Spanish (reusable for French with a lexicon swap)

Target: `series/parenthood-atlas/i18n/es/`. Source of truth: the English files in `series/parenthood-atlas/`.
Linear: ARC-76. Read first: `style/lexicon.yaml`, `style/forbidden-phrases.md`, `style/jargon-to-notes.yml`,
`research/fact-checks/regional-guidelines.md`, and the English `COMPOSITION.md` / `style/voice-checklist.md` of the series.

## 1. What a translation is here
A faithful, natural, publishable translation of meaning — not word-for-word. Same paragraphs, same scenes, same argument, same
numbers, same epistemic calibration. **Do not add, drop, merge or reorder paragraphs, sections, examples or sentences of substance.**
You may split one long English sentence into two Spanish sentences. Never summarize.

## 2. Register
Neutral international Spanish, **tuteo** ("tú/tu/puedes"), no voseo, no "vosotros". Avoid peninsular-only verbs (*coger*) and
Latin-American-only slang. Warm, calm, concrete, never preachy. Gender: prefer "padres", "madre y padre", "quien cuida", "el niño",
"el bebé", "tu hijo" (generic). Decimal **comma** in prose (4,5 meses); keep the source's decimal point **inside** `` `code` `` and `$math$`.
Use angular quotes «…» for dialogue and scare quotes. Keep the em dash (—) as the source does.

## 3. Structure that MUST be preserved byte-for-byte (structural, not translatable)
- File name identical to the English source: `i18n/es/chapters/NN-slug.md`. UTF-8, **LF** line endings, no BOM.
- Heading levels and count. Movement headings keep their Roman numerals: `## I. <Spanish title>` … `## V. <Spanish title>`.
- `<aside class="chapter-takeaway">` … `</aside>` block: same shape (one `### ` title + 3 bullets). Use the fixed strings in
  `lexicon.yaml → chapter_apparatus`: title `### Conclusiones del capítulo {n}: lo que demuestra la evidencia frente a lo que puedes soltar`;
  bold labels **Lo que demuestra la evidencia:** / **Lo que puedes soltar:** / **La regla fundamental:**.
- Footnote anchors `[^chNN-key]` and their definitions: **identical keys**, same order of first appearance, same count.
- `## Notes` and `## Linked evidence cards` headings stay **literally in English** (parsers, hooks and the TTS stripper depend on them;
  the renderer shows "Notas"). Everything else in Notes is translated **except** the structural tokens `Grade:` (with its value, e.g.
  `**Grade: Moderate**`, `**Grade: Low-to-Moderate**`) and `Evidence Card:` / `Evidence Cards:` plus the backticked paths
  `` `evidence-cards/xxx.md` `` — keep those exactly. The `## Linked evidence cards` list is copied unchanged (file paths + codes);
  you may translate the free-text parentheticals.
- `$…$` / `$$…$$` math, `[x]` markers, numbers, percentages, sample sizes, author surnames, journal names and years: unchanged.
  Translate titles of papers only if an official Spanish title exists; otherwise keep English titles in *italics* (in Notes only).
- Chapter H1: `# Capítulo N — <title>` and line 2 `*<subtitle>*` using the **exact** Spanish title/subtitle from
  `i18n/es/series.yaml` for that slug.
- Do **not** translate: URLs, file paths, `[^keys]`, `evidence-cards/...` names, DOIs.

## 4. Epistemic calibration (Grade-to-Verb protocol)
The English bolds calibrated verbs. Mirror each one exactly by grade (singular/plural as the sentence needs):
High → **demuestra / confirma** (pl. **demuestran / confirman**); Moderate → **sugiere / indica** (pl. **sugieren / indican**);
Low → **se asocia con / se vincula con** (pl. **se asocian con / se vinculan con**). Keep them **bold**. Never upgrade or downgrade
certainty. Never write "la ciencia dice", "está probado", "debes", "tienes que", "hay que" outside direct quotations.

## 5. Readability gate (hard — the audit fails the chapter otherwise)
Body prose above `## Notes`: **Flesch-Szigriszt ≥ 65** (INFLESZ "bastante fácil"; ideal 65–75), **average sentence ≤ 20 words**
(hard ceiling 22), **no sentence > 40 words**. Tactics: split long English sentences; prefer short common words
(*usar*, *ver*, *tardar*) over Latinate abstractions (*utilización*, *visualización*); avoid gerund chains and stacked "de … de … de";
prefer active voice. Do **not** drop content to reach the score — split and simplify instead.

## 6. Jargon gate
Clinical terms listed in `style/jargon-to-notes.yml` must **not** appear above `## Notes`. Use the plain-language gloss the English body
already uses (e.g., "capa externa de la placenta", never *sincitiotrofoblasto*). Technical terms may live in `## Notes` only.

## 7. Forbidden phrases and leakage
No phrase from `style/forbidden-phrases.md`, no `*.md` file names, no backticked `[^footnotes]`, no harness meta-language
("escalada progresiva de lentes", "resolución causal de tres niveles") in body prose. No raw search-redirect URLs anywhere.
Never expose outline scaffolding as headings ("El rompecabezas", "Explicaciones en competencia", "El regreso", "El contrato del lector").

## 8. Directives to keep intact
Concentric 5-movement architecture; sensory opening and closing scenes; the 4-beat "Then vs. Now" set-piece (original quest →
historical orthodoxy → replication and revision → modern consensus) with the same length; epistemic boundaries and the three lenses
woven into prose (no standalone lists). Sentences that name English-language public figures, books or studies keep names as in the source.

## 9. Regional guideline footnotes (Spanish edition only)
Body prose stays universal. For Chapters 1, 3 and 4 add the extra footnote(s) whose **exact text and anchor location** are given in
`research/fact-checks/regional-guidelines.md` ("Exact footnote definitions"). They use keys `chNN-es-<slug>`; place the inline
`[^key]` at the sentence indicated and put the definition in `## Notes` in order of first appearance. **Do not write any other
regional or institutional claim; do not invent dates, quotes, guideline names, or numbers.**

## 10. Finish
Write only the target file(s). Do not edit English sources, scripts, or other languages' files. Do not run git. When finished, reply with:
word counts (EN vs ES body above Notes), list of footnote keys in ES, any place where you deliberately deviated from the source and why,
and any direct quotation you translated (so provenance can be checked).
