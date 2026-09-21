# Galaxy mention extraction

These are the saved extraction instructions and output guide used with GPT-5.5
in the Codex CLI harness. They describe the historical model experiment;
`reproduce.py` reads the saved outputs without launching model calls. Bracketed
assignment/path placeholders remain unexpanded. File references inside the
historical prompt describe the original execution workspace, not additional
files required by this submission.

## Inputs and settings

- Source text: the non-empty paper text in the minty-astro-ph subset of MINT-1T;
  figures were not supplied. The case-insensitive whole-word expression
  `\b(galaxy|galaxies)\b` selected the candidate papers.
- The first wave processed 33,672 Gemini KEEP/UNSURE papers; the second processed
  all 54,227 DROP papers. All 87,899 candidates were therefore extracted. The
  historical KEEP/UNSURE-only preamble below is not a final exclusion rule.
  Both waves used identical copies of this instruction and output guide, and
  the same UAT preferred labels and concept URIs. The retained
  `gemini_decision` is a historical triage label.
- Model: `gpt-5.5`, with shell tools and a local SQLite full-text database.
  No external lookup was allowed during extraction. Temperature, seed, and
  extraction reasoning effort are not recorded in the frozen run manifests.
- Up to 10 papers per fresh worker and up to 20 concurrent workers; 8,791
  assignments across the two waves. Each wave ordered papers by
  `(-text_chars, shard, paper_id)`, assigned them to the least-loaded eligible
  batch using `(total_text_chars, paper_count, batch_index)` for ties, then
  ordered papers inside each batch by `(shard, paper_id, source_member)`.
  There was no randomized sampling at this stage.
- The final UAT allowlist is the unchanged second-wave [uat_terms.txt](uat_terms.txt).
  Preferred labels appear before the tab; the second field is the concept URI.
  The first-wave file had the same terms but a conflicting header: “Choose
  0-10 terms, ordered from most relevant to least relevant, and only choose
  terms supported by the quote/summary.” The second-wave header says 0-5;
  both output guides explicitly restrict the response to 0-5 terms.
- The prompt's 30-galaxy limit was an instruction, not a postprocessing
  truncation: the saved output retains the observed 250-row atlas exception.
  Three first-wave quote objects were split to meet the per-quote sentence
  limit, preserving their extracted evidence text.

The workers also read a planning note whose scientific scope excluded
Milky-Way-only work and named stellar streams, debris, and inferred accretion
progenitors within the Milky Way. Named non-Milky-Way galaxies could qualify
when the galaxy itself was discussed, rather than merely serving as an
environment for stars, transients, or calibration comparisons. Those choices
are reflected in the worker instructions below. The planning note's proposal
to omit triage DROP papers was superseded by the completed second wave.

## Recorded usage and runtime

These totals cover identified extraction workers (including retries) and the
two coordinating parents restricted to the recorded extraction windows. They
exclude triage, coordinate resolution, summary generation, monitoring, and
other projects. Repeated cumulative usage snapshots were not counted again.

| Token category | Count |
| --- | ---: |
| Total input, including cached input | 10,125,577,910 |
| Cached input (subset of input) | 9,288,342,912 |
| Uncached input | 837,234,998 |
| Output, including reasoning | 123,996,383 |
| Reasoning output (subset of output) | 38,694,946 |

At the recorded accounting rates of $5 per million uncached input tokens,
$0.50 per million cached input tokens, and $30 per million output tokens, this
is $12,550.237936 API-equivalent (approximately $12,600), not an API invoice.
Cached input and reasoning output must not be counted twice. The largest
observed request input was 246,671 tokens; the accounting did not apply a
long-context premium.

The two recorded run windows total 69.62292114 hours (38.30503051 plus
31.31789063 hours), approximately 70 hours. Multiplying by the maximum of 20
workers gives 1,392.45842287 nominal worker-hours; it is not measured worker
activity. The saved session-start-to-last-token durations total 684.47889167
worker-hours, also a proxy rather than compute time. The manuscript's 71-hour
value uses a different endpoint; the table and figures are not adjusted to
force that value.

## Historical worker instruction

````markdown
# GalaxyWiki GPT-5.5 Batch Subagent Instructions

Use this prompt when deploying extraction subagents for the full GalaxyWiki
GPT-5.5 pass.

Across the full run, the subagents collectively cover the papers retained by
the production prefilter:

```text
Minty astro-ph readable papers
  -> whole-word galaxy|galaxies lexical filter
  -> Gemini 3.1 Flash Lite triage
  -> Gemini KEEP or UNSURE papers only
```

The canonical input list is the orchestrator manifest for this run. The
canonical full-text source is the SQLite database supplied by the orchestrator.
Do not stream tar shards or use any paper text source other than the assigned
SQLite database.

This file intentionally does not duplicate the JSON output schema. Workers must
read and follow:

```text
[SUBAGENT_OUTPUT_GUIDE]
```

which is copied from:

```text
[PROJECT_DIR]/assets/subagentoutputguide.md
```

Replace the bracketed placeholders before spawning each subagent.

```text
You are one GalaxyWiki GPT-5.5 extraction worker in [PROJECT_DIR].

You are part of a larger parallel run over astronomy papers.
Your job is to read exactly your assigned papers and write paper-galaxy evidence
rows for named galaxy-like objects that qualify under the output guide.

You are not alone in the codebase. Other workers may be writing their own batch
output directories at the same time. Do not revert, delete, rename, or modify
files outside your assigned batch output directory. If you notice unrelated
changes elsewhere, ignore them.

You may use shell tools, python3, and uv. Do not use git. Do not call external
model APIs. Do not use SIMBAD, NED, Sesame, VizieR, ADS, arXiv, web search, or
any external lookup. Do not download or stream tar shards. Use the assigned
SQLite database as your only source for paper text.

Assignment id: [ASSIGNMENT_ID]
Assigned paper ids, in required output order: [ASSIGNED_PAPER_IDS_JSON]
Assigned shards: [ASSIGNED_SHARDS_JSON]
Assigned batch output directory: [BATCH_OUTPUT_DIR]
Run directory: [RUN_DIR]
Full-text SQLite database: [FULL_TEXT_SQLITE]
Subagent output guide: [SUBAGENT_OUTPUT_GUIDE]
UAT allowlist: [UAT_TERMS_PATH]

Before extracting, read:
- [SUBAGENT_OUTPUT_GUIDE]
- [UAT_TERMS_PATH]
- [PROJECT_DIR]/notes/full_galaxywiki_prefilter_plan_2026-05-17.md

The prefilter intentionally excludes Milky-Way-only papers from GalaxyWiki. Do
not emit the Milky Way, the Galaxy, Galactic structure, Galactic disk, Galactic
halo, Galactic bulge, Galactic center, Galactic ISM, Galactic stellar
populations, or objects inside the Milky Way as GalaxyWiki galaxy rows.

Also reject Milky-Way fossil-record / Galactic-archaeology structures as
GalaxyWiki rows. Do not emit named stellar streams, halo substructures,
accreted debris clouds, inferred merger progenitors, or accretion-event labels
inside the Milky Way, such as Gaia Sausage/Enceladus, Sequoia, Thamnos, Helmi
streams, or similar objects, unless the paper is directly discussing a named
surviving non-Milky-Way galaxy.

Named non-Milky-Way galaxies may qualify when the paper directly discusses the
galaxy itself. This includes M31, M33, the Magellanic Clouds, named dwarf
galaxies, named AGN hosts, named lensed galaxies, high-redshift galaxy
candidates, merger remnants, and other galaxy-like objects, as defined by the
output guide.

Your task:

1. Query only your assigned papers from [FULL_TEXT_SQLITE].
2. Process papers in exactly the order listed in [ASSIGNED_PAPER_IDS_JSON].
3. For each paper, decide which named galaxy-like objects qualify under
   [SUBAGENT_OUTPUT_GUIDE].
4. Write exactly the files required by [SUBAGENT_OUTPUT_GUIDE] inside
   [BATCH_OUTPUT_DIR] only.
5. Validate your files before finishing.

The SQLite database has a `papers` table with at least these columns:

papers(
  paper_id TEXT PRIMARY KEY,
  shard TEXT NOT NULL,
  source_member TEXT NOT NULL,
  text_chars INTEGER,
  text_utf8_bytes INTEGER,
  full_text TEXT NOT NULL
)

It may include extra metadata columns from the manifest or Gemini triage. Ignore
extra columns unless useful for accounting. Query by paper_id using parameter
binding. Do not rely on the sqlite3 shell being installed; use Python's
standard sqlite3 module if needed.

Use a query shaped like:

SELECT
  paper_id,
  shard,
  source_member,
  text_chars,
  text_utf8_bytes,
  full_text
FROM papers
WHERE paper_id IN (...)

Then reorder the returned rows to match [ASSIGNED_PAPER_IDS_JSON].

Important extraction rules:

- Follow [SUBAGENT_OUTPUT_GUIDE] as the authority for acceptance rules, field
  names, output files, JSONL formatting, sentence counts, evidence quotes,
  summaries, discussion_extent, coordinates, paper_status rows, and
  run_summary.
- Emit paper-galaxy evidence rows only. Do not make final wiki pages.
- Do not deduplicate galaxies across papers.
- Do not canonicalize names using outside knowledge.
- Use the raw name exactly as the paper uses it.
- Include aliases only when the same paper explicitly states them.
- Include coordinates only when the paper explicitly states coordinates for
  that object.
- Use only exact UAT preferred labels from [UAT_TERMS_PATH].
- Keep evidence compact. If a paper discusses one galaxy throughout, choose
  representative evidence instead of quoting the whole paper.
- Do not emit more than 30 accepted galaxy rows for a single paper.
- Prefer precision over recall when the output guide is not satisfied.

Required output location:

Write all final batch files directly inside:

[BATCH_OUTPUT_DIR]

Do not write final files anywhere else. Temporary scratch files are allowed only
inside [BATCH_OUTPUT_DIR] and should be removed or clearly marked as temporary
before finishing.

Validation before finishing:

- Confirm the required output files exist.
- Confirm every JSONL line and run_summary.json parse as valid JSON.
- Confirm every assigned paper appears exactly once in paper_status.jsonl.
- Confirm no unassigned paper appears in outputs.jsonl or paper_status.jsonl.
- Confirm the main counts in paper_status.jsonl, outputs.jsonl, and
  run_summary.json agree.
- Do a quick sanity check that accepted rows follow [SUBAGENT_OUTPUT_GUIDE].

If a paper cannot be processed because text is missing, empty, or malformed,
write an error status for that paper rather than skipping it.

In your final reply, report:
- files written
- assigned paper count
- accepted, rejected, and error paper counts
- accepted paper-galaxy row count
- validation status
- any uncertainty or notable borderline decisions
```

## Placeholder Reference

- `[PROJECT_DIR]`: absolute project directory, e.g.
  `<PROJECT_ROOT>`.
- `[RUN_DIR]`: absolute run directory, e.g.
  `<PROJECT_ROOT>/results/full_galaxywiki_gpt55_batches/<RUN_ID>`.
- `[FULL_TEXT_SQLITE]`: absolute path to the run's GPT-target full-text SQLite
  database.
- `[SUBAGENT_OUTPUT_GUIDE]`: absolute path to the run-copied output guide,
  usually `[RUN_DIR]/subagentoutputguide.md`.
- `[UAT_TERMS_PATH]`: absolute path to the run-copied UAT allowlist, usually
  `[RUN_DIR]/uat_galaxy_terms.txt`.
- `[ASSIGNMENT_ID]`: `batch-0000`, `batch-0001`, etc.
- `[ASSIGNED_PAPER_IDS_JSON]`: JSON array of paper ids assigned to this batch.
- `[ASSIGNED_SHARDS_JSON]`: JSON array of shard names represented in this batch.
- `[BATCH_OUTPUT_DIR]`: absolute directory where the worker writes the batch
  output files.
````

## Historical output guide

The guide below is the response contract; extraction used this Markdown guide,
not a separately enforced JSON Schema.

````markdown
# GalaxyWiki Subagent Output Guide

## Goal

Read each paper and output **paper-galaxy evidence rows**.

A row means:

> This paper directly discusses this named galaxy or galaxy-like object in at least 3 substantive prose sentences, and the row records the evidence.

Do not make final wiki pages.
Do not deduplicate galaxies across papers.
Do not canonicalize names using outside knowledge.
Do not use SIMBAD, NED, or external lookup.
Entity resolution happens later.

---

# Files to write

Each batch must write three files:

```text
outputs.jsonl
paper_status.jsonl
run_summary.json
```

`outputs.jsonl` contains one row per accepted paper-galaxy pair.

Do not write more than 30 `outputs.jsonl` rows for any single paper.

`paper_status.jsonl` contains exactly one row per processed paper, with status `accepted`, `rejected`, or `error`.

`run_summary.json` contains batch-level counts.

---

# Acceptance rule

Accept a galaxy only if all of the following are true:

1. The object is identified by a name, catalog/source designation, paper-local name, or explicit coordinates used as an object identifier.
2. The object is a galaxy or galaxy-like object.
3. The paper contains at least **3 direct prose sentences** about that object.
4. The paper contains exact evidence text that can support a concise summary of what the paper says about the object.

Reject table-only, bibliography-only, figure-label-only, sample-list-only, and generic population mentions with less than three sentences.

If more than 30 galaxy-like objects in one paper appear to qualify, emit at
most 30 rows for that paper. Choose the 30 best-supported and most substantively
discussed objects, prioritizing objects central to the paper over appendix,
atlas, or survey-description entries.

---

# What counts as a galaxy-like object?

Accept named objects such as:

```text
NGC 3923
M31
B2 0648+27
SDSS J...
WISEA J...
GN-z11
```

The object can be a galaxy, galaxy candidate, dwarf galaxy, radio galaxy, AGN host galaxy, interacting galaxy, merger remnant, high-redshift galaxy candidate, etc. This list is not comprehensive, use your own judgement.

The word “galaxy” does not need to appear in the object name.

---

# What does not count?

Reject:

```text
generic galaxy populations
host galaxies with no name, source designation, paper-local name, or coordinates used as an identifier
clusters or groups without individually discussed named galaxies
table-only catalog entries
bibliography-only mentions
figure-label-only mentions
sample membership only
pure simulations unless explicitly about real or observed named galaxies
non-galaxy objects only
```

A sentence like “NGC 3923 is in our sample” does not count as substantive discussion.

---

# Sentence counting rule

Use:

```json
"total_evidence_sentence_count": 3
```

This counts the number of direct galaxy-specific prose sentences in the selected evidence quotes.

It does not need to count every sentence in the whole paper.

If the whole paper is about one galaxy, choose a representative quote and set:

```json
"discussion_extent": "paper_focus"
```

---

# Evidence quote rule

Each accepted row may include 1–3 evidence quotes.

Each quote should contain 1–5 direct discussion sentences.

Across all evidence quotes, `total_evidence_sentence_count` must be between 3 and 8.

Never include more than 8 direct discussion sentences for one paper-galaxy row.

If you select 6–8 evidence sentences, split them across 2–3 quote objects.
Do not put 6 or more counted sentences in a single quote object.

If the paper contains more than 8 relevant sentences about the galaxy, choose the most representative evidence sentences rather than quoting everything.

---

# Summary rule

The summary should describe the main object-specific claims the paper makes about the galaxy.

Aim for 20–40 words.

Do not exceed 40 words.

The summary may be one sentence or two short sentences, but it should stay compact.

Every major claim in the summary must be supported by the evidence quotes.

---

# `outputs.jsonl`

Write one row per accepted paper-galaxy pair.

Example:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "150X_XXXXX",
  "source_member": "150X_XXXXX.json",

  "raw_name": "NGC XXXX",
  "aliases_in_paper": [],

  "summary": "The paper describes NGC XXXX as a disturbed post-merger galaxy, linking its blue shell knots, counter-rotating central disk, and metal-rich tidal plume to debris from a gas-rich dwarf accreted 1.2 Gyr ago.",

  "evidence_quotes": [
    {
      "quote": "Deep optical imaging reveals a system of asymmetric blue shell knots around NGC XXXX. The knots are concentrated along the eastern side of the galaxy and have colors consistent with a young stellar population superposed on older tidal debris.",
      "evidence_sentence_count": 2
    },
    {
      "quote": "Integral-field spectroscopy shows that the central stellar disk counter-rotates relative to the outer body of NGC XXXX. We also detect a faint tidal plume whose metallicity declines smoothly with radius, suggesting that the material originated in a gas-rich dwarf companion accreted roughly 1.2 Gyr ago.",
      "evidence_sentence_count": 2
    }
  ],

  "total_evidence_sentence_count": 4,
  "discussion_extent": "short_paragraph",

  "uat_terms": ["Galaxy interactions"],

  "paper_coordinates": {
    "ra": "06h52m02.50s",
    "dec": "+27d27m39.4s",
    "coordinate_text": "RA = 06h52m02.50s, Dec = +27d27m39.4s"
  }
}
```

---

# Field rules

## `raw_name`

Use the name exactly as the paper uses it.

Do not canonicalize.

Good:

```json
"raw_name": "B2 XXX+XX"
```

Do not replace it with another catalog name unless the paper itself uses that name.

## `aliases_in_paper`

Other names explicitly stated in the same paper.

Use `[]` if none.

## `evidence_quotes`

Each quote object must contain:

```json
{
  "quote": "Exact evidence sentences copied from full_text.",
  "evidence_sentence_count": 3
}
```

The quote must be exact paper text, with only minor whitespace normalization allowed.

The sentence count is the number of direct object-specific prose sentences inside that quote.

## `total_evidence_sentence_count`

Total number of direct discussion sentences across all evidence quotes.

Must be between 3 and 8 for accepted rows.

This must equal the sum of `evidence_sentence_count` across all evidence quotes.

This counts only the selected evidence quotes, not every sentence in the paper about the object.

If the paper contains more than 8 relevant sentences about the galaxy, choose the most representative evidence sentences rather than quoting everything.

## `discussion_extent`

Use one of:

```text
exactly_three_sentences
short_paragraph
multiple_paragraphs
section
paper_focus
unclear_but_qualifies
```

Use `paper_focus` when the paper is mainly or entirely about the galaxy.

## `uat_terms`

Use 0–5 relevant astronomy terms.

Examples:

```json
["Radio galaxies", "Galaxy mergers", "Tidal tails"]
```

Only include terms supported by the paper. These should come from uat_galaxy_terms.txt located at [LOCATION OF uat_galaxy_terms.txt].

Use only the exact preferred-label text before the tab in the allowlist. If no
exact supported term is present in the allowlist, use `[]` rather than inventing
a near match.

## `paper_coordinates`

Only include coordinates if stated in the paper, otherwise put as null.

Do not look them up.

If absent:

```json
"paper_coordinates": {
  "ra": null,
  "dec": null,
  "coordinate_text": null
}
```

---

# `paper_status.jsonl`

Write exactly one row per processed paper.

This file is for accounting and auditing. It should not duplicate the full galaxy evidence rows from `outputs.jsonl`.

## Accepted paper

If the paper has one or more accepted galaxy rows:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "1505_XXXXX",
  "source_member": "1505_XXXXX.json",

  "status": "accepted",
  "accepted_galaxy_row_count": 3,
  "rejection_reason": null
}
```

## Rejected paper

If the paper has no accepted galaxy rows:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "1505_XXXXX",
  "source_member": "1505_XXXXX.json",

  "status": "rejected",
  "accepted_galaxy_row_count": 0,
  "rejection_reason": "No named galaxy is discussed in three or more direct prose sentences."
}
```

## Error paper

If the paper cannot be processed:

```json
{
  "shard": "data/astro-ph-0005X.tar",
  "paper_id": "1505_XXXXX",
  "source_member": "1505_XXXXX.json",

  "status": "error",
  "accepted_galaxy_row_count": 0,
  "rejection_reason": "The paper text was missing, empty, or malformed."
}
```

Allowed `status` values:

```text
accepted
rejected
error
```

`rejection_reason` is a string with less than 10 words.

Use `null` for `rejection_reason` when `status` is `accepted`.

---

# `run_summary.json`

Write one object per batch.

```json
{
  "run_id": "20260517T041000Z",
  "batch_id": "batch-005X",

  "input_paper_count": 10,
  "processed_paper_count": 10,
  "accepted_paper_count": 9,
  "rejected_paper_count": 1,
  "error_paper_count": 0,
  "accepted_galaxy_row_count": 17
}
```

---

# JSONL rules

Every line in every `.jsonl` file must be valid JSON.

Do not include Markdown in JSONL files.

Do not include comments.

Do not include trailing commas.

Use double quotes for strings.

Use `null` for missing optional values.

Use `[]` for empty lists.

---

# Final checklist

Before outputting an accepted row, confirm:

```text
The object has a name, catalog/source designation, paper-local name, or coordinates used as an identifier.
The object is galaxy-like.
The paper has at least 3 direct prose sentences about it.
The paper has no more than 30 accepted galaxy rows.
The quote is exact paper text.
The summary states how the paper describes the galaxy.
The raw name is not canonicalized.
Coordinates are included only if stated in the paper.
The JSON is valid.
```
````
